# tests/agents_tests/test_validation_orchestrator.py

import pytest
from tests.agents_tests.base_agent_tests import BaseAgentTests
from tests.agents_tests.conftest import DependencyProvider
from configs.shared.agent_report_format import ExecutionResult

class TestValidationOrchestrator(BaseAgentTests):
    """
    Test ValidationOrchestrator - agent without dependencies
    Inherits all structural tests from BaseAgentTests
    """
    
    # ============================================
    # FIXTURES - Required by BaseAgentTests
    # ============================================
    
    @pytest.fixture
    def agent_instance(self, dependency_provider: DependencyProvider):
        """
        Create ValidationOrchestrator instance
        No dependencies needed - simple creation
        """
        from agents.validationOrchestrator.validation_orchestrator import ValidationOrchestrator
        
        return ValidationOrchestrator(
            shared_source_config=dependency_provider.get_shared_source_config(),
            enable_parallel=False,
            max_workers=None
        )
    
    @pytest.fixture
    def execution_result(self, agent_instance):
        """
        Execute ValidationOrchestrator
        
        Note: No assertions here - validated_execution_result fixture handles validation
        """
        # ✅ Just return - let validated_execution_result handle validation
        return agent_instance.run_validations_and_save_results()
    
    # ============================================
    # BUSINESS LOGIC TESTS
    # ============================================
    
    def test_has_validation_phases(self, validated_execution_result):
        """Should have validation sub-phases"""
        assert validated_execution_result.is_composite, \
            "ValidationOrchestrator should be composite (have sub-phases)"
        
        assert len(validated_execution_result.sub_results) > 0, \
            "Should have at least one validation phase"
        
        # Check phase names
        phase_names = {r.name for r in validated_execution_result.sub_results}
        
        expected_phases = {
            'DynamicCrossDataValidation',
            'PORequiredFieldValidation',
            'StaticCrossDataValidation'
        }
        
        assert expected_phases.issubset(phase_names), \
            f"Missing expected phases. Found: {phase_names}"
    
    def test_validation_produces_results(self, validated_execution_result):
        """Each validation phase should produce results"""
        expected_phases = {
            'DynamicCrossDataValidation',
            'PORequiredFieldValidation',
            'StaticCrossDataValidation'
        }
        for phase in expected_phases:
            phase_result = validated_execution_result.get_path(phase)
            assert isinstance(phase_result, ExecutionResult)
            assert isinstance(phase_result.data, dict)
    
    def test_validation_schemas_loaded(self, validated_execution_result):
        """Validation should load database schemas"""
        # Add checks specific to your validation logic
        # Example: Check if validation config was loaded
        metadata = validated_execution_result.metadata
        assert isinstance(metadata, dict)
        
        # Add more specific assertions based on implementation
        # Example:
        # assert 'schema_version' in metadata
        # assert 'validation_rules' in metadata

    def test_validation_results_structure(self, validated_execution_result):
        """Validation results should have expected structure"""
        if validated_execution_result is None:
            pytest.skip("ValidationOrchestrator not executed")

        # Should be composite (have validations)
        if validated_execution_result.status in {"success", "degraded", "warning"}:
            assert validated_execution_result.is_composite, \
                "ValidationOrchestrator should have sub-validations"
            
            # Expected validation phases
            phase_names = {r.name for r in validated_execution_result.sub_results}
            expected_phases = {'DynamicCrossDataValidation', 'PORequiredFieldValidation', 'StaticCrossDataValidation'}

            # At least one validation phase should exist if validation succeeded
            assert len(phase_names & expected_phases) > 0, \
                f"No expected validation phases found. Found: {phase_names}"

            for sub in expected_phases:
                self_result = validated_execution_result.get_path(sub)
                result_data = self_result.data["result"] 
                assert "payload" in result_data, \
                    "Missing 'payload' in result data"

# ============================================
# OPTIONAL: Configuration Tests
# ============================================

class TestValidationOrchestratorConfig:
    """
    Test different configurations of ValidationOrchestrator
    Separate from BaseAgentTests to avoid interference
    """
    
    def test_with_parallel_enabled(self, dependency_provider):
        """Test behavior with parallel execution enabled"""
        from agents.validationOrchestrator.validation_orchestrator import ValidationOrchestrator
        
        agent = ValidationOrchestrator(
            shared_source_config=dependency_provider.get_shared_source_config(),
            enable_parallel=True,
            max_workers=2
        )
        
        result = agent.run_validations_and_save_results()
        
        # Should still succeed with parallel execution
        assert result.status in {"success", "degraded", "warning"}
    
    def test_custom_validation_targets(self, dependency_provider):
        """Test with custom validation DataFrame names"""
        from agents.validationOrchestrator.validation_orchestrator import ValidationOrchestrator
        
        # Modify config to test specific validation targets
        config = dependency_provider.get_shared_source_config()
        # Example: config.validation_df_name = ["customTable"]
        
        agent = ValidationOrchestrator(
            shared_source_config=config,
            enable_parallel=False,
            max_workers=None
        )
        
        result = agent.run_validations_and_save_results()
        
        # Verify it validated the correct targets
        assert result.status in {"success", "degraded", "warning"}


# ============================================
# PERFORMANCE TESTS (Optional)
# ============================================

class TestValidationOrchestratorPerformance:
    """Performance benchmarks for validation"""
    
    def test_validation_completes_within_timeout(self, dependency_provider):
        """Validation should complete within reasonable time"""
        import time
        from agents.validationOrchestrator.validation_orchestrator import ValidationOrchestrator
        
        agent = ValidationOrchestrator(
            shared_source_config=dependency_provider.get_shared_source_config(),
            enable_parallel=False,
            max_workers=None
        )
        
        start = time.time()
        result = agent.run_validations_and_save_results()
        duration = time.time() - start
        
        # Should complete in reasonable time (adjust based on your data size)
        assert duration < 60, f"Validation took too long: {duration:.2f}s"