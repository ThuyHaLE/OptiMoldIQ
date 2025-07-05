from agents.orderProgressTracker.order_progress_tracker import OrderProgressTracker

def test_order_progress_tracker():
    order_progress_tracker = OrderProgressTracker(source_path = 'tests/shared_db/DataLoaderAgent/newest',
                                                  annotation_name = "path_annotations.json",
                                                  databaseSchemas_path = 'tests/mock_database/databaseSchemas.json',
                                                  folder_path = "tests/shared_db/ValidationOrchestrator", 
                                                  target_name = "change_log.txt",
                                                  default_dir = "tests/shared_db")
    
    order_progress_tracker.pro_status()

    # Nếu không có exception thì pass
    assert True