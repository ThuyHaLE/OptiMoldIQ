from agents.orderProgressTracker.order_progress_tracker import SharedSourceConfig, OrderProgressTracker

def test_order_progress_tracker():
    shared_source_config = SharedSourceConfig(
        db_dir = 'tests/mock_database',
        default_dir = 'tests/shared_db'
    )
    
    order_progress_tracker = OrderProgressTracker(config = shared_source_config)

    result = order_progress_tracker.run_tracking_and_save_results()

    assert True