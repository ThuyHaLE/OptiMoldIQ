# tests/agents_tests/test_order_progress_tracker.py

import pytest
from tests.agents_tests.base_agent_tests import BaseAgentTests
from tests.agents_tests.conftest import DependencyProvider
from configs.shared.agent_report_format import ExecutionResult

class TestOrderProgressTracker(BaseAgentTests):
    """
    Test OrderProgressTracker - agent with ValidationOrchestrator dependency
    Inherits all structural tests from BaseAgentTests
    """
    
    # ============================================
    # FIXTURES - Required by BaseAgentTests
    # ============================================
    
    @pytest.fixture
    def agent_instance(self, dependency_provider: DependencyProvider):
        """
        Create OrderProgressTracker instance
        Triggers required dependency: ValidationOrchestrator
        """
        from agents.orderProgressTracker.order_progress_tracker import OrderProgressTracker
        
        # ✅ Trigger required dependency using new API
        dependency_provider.trigger("ValidationOrchestrator")
        
        # Create agent
        return OrderProgressTracker(
            config=dependency_provider.get_shared_source_config()
        )
    
    @pytest.fixture
    def execution_result(self, agent_instance):
        """
        Execute OrderProgressTracker
        
        Note: No assertions here - validated_execution_result fixture handles validation
        """
        # ✅ Just return - let validated_execution_result handle validation
        return agent_instance.run_tracking_and_save_results()
    
    # ============================================
    # BUSINESS LOGIC TESTS
    # ============================================
    
    def test_has_tracking_phases(self, validated_execution_result):
        """Should have order tracking sub-phases"""
        assert validated_execution_result.is_composite, \
            "OrderProgressTracker should be composite (have sub-phases)"
        
        assert len(validated_execution_result.sub_results) > 0, \
            "Should have at least one tracking phase"
        
        # Check for expected phase names (adjust based on your implementation)
        phase_names = {r.name for r in validated_execution_result.sub_results}

        expected_phases = {
            'ProgressTracker'
        }
        
        assert expected_phases.issubset(phase_names), \
            f"Missing expected phases. Found: {phase_names}"
    
    def test_tracking_produces_timeline(self, validated_execution_result):
        """Order tracking should produce timeline data"""
        # Check that tracking produced meaningful results
        expected_phases = {
            'ProgressTracker'
        }

        for phase in expected_phases:
            phase_result = validated_execution_result.get_path(phase)
            assert isinstance(phase_result, ExecutionResult)
            assert isinstance(phase_result.data, dict)
    
    def test_uses_validation_data(self, dependency_provider, validated_execution_result):
        """Should use data from ValidationOrchestrator"""
        # Get cached validation result
        validation_result = dependency_provider.get_result("ValidationOrchestrator")
        
        assert validation_result is not None, \
            "ValidationOrchestrator should be cached"
        
        # Verify validation completed successfully before tracking started
        assert validation_result.status in {"success", "degraded", "warning"}, \
            "Dependency should have completed successfully"
        
        # Add checks that tracking actually used validation data
        # Example: Check metadata or specific fields
        metadata = validated_execution_result.metadata
        # assert 'validation_timestamp' in metadata
    
    def test_progress_status_schema_loaded(self, validated_execution_result):
        """Should load progress status schema configuration"""
        # Check metadata for schema info
        metadata = validated_execution_result.metadata
        assert isinstance(metadata, dict)
        
        # Add specific assertions based on your implementation
        # Example:
        # assert 'schema_loaded' in metadata
        # assert metadata.get('schema_version') is not None
    
    def test_dependency_triggered_before_execution(self, dependency_provider):
        """ValidationOrchestrator should be triggered before tracking"""
        assert dependency_provider.is_triggered("ValidationOrchestrator"), \
            "ValidationOrchestrator dependency should be triggered"
        
        # Should be cached
        cached_result = dependency_provider.get_result("ValidationOrchestrator")
        assert cached_result is not None, \
            "Validation result should be cached"
        
    def test_tracker_results_structure(self, validated_execution_result):
        """Tracker results should have expected structure"""
        if validated_execution_result is None:
            pytest.skip("OrderProgressTracker not executed")

        # Should be composite (have trackers)
        if validated_execution_result.status in {"success", "degraded", "warning"}:
            assert validated_execution_result.is_composite, \
                "OrderProgressTracker should have sub-results"
            
            # Expected validation phases
            phase_names = {r.name for r in validated_execution_result.sub_results}
            expected_phases = {'ProgressTracker'}

            # At least one validation phase should exist if validation succeeded
            assert len(phase_names & expected_phases) > 0, \
                f"No expected validation phases found. Found: {phase_names}"

            for sub in expected_phases:
                self_result = validated_execution_result.get_path(sub)
                result_data = self_result.data["result"] 
                assert "payload" in result_data, \
                    "Missing 'payload' in result data"

