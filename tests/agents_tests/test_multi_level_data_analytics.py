from agents.analyticsOrchestrator.multiLevelDataAnalytics.multi_level_data_processor import AnalyticflowConfig, MultiLevelDataAnalytics

def test_multi_level_data_analytics():

    # Process day-level only
    analytics_day = MultiLevelDataAnalytics(
        AnalyticflowConfig(
            record_date="2025-11-16",
            source_path = 'tests/shared_db/DataLoaderAgent/newest', 
            annotation_name = "path_annotations.json",
            databaseSchemas_path = 'tests/mock_database/databaseSchemas.json',
            default_dir ='tests/shared_db'
            )
    )
    results_day = analytics_day.data_process()

    # Process day + month only
    analytics_day_month = MultiLevelDataAnalytics(
        AnalyticflowConfig(
            record_date="2025-11-16",
            record_month="2025-11",
            month_analysis_date="2025-11-16",
            source_path = 'tests/shared_db/DataLoaderAgent/newest', 
            annotation_name = "path_annotations.json",
            databaseSchemas_path = 'tests/mock_database/databaseSchemas.json',
            default_dir ='tests/shared_db'
            )
        )
    results_day_month = analytics_day_month.data_process()

    # Process all levels
    analytics_all = MultiLevelDataAnalytics(
        AnalyticflowConfig(
            record_date="2018-11-06",
            record_month="2019-01",
            month_analysis_date="2019-01-15",
            record_year="2019",
            year_analysis_date="2019-12-31",
            source_path = 'tests/shared_db/DataLoaderAgent/newest', 
            annotation_name = "path_annotations.json",
            databaseSchemas_path = 'tests/mock_database/databaseSchemas.json',
            default_dir ='tests/shared_db'
        )
    )
    results_all = analytics_all.data_process()

    # Nếu không có exception thì pass
    assert True
