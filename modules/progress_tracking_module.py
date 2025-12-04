# modules/progress_tracking_module.py

from pathlib import Path
from typing import Dict, List
from modules.base_module import BaseModule, ModuleResult
from loguru import logger

from agents.orderProgressTracker.order_progress_tracker import OrderProgressTracker

class ProgressTrackingModule(BaseModule):
    """
    Module wrapper for OrderProgressTracker.
    
    Handles data loading and preparation pipeline.
    """
    
    DEFAULT_CONFIG_PATH = 'configs/modules/progress_tracking.yaml'

    @property
    def module_name(self) -> str:
        """Unique module name"""
        return "ProgressTrackingModule"
    
    @property
    def dependencies(self) -> List[str]:
        """No dependencies - this is typically the first module"""
        return []
    
    @property
    def context_outputs(self) -> List[str]:
        """Keys that this module writes to context"""
        return [
            'progress_tracking_result',
            'progress_tracking_log',
            'data_loader_path',
            'annotation_path',
            'validation_changlog_path'
        ]
        
    def execute(self, 
                context: Dict, 
                dependencies: Dict) -> ModuleResult:
        """
        Execute OrderProgressTracker.
        
        Args:
            context: Shared context (empty for first module)
            self.config: Configuration containing:
                - project_root: Project root directory
                - progress_tracking:
                    - source_path: Main shared database (from DataPipeline) directory
                    - annotation_name: Annotation name
                    - databaseSchemas_path: Path to database schemas
                    - folder_path: Change log (from ValidationOrchestrator) directory
                    - target_name: Change log name
                    - default_dir: Default directory for outputs
                    - use_colored_report: Whether to use colored output (default: True)
            dependencies: Empty dict (no dependencies)
            
        Returns:
            ModuleResult with pipeline execution results
        """
        
        self.logger = logger.bind(class_="ProgressTrackingModule")

        try:

            # Extract self.config
            project_root = Path(self.config.get('project_root', '.'))
            progress_tracking_config = self.config.get('progress_tracking', {})

            self.logger.debug("Project root: {}", project_root)

            if not progress_tracking_config:
                self.logger.debug("Cannot load OrderProgressTracker config")
            
            # Main shared database from DataPipeline
            source_path = str(project_root / progress_tracking_config.get(
                'source_path', 
                'agents/shared_db/DataLoaderAgent/newest'))
            annotation_name = progress_tracking_config.get(
                'annotation_name',
                'path_annotations.json')
            
            databaseSchemas_path = str(project_root / progress_tracking_config.get(
                'databaseSchemas_path',
                'database/databaseSchemas.json'
            ))
            
            # Change log from ValidationOrchestrator
            folder_path = str(project_root / progress_tracking_config.get(
                'folder_path',
                'agents/shared_db/ValidationOrchestrator'
            ))
            target_name = progress_tracking_config.get(
                'target_name',
                'change_log.txt')
            
            default_dir = str(project_root / progress_tracking_config.get(
                'default_dir',
                'agents/shared_db' 
            ))
            
            self.logger.info("OrderProgressTracker configuration:")
            self.logger.info(f"  - Annotation Path: {source_path}/{annotation_name}")
            self.logger.info(f"  - Database Schemas: {databaseSchemas_path}")
            self.logger.info(f"  - ValidationOrchestrator Change Log Path: {folder_path}/{target_name}")
            self.logger.info(f"  - Default Dir: {default_dir}")
            
            # Create tracker
            order_progress_tracker = OrderProgressTracker(
                source_path = source_path,
                annotation_name = annotation_name,
                databaseSchemas_path = databaseSchemas_path,
                folder_path = folder_path,
                target_name = target_name,
                default_dir = default_dir)
            
            # Run validations
            self.logger.info("Running tracking...")
            results, log_str = order_progress_tracker.pro_status()

            # Log report
            self.logger.info("Tracking execution completed!")
            
            # Return success result
            return ModuleResult(
                status='success',
                data={
                    'tracking_results': results,
                    'tracking_log': log_str
                },
                message='Tracking completed successfully',
                context_updates={
                    'progress_tracking_result': results,
                    'progress_tracking_log': log_str,
                    'dataschemas_path': databaseSchemas_path,
                    'annotation_path': f"{source_path}/{annotation_name}",
                    'validation_changlog_path': f"{folder_path}/{target_name}"
                }
            )
            
        except Exception as e:
            self.logger.error(f"Tracking failed: {e}", exc_info=True)
            return ModuleResult(
                status='failed',
                data=None,
                message=f"Tracking execution failed: {str(e)}",
                errors=[str(e)]
            )