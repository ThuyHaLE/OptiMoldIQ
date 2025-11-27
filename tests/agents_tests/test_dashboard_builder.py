from agents.analyticsOrchestrator.analyticsConfigs.performance_analyticflow_config import PerformanceAnalyticflowConfig
from agents.analyticsOrchestrator.analyticsConfigs.change_analyticflow_config import ChangeAnalyticflowConfig
from agents.analyticsOrchestrator.analyticsConfigs.analytics_orchestrator_config import AnalyticsOrchestratorConfig
from agents.dashboardBuilder.dashboardBuilderConfigs.performance_plotflow_config import PerformancePlotflowConfig
from agents.dashboardBuilder.dashboardBuilderConfigs.hardware_change_plotflow_config import HardwareChangePlotflowConfig

from agents.dashboardBuilder.dashboardBuilderConfigs.dashboard_builder_config import DashboardBuilderConfig
from agents.dashboardBuilder.dashboard_builder import DashboardBuilder

def test_dashboard_builder():
    
    performance_analytic_config = PerformanceAnalyticflowConfig(
        record_date="2018-11-06",

        record_month="2019-01",
        month_analysis_date="2019-01-15",

        record_year="2019",
        year_analysis_date="2019-12-31",
        
        source_path = 'tests/shared_db/DataLoaderAgent/newest',
        annotation_name = "path_annotations.json",
        databaseSchemas_path = 'database/databaseSchemas.json',

        save_multi_level_performance_analyzer_log = True,
        multi_level_performance_analyzer_dir = "tests/shared_db/DashboardBuilder/MultiLevelPerformancePlotter", 
        )

    change_analytic_config = ChangeAnalyticflowConfig(

        source_path = "tests/shared_db/DataLoaderAgent/newest",
        annotation_name = "path_annotations.json",
        databaseSchemas_path = "tests/mock_database/databaseSchemas.json",
        
        save_hardware_change_analyzer_log = False,
        hardware_change_analyzer_dir = "tests/shared_db/DashboardBuilder/HardwareChangeAnalyzer",

        machine_layout_tracker_dir = "tests/shared_db/DashboardBuilder/HardwareChangePlotter/MachineLayoutTracker",
        machine_layout_tracker_change_log_name = "change_log.txt",

        machine_mold_pair_tracker_dir = "tests/shared_db/DashboardBuilder/HardwareChangePlotter/MachineMoldPairTracker",
        machine_mold_pair_tracker_change_log_name = "change_log.txt"
        )

    analytics_orchestrator_config = AnalyticsOrchestratorConfig(

        save_analytics_orchestrator_log=False,
        analytics_orchestrator_dir='tests/shared_db/DashboardBuilder',
        
        # multiLevelPerformanceAnalyzer config
        performance_config = performance_analytic_config,

        # HardwareChangeAnalyzer config
        change_config=change_analytic_config
    )

    performance_plotflow_config = PerformancePlotflowConfig(
        # HardwareChangePlotter config
        save_multi_level_performance_plotter_log = True,
        multi_level_performance_plotter_dir = "tests/shared_db/DashboardBuilder/MultiLevelPerformancePlotter",

        day_level_visualization_config_path = None,
        month_level_visualization_config_path = None,
        year_level_visualization_config_path = None,

        # Optimal Processing
        enable_parallel = True,  # Enable parallel processing
        max_workers = None,  # Auto-detect optimal worker count

        # AnalyticsOrchestrator config
    analytics_orchestrator_config = analytics_orchestrator_config
        
    )

    hardware_change_plotflow_config = HardwareChangePlotflowConfig(
        
        enable_machine_layout_plotter = True,
        enable_machine_mold_pair_plotter = True,

        # HardwareChangePlotter config
        save_hardware_change_plotter_log = True,
        hardware_change_plotter_dir = "tests/shared_db/DashboardBuilder/HardwareChangePlotter",

        machine_layout_plotter_result_dir = "tests/shared_db/DashboardBuilder/HardwareChangePlotter/MachineLayoutPlotter",
        machine_layout_visualization_config_path = None,

        machine_mold_pair_plotter_result_dir = "tests/shared_db/DashboardBuilder/HardwareChangePlotter/MachineMoldPairPlotter",
        machine_mold_pair_visualization_config_path = None,

        # Optimal Processing
        enable_parallel = True,  # Enable parallel processing
        max_workers = None,  # Auto-detect optimal worker count

        # AnalyticsOrchestrator config
        analytics_orchestrator_config = analytics_orchestrator_config
        
        )
    
    
    dashboard_builder_config = DashboardBuilderConfig(
        enable_multi_level_plotter = True,  # MultiLevelPerformancePlotter
        enable_hardware_change_plotter = True,  # HardwareChangePlotter

        save_dashboard_builder_log = True,
        dashboard_builder_dir = 'tests/shared_db/DashboardBuilder',
        
        performance_plotflow_config = performance_plotflow_config,
        hardware_change_plotflow_config = hardware_change_plotflow_config
    )

    builder = DashboardBuilder(dashboard_builder_config)
    results, log_entries_str = builder.build_dashboards()

    assert True