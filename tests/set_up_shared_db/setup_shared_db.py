from agents.dataPipelineOrchestrator.data_collector import DataCollector
from agents.dataPipelineOrchestrator.data_loader import DataLoaderAgent
from configs.shared.shared_source_config import SharedSourceConfig

shared_source_config = SharedSourceConfig(
    db_dir = 'tests/mock_database',
    default_dir = 'tests/shared_db'
    )

def test_data_collector_run():
    execution_info = DataCollector(config=shared_source_config).process_all_data()
    assert True

def test_data_loader_run():
    execution_info = DataLoaderAgent(config=shared_source_config).process_all_data()
    assert True