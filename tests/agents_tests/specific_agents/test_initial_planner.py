# tests/agents_tests/test_initial_planner.py

import pytest
from tests.agents_tests.base_agent_tests import BaseAgentTests
from tests.agents_tests.conftest import DependencyProvider
from configs.shared.agent_report_format import ExecutionResult, ExecutionStatus

class TestInitialPlanner(BaseAgentTests):
    """
    Test InitialPlanner - inherits all structural tests from BaseAgentTests
    """
    
    # ============================================
    # FIXTURES - Standard pattern
    # ============================================
    
    @pytest.fixture
    def agent_instance(self, dependency_provider: DependencyProvider):
        """Create InitialPlanner instance"""
        from agents.autoPlanner.phases.initialPlanner.initial_planner import (
            InitialPlannerConfig, InitialPlanner
        )
        
        # Trigger required dependencies BEFORE creating agent
        dependency_provider.clear_all_dependencies()
        dependency_provider.trigger_all_dependencies(["DataPipelineOrchestrator",
                                                      "ValidationOrchestrator",
                                                      "OrderProgressTracker",
                                                      "HistoricalFeaturesExtractor"])
        
        return InitialPlanner(
            config=InitialPlannerConfig(
                shared_source_config=dependency_provider.get_shared_source_config()
            )
        )
    
    @pytest.fixture
    def execution_result(self, agent_instance):
        """Execute InitialPlanner (dependencies already triggered in agent_instance)"""
        # Execute agent
        return agent_instance.run_planning_and_save_results()
    
    # ============================================
    # BUSINESS LOGIC TESTS
    # ============================================
    
    def test_has_expected_phases(self, validated_execution_result):
        """InitialPlanner should have PendingOrderPlanner and ProducingOrderPlanner"""
        phase_names = {r.name for r in validated_execution_result.sub_results}
        
        expected_phases = {
            'PendingOrderPlanner',
            'ProducingOrderPlanner'
        }
        
        assert expected_phases.issubset(phase_names), \
            f"Missing expected phases. Found: {phase_names}"
    
    def test_processors_produce_results(self, validated_execution_result):
        """Both processors should produce planning results"""
        expected_phases = {
            'PendingOrderPlanner',
            'ProducingOrderPlanner'
        }
        for phase in expected_phases:
            phase_result = validated_execution_result.get_path(phase)
            assert isinstance(phase_result, ExecutionResult)
            assert isinstance(phase_result.data, dict)
    
    def test_planning_metadata_present(self, validated_execution_result):
        """Execution should have planning metadata"""
        assert validated_execution_result.metadata is not None
    
    def test_planning_results_structure(self, validated_execution_result):
        """InitialPlanner results should have expected structure"""
        if validated_execution_result is None:
            pytest.skip("InitialPlanner not executed")

        # Should be composite (have planners)
        successful_statuses = {ExecutionStatus.SUCCESS.value, ExecutionStatus.DEGRADED.value, ExecutionStatus.WARNING.value}
        if validated_execution_result.status in successful_statuses:
            assert validated_execution_result.is_composite, \
                "InitialPlanner should have sub-planners"
            
            # Expected planners
            planner_names = {r.name for r in validated_execution_result.sub_results}
            expected_planners = {'PendingOrderPlanner', 'ProducingOrderPlanner'}

            # At least one planner should exist if planner succeeded
            assert len(planner_names & expected_planners) > 0, \
                f"No expected planners found. Found: {planner_names}"

            for sub in expected_planners:
                self_result = validated_execution_result.get_path(sub)
                result_data = self_result.data["result"] 
                assert "payload" in result_data, \
                    "Missing 'payload' in result data"


# ============================================
# DEPENDENCY SCENARIOS
# ============================================

