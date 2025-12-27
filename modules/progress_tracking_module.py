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
        
        # Store project root
        self.project_root = Path(self.config.get('project_root', '.'))
        
        # Convert dict to SharedSourceConfig
        self.shared_config = self._build_shared_config()

    def _build_shared_config(self) -> SharedSourceConfig:
        """Build SharedSourceConfig from loaded YAML dict"""
        pipeline_config = self.config.get('progress_tracking', {})
        
        if not pipeline_config:
            self.logger.debug("Using default SharedSourceConfig")
            return SharedSourceConfig()
        
        # Resolve paths relative to project_root
        resolved_config = self._resolve_paths(pipeline_config)
        
        return SharedSourceConfig(**resolved_config)

    def _resolve_paths(self, config: dict) -> dict:
        """Resolve relative paths with project_root"""
        resolved = {}
        for key, value in config.items():
            # Only resolve path-like fields that are strings
            if value and isinstance(value, str) and ('_dir' in key or '_path' in key):
                resolved[key] = str(self.project_root / value)
            else:
                resolved[key] = value
        return resolved
    
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
            'dataschemas_path',
            'annotation_path',
            'validation_change_log_path',
            'progress_tracker_change_log_path',
            'progress_tracker_constant_config_path'
        ]
        
    def execute(self, 
                context: Dict, 
                dependencies: Dict) -> ModuleResult:
        """
        Execute OrderProgressTracker.
        
        Args:
            context: Shared context (empty for first module)
            dependencies: Empty dict (no dependencies)
            
        Returns:
            ModuleResult with pipeline execution results
        """
        
        self.logger = logger.bind(class_="ProgressTrackingModule")

        try:
            # Create tracker
            order_progress_tracker = OrderProgressTracker(config=self.shared_config)

            # Run validations
            self.logger.info("Running tracking...")
            tracker_result = order_progress_tracker.run_tracking_and_save_results()

            # Log report
            self.logger.info("Tracking execution completed!")
            
            # Return success result
            return ModuleResult(
                status='success',
                data={
                    'tracking_results': tracker_result,
                },
                message='Tracking completed successfully',
                context_updates={
                    'progress_tracking_result': tracker_result,
                    'dataschemas_path': self.shared_config.databaseSchemas_path,
                    'annotation_path': self.shared_config.annotation_path,
                    'validation_change_log_path': self.shared_config.validation_change_log_path,
                    'progress_tracker_change_log_path': self.shared_config.progress_tracker_change_log_path,
                    'progress_tracker_constant_config_path': self.shared_config.progress_tracker_constant_config_path
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