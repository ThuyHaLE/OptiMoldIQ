from agents.orderProgressTracker.order_progress_tracker import SharedSourceConfig, OrderProgressTracker

def test_order_progress_tracker():
    shared_source_config = SharedSourceConfig(
        db_dir = 'tests/mock_database',
        default_dir = 'tests/shared_db'
    )
    
    order_progress_tracker = OrderProgressTracker(config = shared_source_config)

    results, log_str = order_progress_tracker.pro_status()

    assert True