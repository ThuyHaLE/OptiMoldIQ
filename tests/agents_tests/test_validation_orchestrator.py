from agents.crossDataChecker.dynamic_cross_data_validator import ValidationOrchestrator

def test_validation_orchestrator():
    validation_orchestrator = ValidationOrchestrator(source_path = 'tests/shared_db/DataLoaderAgent/newest',
                                                     annotation_name = "path_annotations.json",
                                                     databaseSchemas_path = 'tests/mock_database/databaseSchemas.json',
                                                     default_dir = "tests/shared_db")
    validation_orchestrator.run_validations_and_save_results()

    # Nếu không có exception thì pass
    assert True