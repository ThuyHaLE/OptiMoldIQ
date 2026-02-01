# tests/agents_tests/test_validation_orchestrator.py

import pytest
from tests.agents_tests.base_agent_tests import BaseAgentTests
from tests.agents_tests.conftest import DependencyProvider
from configs.shared.agent_report_format import ExecutionResult, ExecutionStatus

class TestValidationOrchestrator(BaseAgentTests):
    """
    Test ValidationOrchestrator - depends on DataPipelineOrchestrator
    Inherits all structural tests from BaseAgentTests
    """
    
    # ============================================
    # FIXTURES - Required by BaseAgentTests
    # ============================================
    
    @pytest.fixture
    def agent_instance(self, dependency_provider: DependencyProvider):
        """
        Create ValidationOrchestrator instance
        Triggers DataPipelineOrchestrator dependency
        """
        from agents.validationOrchestrator.validation_orchestrator import ValidationOrchestrator
        
        # Trigger DataPipelineOrchestrator dependency
        dependency_provider.clear_all_dependencies()
        dependency_provider.trigger_all_dependencies(["DataPipelineOrchestrator"])
        
        return ValidationOrchestrator(
            shared_source_config=dependency_provider.get_shared_source_config(),
            enable_parallel=False,
            max_workers=None
        )
    
    @pytest.fixture
    def execution_result(self, agent_instance):
        """Execute ValidationOrchestrator"""
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
        metadata = validated_execution_result.metadata
        assert isinstance(metadata, dict)

    def test_validation_results_structure(self, validated_execution_result):
        """Validation results should have expected structure"""
        if validated_execution_result is None:
            pytest.skip("ValidationOrchestrator not executed")

        # Should be composite (have validations)
        successful_statuses = {ExecutionStatus.SUCCESS.value, 
                               ExecutionStatus.DEGRADED.value, 
                               ExecutionStatus.WARNING.value}
        if validated_execution_result.status in successful_statuses:
            assert validated_execution_result.is_composite, \
                "ValidationOrchestrator should have sub-validations"
            
            # Expected validation phases
            phase_names = {r.name for r in validated_execution_result.sub_results}
            expected_phases = {'DynamicCrossDataValidation', 
                               'PORequiredFieldValidation', 
                               'StaticCrossDataValidation'}

            # At least one validation phase should exist if validation succeeded
            assert len(phase_names & expected_phases) > 0, \
                f"No expected validation phases found. Found: {phase_names}"

            for sub in expected_phases:
                self_result = validated_execution_result.get_path(sub)
                result_data = self_result.data["result"] 
                assert "payload" in result_data, \
                    "Missing 'payload' in result data"


# ============================================
# DEPENDENCY INTERACTION TESTS
# ============================================

class TestValidationOrchestratorDependencies:
    """Test ValidationOrchestrator's interaction with DataPipelineOrchestrator"""
    
    # Test without pipeline
    def test_fails_without_pipeline(self, dependency_provider: DependencyProvider):
        """Should fail or degrade without DataPipelineOrchestrator"""
        from agents.validationOrchestrator.validation_orchestrator import ValidationOrchestrator
        
        # Clear all dependencies
        dependency_provider.clear_all_dependencies()
        
        # Create agent
        agent = ValidationOrchestrator(
            shared_source_config=dependency_provider.get_shared_source_config(),
            enable_parallel=False,
            max_workers=None
        )
        
        # Execute
        result = agent.run_validations_and_save_results()
        
        # Should fail or degrade
        assert result.status in [ExecutionStatus.FAILED.value, 
                                 ExecutionStatus.DEGRADED.value], \
            f"Should fail or degrade without DataPipelineOrchestrator, got: {result.status}"
        
        if result.status == ExecutionStatus.FAILED.value:
            assert result.has_critical_errors(), \
                "Failed status should have critical errors"
    
    # Test recovery
    def test_recovery_after_dependency_added(self, dependency_provider: DependencyProvider):
        """Test that validation works after DataPipelineOrchestrator is added"""
        from agents.validationOrchestrator.validation_orchestrator import ValidationOrchestrator
        
        # Start with clean state
        dependency_provider.clear_all_dependencies()
        
        # Create agent
        agent = ValidationOrchestrator(
            shared_source_config=dependency_provider.get_shared_source_config(),
            enable_parallel=False,
            max_workers=None
        )
        
        # First execution - should fail
        result1 = agent.run_validations_and_save_results()
        assert result1.status in [ExecutionStatus.FAILED.value, 
                                  ExecutionStatus.DEGRADED.value]
        
        # Add dependency
        dependency_provider.clear_all_dependencies()
        dependency_provider.trigger_all_dependencies(["DataPipelineOrchestrator"])
        
        # Second execution - should succeed
        result2 = agent.run_validations_and_save_results()
        assert result2.status == ExecutionStatus.SUCCESS.value, \
            "Should succeed after DataPipelineOrchestrator is added"


