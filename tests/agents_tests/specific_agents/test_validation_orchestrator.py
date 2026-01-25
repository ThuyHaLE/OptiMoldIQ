# tests/agents_tests/test_validation_orchestrator.py

import pytest
from tests.agents_tests.base_agent_tests import BaseAgentTests
from tests.agents_tests.conftest import DependencyProvider

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
        # Add expected phases based on your implementation
        # Example:
        # expected = {"DatabaseValidator", "SchemaValidator"}
        # assert expected.issubset(phase_names)
    
    def test_parallel_disabled_in_tests(self, agent_instance):
        """Parallel execution should be disabled in test environment"""
        assert agent_instance.enable_parallel is False, \
            "Parallel execution must be disabled for deterministic tests"
        assert agent_instance.max_workers is None, \
            "max_workers should be None when parallel is disabled"
    
    def test_validation_produces_results(self, validated_execution_result):
        """Each validation phase should produce results"""
        for sub_result in validated_execution_result.sub_results:
            # Each phase should have data
            assert isinstance(sub_result.data, dict), \
                f"Phase '{sub_result.name}' should have data dict"
            
            # Can add more specific checks based on your implementation
            # Example: Check for specific keys in data
            # assert 'result' in sub_result.data
    
    def test_no_dependencies_triggered(self, dependency_provider):
        """
        ValidationOrchestrator should not require any dependencies
        Cache should be empty (except shared_config)
        """
        # Only shared_config should be in cache
        assert "ValidationOrchestrator" not in dependency_provider._cache, \
            "ValidationOrchestrator shouldn't be cached yet"
        
        # No other agents should be triggered
        unwanted_deps = {"OrderProgressTracker", "HistoricalFeaturesExtractor"}
        for dep in unwanted_deps:
            assert not dependency_provider.is_triggered(dep), \
                f"Unexpected dependency '{dep}' was triggered"
    
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
    
    # ============================================
    # EDGE CASE TESTS (Optional)
    # ============================================
    
    def test_handles_empty_database_gracefully(self, dependency_provider):
        """Should handle empty database without crashing"""
        # This test depends on your implementation
        # Example: Create agent with empty db and verify graceful handling
        pass
    
    def test_validation_results_are_serializable(self, validated_execution_result):
        """Validation results should be serializable (for saving)"""
        import json
        
        # Try to serialize the data
        for sub_result in validated_execution_result.sub_results:
            try:
                json.dumps(sub_result.data)
            except TypeError as e:
                pytest.fail(
                    f"Phase '{sub_result.name}' data is not JSON serializable: {e}"
                )


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
        
        # Should match reported duration
        assert abs(result.duration - duration) < 1.0, \
            "Reported duration doesn't match actual duration"