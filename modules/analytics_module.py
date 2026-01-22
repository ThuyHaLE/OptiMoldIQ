# modules/analytics_module.py

from pathlib import Path
from typing import Dict, List, Optional
from modules.base_module import BaseModule, ModuleResult
from loguru import logger
from dataclasses import asdict
from configs.shared.shared_source_config import SharedSourceConfig
from agents.analyticsOrchestrator.analytics_orchestrator import ComponentConfig, AnalyticsOrchestratorConfig, AnalyticsOrchestrator

class AnalyticsModule(BaseModule):
    """
    Module wrapper for AnalyticsModule.
    
    Handles analytics pipeline.
    """

    DEFAULT_CONFIG_PATH = 'configs/modules/analytics.yaml'

    def __init__(self, config_path: Optional[str] = None):
        # Load YAML as dict (via BaseModule)
        super().__init__(config_path)
        
        # Extract values from YAML structure
        self.project_root = Path(self.config.get('project_root', '.'))
        self.analytics_config = self.config.get('analytics', {})
        if not self.analytics_config:
            self.logger.debug("AnalyticsModule config not found in loaded YAML dict")

        self.shared_config = self._build_shared_config()

        # Convert dict to AnalyticsOrchestratorConfig
        self.orchestrator_config = self._build_analytics_orchestrator_config()

    def _build_analytics_orchestrator_config(self) -> AnalyticsOrchestratorConfig:
        return AnalyticsOrchestratorConfig(
            shared_source_config = self.shared_config,
            machine_layout_tracker = self._build_component_config(
                self.analytics_config.get('machine_layout_tracker', {}),
            ),
            mold_machine_pair_tracker = self._build_component_config(
                self.analytics_config.get('mold_machine_pair_tracker', {})
            ),
            day_level_processor = self._build_component_config(
                self.analytics_config.get('day_level_processor', {})), 
            month_level_processor = self._build_component_config(
                self.analytics_config.get('month_level_processor', {}) ),
            year_level_processor = self._build_component_config(
                self.analytics_config.get('year_level_processor', {}) ),
            # Top-level logging
            save_orchestrator_log = self.analytics_config.get('save_orchestrator_log', None)
        )
    
    def _build_component_config(self, component_dict) -> ComponentConfig:
        return ComponentConfig(
            enabled = component_dict.get('enabled', None),
            save_result = component_dict.get('save_result', None),
            requested_timestamp = component_dict.get('requested_timestamp', None),
            analysis_date = component_dict.get('analysis_date', None)
            )

    def _build_shared_config(self) -> SharedSourceConfig:
        """Build SharedSourceConfig from loaded YAML dict"""
        shared_source_config = self.analytics_config.get('shared_source_config', {})
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
        return "AnalyticsModule"

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
            'orchestrator_result',
            'orchestrator_config'
        ]

    def execute(self, context, dependency_policy) -> ModuleResult:
        
        """
        Execute AnalyticsModule.
        
        Args:
            context: Shared context (empty for first module)
            self.orchestrator_config: Configuration containing:

                - project_root: Project root directory
                
                - shared_source_config: 
                    - annotation_path (str): Path to the JSON file containing path annotations.
                    - databaseSchemas_path (str): Path to database schema for validation.
                    - machine_layout_tracker_dir (str): Base directory for storing reports.
                    - machine_layout_tracker_change_log_path (str): Path to the MachineLayoutTracker change log.
                    - mold_machine_pair_tracker_dir (str): Base directory for storing reports.
                    - mold_machine_pair_tracker_change_log_path (str): Path to the MoldMachinePairTracker change log.
                    - hardware_change_analyzer_log_path (str): Path to the HardwareChangeAnalyzer change log.
                    - day_level_processor_dir (str): Base directory for storing reports.
                    - day_level_processor_log_path (str): Path to the DayLevelDataProcessor change log.
                    - month_level_processor_dir (str): Base directory for storing reports.
                    - month_level_processor_log_path (str): Path to the MonthLevelDataProcessor change log.
                    - year_level_processor_dir (str): Base directory for storing reports.
                    - year_level_processor_log_path (str): Path to the YearLevelDataProcessor change log.
                    - multi_level_performance_analyzer_log_path (str): Path to the MultiLevelPerformanceAnalyzer change log.
                    - analytics_orchestrator_log_path (str): Path to the AnalyticsOrchestrator change log.

                - machine_layout_tracker (ComponentConfig): Component config for MachineLayoutTracker
                - mold_machine_pair_tracker (ComponentConfig): Component config for MoldMachinePairTracker 
                - day_level_processor (ComponentConfig): Component config for DayLevelDataProcessor 
                - month_level_processor (ComponentConfig): Component config for MonthLevelDataProcessor
                - year_level_processor (ComponentConfig): Component config for YearLevelDataProcessor
                - save_orchestrator_log (bool): Save AnalyticsOrchestrator change log
                
            dependencies: Empty dict (no dependencies)
            
        Returns:
            ModuleResult with pipeline execution results
        """

        self.logger = logger.bind(class_="AnalyticsModule")

        try:
            # Create orchestrator
            orchestrator = AnalyticsOrchestrator(
                config = self.orchestrator_config)
            
            # Run orchestrator
            self.logger.info("Running orchestrator...")
            orchestrator_result = orchestrator.run_analyzing()

            self.logger.info("Orchestrator execution completed!")

            # ✅ CHECK if it has critical errors in sub-results
            if orchestrator_result.has_critical_errors():
                failed_paths = orchestrator_result.get_failed_paths()
                return ModuleResult(
                    status='failed',
                    data={'orchestrator_result': orchestrator_result},
                    message=f'Orchestrator has critical errors in: {failed_paths}',
                    errors=failed_paths
                )
            
            # ✅ CHECK STATUS from ExecutionResult
            if orchestrator_result.status == 'failed':
                return ModuleResult(
                    status='failed',
                    data={'orchestrator_result': orchestrator_result},
                    message=f'Orchestrator failed: {orchestrator_result.error}',
                    errors=[orchestrator_result.error] if orchestrator_result.error else []
                )
 
            # ✅ SUCCESS case
            return ModuleResult(
                status='success',
                data={
                    'orchestrator_result': orchestrator_result,
                },
                message='Orchestrator completed successfully',
                context_updates={
                    'orchestrator_result': orchestrator_result,
                    'orchestrator_config': asdict(self.orchestrator_config)
                }
            )

        except Exception as e:
            # ❌ Only catch NOT expected exception (agent crash)
            self.logger.error(f"Orchestrator failed: {e}", exc_info=True)
            return ModuleResult(
                status='failed',
                data=None,
                message=f"Orchestrator execution failed: {str(e)}",
                errors=[str(e)]
            )