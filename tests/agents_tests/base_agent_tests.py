# tests/agents_tests/base_agent_tests.py

import pytest
from configs.shared.agent_report_format import ExecutionStatus, PhaseSeverity
from abc import ABC, abstractmethod

class BaseAgentTests(ABC):
    """
    Base test class for ALL agents
    
    Subclass only needs to provide:
    - agent_instance fixture
    - execution_result fixture (will be auto-validated via validated_execution_result)
    - agent-specific business logic tests
    
    All structural tests use validated_execution_result to avoid repetitive assertions
    """
    
    @pytest.fixture
    @abstractmethod
    def agent_instance(self):
        """Override in subclass to provide agent instance"""
        pass
    
    @pytest.fixture
    @abstractmethod
    def execution_result(self):
        """
        Override in subclass to provide agent execution
        Will be auto-validated by validated_execution_result fixture
        """
        pass

    # ============================================
    # STRUCTURAL TESTS - Use validated fixture
    # ============================================
    
    def test_result_not_none(self, validated_execution_result):
        """Should always return ExecutionResult"""
        # No need for status check - already validated by fixture
        assert validated_execution_result is not None
    
    def test_has_required_attributes(self, validated_execution_result):
        """Should have all required attributes"""
        required_attrs = ['status', 'name', 'type', 'severity', 'duration', 
                         'data', 'metadata', 'sub_results', 'warnings']
        
        for attr in required_attrs:
            assert hasattr(validated_execution_result, attr), \
                f"Missing required attribute: {attr}"
    
    def test_status_is_valid(self, validated_execution_result):
        """Status should be valid ExecutionStatus"""
        valid_statuses = [s.value for s in ExecutionStatus]
        assert validated_execution_result.status in valid_statuses, \
            f"Invalid status: {validated_execution_result.status}"
    
    def test_severity_is_valid(self, validated_execution_result):
        """Severity should be valid PhaseSeverity"""
        valid_severities = [s.value for s in PhaseSeverity]
        assert validated_execution_result.severity in valid_severities, \
            f"Invalid severity: {validated_execution_result.severity}"
    
    def test_duration_is_valid(self, validated_execution_result):
        """Duration should be non-negative float"""
        assert isinstance(validated_execution_result.duration, (int, float)), \
            f"Duration must be numeric, got {type(validated_execution_result.duration)}"
        assert validated_execution_result.duration >= 0, \
            f"Duration must be non-negative, got {validated_execution_result.duration}"
    
    def test_data_structures(self, validated_execution_result):
        """Should have correct data structure types"""
        assert isinstance(validated_execution_result.data, dict), \
            "data must be a dict"
        assert isinstance(validated_execution_result.metadata, dict), \
            "metadata must be a dict"
        assert isinstance(validated_execution_result.sub_results, list), \
            "sub_results must be a list"
        assert isinstance(validated_execution_result.warnings, list), \
            "warnings must be a list"
    
    def test_composite_has_sub_results(self, validated_execution_result):
        """CompositeAgent should have sub-results"""
        if validated_execution_result.type == "agent":
            assert validated_execution_result.is_composite, \
                "Agent type must be composite"
            assert len(validated_execution_result.sub_results) > 0, \
                "Composite agent must have sub-results"
    
    def test_success_criteria(self, validated_execution_result):
        """Success/Degraded/Warning should not have critical errors"""
        successful_statuses = {
            ExecutionStatus.SUCCESS.value,
            ExecutionStatus.DEGRADED.value,
            ExecutionStatus.WARNING.value
        }
        
        if validated_execution_result.status in successful_statuses:
            assert not validated_execution_result.has_critical_errors(), \
                "Successful execution should not have critical errors"
    
    def test_failed_phases_have_error_info(self, all_sub_results):
        """Failed phases should have error information"""
        for result in all_sub_results:
            if result.status == ExecutionStatus.FAILED.value:
                has_error_info = (
                    result.error is not None or 
                    len(result.warnings) > 0 or 
                    result.traceback is not None
                )
                assert has_error_info, \
                    f"Failed phase '{result.name}' missing error information"
    
    def test_summary_stats_valid(self, execution_summary):
        """Summary stats should be valid and consistent"""
        required_fields = [
            "total_executions", "depth", "success", "failed",
            "skipped", "critical_errors", "warnings", "total_duration"
        ]
        
        for field in required_fields:
            assert field in execution_summary, \
                f"Missing summary field: {field}"
        
        # Verify counts add up
        total = (
            execution_summary["success"] + 
            execution_summary["failed"] + 
            execution_summary["skipped"]
        )
        assert total == execution_summary["total_executions"], \
            f"Count mismatch: {total} != {execution_summary['total_executions']}"
    
    def test_tree_structure_valid(self, validated_execution_result):
        """Tree structure should be valid"""
        depth = validated_execution_result.get_depth()
        assert depth >= 1, "Tree depth must be at least 1"
        
        # Verify all sub-results are valid
        for sub in validated_execution_result.sub_results:
            assert sub is not None, "Sub-result should not be None"
            assert hasattr(sub, 'name'), "Sub-result must have name"
            assert hasattr(sub, 'status'), "Sub-result must have status"
    
    def test_get_path_works(self, validated_execution_result):
        """get_path() should work for valid paths"""
        # Can get self
        self_result = validated_execution_result.get_path(
            validated_execution_result.name
        )
        assert self_result == validated_execution_result
        
        # Invalid path returns None
        invalid = validated_execution_result.get_path("NonExistent.Path")
        assert invalid is None
    
    def test_flatten_works(self, all_sub_results):
        """flatten() should return all nodes"""
        assert len(all_sub_results) > 0, "Should have at least root node"
        
        # All items should be ExecutionResult
        for result in all_sub_results:
            assert hasattr(result, 'name')
            assert hasattr(result, 'status')
    
    # ============================================
    # DEGRADED/FALLBACK TESTS
    # ============================================
    
    def test_degraded_status_means_fallback_used(self, all_sub_results):
        """DEGRADED status should indicate fallback was used"""
        degraded_results = [
            r for r in all_sub_results 
            if r.status == ExecutionStatus.DEGRADED.value
        ]
        
        for result in degraded_results:
            assert result.data.get("fallback_used") is True, \
                f"DEGRADED phase '{result.name}' should have fallback_used=True"
            assert "original_error" in result.data, \
                f"DEGRADED phase '{result.name}' should record original_error"
    
    def test_warnings_present_for_degraded(self, all_sub_results):
        """DEGRADED status should have warnings"""
        degraded_results = [
            r for r in all_sub_results 
            if r.status == ExecutionStatus.DEGRADED.value
        ]
        
        for result in degraded_results:
            assert len(result.warnings) > 0, \
                f"DEGRADED phase '{result.name}' should have warnings"