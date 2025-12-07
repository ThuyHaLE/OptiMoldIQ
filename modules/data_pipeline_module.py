# modules/data_pipeline_module.py

from pathlib import Path
from typing import Dict, List, Optional
from modules.base_module import BaseModule, ModuleResult
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
        
        # Convert dict to SharedSourceConfig
        self.shared_config = self._build_shared_config()

    def _build_shared_config(self) -> SharedSourceConfig:
        """Build SharedSourceConfig from loaded YAML dict"""
        
        # Extract values from YAML structure
        project_root = Path(self.config.get('project_root', '.'))
        pipeline_config = self.config.get('data_pipeline', {})
        
        # Helper function to join paths with project_root
        def resolve_path(path_value: Optional[str]) -> Optional[str]:
            """Join path with project_root if provided, else return None"""
            if path_value is None:
                return None
            return str(project_root / path_value)
        
        # Map YAML fields to SharedSourceConfig
        return SharedSourceConfig(
            # Required fields
            db_dir=resolve_path(pipeline_config.get('db_dir')) or 'database',
            default_dir=resolve_path(pipeline_config.get('default_dir')) or 'agents/shared_db',
            
            # Optional fields
            dynamic_db_dir=resolve_path(pipeline_config.get('dynamic_db_dir')),
            databaseSchemas_path=resolve_path(pipeline_config.get('databaseSchemas_path')),
            data_pipeline_dir=resolve_path(pipeline_config.get('data_pipeline_dir')),
            annotation_path=resolve_path(pipeline_config.get('annotation_path'))
        )

    @property
    def module_name(self) -> str:
        """Unique module name"""
        return "DataPipelineModule"
    
    @property
    def dependencies(self) -> List[str]:
        """No dependencies - this is typically the first module"""
        return []
    
    @property
    def context_outputs(self) -> List[str]:
        """Keys that this module writes to context"""
        return [
            'data_pipeline_result',
            'data_pipeline_log',
            'data_pipeline_dir',
            'annotation_path'
        ]
    
    def execute(self, 
                context: Dict, 
                dependencies: Dict) -> ModuleResult:
        """
        Execute DataPipelineOrchestrator.
        
        Args:
            context: Shared context (empty for first module)
            self.config: Configuration containing:
                - project_root: Project root directory
                - data_pipeline:
                    - dynamic_db_dir: Path to dynamic database
                    - databaseSchemas_path: Path to database schemas
                    - annotation_path: Path to annotations
                    - data_pipeline_dir: Default directory for outputs
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
            results, log_str = orchestrator.run_pipeline()
            
            # Log report
            self.logger.info("Pipeline execution completed!")
            
            # Return success result
            return ModuleResult(
                status='success',
                data={
                    'pipeline_results': results,
                    'pipeline_log': log_str
                },
                message='DataPipeline completed successfully',
                context_updates={
                    'data_pipeline_result': results,
                    'data_pipeline_log': log_str,
                    'data_pipeline_dir': self.shared_config.data_pipeline_dir,
                    'annotation_path': self.shared_config.annotation_path
                }
            )
            
        except Exception as e:
            self.logger.error(f"DataPipeline failed: {e}", exc_info=True)
            return ModuleResult(
                status='failed',
                data=None,
                message=f"DataPipeline execution failed: {str(e)}",
                errors=[str(e)]
            )