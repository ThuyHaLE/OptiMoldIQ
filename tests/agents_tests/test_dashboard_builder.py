# tests/agents_tests/test_analytics_orchestrator.py

import pytest
from tests.agents_tests.base_agent_tests import BaseAgentTests
from tests.agents_tests.conftest import DependencyProvider
from configs.shared.agent_report_format import ExecutionStatus

class TestDashboardBuilder(BaseAgentTests):
    """
    Agent WITHOUT dependencies
    """
    
    @pytest.fixture
    def agent_instance(self, dependency_provider: DependencyProvider):
        """
        ⭐ No dependencies needed - simple creation
        """
        from agents.dashboardBuilder.dashboard_builder_v1 import ComponentConfig, DashboardBuilderConfig, DashboardBuilder
        
        # Get config
        shared_config = dependency_provider.get_shared_source_config()
        shared_config.analytics_orchestrator_dir = 'tests/shared_db/DashboardBuilder'

        return DashboardBuilder(
            config = DashboardBuilderConfig(
                shared_source_config = shared_config,
                
                # Workflow 1: Hardware visualization services
                machine_layout_visualization_service = ComponentConfig(
                    enabled = True,
                    save_result = True
                    ), 
                mold_machine_pair_visualization_service = ComponentConfig(
                    enabled = True,
                    save_result = True
                    ), 
                
                # Workflow 2: Performance visualization services
                day_level_visualization_service = ComponentConfig(
                    enabled = True,
                    save_result = True,
                    requested_timestamp = '2018-11-06'
                ),
                month_level_visualization_service = ComponentConfig(
                    enabled = True,
                    save_result = True,
                    requested_timestamp = '2019-01',
                    analysis_date = '2019-01-15'
                ),
                year_level_visualization_service = ComponentConfig(
                    enabled = True,
                    save_result = True,
                    requested_timestamp = '2019',
                    analysis_date = '2019-12-31'
                ),

                # Top-level logging
                save_builder_log = True
            ))

    @pytest.fixture
    def execution_result(self, agent_instance):
        result = agent_instance.build_dashboard()
        assert result.status != ExecutionStatus.FAILED.value, "Agent execution failed - test setup error"
        return result