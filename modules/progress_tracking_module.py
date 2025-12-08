# modules/progress_tracking_module.py

from pathlib import Path
from typing import Dict, List, Optional
from modules.base_module import BaseModule, ModuleResult
from loguru import logger

from agents.orderProgressTracker.order_progress_tracker import SharedSourceConfig, OrderProgressTracker

class ProgressTrackingModule(BaseModule):
    """
    Module wrapper for OrderProgressTracker.
    
    Handles data loading and preparation pipeline.
    """
    
    DEFAULT_CONFIG_PATH = 'configs/modules/progress_tracking.yaml'

    def __init__(self, config_path: Optional[str] = None):
        # Load YAML as dict (via BaseModule)
        super().__init__(config_path)
        
        # Convert dict to SharedSourceConfig
        self.shared_config = self._build_shared_config()

    def _build_shared_config(self) -> SharedSourceConfig:
        """Build SharedSourceConfig from loaded YAML dict"""
        
        # Extract values from YAML structure
        project_root = Path(self.config.get('project_root', '.'))
        progress_tracking_config = self.config.get('progress_tracking', {})
        if not progress_tracking_config:
            self.logger.debug("ProgressTrackingModule config not found in loaded YAML dict")
        
        # Helper function to join paths with project_root
        def resolve_path(path_value: Optional[str]) -> Optional[str]:
            """Join path with project_root if provided, else return None"""
            if path_value is None:
                return None
            return str(project_root / path_value)
        
        # Map YAML fields to SharedSourceConfig
        return SharedSourceConfig(
            # Required fields
            db_dir=resolve_path(progress_tracking_config.get('db_dir')) or 'database',
            default_dir=resolve_path(progress_tracking_config.get('default_dir')) or 'agents/shared_db',
            
            # Optional fields
            databaseSchemas_path=resolve_path(progress_tracking_config.get('databaseSchemas_path')),
            annotation_path=resolve_path(progress_tracking_config.get('annotation_path')),
            validation_change_log_path=resolve_path(progress_tracking_config.get('validation_change_log_path')),
            progress_tracker_dir=resolve_path(progress_tracking_config.get('progress_tracker_dir'))
        )
    
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
                    - annotation_path: Path to annotations
                    - databaseSchemas_path: Path to database schemas
                    - validation_change_log_path: Change log path (from ValidationOrchestrator)
                    - progress_tracker_dir: Default directory for outputs
            dependencies: Empty dict (no dependencies)
            
        Returns:
            ModuleResult with pipeline execution results
        """
        
        self.logger = logger.bind(class_="ProgressTrackingModule")

        try:
            # Create tracker
            order_progress_tracker = OrderProgressTracker(config = self.shared_config)
            
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
                    'dataschemas_path': self.config.databaseSchemas_path,
                    'annotation_path': self.config.annotation_path,
                    'validation_changlog_path': self.config.validation_change_log_path
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