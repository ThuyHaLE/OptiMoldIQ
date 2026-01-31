# modules/data_pipeline_module.py

from pathlib import Path
from typing import Dict, List, Optional
from modules.base_module import BaseModule, ModuleResult
from dataclasses import asdict
from loguru import logger

from agents.dataPipelineOrchestrator.data_pipeline_orchestrator import SharedSourceConfig, DataPipelineOrchestrator

class DataPipelineModule(BaseModule):
    """
    Module wrapper for DataPipelineOrchestrator.
    
    Handles data loading and preparation pipeline.
    """
    
    DEFAULT_CONFIG_PATH = 'configs/modules/data_pipeline.yaml'

    def __init__(self, config_path: Optional[str] = None):
        # Load YAML as dict (via BaseModule)
        super().__init__(config_path)
        
        # Store project root
        self.project_root = Path(self.config.get('project_root', '.'))

        # Convert dict to SharedSourceConfig
        self.shared_config = self._build_shared_config()

    def _build_shared_config(self) -> SharedSourceConfig:
        """Build SharedSourceConfig from loaded YAML dict"""
        pipeline_config = self.config.get('data_pipeline', {})

        if not pipeline_config:
            self.logger.debug("Using default SharedSourceConfig")

        resolved_config = self._resolve_paths(pipeline_config)
        
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
        return "DataPipelineModule"
    
    @property
    def dependencies(self) -> Dict[str, str]:
        """No dependencies - this is typically the first module"""
        return {}
    
    @property
    def context_outputs(self) -> List[str]:
        """Keys that this module writes to context"""
        return [
            'pipeline_result',
            'shared_configs'
        ]
    
    def execute(self, context, dependency_policy) -> ModuleResult:
        """
        Execute DataPipelineOrchestrator.
        
        Args:
            context: Shared context (empty for first module)
            self.config: Configuration containing:
                - project_root: Project root directory
                - data_pipeline:
                    - databaseSchemas_path: Path to database schemas
                    - data_pipeline_dir: Default directory for outputs
                    - data_pipeline_change_log_path: Path to DataPipelineOrchestrator change log
                    - manual_review_notifications_dir: Path to healing notifications directory
                    - shared_database_dir: Path to shared database directory
                    - annotation_path: Path to annotations
            dependencies: Empty dict (no dependencies)
        Returns:
            ModuleResult with pipeline execution results
        """
        
        self.logger = logger.bind(class_="DataPipelineModule")

        try:
            # Create orchestrator
            orchestrator = DataPipelineOrchestrator(config=self.shared_config)
            
            # Run pipeline
            self.logger.info("Running data pipeline...")
            pipeline_result = orchestrator.run_collecting_and_save_results()
            
            # Log report
            self.logger.info("Pipeline execution completed!")

            # ✅ CHECK if it has critical errors in sub-results
            if pipeline_result.has_critical_errors():
                failed_paths = pipeline_result.get_failed_paths()
                return ModuleResult(
                    status='failed',
                    data={'pipeline_result': pipeline_result},
                    message=f'Validation has critical errors in: {failed_paths}',
                    errors=failed_paths
                )
            
            # ✅ CHECK STATUS from ExecutionResult
            if pipeline_result.status == 'failed':
                return ModuleResult(
                    status='failed',
                    data={'pipeline_result': pipeline_result},
                    message=f'Pipeline failed: {pipeline_result.error}',
                    errors=[pipeline_result.error] if pipeline_result.error else []
                )
 
            # ✅ SUCCESS case
            return ModuleResult(
                status='success',
                data={
                    'pipeline_result': pipeline_result,
                },
                message='Pipeline completed successfully',
                context_updates={
                    'pipeline_result': pipeline_result,
                    'shared_configs': asdict(self.shared_config),
                }
            )
            
        except Exception as e:
            # ❌ Only catch NOT expected exception (agent crash)
            self.logger.error(f"Pipeline failed: {e}", exc_info=True)
            return ModuleResult(
                status='failed',
                data=None,
                message=f"Pipeline execution failed: {str(e)}",
                errors=[str(e)]
            )