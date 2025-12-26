# tests/agents_tests/test_historical_features_extractor.py

import pytest
from tests.agents_tests.base_agent_tests import BaseAgentTests
from tests.agents_tests.conftest import DependencyProvider
from configs.shared.agent_report_format import ExecutionStatus

class TestHistoricalFeaturesExtractor(BaseAgentTests):
    """
    Agent with dependency - auto declares its needs via dependency_provider
    """
    
    @pytest.fixture
    def agent_instance(self, dependency_provider: DependencyProvider):
        """
        ⭐ Agent self declares dependency requirements
        """
        from agents.autoPlanner.featureExtractor.initial.historicalFeaturesExtractor.historical_features_extractor import (
            HistoricalFeaturesExtractor, FeaturesExtractorConfig
        )
        
        # Get config
        shared_config = dependency_provider.get_shared_source_config()
        
        # Trigger dependency (only if this test runs)
        dependency_provider.trigger_order_progress_tracker(shared_config)
        
        # Create agent
        return HistoricalFeaturesExtractor(
            config=FeaturesExtractorConfig(
                efficiency=0.85,
                loss=0.03,
                shared_source_config=shared_config
            )
        )
    
    @pytest.fixture
    def execution_result(self, agent_instance):
        result = agent_instance.run_extraction_and_save_results()
        assert result.status != ExecutionStatus.FAILED.value, "Agent execution failed - test setup error"
        return result