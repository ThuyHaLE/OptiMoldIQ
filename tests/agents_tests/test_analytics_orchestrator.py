from agents.analyticsOrchestrator.analytics_orchestrator import AnalyticsOrchestratorConfig, AnalyticsOrchestrator

def test_analytics_orchestrator():
    
    orchestrator = AnalyticsOrchestrator(
        AnalyticsOrchestratorConfig(
        # Enable AnalyticsOrchestrator components
        enable_change_analysis = True,
        enable_multi_level_analysis = True,

        # Database sources
        source_path = "tests/shared_db/DataLoaderAgent/newest",
        annotation_name = "path_annotations.json",
        databaseSchemas_path = "tests/mock_database/databaseSchemas.json",
        default_dir = "tests/shared_db/AnalyticsOrchestrator",

        # HardwareChangeAnalyzer config
        enable_machine_layout_tracker = True,
        enable_machine_mold_pair_tracker = True,
        change_tracker_output_dir = "tests/shared_db/AnalyticsOrchestrator/DataChangeAnalyzer",
        machine_layout_tracker_dir = "tests/shared_db/AnalyticsOrchestrator/DataChangeAnalyzer/UpdateMachineLayout/tracker_results",
        machine_layout_tracker_change_log_name = "change_log.txt",
        machine_mold_pair_tracker_dir = "tests/shared_db/AnalyticsOrchestrator/DataChangeAnalyzer/UpdateMoldOverview/tracker_results",
        machine_mold_pair_tracker_change_log_name = "change_log.txt",

        # MultiLevelPerformanceAnalyzer config
        record_date="2018-11-06",
        day_save_output = False,
        record_month="2019-01",
        month_analysis_date="2019-01-15",
        month_save_output = False,
        record_year="2019",
        year_analysis_date="2019-12-31",
        year_save_output = True,
        multi_level_output_dir = "tests/shared_db/AnalyticsOrchestrator/MultiLevelDataPlotter"
        )
    )

    results = orchestrator.run_analytics()

    assert True