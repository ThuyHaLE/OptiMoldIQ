# modules/data_pipeline_module.py

from pathlib import Path
from typing import Dict, List
from modules.base_module import BaseModule, ModuleResult
from loguru import logger

from agents.dataPipelineOrchestrator.data_pipeline_orchestrator import DataPipelineOrchestrator

class DataPipelineModule(BaseModule):
    """
    Module wrapper for DataPipelineOrchestrator.
    
    Handles data loading and preparation pipeline.
    """
    
    DEFAULT_CONFIG_PATH = 'configs/modules/data_pipeline.yaml'

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
            'data_loader_path',
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
                    - dynamic_db_source_dir: Path to dynamic database
                    - databaseSchemas_path: Path to database schemas
                    - annotation_path: Path to annotations (optional, will use default)
                    - default_dir: Default directory for outputs
                    - use_colored_report: Whether to use colored output (default: True)
            dependencies: Empty dict (no dependencies)
            
        Returns:
            ModuleResult with pipeline execution results
        """
        
        self.logger = logger.bind(class_="DataPipelineModule")

        try:

            # Extract self.config
            project_root = Path(self.config.get('project_root', '.'))
            pipeline_config = self.config.get('data_pipeline', {})

            self.logger.debug("Project root: {}", project_root)
            
            if not pipeline_config:
                self.logger.debug("Cannot load DataPipelineOrchestrator config")
            
            # Build paths
            dynamic_db_source_dir = str(project_root / pipeline_config.get(
                'dynamic_db_source_dir',
                'database/dynamicDatabase' 
            ))
            
            databaseSchemas_path = str(project_root / pipeline_config.get(
                'databaseSchemas_path',
                'database/databaseSchemas.json'
            ))
            
            default_dir = str(project_root / pipeline_config.get(
                'default_dir',
                'agents/shared_db' 
            ))
            
            # Annotation path (optional - orchestrator will use default if not provided)
            annotation_path = pipeline_config.get('annotation_path')
            if annotation_path:
                annotation_path = str(project_root / annotation_path)
            else:
                # Will be auto-generated: {default_dir}/DataLoaderAgent/newest/path_annotations.json
                annotation_path = str(Path(default_dir) / 'DataLoaderAgent/newest/path_annotations.json')
            
            self.logger.info("DataPipelineOrchestrator configuration:")
            self.logger.info(f"  - Dynamic DB Source: {dynamic_db_source_dir}")
            self.logger.info(f"  - Database Schemas: {databaseSchemas_path}")
            self.logger.info(f"  - Annotation Path: {annotation_path}")
            self.logger.info(f"  - Default Dir: {default_dir}")
            
            # Create orchestrator
            orchestrator = DataPipelineOrchestrator(
                dynamic_db_source_dir=dynamic_db_source_dir,
                databaseSchemas_path=databaseSchemas_path,
                annotation_path=annotation_path,
                default_dir=default_dir
            )
            
            # Run pipeline
            self.logger.info("Running data pipeline...")
            results, log_str = orchestrator.run_pipeline()
            
            # Log report
            self.logger.info("Pipeline execution completed!")
            
            # Determine data loader path (where processed data is stored)
            data_loader_path = str(Path(default_dir) / 'DataLoaderAgent/newest')
            
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
                    'data_loader_path': data_loader_path,
                    'annotation_path': annotation_path
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