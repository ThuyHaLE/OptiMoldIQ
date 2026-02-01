# tests/agents_tests/test_order_progress_tracker.py

import pytest
from tests.agents_tests.base_agent_tests import BaseAgentTests
from tests.agents_tests.conftest import DependencyProvider
from configs.shared.agent_report_format import ExecutionResult, ExecutionStatus

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
        """Create OrderProgressTracker instance with ValidationOrchestrator dependency"""
        from agents.orderProgressTracker.order_progress_tracker import OrderProgressTracker
        
        # Trigger required dependency
        dependency_provider.clear_all_dependencies()
        dependency_provider.trigger_all_dependencies(["DataPipelineOrchestrator",
                                                      "ValidationOrchestrator"])
        
        # Create agent
        return OrderProgressTracker(
            config=dependency_provider.get_shared_source_config()
        )
    
    @pytest.fixture
    def execution_result(self, agent_instance):
        """Execute OrderProgressTracker"""
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
        
        # Check for expected phase names
        phase_names = {r.name for r in validated_execution_result.sub_results}
        expected_phases = {'ProgressTracker'}
        
        assert expected_phases.issubset(phase_names), \
            f"Missing expected phases. Found: {phase_names}"
    
    def test_tracking_produces_timeline(self, validated_execution_result):
        """Order tracking should produce timeline data"""
        expected_phases = {'ProgressTracker'}

        for phase in expected_phases:
            phase_result = validated_execution_result.get_path(phase)
            assert isinstance(phase_result, ExecutionResult)
            assert isinstance(phase_result.data, dict)
    
    def test_progress_status_schema_loaded(self, validated_execution_result):
        """Should load progress status schema configuration"""
        metadata = validated_execution_result.metadata
        assert isinstance(metadata, dict)
        
    def test_tracker_results_structure(self, validated_execution_result):
        """Tracker results should have expected structure"""
        if validated_execution_result is None:
            pytest.skip("OrderProgressTracker not executed")

        # Should be composite (have trackers)
        successful_statuses = {ExecutionStatus.SUCCESS.value, 
                               ExecutionStatus.DEGRADED.value, 
                               ExecutionStatus.WARNING.value}
        if validated_execution_result.status in successful_statuses:
            assert validated_execution_result.is_composite, \
                "OrderProgressTracker should have sub-results"
            
            # Expected tracking phases
            phase_names = {r.name for r in validated_execution_result.sub_results}
            expected_phases = {'ProgressTracker'}

            # At least one tracking phase should exist if tracking succeeded
            assert len(phase_names & expected_phases) > 0, \
                f"No expected tracking phases found. Found: {phase_names}"

            for sub in expected_phases:
                self_result = validated_execution_result.get_path(sub)
                result_data = self_result.data["result"] 
                assert "payload" in result_data, \
                    "Missing 'payload' in result data"


# ============================================
# DEPENDENCY INTERACTION TESTS
# ============================================

class TestOrderProgressTrackerDependencies:
    """Test OrderProgressTracker's interaction with dependencies"""
    
    # Test negative case properly
    def test_fails_without_validation(self, dependency_provider: DependencyProvider):
        """Should handle missing ValidationOrchestrator gracefully"""
        from agents.orderProgressTracker.order_progress_tracker import OrderProgressTracker
        
        # Clear all dependencies
        dependency_provider.clear_all_dependencies()
        
        # Create agent
        agent = OrderProgressTracker(
            config=dependency_provider.get_shared_source_config()
        )
        
        # Execute - should fail or degrade gracefully
        result = agent.run_tracking_and_save_results()
        
        # Use ExecutionStatus enum
        assert result.status in [ExecutionStatus.FAILED.value, 
                                 ExecutionStatus.DEGRADED.value], \
            f"Should fail or degrade without required dependency, got: {result.status}"
        
        if result.status == ExecutionStatus.FAILED.value:
            assert result.has_critical_errors(), \
                "Failed status should have critical errors"
        
        elif result.status == ExecutionStatus.DEGRADED.value:
            assert result.data.get("fallback_used") is True, \
                "DEGRADED status should indicate fallback was used"
    
    # Test recovery scenario
    def test_recovery_after_dependency_added(self, dependency_provider: DependencyProvider):
        """Test that tracker works after ValidationOrchestrator is added"""
        from agents.orderProgressTracker.order_progress_tracker import OrderProgressTracker
        
        # Start with clean state
        dependency_provider.clear_all_dependencies()
        
        # Create agent
        agent = OrderProgressTracker(
            config=dependency_provider.get_shared_source_config()
        )
        
        # First execution - should fail
        result1 = agent.run_tracking_and_save_results()
        assert result1.status in [ExecutionStatus.FAILED.value, 
                                  ExecutionStatus.DEGRADED.value]
        
        # Add dependency
        dependency_provider.clear_all_dependencies()
        dependency_provider.trigger_all_dependencies(["DataPipelineOrchestrator",
                                                      "ValidationOrchestrator"])
        
        # Second execution - should succeed
        result2 = agent.run_tracking_and_save_results()
        assert result2.status == ExecutionStatus.SUCCESS.value, \
            "Should succeed after DataPipelineOrchestrator and ValidationOrchestrator is added"

# ============================================
# PERFORMANCE TESTS
# ============================================

class TestOrderProgressTrackerPerformance:
    """Performance benchmarks"""
    
    def test_tracking_completes_within_timeout(self, dependency_provider: DependencyProvider):
        """Tracking should complete in reasonable time"""
        import time
        from agents.orderProgressTracker.order_progress_tracker import OrderProgressTracker
        
        dependency_provider.clear_all_dependencies()
        dependency_provider.trigger_all_dependencies(["DataPipelineOrchestrator",
                                                      "ValidationOrchestrator"])
        
        agent = OrderProgressTracker(
            config=dependency_provider.get_shared_source_config()
        )
        
        start = time.time()
        result = agent.run_tracking_and_save_results()
        duration = time.time() - start
        
        # Adjust timeout based on your data size
        assert duration < 120, f"Tracking took too long: {duration:.2f}s"
        
        # Should match reported duration
        assert abs(result.duration - duration) < 1.0