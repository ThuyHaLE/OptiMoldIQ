from agents.analyticsOrchestrator.analyticsConfigs.performance_analyticflow_config import PerformanceAnalyticflowConfig
from agents.analyticsOrchestrator.analyticsConfigs.change_analyticflow_config import ChangeAnalyticflowConfig
from agents.analyticsOrchestrator.analyticsConfigs.analytics_orchestrator_config import AnalyticsOrchestratorConfig
from agents.dashboardBuilder.dashboardBuilderConfigs.performance_plotflow_config import PerformancePlotflowConfig
from agents.dashboardBuilder.dashboardBuilderConfigs.hardware_change_plotflow_config import HardwareChangePlotflowConfig

from agents.dashboardBuilder.dashboardBuilderConfigs.dashboard_builder_config import DashboardBuilderConfig
from agents.dashboardBuilder.dashboard_builder import DashboardBuilder

def test_dashboard_builder():

    # PerformanceAnalyticflowConfig
    performance_analytic_config = PerformanceAnalyticflowConfig(
        
        # Enable MultiLevelPerformanceAnalyzer components

        #--------------------------------#
        # DAY-LEVEL PERFORMANCE ANALYZER #
        #--------------------------------#

        # Trigger MultiLevelPerformanceAnalyzer-DayLevelDataProcessor if record_date is not None
        record_date="2018-11-06", # Default: None
        day_save_output = False, # Default: False

        #----------------------------------#
        # MONTH-LEVEL PERFORMANCE ANALYZER #
        #----------------------------------#

        # Trigger MultiLevelPerformanceAnalyzer-MonthLevelDataProcessor if record_month is not None
        record_month="2019-01", # Default: None
        month_analysis_date="2019-01-15", # Default: None    
        month_save_output = False, # Default: False

        #---------------------------------#
        # YEAR-LEVEL PERFORMANCE ANALYZER #
        #---------------------------------#     

        # Trigger MultiLevelPerformanceAnalyzer-YearLevelDataProcessor if record_year is not None
        record_year="2019", # Default: None
        year_analysis_date="2019-12-31", # Default: None
        year_save_output = False, # Default: False
        
        #-------------------------------------------------#
        # MULTI-LEVEL PERFORMANCE ANALYZER GENERAL CONFIG #
        #-------------------------------------------------#

        source_path = 'tests/shared_db/DataLoaderAgent/newest', # Default: 'agents/shared_db/DataLoaderAgent/newest' 
        annotation_name = "path_annotations.json", # Default: "path_annotations.json"
        databaseSchemas_path = 'database/databaseSchemas.json', # Default: 'database/databaseSchemas.json'
    
        save_multi_level_performance_analyzer_log = True, # Default: True
        multi_level_performance_analyzer_dir = "tests/shared_db/DashboardBuilder/MultiLevelPerformancePlotter", 
        #Default: "agents/shared_db/AnalyticsOrchestrator/MultiLevelPerformanceAnalyzer"
        )

    # ChangeAnalyticflowConfig
    change_analytic_config = ChangeAnalyticflowConfig(
        
        # Enable HardwareChangeAnalyzer components

        #------------------------#
        # MACHINE LAYOUT TRACKER #
        #------------------------#

        # Trigger HardwareChangeAnalyzer-MachineLayoutTracker if True
        enable_machine_layout_tracker = False, # Default: False

        machine_layout_tracker_dir = "tests/shared_db/DashboardBuilder/HardwareChangePlotter/MachineLayoutTracker", 
        #Default: "agents/shared_db/HardwareChangeAnalyzer/MachineLayoutTracker"
        machine_layout_tracker_change_log_name = "change_log.txt", 
        #Default: "change_log.txt"

        #---------------------------#
        # MACHINE-MOLD PAIR TRACKER #
        #---------------------------#

        # Trigger HardwareChangeAnalyzer-MachineMoldPairTracker if True
        enable_machine_mold_pair_tracker = False, # Default: False

        machine_mold_pair_tracker_dir = "tests/shared_db/DashboardBuilder/HardwareChangePlotter/MachineMoldPairTracker", 
        #Default: "agents/shared_db/HardwareChangeAnalyzer/MachineMoldPairTracker"
        machine_mold_pair_tracker_change_log_name = "change_log.txt" ,
        #Default: "change_log.txt"

        #-----------------------------------------#
        # HARDWARE CHANGE ANALYZER GENERAL CONFIG #
        #-----------------------------------------#

        source_path = "tests/shared_db/DataLoaderAgent/newest", # Default: 'agents/shared_db/DataLoaderAgent/newest'
        annotation_name = "path_annotations.json", # Default: "path_annotations.json"
        databaseSchemas_path = "tests/mock_database/databaseSchemas.json", # Default: 'database/databaseSchemas.json'

        save_hardware_change_analyzer_log = True, # Default: True
        hardware_change_analyzer_dir = "tests/shared_db/DashboardBuilder/HardwareChangeAnalyzer", 
        # Default: "agents/shared_db/HardwareChangeAnalyzer"

    )

    # AnalyticsOrchestratorConfig
    analytics_orchestrator_config = AnalyticsOrchestratorConfig(
        
        # Enable AnalyticsOrchestrator components
        
        #--------------------------#
        # HARDWARE CHANGE ANALYZER #
        #--------------------------# 

        # Trigger AnalyticsOrchestrator-HardwareChangeAnalyzer if True
        enable_hardware_change_analysis = False, # Default: False 
        # Trigger HardwareChangeAnalyzer-MachineLayoutTracker if True and HardwareChangeAnalyzer enabled
        enable_hardware_change_machine_layout_tracker = False, # Default: False
        # Trigger HardwareChangeAnalyzer-MachineMoldPairTracker if True and HardwareChangeAnalyzer enabled
        enable_hardware_change_machine_mold_pair_tracker = False, # Default: False

        #----------------------------------#
        # MULTI-LEVEL PERFORMANCE ANALYZER #
        #----------------------------------#

        # Trigger AnalyticsOrchestrator-MultiLevelPerformanceAnalyzer if True
        enable_multi_level_analysis = False, # Default: False

        # Trigger MultiLevelPerformanceAnalyzer-DayLevelDataProcessor if True and MultiLevelPerformanceAnalyzer enabled
        enable_multi_level_day_level_processor = False, # Default: False
        # Trigger MultiLevelPerformanceAnalyzer-MonthLevelDataProcessor if True and MultiLevelPerformanceAnalyzer enabled
        enable_multi_level_month_level_processor = False, # Default: False
        # Trigger MultiLevelPerformanceAnalyzer-YearLevelDataProcessor if True and MultiLevelPerformanceAnalyzer enabled
        enable_multi_level_year_level_processor = False, # Default: False
        
        #---------------------------------------#
        # ANALYTICS ORCHESTRATOR GENERAL CONFIG #
        #---------------------------------------#

        save_analytics_orchestrator_log = True, # Default: True
        analytics_orchestrator_dir='tests/shared_db/DashboardBuilder',
        #Default: 'agents/shared_db/AnalyticsOrchestrator'

        #---------------------#
        # DEPENDENCIES CONFIG #
        #---------------------#

        # PerformanceAnalyticflowConfig for MultiLevelPerformanceAnalyzer if MultiLevelPerformanceAnalyzer True
        performance_config = performance_analytic_config,
        #Default: PerformanceAnalyticflowConfig = field(default_factory=PerformanceAnalyticflowConfig)

        # ChangeAnalyticflowConfig for HardwareChangeAnalyzer if HardwareChangeAnalyzer True
        change_config=change_analytic_config
        #Default: ChangeAnalyticflowConfig = field(default_factory=ChangeAnalyticflowConfig)

        #--------------------#
        # AUTO CONFIGURATION #
        #--------------------#
        # Auto-configured by AnalyticsOrchestrator._apply_auto_configuration() at initialization.
        # Parent enable flags are automatically propagated to nested analyzer configs:
        #
        # enable_multi_level_analysis → performance_config.enable_*_level_processor
        # enable_hardware_change_analysis → change_config.enable_*_tracker
        #
        # Manual settings below will be overridden. See _apply_auto_configuration() for details.
        
    )

    # PerformancePlotflowConfig
    performance_plotflow_config = PerformancePlotflowConfig(
        
        # Enable MultiLevelPerformancePlotter components

        #-------------------------------#
        # DAY-LEVEL PERFORMANCE PLOTTER #
        #-------------------------------#

        # Trigger MultiLevelPerformancePlotter-DayLevelDataPlotter if True
        # MultiLevelPerformancePlotter-DayLevelDataPlotter trigger AnalyticsOrchestrator-MultiLevelPerformanceAnalyzer-DayLevelDataPlotter
        enable_day_level_plotter = False, # Default: False
        day_level_visualization_config_path = None, # Default: None

        #---------------------------------#
        # MONTH-LEVEL PERFORMANCE PLOTTER #
        #---------------------------------#

        # Trigger MultiLevelPerformancePlotter-MonthLevelDataPlotter if True
        # MultiLevelPerformancePlotter-MonthLevelDataPlotter trigger AnalyticsOrchestrator-MultiLevelPerformanceAnalyzer-MonthLevelDataPlotter
        enable_month_level_plotter = False, # Default: False
        month_level_visualization_config_path = None, # Default: None
        
        #--------------------------------#
        # YEAR-LEVEL PERFORMANCE PLOTTER #
        #--------------------------------#

        # Trigger MultiLevelPerformancePlotter-YearLevelDataPlotter if True
        # MultiLevelPerformancePlotter-YearLevelDataPlotter trigger AnalyticsOrchestrator-MultiLevelPerformanceAnalyzer-YearLevelDataPlotter
        enable_year_level_plotter = False, # Default: False
        year_level_visualization_config_path = None, # Default: None
        
        #------------------------------------------------#
        # MULTI-LEVEL PERFORMANCE PLOTTER GENERAL CONFIG #
        #------------------------------------------------#

        save_multi_level_performance_plotter_log = True, # Default: True
        multi_level_performance_plotter_dir = "tests/shared_db/DashboardBuilder/MultiLevelPerformancePlotter",
        #Default: "agents/shared_db/DashboardBuilder/MultiLevelPerformancePlotter"

        # Optimal Processing
        enable_parallel = True,  # Enable parallel processing # Default: True
        max_workers = None,  # Auto-detect optimal worker count # Default: None

        #---------------------#
        # DEPENDENCIES CONFIG #
        #---------------------#

        # AnalyticsOrchestratorConfig for AnalyticsOrchestrator if MultiLevelPerformancePlotter True
        analytics_orchestrator_config = analytics_orchestrator_config
        #Default: AnalyticsOrchestratorConfig = field(default_factory=AnalyticsOrchestratorConfig)

        #--------------------#
        # AUTO CONFIGURATION #
        #--------------------#
        # Auto-configured by MultiLevelPerformancePlotter._apply_auto_configuration() at initialization.
        # Propagation rules:
        #
        #   Any level plotter enabled → enable_multi_level_analysis = True
        #   record_date/month/year exists → corresponding save_output = True
        #   Analyzer logging forced enabled
        #
        # Manual analytics_orchestrator_config settings will be overridden. Check logs for details.

    )

    # HardwareChangePlotflowConfig
    hardware_change_plotflow_config = HardwareChangePlotflowConfig(

        # Enable HardwareChangePlotter components

        #-------------------------------#
        # MACHINE LAYOUT CHANGE PLOTTER #
        #-------------------------------#

        # Trigger HardwareChangePlotter-MachineLayoutPlotter if True
        # HardwareChangePlotter-MachineLayoutPlotter trigger AnalyticsOrchestrator-HardwareChangeAnalyzer-MachineLayoutTracker
        
        enable_machine_layout_plotter = False, # Default: False

        machine_layout_plotter_result_dir = "tests/shared_db/DashboardBuilder/HardwareChangePlotter/MachineLayoutPlotter",
        # Default: "agents/shared_db/DashboardBuilder/HardwareChangePlotter/MachineLayoutPlotter"
        machine_layout_visualization_config_path = None, # Default: None

        #----------------------------------#
        # MACHINE-MOLD PAIR CHANGE PLOTTER #
        #----------------------------------#

        # Trigger HardwareChangePlotter-MachineMoldPairPlotter if True
        # HardwareChangePlotter-MachineMoldPairPlotter trigger AnalyticsOrchestrator-HardwareChangeAnalyzer-MachineMoldPairPlotter
        enable_machine_mold_pair_plotter = False, # Default: False

        machine_mold_pair_plotter_result_dir = "tests/shared_db/DashboardBuilder/HardwareChangePlotter/MachineMoldPairPlotter",
        #Default: "agents/shared_db/DashboardBuilder/HardwareChangePlotter/MachineMoldPairPlotter"
        machine_mold_pair_visualization_config_path = None, # Default: None
        
        #----------------------------------------#
        # HARDWARE CHANGE PLOTTER GENERAL CONFIG #
        #----------------------------------------#
        save_hardware_change_plotter_log = True, # Default: True
        hardware_change_plotter_dir = "tests/shared_db/DashboardBuilder/HardwareChangePlotter",
        # Default: "agents/shared_db/DashboardBuilder/HardwareChangePlotter"

        # Optimal Processing
        enable_parallel = True,  # Enable parallel processing # Default: True
        max_workers = None,  # Auto-detect optimal worker count # Default: None

        #---------------------#
        # DEPENDENCIES CONFIG #
        #---------------------#

        # AnalyticsOrchestratorConfig for AnalyticsOrchestrator if MachineLayoutPlotter True
        analytics_orchestrator_config = analytics_orchestrator_config
        #Default: AnalyticsOrchestratorConfig = field(default_factory=AnalyticsOrchestratorConfig)

        #--------------------#
        # AUTO CONFIGURATION #
        #--------------------#
        # Auto-configured by HardwareChangePlotter._apply_auto_configuration() at initialization.
        # Propagation rules:
        #
        #   Any plotter enabled → enable_hardware_change_analysis = True
        #   Specific plotter → corresponding tracker enabled
        #   Intermediate logging forced disabled (orchestrator & analyzer logs)
        #
        # Manual analytics_orchestrator_config settings will be overridden. Check logs for details.

        )

    # DashboardBuilderConfig
    dashboard_builder_config = DashboardBuilderConfig(
        
        # Enable DashboardBuilder components

        #-------------------------#
        # HARDWARE CHANGE PLOTTER #
        #-------------------------#

        #  Trigger HardwareChangePlotter if True 
        enable_hardware_change_plotter = True, # Default: False
        
        # Trigger HardwareChangePlotter-MachineLayoutPlotter if True and HardwareChangePlotter enabled
        enable_hardware_change_machine_layout_plotter = True, # Default: False
        # Trigger HardwareChangePlotter-MachineMoldPairPlotter if True
        enable_hardware_change_machine_mold_pair_plotter = True, # Default: False
        
        #---------------------------------#
        # MULTI-LEVEL PERFORMANCE PLOTTER #
        #---------------------------------#

        # Trigger MultiLevelPerformancePlotter if True
        enable_multi_level_plotter = True, # Default: False
        
        # Trigger MultiLevelPerformancePlotter-DayLevelDataPlotter if True and MultiLevelPerformancePlotter enabled
        enable_multi_level_day_level_plotter = True, # Default: False
        # Trigger MultiLevelPerformancePlotter-MonthLevelDataPlotter if True and MultiLevelPerformancePlotter enabled
        enable_multi_level_month_level_plotter = True, # Default: False
        # Trigger MultiLevelPerformancePlotter-YearLevelDataPlotter if True and MultiLevelPerformancePlotter enabled
        enable_multi_level_year_level_plotter = True, # Default: False

        #----------------------------------#
        # DASHBOARD BUILDER GENERAL CONFIG #
        #----------------------------------#

        save_dashboard_builder_log = True, # Default: False
        dashboard_builder_dir = 'tests/shared_db/DashboardBuilder', #Default: 'agents/shared_db/DashboardBuilder'
        
        #---------------------#
        # DEPENDENCIES CONFIG #
        #---------------------#

        # PerformancePlotflowConfig for MultiLevelPerformancePlotter if MultiLevelPerformancePlotter enabled
        performance_plotflow_config = performance_plotflow_config,
        #Default: PerformancePlotflowConfig = field(default_factory=PerformancePlotflowConfig)

        # HardwareChangePlotflowConfig for HardwareChangePlotter if HardwareChangePlotter enabled
        hardware_change_plotflow_config = hardware_change_plotflow_config
        #Default: HardwareChangePlotflowConfig = field(default_factory=HardwareChangePlotflowConfig)

        #--------------------#
        # AUTO CONFIGURATION #
        #--------------------#
        # Auto-configured by DashboardBuilder._apply_auto_configuration() at initialization.
        # Parent enable flags are automatically propagated to nested plotter configs:
        #
        # enable_multi_level_plotter → performance_plotflow_config.enable_*_level_plotter
        # enable_hardware_change_plotter → hardware_change_plotflow_config.enable_*_plotter
        #
        # Manual settings below will be overridden. See _apply_auto_configuration() for details.

    ) 

    builder = DashboardBuilder(dashboard_builder_config)
    results, log_entries_str = builder.build_dashboards()

    assert True

test_dashboard_builder()