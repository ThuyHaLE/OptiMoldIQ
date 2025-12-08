from agents.validationOrchestrator.validation_orchestrator import SharedSourceConfig, ValidationOrchestrator

def test_validation_orchestrator():

    shared_source_config = SharedSourceConfig(
        db_dir = 'tests/mock_database',
        default_dir = 'tests/shared_db'
    )

    final_report, validation_log_str = ValidationOrchestrator(
        shared_source_config=shared_source_config,
        enable_parallel = False,
        max_workers = None).run_validations_and_save_results()
    
    assert True