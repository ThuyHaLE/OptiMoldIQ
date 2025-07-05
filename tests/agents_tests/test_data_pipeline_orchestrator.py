from agents.dataPipelineOrchestrator.data_pipeline_orchestrator import DataPipelineOrchestrator

def test_data_pipeline_orchestrator():
    data_pipeline_orchestrator = DataPipelineOrchestrator(dynamic_db_source_dir="tests/mock_database/dynamicDatabase",
                                                          databaseSchemas_path = "tests/mock_database/databaseSchemas.json",
                                                          annotation_path = 'tests/shared_db/DataLoaderAgent/newest/path_annotations.json"',
                                                          default_dir= "tests/shared_db")
    
    data_pipeline_orchestrator.run_pipeline()

    assert True