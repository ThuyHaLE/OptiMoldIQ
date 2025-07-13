from agents.dataPipelineOrchestrator.data_collector import DataCollector
from agents.dataPipelineOrchestrator.data_loader import DataLoaderAgent

def test_data_collector_run():
    DataCollector(
        source_dir="tests/mock_database/dynamicDatabase",
        default_dir="tests/shared_db"
    ).process_all_data()
    assert True

def test_data_loader_run():
    DataLoaderAgent(
        databaseSchemas_path="tests/mock_database/databaseSchemas.json",
        annotation_path="tests/shared_db/DataLoaderAgent/newest/path_annotations.json",
        default_dir="tests/shared_db"
    ).process_all_data()
    assert True