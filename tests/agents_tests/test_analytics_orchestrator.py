from agents.analyticsOrchestrator.analyticsConfigs.change_analyticflow_config import ChangeAnalyticflowConfig
from agents.analyticsOrchestrator.analyticsConfigs.performance_analyticflow_config import PerformanceAnalyticflowConfig
from agents.analyticsOrchestrator.analytics_orchestrator import AnalyticsOrchestratorConfig, AnalyticsOrchestrator

def test_analytics_orchestrator():
    
    # ChangeAnalyticflowConfig
    change_analytic_config = ChangeAnalyticflowConfig(

        # Enable HardwareChangeAnalyzer components

        #------------------------#
        # MACHINE LAYOUT TRACKER #
        #------------------------#

        # Trigger HardwareChangeAnalyzer-MachineLayoutTracker if record_date is not None
        enable_machine_layout_tracker = False, # Default: False

        machine_layout_tracker_dir = "tests/shared_db/DashboardBuilder/HardwareChangePlotter/MachineLayoutTracker",
        #Default: "agents/shared_db/HardwareChangeAnalyzer/MachineLayoutTracker"
        machine_layout_tracker_change_log_name = "change_log.txt",
        #Default: "change_log.txt"

        #---------------------------#
        # MACHINE-MOLD PAIR TRACKER #
        #---------------------------#

        # Trigger HardwareChangeAnalyzer-MachineMoldPairTracker if record_date is not None
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
    
    # AnalyticsOrchestratorConfig
    analytics_orchestrator_config = AnalyticsOrchestratorConfig(

        # Enable AnalyticsOrchestrator components

        #--------------------------#
        # HARDWARE CHANGE ANALYZER #
        #--------------------------#

        # Trigger AnalyticsOrchestrator-HardwareChangeAnalyzer if True
        enable_hardware_change_analysis = False, # Default: False

        #----------------------------------#
        # MULTI-LEVEL PERFORMANCE ANALYZER #
        #----------------------------------#

        # Trigger AnalyticsOrchestrator-MultiLevelPerformanceAnalyzer if True
        enable_multi_level_analysis = False, # Default: False

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

    )
    
    orchestrator = AnalyticsOrchestrator(analytics_orchestrator_config)

    orchestrator_results, orchestrator_log_str = orchestrator.run_analytics()

    assert True