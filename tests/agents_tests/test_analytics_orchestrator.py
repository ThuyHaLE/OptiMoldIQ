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

        # Trigger HardwareChangeAnalyzer-MachineLayoutTracker if True
        enable_machine_layout_tracker = False, # Default: False

        machine_layout_tracker_dir = "tests/shared_db/AnalyticsOrchestrator/HardwareChangeAnalyzer/MachineLayoutTracker",
        #Default: "agents/shared_db/HardwareChangeAnalyzer/MachineLayoutTracker"
        machine_layout_tracker_change_log_name = "change_log.txt",
        #Default: "change_log.txt"

        #---------------------------#
        # MACHINE-MOLD PAIR TRACKER #
        #---------------------------#

        # Trigger HardwareChangeAnalyzer-MachineMoldPairTracker if True
        enable_machine_mold_pair_tracker = False, # Default: False

        machine_mold_pair_tracker_dir = "tests/shared_db/AnalyticsOrchestrator/HardwareChangeAnalyzer/MachineMoldPairTracker",
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
        hardware_change_analyzer_dir = "tests/shared_db/AnalyticsOrchestrator/HardwareChangeAnalyzer",
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
        month_save_output = True, # Default: False

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
        multi_level_performance_analyzer_dir = "tests/shared_db/AnalyticsOrchestrator/MultiLevelPerformanceAnalyzer",
        #Default: "agents/shared_db/AnalyticsOrchestrator/MultiLevelPerformanceAnalyzer"
        )
    
    # AnalyticsOrchestratorConfig
    analytics_orchestrator_config = AnalyticsOrchestratorConfig(

        # Enable AnalyticsOrchestrator components

        #--------------------------#
        # HARDWARE CHANGE ANALYZER #
        #--------------------------#

        # Trigger AnalyticsOrchestrator-HardwareChangeAnalyzer if True
        enable_hardware_change_analysis = True, # Default: False

        # Trigger HardwareChangeAnalyzer-MachineLayoutTracker if True and HardwareChangeAnalyzer enabled
        enable_hardware_change_machine_layout_tracker = True, # Default: False
        # Trigger HardwareChangeAnalyzer-MachineMoldPairTracker if True and HardwareChangeAnalyzer enabled
        enable_hardware_change_machine_mold_pair_tracker = True, # Default: False

        #----------------------------------#
        # MULTI-LEVEL PERFORMANCE ANALYZER #
        #----------------------------------#

        # Trigger AnalyticsOrchestrator-MultiLevelPerformanceAnalyzer if True
        enable_multi_level_analysis = True, # Default: False

        # Trigger MultiLevelPerformanceAnalyzer-DayLevelDataProcessor if True and MultiLevelPerformanceAnalyzer enabled
        enable_multi_level_day_level_processor = True, # Default: False
        # Trigger MultiLevelPerformanceAnalyzer-MonthLevelDataProcessor if True and MultiLevelPerformanceAnalyzer enabled
        enable_multi_level_month_level_processor = True, # Default: False
        # Trigger MultiLevelPerformanceAnalyzer-YearLevelDataProcessor if True and MultiLevelPerformanceAnalyzer enabled
        enable_multi_level_year_level_processor = True, # Default: False

        #---------------------------------------#
        # ANALYTICS ORCHESTRATOR GENERAL CONFIG #
        #---------------------------------------#

        save_analytics_orchestrator_log = True, # Default: True
        analytics_orchestrator_dir='tests/shared_db/AnalyticsOrchestrator',
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
    
    orchestrator = AnalyticsOrchestrator(analytics_orchestrator_config)

    orchestrator_results, orchestrator_log_str = orchestrator.run_analytics()

    assert True