from configs.shared.shared_source_config import SharedSourceConfig
from agents.autoPlanner.initialPlanner.processor.producing_processor import ProducingProcessorConfig, ProducingProcessor
from agents.autoPlanner.initialPlanner.processor.pending_processor import PendingProcessorConfig, PendingProcessor

def test_initial_planner():
    shared_source_config = SharedSourceConfig(
        db_dir = 'tests/mock_database',
        default_dir = 'tests/shared_db'
    )

    # ProducingProcessor
    processor = ProducingProcessor(
        config = ProducingProcessorConfig(
            shared_source_config = shared_source_config))
    results, log_str  = processor.process_and_save_results()
    
    # PendingProcessor
    processor = PendingProcessor(
        config = PendingProcessorConfig(
            shared_source_config = shared_source_config)
    )
    results, log_str  = processor.process_and_save_results()

    assert True