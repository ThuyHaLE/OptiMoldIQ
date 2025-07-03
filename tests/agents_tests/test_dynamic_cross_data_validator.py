from agents.crossDataChecker.dynamic_cross_data_validator import DynamicCrossDataValidator

def test_dynamic_cross_data_validator():
    dynamic_cross_data_validator = DynamicCrossDataValidator(source_path = 'tests/shared_db/DataLoaderAgent/newest',
                                                             annotation_name = "path_annotations.json",
                                                             databaseSchemas_path = 'tests/mock_database/databaseSchemas.json',
                                                             default_dir = "tests/shared_db")
    dynamic_cross_data_validator.run_validations_and_save_results()

    # Nếu không có exception thì pass
    assert True