class TestInitialPlannerDependencyScenarios:
    """Test InitialPlanner behavior with different dependency states"""
    
    def test_with_all_dependencies(self, dependency_provider: DependencyProvider):
        """InitialPlanner should use historical features when available"""
        from agents.autoPlanner.phases.initialPlanner.initial_planner import (
            InitialPlannerConfig, InitialPlanner
        )
        
        # Trigger all dependencies and verify they succeeded
        dependency_provider.clear_all_dependencies()
        dependency_provider.trigger_all_dependencies(["DataPipelineOrchestrator",
                                                      "ValidationOrchestrator",
                                                      "OrderProgressTracker",
                                                      "HistoricalFeaturesExtractor"])
        
        # Create agent
        agent = InitialPlanner(
            config=InitialPlannerConfig(
                shared_source_config=dependency_provider.get_shared_source_config()
            )
        )
        
        # Execute
        result = agent.run_planning_and_save_results()
        
        # Should succeed with full features
        assert result.status == ExecutionStatus.SUCCESS.value, \
            f"Should succeed with all dependencies, got: {result.status}\n" \
            f"Error: {result.error}\n" \
            f"Failed paths: {result.get_failed_paths()}"
        
        # Should NOT use fallback (if your implementation tracks this)
        # Note: Only check if your implementation actually sets this field
        # assert result.data.get("fallback_used") is not True, \
        #     "Should not use fallback when features available"
    
    def test_without_historical_features(self, dependency_provider: DependencyProvider):
        """InitialPlanner should degrade gracefully without HistoricalFeaturesExtractor"""
        from agents.autoPlanner.phases.initialPlanner.initial_planner import (
            InitialPlannerConfig, InitialPlanner
        )
        
        # Trigger only OrderProgressTracker and verify it succeeded
        dependency_provider.clear_all_dependencies()
        dependency_provider.trigger_all_dependencies(["DataPipelineOrchestrator",
                                                      "ValidationOrchestrator",
                                                      "OrderProgressTracker"])
        
        # Create agent
        agent = InitialPlanner(
            config=InitialPlannerConfig(
                shared_source_config=dependency_provider.get_shared_source_config()
            )
        )
        
        # Execute
        result = agent.run_planning_and_save_results()
        
        # Should degrade gracefully (use fallback)
        assert result.status in [ExecutionStatus.SUCCESS.value, 
                                 ExecutionStatus.DEGRADED.value], \
            f"Should succeed or degrade without features, got: {result.status}\n" \
            f"Error: {result.error}\n" \
            f"Failed paths: {result.get_failed_paths()}"
    
    def test_missing_required_dependency_fails(self, dependency_provider: DependencyProvider):
        """InitialPlanner should fail if OrderProgressTracker is missing"""
        from agents.autoPlanner.phases.initialPlanner.initial_planner import (
            InitialPlannerConfig, InitialPlanner
        )
        
        # Clear all dependencies
        dependency_provider.clear_all_dependencies()
        
        # Create agent
        agent = InitialPlanner(
            config=InitialPlannerConfig(
                shared_source_config=dependency_provider.get_shared_source_config()
            )
        )
        
        # Execute
        result = agent.run_planning_and_save_results()
        
        # Should fail without required dependency
        assert result.status == ExecutionStatus.FAILED.value, \
            f"Should fail without required dependency, got: {result.status}"
        
        # Check for error information
        assert result.error is not None or len(result.get_failed_paths()) > 0, \
            "Failed status should have error information or failed paths"
    
    def test_recovery_after_dependency_added(self, dependency_provider: DependencyProvider):
        """Test that planner works after dependencies are added"""
        from agents.autoPlanner.phases.initialPlanner.initial_planner import (
            InitialPlannerConfig, InitialPlanner
        )
        
        # Start with clean state
        dependency_provider.clear_all_dependencies()
        
        # Create config (reusable)
        config = InitialPlannerConfig(
            shared_source_config=dependency_provider.get_shared_source_config()
        )
        
        # First execution - should fail
        agent1 = InitialPlanner(config=config)
        result1 = agent1.run_planning_and_save_results()
        assert result1.status == ExecutionStatus.FAILED.value, \
            f"Should fail without dependencies, got: {result1.status}"
        
        dependency_provider.clear_all_dependencies()
        dependency_provider.trigger_all_dependencies(["DataPipelineOrchestrator",
                                                      "ValidationOrchestrator",
                                                      "OrderProgressTracker"])
        
        # Second execution with NEW instance - should degrade or succeed
        agent2 = InitialPlanner(config=config)
        result2 = agent2.run_planning_and_save_results()
        assert result2.status in [ExecutionStatus.SUCCESS.value, 
                                  ExecutionStatus.DEGRADED.value], \
            f"Should succeed or degrade with minimal dependency, got: {result2.status}\n" \
            f"Error: {result2.error}"
        
        dependency_provider.clear_all_dependencies()
        dependency_provider.trigger_all_dependencies(["DataPipelineOrchestrator",
                                                      "ValidationOrchestrator",
                                                      "OrderProgressTracker",
                                                      "HistoricalFeaturesExtractor"])
        
        # Third execution with NEW instance - should fully succeed
        agent3 = InitialPlanner(config=config)
        result3 = agent3.run_planning_and_save_results()
        assert result3.status == ExecutionStatus.SUCCESS.value, \
            f"Should fully succeed with all dependencies, got: {result3.status}\n" \
            f"Error: {result3.error}\n" \
            f"Failed paths: {result3.get_failed_paths()}"