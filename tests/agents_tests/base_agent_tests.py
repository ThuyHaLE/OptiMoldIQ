# tests/base_agent_tests.py
import pytest
from configs.shared.agent_report_format import ExecutionStatus, PhaseSeverity
from abc import ABC, abstractmethod

class BaseAgentTests(ABC):
    """
    Base test class for ALL agents
    
    Subclass only needs to provide:
    - agent_instance fixture
    - agent-specific business logic tests
    """
    
    @pytest.fixture
    @abstractmethod
    def agent_instance(self):
        """Override in subclass to provide agent instance"""
        pass
    
    @pytest.fixture
    @abstractmethod
    def execution_result(self):
        """Override in subclass to provide agent execution"""
        pass

    # ============================================
    # STRUCTURAL TESTS - Same for ALL agents
    # ============================================
    
    def test_result_not_none(self, execution_result):
        """Should always return ExecutionResult"""
        assert execution_result is not None
    
    def test_has_required_attributes(self, execution_result):
        """Should have all required attributes"""
        required_attrs = ['status', 'name', 'type', 'severity', 'duration']
        for attr in required_attrs:
            assert hasattr(execution_result, attr), f"Missing attribute: {attr}"
    
    def test_status_is_valid(self, execution_result):
        """Status should be valid ExecutionStatus"""
        assert execution_result.status in [s.value for s in ExecutionStatus]
    
    def test_severity_is_valid(self, execution_result):
        """Severity should be valid PhaseSeverity"""
        assert execution_result.severity in [s.value for s in PhaseSeverity]
    
    def test_duration_is_valid(self, execution_result):
        """Duration should be non-negative float"""
        assert isinstance(execution_result.duration, float)
        assert execution_result.duration >= 0
    
    def test_data_structures(self, execution_result):
        """Should have correct data structure types"""
        assert isinstance(execution_result.data, dict)
        assert isinstance(execution_result.metadata, dict)
        assert isinstance(execution_result.sub_results, list)
        assert isinstance(execution_result.warnings, list)
    
    def test_composite_has_sub_results(self, execution_result):
        """CompositeAgent should have sub-results"""
        if execution_result.type == "agent":
            assert execution_result.is_composite
            assert len(execution_result.sub_results) > 0
    
    def test_success_criteria(self, execution_result):
        """Success should meet all criteria"""
        if execution_result.status == ExecutionStatus.SUCCESS.value:
            assert execution_result.all_successful()
            assert not execution_result.has_critical_errors()
    
    def test_critical_errors_mean_failure(self, execution_result):
        """Critical errors should result in failed status"""
        if execution_result.has_critical_errors():
            assert execution_result.status == ExecutionStatus.FAILED.value
            assert execution_result.severity == PhaseSeverity.CRITICAL.value
    
    def test_failed_phases_have_error_info(self, execution_result):
        """Failed phases should have error information"""
        for sub in execution_result.sub_results:
            if sub.status == "failed":
                assert sub.error is not None or len(sub.warnings) > 0
    
    def test_summary_stats_valid(self, execution_result):
        """Summary stats should be valid"""
        stats = execution_result.summary_stats()
        
        required_fields = [
            "total_executions", "depth", "success", "failed",
            "skipped", "critical_errors", "warnings", "total_duration"
        ]
        for field in required_fields:
            assert field in stats
        
        # Counts should add up
        assert (
            stats["success"] + stats["failed"] + stats["skipped"] ==
            stats["total_executions"]
        )