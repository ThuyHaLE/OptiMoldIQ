# modules/validation_module.py

from pathlib import Path
from typing import Dict, List, Optional
from modules.base_module import BaseModule, ModuleResult
from loguru import logger
from dataclasses import asdict
from agents.validationOrchestrator.validation_orchestrator import SharedSourceConfig, ValidationOrchestrator

class ValidationModule(BaseModule):
    """
    Module wrapper for ValidationOrchestrator.
    
    Handles validation pipeline.
    """
    
    DEFAULT_CONFIG_PATH = 'configs/modules/validation.yaml'

    def __init__(self, config_path: Optional[str] = None):
        # Load YAML as dict (via BaseModule)
        super().__init__(config_path)
        
        # Extract values from YAML structure
        self.project_root = Path(self.config.get('project_root', '.'))
        self.validation_config = self.config.get('validation', {})
        if not self.validation_config:
            self.logger.debug("ValidationModule config not found in loaded YAML dict")
    
        # Convert dict to SharedSourceConfig
        self.shared_config = self._build_shared_config()

    def _build_shared_config(self) -> SharedSourceConfig:
        """Build SharedSourceConfig from loaded YAML dict"""
        shared_source_config = self.validation_config.get('shared_source_config', {})
        if not shared_source_config:
            self.logger.debug("Using default SharedSourceConfig")
        resolved_config = self._resolve_paths(shared_source_config)
        return SharedSourceConfig(**resolved_config)

    def _resolve_paths(self, config: dict) -> dict:
        """Resolve relative paths with project_root"""
        resolved = {}
        for key, value in config.items():
            if value and isinstance(value, str) and ('_dir' in key or '_path' in key):
                resolved[key] = str(self.project_root / value)
            else:
                resolved[key] = value
        return resolved
    
    @property
    def module_name(self) -> str:
        """Unique module name"""
        return "ValidationModule"
    
    @property
    def dependencies(self) -> Dict[str, str]:
        """One dependency - this is the second module"""
        return {
            'DataPipelineModule': self.shared_config.annotation_path, 
        }
    
    @property
    def context_outputs(self) -> List[str]:
        """Keys that this module writes to context"""
        return [
            'validation_result',
            'shared_configs',
            'enable_parallel',
            'max_workers'
        ]

    def execute(self, context, dependency_policy) -> ModuleResult:
        """
        Execute ValidationOrchestrator.
        
        Args:
            context: Shared context (empty for first module)
            self.config: Configuration containing:
                - project_root: Project root directory
                - validation:
                    - validation_df_name (List[str]): List of dataframe names that require validation.
                    Supported values: ["purchaseOrders", "productRecords"].
                    - annotation_path (str): Path to the JSON file containing path annotations.
                    - databaseSchemas_path (str): Path to database schemas used for validation.
                    - validation_change_log_path (str): Path to the ValidationOrchestrator change log.
                    - validation_dir (str): Default directory for validation outputs and temporary files.
                - enable_parallel: enable parallel process (default: False)
                - max_workers: max workers for parallel process (default: None - auto)
            dependencies: Empty dict (no dependencies)
            
        Returns:
            ModuleResult with pipeline execution results
        """

        self.logger = logger.bind(class_="ValidationModule")

        try:
            
            # Create orchestrator
            validation_orchestrator = ValidationOrchestrator(
                shared_source_config=self.shared_config,
                enable_parallel = self.validation_config.get('enable_parallel', True),
                max_workers = self.validation_config.get('max_workers', None))

            # Run validations
            self.logger.info("Running validations...")
            validation_result = validation_orchestrator.run_validations_and_save_results()

            self.logger.info("Validation execution completed!")

            # ✅ CHECK if it has critical errors in sub-results
            if validation_result.has_critical_errors():
                failed_paths = validation_result.get_failed_paths()
                return ModuleResult(
                    status='failed',
                    data={'validation_result': validation_result},
                    message=f'Validation has critical errors in: {failed_paths}',
                    errors=failed_paths
                )
            
            # ✅ CHECK STATUS from ExecutionResult
            if validation_result.status == 'failed':
                return ModuleResult(
                    status='failed',
                    data={'validation_result': validation_result},
                    message=f'Validation failed: {validation_result.error}',
                    errors=[validation_result.error] if validation_result.error else []
                )
 
            # ✅ SUCCESS case
            return ModuleResult(
                status='success',
                data={
                    'validation_result': validation_result,
                },
                message='Validation completed successfully',
                context_updates={
                    'validation_result': validation_result,
                    'shared_configs': asdict(self.shared_config),
                    'enable_parallel': self.validation_config.get('enable_parallel', True),
                    'max_workers': self.validation_config.get('max_workers', None)
                }
            )
            
        except Exception as e:
            # ❌ Only catch NOT expected exception (agent crash)
            self.logger.error(f"Validation failed: {e}", exc_info=True)
            return ModuleResult(
                status='failed',
                data=None,
                message=f"Validation execution failed: {str(e)}",
                errors=[str(e)]
            )