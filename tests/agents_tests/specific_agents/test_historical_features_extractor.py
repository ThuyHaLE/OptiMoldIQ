# tests/agents_tests/test_historical_features_extractor.py

import pytest
from configs.shared.agent_report_format import ExecutionStatus
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
        """Create HistoricalFeaturesExtractor instance"""
        from agents.autoPlanner.featureExtractor.initial.historicalFeaturesExtractor.historical_features_extractor import (
            HistoricalFeaturesExtractor, FeaturesExtractorConfig
        )
        
        # Trigger required dependency
        dependency_provider.trigger("OrderProgressTracker")
        
        return HistoricalFeaturesExtractor(
            config=FeaturesExtractorConfig(
                efficiency=0.85,
                loss=0.03,
                shared_source_config=dependency_provider.get_shared_source_config()
            )
        )
    
    @pytest.fixture
    def execution_result(self, agent_instance):
        """Execute HistoricalFeaturesExtractor"""
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
            'MoldMachineFeatureWeightCalculator',
            'MoldStabilityIndexCalculator'
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
        """Extractor results should have expected structure"""
        if validated_execution_result is None:
            pytest.skip("HistoricalFeaturesExtractor not executed")

        # Should be composite (have trackers)
        if validated_execution_result.status in {"success", "degraded", "warning"}:
            assert validated_execution_result.is_composite, \
                "HistoricalFeaturesExtractor should have sub-results"

            # Expected calculation phases
            phase_names = {r.name for r in validated_execution_result.sub_results}
            expected_phases = {
                'MoldMachineFeatureWeightCalculator',
                'MoldStabilityIndexCalculator'}

            # At least one calculation phase should exist if extraction succeeded
            assert len(phase_names & expected_phases) > 0, \
                f"No expected calculation phases found. Found: {phase_names}"

            for sub in expected_phases:
                self_result = validated_execution_result.get_path(sub)
                result_data = self_result.data["result"] 
                assert "payload" in result_data, \
                    "Missing 'payload' in result data"
    
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


# ============================================
# DEPENDENCY INTERACTION TESTS
# ============================================

class TestHistoricalFeaturesExtractorDependencies:
    """Test HistoricalFeaturesExtractor's interaction with dependencies"""
    
    # Test negative case
    def test_fails_without_order_tracking(self, isolated_dependency_provider):
        """Should handle missing OrderProgressTracker gracefully"""
        from agents.autoPlanner.featureExtractor.initial.historicalFeaturesExtractor.historical_features_extractor import (
            HistoricalFeaturesExtractor, FeaturesExtractorConfig
        )
        
        # Clear dependency (both cache + files)
        if isolated_dependency_provider.is_materialized("OrderProgressTracker"):
            isolated_dependency_provider.clear_dependency("OrderProgressTracker", cascade=True)
        
        # Verify clean state
        assert not isolated_dependency_provider.is_triggered("OrderProgressTracker"), \
            "OrderProgressTracker should not be in cache"
        assert not isolated_dependency_provider.is_materialized("OrderProgressTracker"), \
            "OrderProgressTracker files should not exist on disk"
        
        # Create agent
        agent = HistoricalFeaturesExtractor(
            config=FeaturesExtractorConfig(
                efficiency=0.85,
                loss=0.03,
                shared_source_config=isolated_dependency_provider.get_shared_source_config()
            )
        )
        
        # Execute - should fail or degrade gracefully
        result = agent.run_extraction_and_save_results()
        
        # Assert với ExecutionStatus enum
        assert result.status in [ExecutionStatus.FAILED.value, 
                                 ExecutionStatus.DEGRADED.value], \
            f"Should fail or degrade without required dependency, got: {result.status}"
        
        if result.status == ExecutionStatus.FAILED.value:
            assert result.has_critical_errors(), \
                "Failed status should have critical errors"
    
    #  Reuse test với session-scoped OK
    def test_reuses_cached_dependencies(self, dependency_provider):
        """Should reuse cached dependency results"""
        from agents.autoPlanner.featureExtractor.initial.historicalFeaturesExtractor.historical_features_extractor import (
            HistoricalFeaturesExtractor, FeaturesExtractorConfig
        )
        
        # Trigger dependency
        tracking_result_1 = dependency_provider.trigger("OrderProgressTracker")
        
        # Create config
        config = FeaturesExtractorConfig(
            efficiency=0.85,
            loss=0.03,
            shared_source_config=dependency_provider.get_shared_source_config()
        )
        
        # Create and execute first extractor
        agent1 = HistoricalFeaturesExtractor(config=config)
        result1 = agent1.run_extraction_and_save_results()
        
        # Trigger again - should return cached (same instance)
        tracking_result_2 = dependency_provider.trigger("OrderProgressTracker")
        assert tracking_result_1 is tracking_result_2, \
            "Should reuse cached OrderProgressTracker result"
        
        # Create second extractor
        agent2 = HistoricalFeaturesExtractor(config=config)
        result2 = agent2.run_extraction_and_save_results()
        
        # Both should succeed
        successful_statuses = {ExecutionStatus.SUCCESS.value, 
                               ExecutionStatus.DEGRADED.value, 
                               ExecutionStatus.WARNING.value}
        assert result1.status in successful_statuses
        assert result2.status in successful_statuses
    
    # Test recovery scenario
    def test_recovery_after_dependency_added(self, isolated_dependency_provider):
        """Test that agent works after dependency is added"""
        from agents.autoPlanner.featureExtractor.initial.historicalFeaturesExtractor.historical_features_extractor import (
            HistoricalFeaturesExtractor, FeaturesExtractorConfig
        )
        
        # Start with clean state
        isolated_dependency_provider.clear_all_dependencies()
        
        # Create agent
        agent = HistoricalFeaturesExtractor(
            config=FeaturesExtractorConfig(
                efficiency=0.85,
                loss=0.03,
                shared_source_config=isolated_dependency_provider.get_shared_source_config()
            )
        )
        
        # First execution - should fail
        result1 = agent.run_extraction_and_save_results()
        assert result1.status in [ExecutionStatus.FAILED.value, 
                                  ExecutionStatus.DEGRADED.value]
        
        # Now add dependencies
        isolated_dependency_provider.trigger("OrderProgressTracker")
        
        # Second execution - should succeed
        result2 = agent.run_extraction_and_save_results()
        assert result2.status == ExecutionStatus.SUCCESS.value, \
            "Should succeed after dependencies are added"

# ============================================
# CONFIGURATION TESTS
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
        
        successful_statuses = {ExecutionStatus.SUCCESS.value, 
                               ExecutionStatus.DEGRADED.value, 
                               ExecutionStatus.WARNING.value}
        assert result.status in successful_statuses
        
        # Verify parameters were applied
        assert agent.config.efficiency == efficiency
        assert agent.config.loss == loss

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