# tests/agents_tests/test_initial_planner.py

import pytest
from tests.agents_tests.base_agent_tests import BaseAgentTests
from tests.agents_tests.conftest import DependencyProvider

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
        """
        Execute InitialPlanner with all dependencies
        
        Note: No assertions here - let validated_execution_result handle validation
        """
        # Trigger required dependencies
        dependency_provider.trigger("OrderProgressTracker")
        dependency_provider.trigger("HistoricalFeaturesExtractor")
        
        # Execute agent
        return agent_instance.run_planning_and_save_results()
    
    # ============================================
    # BUSINESS LOGIC TESTS
    # ============================================
    
    def test_has_expected_phases(self, validated_execution_result):
        """InitialPlanner should have ProducingProcessor and PendingProcessor"""
        phase_names = {r.name for r in validated_execution_result.sub_results}
        
        expected_phases = {
            "ProducingProcessor",
            "PendingProcessor"
        }
        
        assert expected_phases.issubset(phase_names), \
            f"Missing expected phases. Found: {phase_names}"
    
    def test_processors_produce_results(self, validated_execution_result):
        """Both processors should produce planning results"""
        for sub_result in validated_execution_result.sub_results:
            if sub_result.name in ["ProducingProcessor", "PendingProcessor"]:
                # Each processor should have data
                assert sub_result.data is not None
                assert isinstance(sub_result.data, dict)
    
    def test_planning_metadata_present(self, validated_execution_result):
        """Execution should have planning metadata"""
        assert validated_execution_result.metadata is not None
        # Add specific metadata checks based on your implementation


# ============================================
# OPTIONAL: Test with/without dependencies
# ============================================

class TestInitialPlannerDependencyScenarios:
    """
    Test InitialPlanner behavior with different dependency states
    
    Note: This is SEPARATE from BaseAgentTests to avoid interference
    """
    
    @pytest.fixture(
        params=[
            {"has_features": True, "label": "with_features"},
            {"has_features": False, "label": "without_features"}
        ],
        ids=lambda p: p["label"]
    )
    def dependency_scenario(self, request, dependency_provider):
        """Setup different dependency scenarios"""
        from agents.autoPlanner.phases.initialPlanner.initial_planner import (
            InitialPlannerConfig, InitialPlanner
        )
        
        scenario = request.param
        
        # Always trigger OrderProgressTracker (required)
        dependency_provider.trigger("OrderProgressTracker")
        
        # Conditionally trigger HistoricalFeaturesExtractor
        if scenario["has_features"]:
            dependency_provider.trigger("HistoricalFeaturesExtractor")
        
        # Create agent
        agent = InitialPlanner(
            config=InitialPlannerConfig(
                shared_source_config=dependency_provider.get_shared_source_config()
            )
        )
        
        return {
            "agent": agent,
            "scenario": scenario,
            "dependency_provider": dependency_provider
        }
    
    def test_planner_adapts_to_dependency_availability(self, dependency_scenario):
        """
        InitialPlanner should adapt behavior based on available dependencies
        
        - With features: should use historical data for optimization
        - Without features: should use fallback/default planning
        """
        agent = dependency_scenario["agent"]
        scenario = dependency_scenario["scenario"]
        
        # Execute
        result = agent.run_planning_and_save_results()
        
        # Should succeed in both cases
        assert result.status in {
            "success",
            "degraded",  # Acceptable if fallback used
            "warning"
        }
        
        # Verify behavior based on scenario
        if scenario["has_features"]:
            # Should use feature-based planning
            # Check for specific indicators in result
            pass  # Add your business logic checks
        else:
            # Should use fallback planning
            # May have degraded status
            if result.status == "degraded":
                assert result.data.get("fallback_used") is True
    
    def test_missing_required_dependency_fails(self, dependency_provider):
        """
        InitialPlanner should fail if OrderProgressTracker is missing
        
        Note: This tests error handling
        """
        from agents.autoPlanner.phases.initialPlanner.initial_planner import (
            InitialPlannerConfig, InitialPlanner
        )
        
        # DON'T trigger OrderProgressTracker
        
        agent = InitialPlanner(
            config=InitialPlannerConfig(
                shared_source_config=dependency_provider.get_shared_source_config()
            )
        )
        
        result = agent.run_planning_and_save_results()
        
        # Should fail gracefully
        assert result.status in {"failed", "partial"}
        assert result.error is not None or len(result.warnings) > 0


# ============================================
# ALTERNATIVE: Simpler approach
# ============================================

class TestInitialPlannerSimple(BaseAgentTests):
    """
    Simpler version: Just test with full dependencies
    Test scenarios separately if needed
    """
    
    @pytest.fixture
    def agent_instance(self, dependency_provider):
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
        """Execute with all dependencies"""
        # ✅ Use new API
        dependency_provider.trigger("OrderProgressTracker")
        dependency_provider.trigger("HistoricalFeaturesExtractor")
        
        # ✅ No assertion - let validated_execution_result handle it
        return agent_instance.run_planning_and_save_results()
    
    # Business logic tests here...
    
    def test_planning_results_structure(self, validated_execution_result):
        """Test specific to InitialPlanner"""
        # Your business logic
        pass