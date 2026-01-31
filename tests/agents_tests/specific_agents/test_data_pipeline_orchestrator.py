# tests/agents_tests/test_data_pipeline_orchestrator.py

import pytest
from tests.agents_tests.base_agent_tests import BaseAgentTests
from tests.agents_tests.conftest import DependencyProvider
from configs.shared.agent_report_format import ExecutionResult

class TestDataPipelineOrchestrator(BaseAgentTests):
    """
    Test DataPipelineOrchestrator - agent without dependencies
    Inherits all structural tests from BaseAgentTests
    """
    
    # ============================================
    # FIXTURES - Required by BaseAgentTests
    # ============================================
    
    @pytest.fixture
    def agent_instance(self, dependency_provider: DependencyProvider):
        """
        Create DataPipelineOrchestrator instance
        No dependencies needed - simple creation
        """
        from agents.dataPipelineOrchestrator.data_pipeline_orchestrator import DataPipelineOrchestrator
        
        return DataPipelineOrchestrator(
            config=dependency_provider.get_shared_source_config(),
        )
    
    @pytest.fixture
    def execution_result(self, agent_instance):
        """
        Execute DataPipelineOrchestrator
        
        Note: No assertions here - validated_execution_result fixture handles collector
        """
        # ✅ Just return - let validated_execution_result handle collector
        return agent_instance.run_collecting_and_save_results()
    
    # ============================================
    # BUSINESS LOGIC TESTS
    # ============================================
    
    def test_has_collector_phases(self, validated_execution_result):
        """Should have collector sub-phases"""
        assert validated_execution_result.is_composite, \
            "Collector should be composite (have sub-phases)"
        
        assert len(validated_execution_result.sub_results) > 0, \
            "Should have at least one collector phase"
        
        # Check phase names
        phase_names = {r.name for r in validated_execution_result.sub_results}
        
        expected_phases = {
            'DataPipelineProcessor'
        }
        
        assert expected_phases.issubset(phase_names), \
            f"Missing expected phases. Found: {phase_names}"
    
    def test_collector_produces_results(self, validated_execution_result):
        """Each collector phase should produce results"""
        expected_phases = {
            'DataPipelineProcessor'
        }
        for phase in expected_phases:
            phase_result = validated_execution_result.get_path(phase)
            assert isinstance(phase_result, ExecutionResult)
            assert isinstance(phase_result.data, dict)
    
    def test_collector_schemas_loaded(self, validated_execution_result):
        """Collector should load database schemas"""
        # Add checks specific to your collector logic
        # Example: Check if collector config was loaded
        metadata = validated_execution_result.metadata
        assert isinstance(metadata, dict)
        
        # Add more specific assertions based on implementation
        # Example:
        # assert 'schema_version' in metadata
        # assert 'collector_rules' in metadata

    def test_collector_results_structure(self, validated_execution_result):
        """Collector results should have expected structure"""
        if validated_execution_result is None:
            pytest.skip("DataPipelineProcessor not executed")

        # Should be composite (have collectors)
        if validated_execution_result.status in {"success", "degraded", "warning"}:
            assert validated_execution_result.is_composite, \
                "DataPipelineProcessor should have sub-collectors"
            
            # Expected collector phases
            phase_names = {r.name for r in validated_execution_result.sub_results}
            expected_phases = {'DataPipelineProcessor'}

            # At least one collector phase should exist if collector succeeded
            assert len(phase_names & expected_phases) > 0, \
                f"No expected collector phases found. Found: {phase_names}"

            for sub in expected_phases:
                self_result = validated_execution_result.get_path(sub)
                result_data = self_result.data["result"] 
                assert "payload" in result_data, \
                    "Missing 'payload' in result data"

# ============================================
# PERFORMANCE TESTS (Optional)
# ============================================

class TestCollectorOrchestratorPerformance:
    """Performance benchmarks for collector"""
    
    def test_collector_completes_within_timeout(self, dependency_provider):
        """DataPipelineOrchestrator should complete within reasonable time"""
        import time

        from agents.dataPipelineOrchestrator.data_pipeline_orchestrator import DataPipelineOrchestrator
    
        agent = DataPipelineOrchestrator(
            config=dependency_provider.get_shared_source_config(),
        )
        
        start = time.time()
        result = agent.run_collecting_and_save_results()
        duration = time.time() - start
        
        # Should complete in reasonable time (adjust based on your data size)
        assert duration < 120, f"Collector took too long: {duration:.2f}s"