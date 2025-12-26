# tests/agents_tests/test_initial_planner.py

import pytest
from tests.agents_tests.base_agent_tests import BaseAgentTests
from tests.agents_tests.conftest import DependencyProvider
from configs.shared.agent_report_format import ExecutionStatus

class TestInitialPlanner(BaseAgentTests):
    """Test InitialPlanner with/without dependency"""
    
    @pytest.fixture(params=[True, False], ids=["with_dependency", "without_dependency"])
    def agent_instance(self, dependency_provider: DependencyProvider, request):
        """
        ⭐ Parametrized: test cả 2 trường hợp
        """
        from agents.autoPlanner.phases.initialPlanner.initial_planner import InitialPlannerConfig, InitialPlanner
        
        shared_config = dependency_provider.get_shared_source_config()

        dependency_provider.trigger_order_progress_tracker(shared_config)

        if request.param:  # True = with dependency
            dependency_provider.trigger_historical_features_extractor(shared_config)
        
        return InitialPlanner(
            config=InitialPlannerConfig(
                shared_source_config=shared_config
            )
        )
    
    @pytest.fixture
    def execution_result(self, agent_instance):
        result = agent_instance.run_planning_and_save_results()
        assert result.status != ExecutionStatus.FAILED.value, "Agent execution failed"
        return result