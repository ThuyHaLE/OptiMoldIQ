from agents.validationOrchestrator.validation_orchestrator import ValidationOrchestrator

def test_validation_orchestrator():
    validation_orchestrator = ValidationOrchestrator(
    source_path = 'tests/shared_db/DataLoaderAgent/newest',
    annotation_name = "path_annotations.json",
    databaseSchemas_path = 'tests/mock_database/databaseSchemas.json',
    default_dir = "tests/shared_db")

    results, log_str = validation_orchestrator.run_validations_and_save_results()

    assert True