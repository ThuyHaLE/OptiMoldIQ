from configs.shared.shared_source_config import SharedSourceConfig
from agents.autoPlanner.featureExtractor.initial.historicalFeaturesExtractor.historical_features_extractor import (
    HistoricalFeaturesExtractor, FeaturesExtractorConfig)

def test_historical_features_extractor():
    features_extractor_config = FeaturesExtractorConfig(
        shared_source_config = SharedSourceConfig(
            db_dir = 'tests/mock_database',
            default_dir = 'tests/shared_db'
            )
        )   
    extractor = HistoricalFeaturesExtractor(config = features_extractor_config)
    result, log_str = extractor.run_extraction()
    assert True