# tests/agents_tests/test_validation_orchestrator.py

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
        from agents.validationOrchestrator.validation_orchestrator import ValidationOrchestrator
        
        # Get config
        shared_config = dependency_provider.get_shared_source_config()

        return ValidationOrchestrator(
            shared_source_config=shared_config,
            enable_parallel=False,
            max_workers=None)

    @pytest.fixture
    def execution_result(self, agent_instance):
        result = agent_instance.run_validations_and_save_results()
        assert result.status != ExecutionStatus.FAILED.value, "Agent execution failed - test setup error"
        return result