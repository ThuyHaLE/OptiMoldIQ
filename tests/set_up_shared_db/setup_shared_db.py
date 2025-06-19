from agents.dataCollector import DataCollector
from agents.dataLoader import DataLoaderAgent

def test_data_collector_run():
    DataCollector(
        source_dir="tests/mock_data/dynamicDatabase",
        default_dir="tests/shared_db"
    )
    assert True

def test_data_loader_run():
    DataLoaderAgent(
        databaseSchemas_path="tests/mock_data/databaseSchemas.json",
        annotation_path="tests/shared_db/DataLoaderAgent/newest/path_annotations.json",
        default_dir="tests/shared_db"
    )
    assert True