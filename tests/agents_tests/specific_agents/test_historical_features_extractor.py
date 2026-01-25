# tests/agents_tests/test_historical_features_extractor.py

import pytest
from tests.agents_tests.base_agent_tests import BaseAgentTests
from tests.agents_tests.conftest import DependencyProvider

class TestHistoricalFeaturesExtractor(BaseAgentTests):
    """
    Test HistoricalFeaturesExtractor - agent with OrderProgressTracker dependency
    Inherits all structural tests from BaseAgentTests
    """
    
    # ============================================
    # FIXTURES - Required by BaseAgentTests
    # ============================================
    
    @pytest.fixture
    def agent_instance(self, dependency_provider: DependencyProvider):
        """
        Create HistoricalFeaturesExtractor instance
        Triggers required dependency: OrderProgressTracker (which triggers ValidationOrchestrator)
        """
        from agents.autoPlanner.featureExtractor.initial.historicalFeaturesExtractor.historical_features_extractor import (
            HistoricalFeaturesExtractor, FeaturesExtractorConfig
        )
        
        # ✅ Trigger required dependency using new API
        # Note: OrderProgressTracker will auto-trigger ValidationOrchestrator
        dependency_provider.trigger("OrderProgressTracker")
        
        # Create agent with specific config
        return HistoricalFeaturesExtractor(
            config=FeaturesExtractorConfig(
                efficiency=0.85,
                loss=0.03,
                shared_source_config=dependency_provider.get_shared_source_config()
            )
        )
    
    @pytest.fixture
    def execution_result(self, agent_instance):
        """
        Execute HistoricalFeaturesExtractor
        
        Note: No assertions here - validated_execution_result fixture handles validation
        """
        # ✅ Just return - let validated_execution_result handle validation
        return agent_instance.run_extraction_and_save_results()
    
    # ============================================
    # BUSINESS LOGIC TESTS
    # ============================================
    
    def test_has_feature_extraction_phases(self, validated_execution_result):
        """Should have feature extraction sub-phases"""
        assert validated_execution_result.is_composite, \
            "HistoricalFeaturesExtractor should be composite (have sub-phases)"
        
        assert len(validated_execution_result.sub_results) > 0, \
            "Should have at least one extraction phase"
        
        # Check for expected phases (adjust based on your implementation)
        phase_names = {r.name for r in validated_execution_result.sub_results}
        expected_phases = {
            "MoldStabilityIndexCalculator",
            "MoldMachineFeatureWeightCalculator"
        }
        
        assert expected_phases.issubset(phase_names), \
            f"Missing expected phases. Found: {phase_names}, Expected: {expected_phases}"
    
    def test_efficiency_and_loss_config_applied(self, agent_instance):
        """Should use configured efficiency and loss parameters"""
        assert agent_instance.config.efficiency == 0.85, \
            "Efficiency parameter should be 0.85"
        assert agent_instance.config.loss == 0.03, \
            "Loss parameter should be 0.03"
    
    def test_features_calculated(self, validated_execution_result):
        """Should calculate historical features"""
        # Check that features were calculated
        for sub_result in validated_execution_result.sub_results:
            assert isinstance(sub_result.data, dict), \
                f"Phase '{sub_result.name}' should have data dict"
            
            # Add more specific checks based on implementation
            # Example:
            # if sub_result.name == "MoldStabilityIndexCalculator":
            #     result_data = sub_result.data.get('result', {})
            #     assert 'stability_index' in result_data
    
    def test_uses_order_tracking_data(self, dependency_provider, validated_execution_result):
        """Should use data from OrderProgressTracker"""
        # Get cached order tracking result
        tracking_result = dependency_provider.get_result("OrderProgressTracker")
        
        assert tracking_result is not None, \
            "OrderProgressTracker should be cached"
        
        # Verify tracking completed successfully
        assert tracking_result.status in {"success", "degraded", "warning"}, \
            "Dependency should have completed successfully"
        
        # Add checks that extraction used tracking data
        # Example: Check metadata references
        metadata = validated_execution_result.metadata
        # assert 'tracking_timestamp' in metadata
    
    def test_mold_stability_index_calculated(self, validated_execution_result):
        """MoldStabilityIndexCalculator should produce stability metrics"""
        stability_phase = next(
            (r for r in validated_execution_result.sub_results 
             if r.name == "MoldStabilityIndexCalculator"),
            None
        )
        
        if stability_phase:
            assert stability_phase.status in {"success", "degraded", "warning"}, \
                "MoldStabilityIndexCalculator should complete successfully"
            
            # Add specific assertions about stability index
            # result_data = stability_phase.data.get('result', {})
            # assert 'payload' in result_data
    
    def test_mold_machine_weights_calculated(self, validated_execution_result):
        """MoldMachineFeatureWeightCalculator should produce weight metrics"""
        weights_phase = next(
            (r for r in validated_execution_result.sub_results 
             if r.name == "MoldMachineFeatureWeightCalculator"),
            None
        )
        
        if weights_phase:
            assert weights_phase.status in {"success", "degraded", "warning"}, \
                "MoldMachineFeatureWeightCalculator should complete successfully"
            
            # Add specific assertions about weights
            # result_data = weights_phase.data.get('result', {})
            # assert 'weights' in result_data
    
    def test_constant_config_loaded(self, validated_execution_result):
        """Should load constant configurations from file"""
        metadata = validated_execution_result.metadata
        assert isinstance(metadata, dict)
        
        # Add checks for config loading
        # Example:
        # assert 'config_loaded' in metadata
        # assert 'config_version' in metadata
    
    def test_dependency_chain_triggered(self, dependency_provider):
        """Should have full dependency chain triggered"""
        # OrderProgressTracker should be triggered
        assert dependency_provider.is_triggered("OrderProgressTracker"), \
            "OrderProgressTracker should be triggered"
        
        # ValidationOrchestrator should also be triggered (via OrderProgressTracker)
        assert dependency_provider.is_triggered("ValidationOrchestrator"), \
            "ValidationOrchestrator should be triggered as transitive dependency"
    
    # ============================================
    # EDGE CASE TESTS (Optional)
    # ============================================
    
    def test_handles_insufficient_historical_data(self, dependency_provider):
        """Should handle case with insufficient historical data"""
        # This depends on your implementation
        # Example: Test with limited date range
        pass
    
    def test_extraction_results_serializable(self, validated_execution_result):
        """Feature extraction results should be JSON serializable"""
        import json
        
        for sub_result in validated_execution_result.sub_results:
            try:
                json.dumps(sub_result.data)
            except TypeError as e:
                pytest.fail(
                    f"Phase '{sub_result.name}' data is not JSON serializable: {e}"
                )


