from agents.validationOrchestrator.static_cross_data_checker import StaticCrossDataChecker

def test_static_cross_data_checker():
    static_cross_data_checker = StaticCrossDataChecker(checking_df_name = ['productRecords', 'purchaseOrders'],
                                                       source_path = 'tests/shared_db/DataLoaderAgent/newest',
                                                       annotation_name = "path_annotations.json",
                                                       databaseSchemas_path = 'tests/mock_database/databaseSchemas.json',
                                                       default_dir = "tests/shared_db")
    static_cross_data_checker.run_validations_and_save_results()

    # Nếu không có exception thì pass
    assert True