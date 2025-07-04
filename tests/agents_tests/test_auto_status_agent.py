from agents.autoStatus.auto_status_agent import AutoStatusAgent

def test_auto_status_agent():
    auto_status_agent = AutoStatusAgent(source_path = 'tests/shared_db/DataLoaderAgent/newest',
                                        annotation_name = "path_annotations.json",
                                        databaseSchemas_path = 'tests/mock_database/databaseSchemas.json',
                                        folder_path = "tests/shared_db/ValidationOrchestrator", 
                                        target_name = "change_log.txt",
                                        default_dir = "tests/shared_db")
    
    auto_status_agent.pro_status()

    # Nếu không có exception thì pass
    assert True