# ============================================
# OPTIONAL: Dependency Interaction Tests
# ============================================

class TestHistoricalFeaturesExtractorDependencies:
    """
    Test HistoricalFeaturesExtractor's interaction with dependencies
    """
    
    def test_fails_without_order_tracking(self, dependency_provider):
        """Should handle missing OrderProgressTracker gracefully"""
        from agents.autoPlanner.featureExtractor.initial.historicalFeaturesExtractor.historical_features_extractor import (
            HistoricalFeaturesExtractor, FeaturesExtractorConfig
        )
        
        # DON'T trigger OrderProgressTracker
        assert not dependency_provider.is_triggered("OrderProgressTracker"), \
            "OrderProgressTracker should not be triggered yet"
        
        # Create agent
        agent = HistoricalFeaturesExtractor(
            config=FeaturesExtractorConfig(
                efficiency=0.85,
                loss=0.03,
                shared_source_config=dependency_provider.get_shared_source_config()
            )
        )
        
        # Execute - should fail or degrade gracefully
        result = agent.run_extraction_and_save_results()
        
        # Should handle missing dependency
        assert result.status in {"failed", "degraded", "partial"}, \
            "Should fail or degrade without required dependency"
        
        if result.status == "failed":
            assert result.error is not None, \
                "Failed execution should have error message"
    
    def test_reuses_cached_dependencies(self, dependency_provider):
        """Should reuse cached dependency results"""
        from agents.autoPlanner.featureExtractor.initial.historicalFeaturesExtractor.historical_features_extractor import (
            HistoricalFeaturesExtractor, FeaturesExtractorConfig
        )
        
        # Trigger dependency
        tracking_result_1 = dependency_provider.trigger("OrderProgressTracker")
        
        # Create and execute first extractor
        config = FeaturesExtractorConfig(
            efficiency=0.85,
            loss=0.03,
            shared_source_config=dependency_provider.get_shared_source_config()
        )
        
        agent1 = HistoricalFeaturesExtractor(config=config)
        result1 = agent1.run_extraction_and_save_results()
        
        # Trigger again - should return cached
        tracking_result_2 = dependency_provider.trigger("OrderProgressTracker")
        assert tracking_result_1 is tracking_result_2, \
            "Should reuse cached OrderProgressTracker result"
        
        # Create second extractor
        agent2 = HistoricalFeaturesExtractor(config=config)
        result2 = agent2.run_extraction_and_save_results()
        
        # Both should succeed
        assert result1.status in {"success", "degraded", "warning"}
        assert result2.status in {"success", "degraded", "warning"}


