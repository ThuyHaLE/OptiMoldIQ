# modules/progress_tracking_module.py

from pathlib import Path
from typing import Dict, List, Optional
from modules.base_module import BaseModule, ModuleResult
from loguru import logger
from dataclasses import asdict
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
    def dependencies(self) -> Dict[str, str]:
        """Two dependencies - this is typically the third module"""
        return {
            'DataPipelineModule': self.shared_config.annotation_path, 
            'ValidationModule': self.shared_config.validation_change_log_path, 
        }

    @property
    def context_outputs(self) -> List[str]:
        """Keys that this module writes to context"""
        return [
            'tracking_result',
            'configs'
        ]
        
    def execute(self, context, dependency_policy) -> ModuleResult:
        """
        Execute OrderProgressTracker.
        
        Args:
            Configuration containing:
                - project_root: Project root directory
                - progress_tracking:
                    - annotation_path (str): Path to the JSON file containing path annotations.
                    - databaseSchemas_path (str): Path to database schema for validation.
                    - validation_change_log_path (str): Path to the ValidationOrchestrator change log.
                    - progress_tracker_dir (str): Default directory for output and temporary files.
                    - progress_tracker_change_log_path (str): Path to the OrderProgressTracker change log.
                    - progress_tracker_constant_config_path (str): Path to the OrderProgressTracker constant config.   
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

            # ✅ CHECK if it has critical errors in sub-results
            if tracker_result.has_critical_errors():
                failed_paths = tracker_result.get_failed_paths()
                return ModuleResult(
                    status='failed',
                    data={'tracking_result': tracker_result},
                    message=f'Tracking has critical errors in: {failed_paths}',
                    errors=failed_paths
                )
            
            # ✅ CHECK STATUS from ExecutionResult
            if tracker_result.status == 'failed':
                return ModuleResult(
                    status='failed',
                    data={'tracking_result': tracker_result},
                    message=f'Tracking failed: {tracker_result.error}',
                    errors=[tracker_result.error] if tracker_result.error else []
                )
        
            # ✅ SUCCESS case
            return ModuleResult(
                status='success',
                data={
                    'tracking_result': tracker_result,
                },
                message='Tracking completed successfully',
                context_updates={
                    'tracking_result': tracker_result,
                    'configs': asdict(self.shared_config)
                }
            )

        except Exception as e:
            # ❌ Only catch NOT expected exception (agent crash)
            self.logger.error(f"Tracking failed: {e}", exc_info=True)
            return ModuleResult(
                status='failed',
                data=None,
                message=f"Tracking execution failed: {str(e)}",
                errors=[str(e)]
            )