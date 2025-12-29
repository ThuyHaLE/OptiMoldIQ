# modules/dashboard_module.py

from pathlib import Path
from typing import Dict, List
from modules.base_module import BaseModule, ModuleResult

from loguru import logger

from agents.dashboardBuilder.dashboard_builder import DashboardBuilder
from agents.dashboardBuilder.dashboardBuilderConfigs.dashboard_builder_config import DashboardBuilderConfig
from agents.dashboardBuilder.dashboardBuilderConfigs.performance_plotflow_config import PerformancePlotflowConfig
from agents.dashboardBuilder.dashboardBuilderConfigs.hardware_change_plotflow_config import HardwareChangePlotflowConfig
from agents.analyticsOrchestrator.analyticsConfigs.analytics_orchestrator_config import AnalyticsOrchestratorConfig
from agents.analyticsOrchestrator.analyticsConfigs.performance_analyticflow_config import PerformanceAnalyticflowConfig
from agents.analyticsOrchestrator.analyticsConfigs.change_analyticflow_config import ChangeAnalyticflowConfig
            
class DashboardModule(BaseModule):
    """
    Module wrapper for DashboardBuilder.
    
    Handles visualization and dashboard generation with auto-configuration.
    """

    DEFAULT_CONFIG_PATH = 'configs/modules/dashboard.yaml'

    @property
    def module_name(self) -> str:
        """Unique module name"""
        return "DashboardModule"
    
    @property
    def dependencies(self) -> Dict[str, str]:
        """Two dependencies - this is typically the third module"""
        return {
            'DataPipelineModule': "tests/shared_db/DataPipelineOrchestrator/DataLoaderAgent/newest/path_annotations.json",
            'ValidationModule': "tests/shared_db/ValidationOrchestrator/change_log.txt"
        }

    @property
    def context_outputs(self) -> List[str]:
        """Keys that this module writes to context"""
        return [
            'dashboard_builder_result',
            'dashboard_builder_log'
        ]
    
    def execute(self, context, dependency_policy) -> ModuleResult:
        """
        Execute DashboardBuilder with auto-configuration.
        
        Auto-propagation hierarchy:
        DashboardBuilder (parent)
          ├─> HardwareChangePlotter
          │     └─> AnalyticsOrchestrator (HardwareChangeAnalyzer)
          └─> MultiLevelPerformancePlotter
                └─> AnalyticsOrchestrator (MultiLevelPerformanceAnalyzer)
        """
        
        self.logger = logger.bind(class_="DashboardModule")

        try:
            
            self.project_root = Path(self.config.get('project_root', '.'))
            self.dashboard_config = self.config.get('dashboard', {})

            self.logger.debug("Project root: {}", self.project_root)
            
            if not self.dashboard_config:
                self.logger.debug("Cannot load DashboardBuilder config")
            
            # Extract parent enable flags
            parent_enable_flags = self._extract_parent_flags(self.dashboard_config)
            
            self.logger.info("Building DashboardBuilder configuration...")
            self.logger.info(f"  Hardware Change Plotter: {parent_enable_flags['enable_hardware_change_plotter']}")
            self.logger.info(f"  Multi-level Plotter: {parent_enable_flags['enable_multi_level_plotter']}")
            
            # Build nested configs bottom-up
            # Level 3: Analytics configs (deepest)
            performance_analytic_config = self._build_performance_analytic_config()
            change_analytic_config = self._build_change_analytic_config()
            
            # Level 2: Analytics orchestrator config
            analytics_orchestrator_config = self._build_analytics_orchestrator_config(
                performance_analytic_config, change_analytic_config
            )
            
            # Level 1: Plotflow configs
            performance_plotflow_config = self._build_performance_plotflow_config(
                analytics_orchestrator_config, parent_enable_flags
            )
            hardware_change_plotflow_config = self._build_hardware_change_plotflow_config(
                analytics_orchestrator_config, parent_enable_flags
            )
            
            # Level 0: Dashboard builder config (top)
            builder_config = self._build_dashboard_builder_config(
                performance_plotflow_config, 
                hardware_change_plotflow_config, parent_enable_flags
            )
            
            self.logger.info("Configuration built successfully. Starting dashboard generation...")
            
            # Execute builder
            # NOTE: DashboardBuilder.__init__ will call _apply_auto_configuration()
            builder = DashboardBuilder(builder_config)
            results, log_entries_str = builder.build_dashboards()
            
            self.logger.info("Dashboard generation completed successfully")
            
            return ModuleResult(
                status='success',
                data={
                    'dashboard_results': results,
                    'dashboard_log': log_entries_str
                },
                message='DashboardBuilder completed successfully',
                context_updates={
                    'dashboard_builder_result': results,
                    'dashboard_builder_log': log_entries_str
                }
            )
            
        except Exception as e:
            self.logger.error(f"DashboardBuilder failed: {e}", exc_info=True)
            return ModuleResult(
                status='failed',
                data=None,
                message=f"DashboardBuilder execution failed: {str(e)}",
                errors=[str(e)]
            )
    
    def _extract_parent_flags(self, dashboard_config: Dict) -> Dict:
        """Extract all parent-level enable flags"""
        return {
            # Hardware Change Plotter
            'enable_hardware_change_plotter': dashboard_config.get(
                'enable_hardware_change_plotter', False),
            'enable_hardware_change_machine_layout_plotter': dashboard_config.get(
                'enable_hardware_change_machine_layout_plotter', False),
            'enable_hardware_change_machine_mold_pair_plotter': dashboard_config.get(
                'enable_hardware_change_machine_mold_pair_plotter', False),
            
            # Multi-level Plotter
            'enable_multi_level_plotter': dashboard_config.get(
                'enable_multi_level_plotter', False),
            'enable_multi_level_day_level_plotter': dashboard_config.get(
                'enable_multi_level_day_level_plotter', False),
            'enable_multi_level_month_level_plotter': dashboard_config.get(
                'enable_multi_level_month_level_plotter', False),
            'enable_multi_level_year_level_plotter': dashboard_config.get(
                'enable_multi_level_year_level_plotter', False),
        }
    
    def _build_performance_analytic_config(self):
        """Build PerformanceAnalyticflowConfig (Level 3)"""
        
        perf_config = self.dashboard_config.get('performance_analysis', {})

        if not perf_config:
                self.logger.debug("Cannot load PerformanceAnalytic config")
        
        return PerformanceAnalyticflowConfig(
            # Day Level
            record_date=perf_config.get('record_date'),
            day_save_output=perf_config.get('day_save_output', False),
            
            # Month Level
            record_month=perf_config.get('record_month'),
            month_analysis_date=perf_config.get('month_analysis_date'),
            month_save_output=perf_config.get('month_save_output', False),
            
            # Year Level
            record_year=perf_config.get('record_year'),
            year_analysis_date=perf_config.get('year_analysis_date'),
            year_save_output=perf_config.get('year_save_output', False),
            
            # Shared
            source_path=perf_config.get(
                'source_path', 
                'agents/shared_db/DataLoaderAgent/newest'),

            annotation_name=perf_config.get(
                'annotation_name', 
                'path_annotations.json'),

            databaseSchemas_path=str(self.project_root / perf_config.get(
                'databaseSchemas_path', 'database/databaseSchemas.json')),

            save_multi_level_performance_analyzer_log=perf_config.get('save_log', True),

            multi_level_performance_analyzer_dir=str(self.project_root / perf_config.get(
                'analyzer_dir',
                'agents/shared_db/DashboardBuilder/MultiLevelPerformancePlotter'
            ))
        )
    
    def _build_change_analytic_config(self):
        """Build ChangeAnalyticflowConfig (Level 3)"""
        
        change_config = self.dashboard_config.get('change_analysis', {})

        if not change_config:
                self.logger.debug("Cannot load ChangeAnalytic config")
        
        return ChangeAnalyticflowConfig(
            # Machine Layout Tracker
            enable_machine_layout_tracker=change_config.get('enable_machine_layout_tracker', False),
            machine_layout_tracker_dir=str(self.project_root / change_config.get(
                'machine_layout_tracker_dir',
                'agents/shared_db/DashboardBuilder/HardwareChangePlotter/MachineLayoutTracker'
            )),
            machine_layout_tracker_change_log_name=change_config.get(
                'machine_layout_tracker_change_log_name', 'change_log.txt'),
            
            # Machine-Mold Pair Tracker
            enable_machine_mold_pair_tracker=change_config.get('enable_machine_mold_pair_tracker', False),
            machine_mold_pair_tracker_dir=str(self.project_root / change_config.get(
                'machine_mold_pair_tracker_dir',
                'agents/shared_db/DashboardBuilder/HardwareChangePlotter/MachineMoldPairTracker'
            )),
            machine_mold_pair_tracker_change_log_name=change_config.get(
                'machine_mold_pair_tracker_change_log_name', 'change_log.txt'),
            
            # Shared
            source_path=change_config.get(
                'source_path', 
                'agents/shared_db/DataLoaderAgent/newest'),

            annotation_name=change_config.get(
                'annotation_name', 
                'path_annotations.json'),

            databaseSchemas_path=str(self.project_root / change_config.get(
                'databaseSchemas_path', 'database/databaseSchemas.json')),

            save_hardware_change_analyzer_log=change_config.get('save_log', True),

            hardware_change_analyzer_dir=str(self.project_root / change_config.get(
                'analyzer_dir',
                'agents/shared_db/DashboardBuilder/HardwareChangeAnalyzer'
            ))
        )
    
    def _build_analytics_orchestrator_config(self, 
                                             performance_config, 
                                             change_config):
        """Build AnalyticsOrchestratorConfig (Level 2)"""
        
        analytics_config = self.dashboard_config.get('analytics_orchestrator', {})

        if not analytics_config:
                self.logger.debug("Cannot load AnalyticsOrchestrator config")
        
        return AnalyticsOrchestratorConfig(
            # Parent flags (will be auto-configured by plotters)
            enable_hardware_change_analysis=analytics_config.get(
                'enable_hardware_change_analysis', False),
            enable_multi_level_analysis=analytics_config.get(
                'enable_multi_level_analysis', False),
            
            # Sub-component flags (will be auto-configured)
            enable_hardware_change_machine_layout_tracker=analytics_config.get(
                'enable_hardware_change_machine_layout_tracker', False),
            enable_hardware_change_machine_mold_pair_tracker=analytics_config.get(
                'enable_hardware_change_machine_mold_pair_tracker', False),
            enable_multi_level_day_level_processor=analytics_config.get(
                'enable_multi_level_day_level_processor', False),
            enable_multi_level_month_level_processor=analytics_config.get(
                'enable_multi_level_month_level_processor', False),
            enable_multi_level_year_level_processor=analytics_config.get(
                'enable_multi_level_year_level_processor', False),
            
            # General
            save_analytics_orchestrator_log=analytics_config.get('save_log', True),
            analytics_orchestrator_dir=str(self.project_root / analytics_config.get(
                'dir',
                'agents/shared_db/DashboardBuilder'
            )),
            
            # Nested configs
            performance_config=performance_config,
            change_config=change_config
        )
    
    def _build_performance_plotflow_config(self, 
                                           analytics_config, 
                                           parent_flags: Dict):
        """Build PerformancePlotflowConfig (Level 1)"""
        
        perf_plot_config = self.dashboard_config.get('performance_plotflow', {})

        if not perf_plot_config:
                self.logger.debug("Cannot load PerformancePlotter config")
        
        # Auto-propagate from parent
        multi_level_enabled = parent_flags['enable_multi_level_plotter']
        
        return PerformancePlotflowConfig(
            # Day Level (auto-propagated if parent enabled)
            enable_day_level_plotter=parent_flags['enable_multi_level_day_level_plotter'] if multi_level_enabled else False,
            day_level_visualization_config_path=perf_plot_config.get(
                'day_level_visualization_config_path'),
            
            # Month Level
            enable_month_level_plotter=parent_flags['enable_multi_level_month_level_plotter'] if multi_level_enabled else False,
            month_level_visualization_config_path=perf_plot_config.get(
                'month_level_visualization_config_path'),
            
            # Year Level
            enable_year_level_plotter=parent_flags['enable_multi_level_year_level_plotter'] if multi_level_enabled else False,
            year_level_visualization_config_path=perf_plot_config.get(
                'year_level_visualization_config_path'),
            
            # General
            save_multi_level_performance_plotter_log=perf_plot_config.get('save_log', True),
            multi_level_performance_plotter_dir=str(self.project_root / perf_plot_config.get(
                'plotter_dir',
                'agents/shared_db/DashboardBuilder/MultiLevelPerformancePlotter'
            )),
            
            # Parallel processing
            enable_parallel=perf_plot_config.get('enable_parallel', True),
            max_workers=perf_plot_config.get('max_workers'),
            
            # Nested config
            analytics_orchestrator_config=analytics_config
        )
    
    def _build_hardware_change_plotflow_config(self, 
                                               analytics_config, 
                                               parent_flags: Dict):
        """Build HardwareChangePlotflowConfig (Level 1)"""
        
        hw_plot_config = self.dashboard_config.get('hardware_change_plotflow', {})

        if not hw_plot_config:
                self.logger.debug("Cannot load HardwareChangePlotter config")
        
        # Auto-propagate from parent
        hw_change_enabled = parent_flags['enable_hardware_change_plotter']
        
        return HardwareChangePlotflowConfig(
            # Machine Layout Plotter (auto-propagated if parent enabled)
            enable_machine_layout_plotter=parent_flags['enable_hardware_change_machine_layout_plotter'] if hw_change_enabled else False,
            machine_layout_plotter_result_dir=str(self.project_root / hw_plot_config.get(
                'machine_layout_plotter_result_dir',
                'agents/shared_db/DashboardBuilder/HardwareChangePlotter/MachineLayoutPlotter'
            )),
            machine_layout_visualization_config_path=hw_plot_config.get(
                'machine_layout_visualization_config_path'),
            
            # Machine-Mold Pair Plotter
            enable_machine_mold_pair_plotter=parent_flags['enable_hardware_change_machine_mold_pair_plotter'] if hw_change_enabled else False,
            machine_mold_pair_plotter_result_dir=str(self.project_root / hw_plot_config.get(
                'machine_mold_pair_plotter_result_dir',
                'agents/shared_db/DashboardBuilder/HardwareChangePlotter/MachineMoldPairPlotter'
            )),
            machine_mold_pair_visualization_config_path=hw_plot_config.get(
                'machine_mold_pair_visualization_config_path'),
            
            # General
            save_hardware_change_plotter_log=hw_plot_config.get('save_log', True),
            hardware_change_plotter_dir=str(self.project_root / hw_plot_config.get(
                'plotter_dir',
                'agents/shared_db/DashboardBuilder/HardwareChangePlotter'
            )),
            
            # Parallel processing
            enable_parallel=hw_plot_config.get('enable_parallel', True),
            max_workers=hw_plot_config.get('max_workers'),
            
            # Nested config
            analytics_orchestrator_config=analytics_config
        )
    
    def _build_dashboard_builder_config(self,
                                        performance_plotflow_config, 
                                        hardware_change_plotflow_config,
                                        parent_flags: Dict):
        """Build DashboardBuilderConfig (Level 0 - Top)"""
        
        return DashboardBuilderConfig(
            # Parent enable flags (from YAML)
            enable_hardware_change_plotter=parent_flags['enable_hardware_change_plotter'],
            enable_hardware_change_machine_layout_plotter=parent_flags['enable_hardware_change_machine_layout_plotter'],
            enable_hardware_change_machine_mold_pair_plotter=parent_flags['enable_hardware_change_machine_mold_pair_plotter'],
            
            enable_multi_level_plotter=parent_flags['enable_multi_level_plotter'],
            enable_multi_level_day_level_plotter=parent_flags['enable_multi_level_day_level_plotter'],
            enable_multi_level_month_level_plotter=parent_flags['enable_multi_level_month_level_plotter'],
            enable_multi_level_year_level_plotter=parent_flags['enable_multi_level_year_level_plotter'],
            
            # General
            save_dashboard_builder_log=self.dashboard_config.get('save_log', True),
            dashboard_builder_dir=str(self.project_root / self.dashboard_config.get(
                'builder_dir',
                'agents/shared_db/DashboardBuilder'
            )),
            
            # Nested configs
            performance_plotflow_config=performance_plotflow_config,
            hardware_change_plotflow_config=hardware_change_plotflow_config
        )