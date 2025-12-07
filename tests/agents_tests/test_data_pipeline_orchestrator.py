from agents.dataPipelineOrchestrator.data_pipeline_orchestrator import SharedSourceConfig, DataPipelineOrchestrator

def test_data_pipeline_orchestrator():
    shared_source_config = SharedSourceConfig(
        db_dir = 'tests/mock_database',
        default_dir = 'tests/shared_db'
    )

    data_pipeline_orchestrator = DataPipelineOrchestrator(
        config = shared_source_config)
    result, log_str = data_pipeline_orchestrator.run_pipeline()

    assert True
