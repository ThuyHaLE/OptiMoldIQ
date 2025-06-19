from agents.dataAnalytics.multiLevelDataAnalytics.day_level_data_analytics import DayLevelDataAnalytics

def test_day_level_data_analytics():
    analytics = DayLevelDataAnalytics(selected_date = "2018-11-01",
                      source_path = 'tests/shared_db/DataLoaderAgent/newest',
                      annotation_name = "path_annotations.json",
                      databaseSchemas_path = 'tests/mock_database/databaseSchemas.json',
                      default_dir = "tests/shared_db")
    
    analytics.report_dayworkingshift_level()

    # Nếu không có exception thì pass
    assert True