# ============================================
# OPTIONAL: Dependency Interaction Tests
# ============================================

class TestOrderProgressTrackerDependencies:
    """
    Test OrderProgressTracker's interaction with dependencies
    Separate class to avoid interfering with BaseAgentTests
    """
    
    def test_fails_without_validation(self, dependency_provider):
        """Should handle missing ValidationOrchestrator gracefully"""
        from agents.orderProgressTracker.order_progress_tracker import OrderProgressTracker
        
        # DON'T trigger ValidationOrchestrator
        assert not dependency_provider.is_triggered("ValidationOrchestrator"), \
            "ValidationOrchestrator should not be triggered yet"
        
        # Create agent
        agent = OrderProgressTracker(
            config=dependency_provider.get_shared_source_config()
        )
        
        # Execute - should fail or degrade gracefully
        result = agent.run_tracking_and_save_results()
        
        # Should either fail or use fallback
        assert result.status == "degraded", \
            "Should fail or degrade without required dependency"
    
    def test_reuses_cached_validation(self, dependency_provider):
        """Should reuse cached validation result"""
        from agents.orderProgressTracker.order_progress_tracker import OrderProgressTracker
        
        # Trigger validation once
        validation_result_1 = dependency_provider.trigger("ValidationOrchestrator")
        
        # Create and execute tracker
        agent1 = OrderProgressTracker(
            config=dependency_provider.get_shared_source_config()
        )
        result1 = agent1.run_tracking_and_save_results()
        
        # Trigger validation again - should return cached result
        validation_result_2 = dependency_provider.trigger("ValidationOrchestrator")
        
        # Should be the same object (cached)
        assert validation_result_1 is validation_result_2, \
            "Should reuse cached validation result"
        
        # Create second tracker - should also use cached validation
        agent2 = OrderProgressTracker(
            config=dependency_provider.get_shared_source_config()
        )
        result2 = agent2.run_tracking_and_save_results()
        
        # Both should succeed
        assert result1.status in {"success", "degraded", "warning"}
        assert result2.status in {"success", "degraded", "warning"}

# ============================================
# OPTIONAL: Configuration Tests
# ============================================

class TestOrderProgressTrackerConfig:
    """Test different configurations"""
    
    def test_with_custom_config_path(self, dependency_provider):
        """Test with custom constant config path"""
        from agents.orderProgressTracker.order_progress_tracker import OrderProgressTracker
        
        # Trigger dependency
        dependency_provider.trigger("ValidationOrchestrator")
        
        # Get config and modify it
        config = dependency_provider.get_shared_source_config()
        # Example: config.progress_tracker_constant_config_path = "custom/path.json"
        
        agent = OrderProgressTracker(config=config)
        result = agent.run_tracking_and_save_results()
        
        # Should still work with custom config
        assert result.status in {"success", "degraded", "warning"}
    
    def test_change_log_created(self, dependency_provider, tmp_path):
        """Test that change log is created"""
        from agents.orderProgressTracker.order_progress_tracker import OrderProgressTracker
        
        # Trigger dependency
        dependency_provider.trigger("ValidationOrchestrator")
        
        # Setup temp change log path
        config = dependency_provider.get_shared_source_config()
        config.progress_tracker_change_log_path = str(tmp_path / "test_change_log.txt")
        
        agent = OrderProgressTracker(config=config)
        result = agent.run_tracking_and_save_results()
        
        # Verify change log exists (if agent creates it)
        # assert (tmp_path / "test_change_log.txt").exists()

# ============================================
# OPTIONAL: Performance Tests
# ============================================

class TestOrderProgressTrackerPerformance:
    """Performance benchmarks"""
    
    def test_tracking_completes_within_timeout(self, dependency_provider):
        """Tracking should complete in reasonable time"""
        import time
        from agents.orderProgressTracker.order_progress_tracker import OrderProgressTracker
        
        dependency_provider.trigger("ValidationOrchestrator")
        
        agent = OrderProgressTracker(
            config=dependency_provider.get_shared_source_config()
        )
        
        start = time.time()
        result = agent.run_tracking_and_save_results()
        duration = time.time() - start
        
        # Adjust timeout based on your data size
        assert duration < 120, f"Tracking took too long: {duration:.2f}s"