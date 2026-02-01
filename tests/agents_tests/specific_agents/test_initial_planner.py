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
        
        return InitialPlanner(
            config=InitialPlannerConfig(
                shared_source_config=dependency_provider.get_shared_source_config()
            )
        )
    
    @pytest.fixture
    def execution_result(self, agent_instance, dependency_provider):
        """Execute InitialPlanner with all dependencies"""
        # Trigger required dependencies
        dependency_provider.trigger("OrderProgressTracker")
        dependency_provider.trigger("HistoricalFeaturesExtractor")
        
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
# DEPENDENCY SCENARIOS - FIXED
# ============================================

class TestInitialPlannerDependencyScenarios:
    """Test InitialPlanner behavior with different dependency states"""
    
    # Test with features (positive case)
    def test_with_all_dependencies(self, dependency_provider):
        """InitialPlanner should use historical features when available"""
        from agents.autoPlanner.phases.initialPlanner.initial_planner import (
            InitialPlannerConfig, InitialPlanner
        )
        
        # Trigger all dependencies
        dependency_provider.trigger("OrderProgressTracker")
        dependency_provider.trigger("HistoricalFeaturesExtractor")
        
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
            f"Should succeed with all dependencies, got: {result.status}"
        
        # Should NOT use fallback
        assert result.data.get("fallback_used") is not True, \
            "Should not use fallback when features available"
    
    # Test without features (partial dependency)
    def test_without_historical_features(self, isolated_dependency_provider):
        """InitialPlanner should degrade gracefully without HistoricalFeaturesExtractor"""
        from agents.autoPlanner.phases.initialPlanner.initial_planner import (
            InitialPlannerConfig, InitialPlanner
        )
        
        # Clear all first
        isolated_dependency_provider.clear_all_dependencies()
        
        # Trigger only OrderProgressTracker
        isolated_dependency_provider.trigger("OrderProgressTracker")
        
        # Verify state
        assert isolated_dependency_provider.is_materialized("OrderProgressTracker")
        assert not isolated_dependency_provider.is_materialized("HistoricalFeaturesExtractor"), \
            "HistoricalFeaturesExtractor should not exist"
        
        # Create agent
        agent = InitialPlanner(
            config=InitialPlannerConfig(
                shared_source_config=isolated_dependency_provider.get_shared_source_config()
            )
        )
        
        # Execute
        result = agent.run_planning_and_save_results()
        
        # Should degrade gracefully (use fallback)
        assert result.status in [ExecutionStatus.SUCCESS.value, ExecutionStatus.DEGRADED.value], \
            f"Should succeed or degrade without features, got: {result.status}"
        
        # If degraded, should use fallback
        if result.status == ExecutionStatus.DEGRADED.value:
            assert result.data.get("fallback_used") is True, \
                "DEGRADED status should indicate fallback was used"
    
    # Test without required dependency
    def test_missing_required_dependency_fails(self, isolated_dependency_provider):
        """InitialPlanner should fail if OrderProgressTracker is missing"""
        from agents.autoPlanner.phases.initialPlanner.initial_planner import (
            InitialPlannerConfig, InitialPlanner
        )
        
        # Clear all dependencies
        isolated_dependency_provider.clear_all_dependencies()
        
        # Verify clean state
        assert not isolated_dependency_provider.is_materialized("OrderProgressTracker"), \
            "OrderProgressTracker files should not exist"
        assert not isolated_dependency_provider.is_materialized("HistoricalFeaturesExtractor"), \
            "HistoricalFeaturesExtractor files should not exist"
        
        # Create agent
        agent = InitialPlanner(
            config=InitialPlannerConfig(
                shared_source_config=isolated_dependency_provider.get_shared_source_config()
            )
        )
        
        # Execute
        result = agent.run_planning_and_save_results()
        
        # Should fail without required dependency
        assert result.status == ExecutionStatus.FAILED.value, \
            f"Should fail without required dependency, got: {result.status}"
        
        assert result.has_critical_errors(), \
            "Failed status should have critical errors"
    
    # Test dependency chain
    def test_dependency_chain_verification(self, dependency_provider):
        """Verify full dependency chain is available"""
        from agents.autoPlanner.phases.initialPlanner.initial_planner import (
            InitialPlannerConfig, InitialPlanner
        )
        
        # Trigger HistoricalFeaturesExtractor (which triggers chain)
        dependency_provider.trigger("HistoricalFeaturesExtractor")
        
        # Verify entire chain is triggered
        assert dependency_provider.is_triggered("OrderProgressTracker"), \
            "OrderProgressTracker should be triggered transitively"
        assert dependency_provider.is_triggered("HistoricalFeaturesExtractor"), \
            "HistoricalFeaturesExtractor should be triggered"
        
        # Create and execute agent
        agent = InitialPlanner(
            config=InitialPlannerConfig(
                shared_source_config=dependency_provider.get_shared_source_config()
            )
        )
        
        result = agent.run_planning_and_save_results()
        
        # Should succeed with full chain
        assert result.status == ExecutionStatus.SUCCESS.value
    
    # Test recovery scenario
    def test_recovery_after_dependency_added(self, isolated_dependency_provider):
        """Test that planner works after dependencies are added"""
        from agents.autoPlanner.phases.initialPlanner.initial_planner import (
            InitialPlannerConfig, InitialPlanner
        )
        
        # Start with clean state
        isolated_dependency_provider.clear_all_dependencies()
        
        # Create agent
        agent = InitialPlanner(
            config=InitialPlannerConfig(
                shared_source_config=isolated_dependency_provider.get_shared_source_config()
            )
        )
        
        # First execution - should fail
        result1 = agent.run_planning_and_save_results()
        assert result1.status == ExecutionStatus.FAILED.value
        
        # Add minimal dependency
        isolated_dependency_provider.trigger("OrderProgressTracker")
        
        # Second execution - should degrade or succeed
        result2 = agent.run_planning_and_save_results()
        assert result2.status in [ExecutionStatus.SUCCESS.value, 
                                  ExecutionStatus.DEGRADED.value], \
            "Should succeed or degrade with minimal dependency"
        
        # Add full dependencies
        isolated_dependency_provider.trigger("HistoricalFeaturesExtractor")
        
        # Third execution - should fully succeed
        result3 = agent.run_planning_and_save_results()
        assert result3.status == ExecutionStatus.SUCCESS.value, \
            "Should fully succeed with all dependencies"