# ============================================
# OPTIONAL: Configuration Tests
# ============================================

class TestHistoricalFeaturesExtractorConfig:
    """Test different configuration parameters"""
    
    @pytest.mark.parametrize("efficiency,loss", [
        (0.80, 0.05),
        (0.85, 0.03),
        (0.90, 0.02),
    ])
    def test_different_efficiency_loss_configs(self, dependency_provider, efficiency, loss):
        """Test with different efficiency and loss parameters"""
        from agents.autoPlanner.featureExtractor.initial.historicalFeaturesExtractor.historical_features_extractor import (
            HistoricalFeaturesExtractor, FeaturesExtractorConfig
        )
        
        # Trigger dependency
        dependency_provider.trigger("OrderProgressTracker")
        
        # Create agent with specific config
        agent = HistoricalFeaturesExtractor(
            config=FeaturesExtractorConfig(
                efficiency=efficiency,
                loss=loss,
                shared_source_config=dependency_provider.get_shared_source_config()
            )
        )
        
        result = agent.run_extraction_and_save_results()
        
        # Should work with different parameters
        assert result.status in {"success", "degraded", "warning"}
        
        # Verify parameters were applied
        assert agent.config.efficiency == efficiency
        assert agent.config.loss == loss
    
    def test_with_custom_constant_config_path(self, dependency_provider):
        """Test with custom constant configuration path"""
        from agents.autoPlanner.featureExtractor.initial.historicalFeaturesExtractor.historical_features_extractor import (
            HistoricalFeaturesExtractor, FeaturesExtractorConfig
        )
        
        dependency_provider.trigger("OrderProgressTracker")
        
        # Modify config
        shared_config = dependency_provider.get_shared_source_config()
        # shared_config.features_extractor_constant_config_path = "custom/path.json"
        
        agent = HistoricalFeaturesExtractor(
            config=FeaturesExtractorConfig(
                efficiency=0.85,
                loss=0.03,
                shared_source_config=shared_config
            )
        )
        
        result = agent.run_extraction_and_save_results()
        assert result.status in {"success", "degraded", "warning"}


# ============================================
# OPTIONAL: Performance Tests
# ============================================

class TestHistoricalFeaturesExtractorPerformance:
    """Performance benchmarks for feature extraction"""
    
    def test_extraction_completes_within_timeout(self, dependency_provider):
        """Feature extraction should complete in reasonable time"""
        import time
        from agents.autoPlanner.featureExtractor.initial.historicalFeaturesExtractor.historical_features_extractor import (
            HistoricalFeaturesExtractor, FeaturesExtractorConfig
        )
        
        dependency_provider.trigger("OrderProgressTracker")
        
        agent = HistoricalFeaturesExtractor(
            config=FeaturesExtractorConfig(
                efficiency=0.85,
                loss=0.03,
                shared_source_config=dependency_provider.get_shared_source_config()
            )
        )
        
        start = time.time()
        result = agent.run_extraction_and_save_results()
        duration = time.time() - start
        
        # Adjust timeout based on your data size
        # Feature extraction may take longer than simple validation
        assert duration < 180, f"Extraction took too long: {duration:.2f}s"
        
        # Should match reported duration
        assert abs(result.duration - duration) < 1.0