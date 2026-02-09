# modules/dashboard_module.py

from pathlib import Path
from typing import Dict, Optional
from modules.base_module import BaseModule, ModuleResult
from loguru import logger
from configs.shared.shared_source_config import SharedSourceConfig
from agents.dashboardBuilder.dashboard_builder import ComponentConfig, DashboardBuilderConfig, DashboardBuilder

class DashboardModule(BaseModule):
    """
    Module wrapper for DashboardModule.
    
    Handles dashboard generation.
    """

    DEFAULT_CONFIG_PATH = 'configs/modules/dashboard.yaml'

    def __init__(self, config_path: Optional[str] = None):
        # Load YAML as dict (via BaseModule)
        super().__init__(config_path)
        
        # Extract values from YAML structure
        self.project_root = Path(self.config.get('project_root', '.'))
        self.dashboard_config = self.config.get('dashboard', {})
        if not self.dashboard_config:
            self.logger.debug("DashboardModule config not found in loaded YAML dict")

        self.shared_config = self._build_shared_config()

        # Convert dict to DashboardBuilderConfig
        self.builder_config = self._build_dashboard_builder_config()

    def _build_dashboard_builder_config(self) -> DashboardBuilderConfig:
        return DashboardBuilderConfig(
            shared_source_config = self.shared_config,
            machine_layout_visualization_service = self._build_component_config(
                self.dashboard_config.get('machine_layout_visualization_service', {}),
            ),
            mold_machine_pair_visualization_service = self._build_component_config(
                self.dashboard_config.get('mold_machine_pair_visualization_service', {})
            ),
            day_level_visualization_service = self._build_component_config(
                self.dashboard_config.get('day_level_visualization_service', {})), 
            month_level_visualization_service = self._build_component_config(
                self.dashboard_config.get('month_level_visualization_service', {}) ),
            year_level_visualization_service = self._build_component_config(
                self.dashboard_config.get('year_level_visualization_service', {}) ),
                
            # Top-level logging
            save_builder_log = self.dashboard_config.get('save_builder_log', None)
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
        shared_source_config = self.dashboard_config.get('shared_source_config', {})
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
        return "DashboardModule"

    @property
    def dependencies(self) -> Dict[str, str]:
        """One dependency - this is the second module"""
        return {
            'DataPipelineModule': self.shared_config.annotation_path, 
        }

    def execute(self) -> ModuleResult:
        
        """
        Execute DashboardModule.
        
        Args:
            Configuration containing:
                - project_root: Project root directory
                - shared_source_config: 
                    - annotation_path (str): Path to the JSON file containing path annotations.
                    - databaseSchemas_path (str): Path to database schema for validation.
                    - day_level_visualization_pipeline_dir (str): Base directory for storing reports.
                    - day_level_visualization_pipeline_log_path (str): Path to the DayLevelVisualizationPipeline change log.
                    - month_level_visualization_pipeline_dir (str): Base directory for storing reports.
                    - month_level_visualization_pipeline_log_path (str): Path to the MonthLevelVisualizationPipeline change log.
                    - year_level_visualization_pipeline_dir (str): Base directory for storing reports.
                    - year_level_visualization_pipeline_log_path (str): Path to the YearLevelVisualizationPipeline change log.
                    - multi_level_performance_visualization_service_log_path (str): Path to the MultiLevelPerformanceVisualizationService change log.
                    - hardware_change_visualization_service_dir (str): Base directory for storing reports/visualizations.
                    - hardware_change_visualization_service_log_path (str): Path to the HardwareChangeVisualizationService change log.
                    - machine_layout_visualization_pipeline_dir (str): Base directory for storing reports/visualizations.
                    - machine_layout_visualization_pipeline_change_log_path (str): Path to the MachineLayoutVisualizationPipeline change log.
                    - mold_machine_pair_visualization_pipeline_dir (str): Base directory for storing reports/visualizations.
                    - mold_machine_pair_visualization_pipeline_change_log_path (str): Path to the MoldMachinePairVisualizationPipeline change log.
                    - dashboard_builder_log_path (str): Path to save the DashboardBuilder change log.
                - machine_layout_visualization_service: (ComponentConfig): Component config for MachineLayoutVisualizationPipeline
                - mold_machine_pair_visualization_service: Component config for MoldMachinePairVisualizationPipeline
                - day_level_visualization_service (ComponentConfig): Component config for DayLevelVisualizationPipeline
                - month_level_visualization_service (ComponentConfig): Component config for MonthLevelVisualizationPipeline
                - year_level_visualization_service (ComponentConfig): Component config for YearLevelVisualizationPipeline
                - save_builder_log (bool): Save DashboardBuilder change log       
        Returns:
            ModuleResult with pipeline execution results
        """

        self.logger = logger.bind(class_="DashboardModule")

        try:
            # Create builder
            builder = DashboardBuilder(
                config = self.builder_config)
            
            # Run builder
            self.logger.info("Running builder...")
            builder_result = builder.build_dashboard()

            self.logger.info("Builder execution completed!")

            # ✅ CHECK if it has critical errors in sub-results
            if builder_result.has_critical_errors():
                failed_paths = builder_result.get_failed_paths()
                return ModuleResult(
                    status='failed',
                    data={'builder_result': builder_result},
                    message=f'Builder has critical errors in: {failed_paths}',
                    errors=failed_paths
                )
            
            # ✅ CHECK STATUS from ExecutionResult
            if builder_result.status == 'failed':
                return ModuleResult(
                    status='failed',
                    data={'builder_result': builder_result},
                    message=f'Builder failed: {builder_result.error}',
                    errors=[builder_result.error] if builder_result.error else []
                )
 
            # ✅ SUCCESS case
            return ModuleResult(
                status='success',
                data={
                    'builder_result': builder_result,
                },
                message='Builder completed successfully'
            )

        except Exception as e:
            # ❌ Only catch NOT expected exception (agent crash)
            self.logger.error(f"Builder failed: {e}", exc_info=True)
            return ModuleResult(
                status='failed',
                data=None,
                message=f"Builder execution failed: {str(e)}",
                errors=[str(e)]
            )