from agents.validationOrchestrator.validation_orchestrator import SharedSourceConfig, ValidationOrchestrator

def test_validation_orchestrator():

    shared_source_config = SharedSourceConfig(
        db_dir = 'tests/mock_database',
        default_dir = 'tests/shared_db'
    )

    result = ValidationOrchestrator(
        shared_source_config=shared_source_config,
        enable_parallel = False,
        max_workers = None).run_validations_and_save_results()
    
    assert True