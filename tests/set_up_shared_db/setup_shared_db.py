from agents.dataPipelineOrchestrator.data_pipeline_orchestrator import DataPipelineOrchestrator
from configs.shared.shared_source_config import SharedSourceConfig

shared_source_config = SharedSourceConfig(
    db_dir = 'tests/mock_database',
    default_dir = 'tests/shared_db'
    )

def test_data_collector_run():
    pipeline_processsor = DataPipelineOrchestrator(config = shared_source_config)
    pipeline_result = pipeline_processsor.run_collecting_and_save_results()
    assert True