from configs.shared.shared_source_config import SharedSourceConfig
from agents.autoPlanner.initialPlanner.optimizer.hybrid_suggest_optimizer.hybrid_suggest_optimizer import HybridSuggestConfig, HybridSuggestOptimizer

def test_hybrid_suggest_optimizer():
    shared_source_config = SharedSourceConfig(
        db_dir = 'tests/mock_database',
        default_dir = 'tests/shared_db'
    )
    optimizer = HybridSuggestOptimizer(
        config = HybridSuggestConfig(
            shared_source_config = shared_source_config))
    result = optimizer.process()
    
    assert True