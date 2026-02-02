# tests/agents_tests/test_data_pipeline_orchestrator.py

import pytest
from tests.agents_tests.base_agent_tests import BaseAgentTests
from tests.agents_tests.conftest import DependencyProvider
from configs.shared.agent_report_format import ExecutionResult, ExecutionStatus

class TestDataPipelineOrchestrator(BaseAgentTests):
    """
    Test DataPipelineOrchestrator - ROOT dependency (no dependencies)
    Inherits all structural tests from BaseAgentTests
    """
    
    # ============================================
    # FIXTURES - Required by BaseAgentTests
    # ============================================
    
    @pytest.fixture
    def agent_instance(self, dependency_provider: DependencyProvider):
        """
        Create DataPipelineOrchestrator instance
        ✅ No dependencies needed - this is the root node
        """
        from agents.dataPipelineOrchestrator.data_pipeline_orchestrator import DataPipelineOrchestrator
        
        return DataPipelineOrchestrator(
            config=dependency_provider.get_shared_source_config(),
        )
    
    @pytest.fixture
    def execution_result(self, agent_instance):
        """Execute DataPipelineOrchestrator"""
        return agent_instance.run_collecting_and_save_results()
    
    # ============================================
    # BUSINESS LOGIC TESTS
    # ============================================
    
    def test_has_collector_phases(self, validated_execution_result):
        """Should have collector sub-phases"""
        assert validated_execution_result.is_composite, \
            "DataPipelineOrchestrator should be composite (have sub-phases)"
        
        assert len(validated_execution_result.sub_results) > 0, \
            "Should have at least one collector phase"
        
        # Check phase names
        phase_names = {r.name for r in validated_execution_result.sub_results}
        expected_phases = {'DataPipelineProcessor'}
        
        assert expected_phases.issubset(phase_names), \
            f"Missing expected phases. Found: {phase_names}"
    
    def test_collector_produces_results(self, validated_execution_result):
        """Each collector phase should produce results"""
        expected_phases = {'DataPipelineProcessor'}
        
        for phase in expected_phases:
            phase_result = validated_execution_result.get_path(phase)
            assert isinstance(phase_result, ExecutionResult)
            assert isinstance(phase_result.data, dict)
    
    def test_collector_schemas_loaded(self, validated_execution_result):
        """Collector should load database schemas"""
        metadata = validated_execution_result.metadata
        assert isinstance(metadata, dict)

    def test_collector_results_structure(self, validated_execution_result):
        """Collector results should have expected structure"""
        if validated_execution_result is None:
            pytest.skip("DataPipelineOrchestrator not executed")

        # Should be composite (have collectors)
        successful_statuses = {ExecutionStatus.SUCCESS.value, 
                               ExecutionStatus.DEGRADED.value, 
                               ExecutionStatus.WARNING.value}
        if validated_execution_result.status in successful_statuses:
            assert validated_execution_result.is_composite, \
                "DataPipelineOrchestrator should have sub-collectors"
            
            # Expected collector phases
            phase_names = {r.name for r in validated_execution_result.sub_results}
            expected_phases = {'DataPipelineProcessor'}

            # At least one collector phase should exist
            assert len(phase_names & expected_phases) > 0, \
                f"No expected collector phases found. Found: {phase_names}"

            for sub in expected_phases:
                self_result = validated_execution_result.get_path(sub)
                result_data = self_result.data["result"] 
                assert "payload" in result_data, \
                    "Missing 'payload' in result data"


# ============================================
# PERFORMANCE TESTS
# ============================================

class TestDataPipelineOrchestratorPerformance:
    """Performance benchmarks for data pipeline"""
    
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
        
        assert result.duration > 0
        
        # Should complete in reasonable time
        assert duration < 300, f"Pipeline took too long: {duration:.2f}s"