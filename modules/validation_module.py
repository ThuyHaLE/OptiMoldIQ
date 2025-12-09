# modules/validation_module.py

from pathlib import Path
from typing import Dict, List, Optional
from modules.base_module import BaseModule, ModuleResult
from loguru import logger

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
    def dependencies(self) -> List[str]:
        """No dependencies - this is typically the first module"""
        return []
    
    @property
    def context_outputs(self) -> List[str]:
        """Keys that this module writes to context"""
        return [
            'validation_orchestrator_result',
            'validation_orchestrator_log',
            'dataschemas_path',
            'annotation_path',
            'enable_parallel',
            'max_workers'
        ]

    def execute(self, 
                context: Dict, 
                dependencies: Dict) -> ModuleResult:
        """
        Execute ValidationOrchestrator.
        
        Args:
            context: Shared context (empty for first module)
            self.config: Configuration containing:
                - project_root: Project root directory
                - validation:
                    - validation_df_name: List df name for validation (default: ["productRecords", "purchaseOrders"])
                    - annotation_path: Path to annotations
                    - databaseSchemas_path: Path to database schemas
                    - validation_dir: Default directory for outputs
                - enable_parallel: enable parallel process (default: False)
                - max_workers: max workers for parallel process (default: None - auto)
            dependencies: Empty dict (no dependencies)
            
        Returns:
            ModuleResult with pipeline execution results
        """
        
        self.logger = logger.bind(class_="ValidationModule")

        try:
            
            # Create orchestrator
            orchestrator = ValidationOrchestrator(
                shared_source_config=self.shared_config,
                enable_parallel = self.validation_config.enable_parallel,
                max_workers = self.validation_config.max_workers)

            # Run validations
            self.logger.info("Running validations...")
            results, log_str = orchestrator.run_validations_and_save_results()

            self.logger.info("Validation execution completed!")
 
            # Return success result
            return ModuleResult(
                status='success',
                data={
                    'validation_results': results,
                    'validation_log': log_str
                },
                message='Validation completed successfully',
                context_updates={
                    'validation_orchestrator_result': results,
                    'validation_orchestrator_log': log_str,
                    'dataschemas_path': self.shared_config.databaseSchemas_path,
                    'annotation_path': self.shared_config.annotation_path,
                    'enable_parallel': self.validation_config.enable_parallel,
                    'max_workers': self.validation_config.max_workers
                }
            )
            
        except Exception as e:
            self.logger.error(f"Validation failed: {e}", exc_info=True)
            return ModuleResult(
                status='failed',
                data=None,
                message=f"Validation execution failed: {str(e)}",
                errors=[str(e)]
            )