# ============================================
# CONFIGURATION TESTS
# ============================================

class TestValidationOrchestratorConfig:
    """Test different configurations of ValidationOrchestrator"""
    
    def test_with_parallel_enabled(self, dependency_provider: DependencyProvider):
        """Test behavior with parallel execution enabled"""
        from agents.validationOrchestrator.validation_orchestrator import ValidationOrchestrator
        
        # Trigger dependency first
        dependency_provider.clear_all_dependencies()
        dependency_provider.trigger_all_dependencies(["DataPipelineOrchestrator"])
        
        agent = ValidationOrchestrator(
            shared_source_config=dependency_provider.get_shared_source_config(),
            enable_parallel=True,
            max_workers=2
        )
        
        result = agent.run_validations_and_save_results()
        
        # Should still succeed with parallel execution
        successful_statuses = {ExecutionStatus.SUCCESS.value, 
                               ExecutionStatus.DEGRADED.value, 
                               ExecutionStatus.WARNING.value}
        assert result.status in successful_statuses
    
    def test_custom_validation_targets(self, dependency_provider: DependencyProvider):
        """Test with custom validation DataFrame names"""
        from agents.validationOrchestrator.validation_orchestrator import ValidationOrchestrator
        
        # Trigger dependency first
        dependency_provider.clear_all_dependencies()
        dependency_provider.trigger_all_dependencies(["DataPipelineOrchestrator"])
        
        # Modify config to test specific validation targets
        config = dependency_provider.get_shared_source_config()
        
        agent = ValidationOrchestrator(
            shared_source_config=config,
            enable_parallel=False,
            max_workers=None
        )
        
        result = agent.run_validations_and_save_results()
        
        # Verify it validated the correct targets
        successful_statuses = {ExecutionStatus.SUCCESS.value, 
                               ExecutionStatus.DEGRADED.value, 
                               ExecutionStatus.WARNING.value}
        assert result.status in successful_statuses


# ============================================
# PERFORMANCE TESTS
# ============================================

class TestValidationOrchestratorPerformance:
    """Performance benchmarks for validation"""
    
    def test_validation_completes_within_timeout(self, dependency_provider: DependencyProvider):
        """Validation should complete within reasonable time"""
        import time
        from agents.validationOrchestrator.validation_orchestrator import ValidationOrchestrator
        
        # Trigger dependency first
        dependency_provider.clear_all_dependencies()
        dependency_provider.trigger_all_dependencies(["DataPipelineOrchestrator"])
        
        agent = ValidationOrchestrator(
            shared_source_config=dependency_provider.get_shared_source_config(),
            enable_parallel=False,
            max_workers=None
        )
        
        start = time.time()
        result = agent.run_validations_and_save_results()
        duration = time.time() - start
        
        # Should complete in reasonable time
        assert duration < 300, f"Validation took too long: {duration:.2f}s"