# ============================================
# PARAMETRIZED TESTS - Advanced
# ============================================

class TestInitialPlannerParametrized:
    """Parametrized tests for different scenarios"""
    
    @pytest.mark.parametrize("scenario", [
        {
            "name": "full_dependencies",
            "deps": ["OrderProgressTracker", "HistoricalFeaturesExtractor"],
            "expected_status": ExecutionStatus.SUCCESS.value,
            "should_use_fallback": False
        },
        {
            "name": "minimal_dependencies",
            "deps": ["OrderProgressTracker"],
            "expected_status": [ExecutionStatus.SUCCESS.value, 
                                ExecutionStatus.DEGRADED.value],
            "should_use_fallback": True
        },
        {
            "name": "no_dependencies",
            "deps": [],
            "expected_status": ExecutionStatus.FAILED.value,
            "should_use_fallback": None  # Should fail before fallback
        }
    ], ids=lambda s: s["name"])

    def test_planner_with_different_dependencies(self, isolated_dependency_provider, scenario):
        """Test InitialPlanner behavior with different dependency combinations"""
        from agents.autoPlanner.phases.initialPlanner.initial_planner import (
            InitialPlannerConfig, InitialPlanner
        )
        
        # Setup dependencies
        isolated_dependency_provider.clear_all_dependencies()
        for dep in scenario["deps"]:
            isolated_dependency_provider.trigger(dep)
        
        # Create agent
        agent = InitialPlanner(
            config=InitialPlannerConfig(
                shared_source_config=isolated_dependency_provider.get_shared_source_config()
            )
        )
        
        # Execute
        result = agent.run_planning_and_save_results()
        
        # Verify expected status
        expected = scenario["expected_status"]
        if isinstance(expected, list):
            assert result.status in expected, \
                f"Expected one of {expected}, got: {result.status}"
        else:
            assert result.status == expected, \
                f"Expected {expected}, got: {result.status}"
        
        # Verify fallback behavior
        if scenario["should_use_fallback"] is not None:
            fallback_used = result.data.get("fallback_used", False)
            if scenario["should_use_fallback"]:
                assert fallback_used, "Should use fallback in this scenario"
            else:
                assert not fallback_used, "Should not use fallback in this scenario"