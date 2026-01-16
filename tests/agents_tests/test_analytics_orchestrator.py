# tests/agents_tests/test_analytics_orchestrator.py

import pytest
from tests.agents_tests.base_agent_tests import BaseAgentTests
from tests.agents_tests.conftest import DependencyProvider
from configs.shared.agent_report_format import ExecutionStatus

class TestValidationOrchestrator(BaseAgentTests):
    """
    Agent WITHOUT dependencies
    """
    
    @pytest.fixture
    def agent_instance(self, dependency_provider: DependencyProvider):
        """
        ⭐ No dependencies needed - simple creation
        """
        from agents.analyticsOrchestrator.analytics_orchestrator_v1 import (
            ComponentConfig, AnalyticsOrchestratorConfig, AnalyticsOrchestrator)
        
        # Get config
        shared_config = dependency_provider.get_shared_source_config()

        return AnalyticsOrchestrator(
            config = AnalyticsOrchestratorConfig(
                shared_source_config = shared_config,
                
                # Workflow 1: Hardware trackers
                machine_layout_tracker = ComponentConfig(
                    enabled = True,
                    save_result = True),
                mold_machine_pair_tracker = ComponentConfig(
                    enabled = True,
                    save_result = True),
                
                # Workflow 2: Performance processors
                day_level_processor = ComponentConfig(
                    enabled = True,
                    save_result = True,
                    requested_timestamp = '2018-11-06'),
                month_level_processor = ComponentConfig(
                    enabled = True,
                    save_result = True,
                    requested_timestamp = '2019-01',
                    analysis_date = '2019-01-15'),
                year_level_processor = ComponentConfig(
                    enabled = True,
                    save_result = True,
                    requested_timestamp = '2019',
                    analysis_date = '2019-12-31'),
                
                # Top-level logging
                save_orchestrator_log = True
            )
        )

    @pytest.fixture
    def execution_result(self, agent_instance):
        result = agent_instance.run_analyzing()
        assert result.status != ExecutionStatus.FAILED.value, "Agent execution failed - test setup error"
        return result