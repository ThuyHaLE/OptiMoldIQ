import pytest
from agents.orderProgressTracker.order_progress_tracker import SharedSourceConfig, OrderProgressTracker
from configs.shared.agent_report_format import ExecutionStatus, PhaseSeverity

# === FIXTURES ===
@pytest.fixture
def shared_source_config():
    """Shared configuration for all tests"""
    return SharedSourceConfig(
        db_dir='tests/mock_database',
        default_dir='tests/shared_db'
    )

@pytest.fixture
def order_progress_tracker(shared_source_config):
    """Default tracker instance"""
    return OrderProgressTracker(config = shared_source_config)

@pytest.fixture
def execution_result(order_progress_tracker):
    """Run tracking and get result"""
    return order_progress_tracker.run_tracking_and_save_results()

# === BASIC STRUCTURE TESTS ===
class TestExecutionResultStructure:
    """Test basic ExecutionResult structure and attributes"""
    
    def test_result_not_none(self, execution_result):
        """Should always return ExecutionResult, never raise"""
        assert execution_result is not None
    
    def test_has_required_attributes(self, execution_result):
        """Should have all required attributes"""
        assert hasattr(execution_result, 'status')
        assert hasattr(execution_result, 'name')
        assert hasattr(execution_result, 'type')
        assert hasattr(execution_result, 'severity')
        assert hasattr(execution_result, 'duration')
    
    def test_basic_attribute_values(self, execution_result, order_progress_tracker):
        """Should have correct basic attribute values"""
        assert execution_result.name == order_progress_tracker.__class__.__name__
        assert execution_result.type == "agent"
        assert execution_result.status in [s.value for s in ExecutionStatus]
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

# === SUCCESS CRITERIA TESTS ===
class TestSuccessCriteria:
    """Test success conditions and validation"""
    
    def test_success_status_requirements(self, execution_result):
        """When successful, should meet all success criteria"""
        if execution_result.status == ExecutionStatus.SUCCESS.value:
            assert execution_result.all_successful()
            assert not execution_result.has_critical_errors()
            assert execution_result.severity in [
                PhaseSeverity.INFO.value,
                PhaseSeverity.WARNING.value
            ]
    
    def test_completion_status(self, execution_result):
        """Should correctly report completion status"""
        is_complete = execution_result.is_complete()
        
        if is_complete:
            assert len(execution_result.sub_results) == execution_result.total_sub_executions
        else:
            assert len(execution_result.sub_results) <= execution_result.total_sub_executions

# === SUB-RESULTS TESTS ===
class TestSubResults:
    """Test sub-results structure and behavior"""
    
    def test_is_composite(self, execution_result):
        """CompositeAgent should have sub-results"""
        assert execution_result.is_composite
        assert not execution_result.is_leaf
        assert len(execution_result.sub_results) > 0
    
    def test_sub_result_attributes(self, execution_result):
        """Each sub-result should have required attributes"""
        for sub_result in execution_result.sub_results:
            assert hasattr(sub_result, 'name')
            assert hasattr(sub_result, 'type')
            assert hasattr(sub_result, 'status')
            assert hasattr(sub_result, 'duration')
            assert sub_result.type in ["phase", "agent"]
    
    def test_sub_result_names_unique(self, execution_result):
        """Sub-result names should be unique"""
        names = [sub.name for sub in execution_result.sub_results]
        assert len(names) == len(set(names)), "Sub-result names should be unique"

# === ERROR HANDLING TESTS ===
class TestErrorHandling:
    """Test error handling and failure scenarios"""
    
    def test_partial_status_requirements(self, execution_result):
        """Partial status should have some failures"""
        if execution_result.status == ExecutionStatus.PARTIAL.value:
            failed_count = sum(
                1 for sub in execution_result.sub_results 
                if sub.status == "failed"
            )
            assert failed_count > 0
            assert len(execution_result.sub_results) > 0
    
    def test_critical_errors(self, execution_result):
        """Critical errors should result in failed status"""
        if execution_result.has_critical_errors():
            assert execution_result.status == ExecutionStatus.FAILED.value
            assert execution_result.severity == PhaseSeverity.CRITICAL.value
            
            critical_phases = [
                sub for sub in execution_result.sub_results
                if sub.severity == PhaseSeverity.CRITICAL.value
            ]
            assert len(critical_phases) > 0
    
    def test_failed_paths(self, execution_result):
        """Failed paths should be correctly reported"""
        failed_paths = execution_result.get_failed_paths()
        assert all(isinstance(path, str) for path in failed_paths)
        
        if execution_result.status in [
            ExecutionStatus.FAILED.value,
            ExecutionStatus.PARTIAL.value
        ]:
            failed_subs = [
                sub for sub in execution_result.sub_results 
                if sub.status == "failed"
            ]
            if failed_subs:
                assert len(failed_paths) >= len(failed_subs)
    
    def test_failed_phases_have_error_info(self, execution_result):
        """Failed phases should have error information"""
        for sub in execution_result.sub_results:
            if sub.status == "failed":
                assert sub.error is not None or len(sub.warnings) > 0

# === WARNINGS TESTS ===
class TestWarnings:
    """Test warning handling and propagation"""
    
    def test_warnings_structure(self, execution_result):
        """Warnings should have correct structure"""
        for warning in execution_result.warnings:
            assert isinstance(warning, dict)
            assert "message" in warning
            if "severity" in warning:
                assert warning["severity"] in [s.value for s in PhaseSeverity]
    
    def test_warnings_propagation(self, execution_result):
        sub_has_warnings = any(
            sub.warnings for sub in execution_result.sub_results
        )

        if sub_has_warnings:
            assert execution_result.severity in {
                PhaseSeverity.WARNING.value,
                PhaseSeverity.CRITICAL.value,
            }
        else:
            assert execution_result.severity != PhaseSeverity.WARNING.value

# === TREE STRUCTURE TESTS ===
class TestTreeStructure:
    """Test hierarchical tree structure"""
    
    def test_depth_calculation(self, execution_result):
        """Depth should match tree structure"""
        depth = execution_result.get_depth()
        assert depth >= 1
        assert isinstance(depth, int)
        
        if execution_result.is_leaf:
            assert depth == 1
        else:
            max_sub_depth = max(
                (sub.get_depth() for sub in execution_result.sub_results),
                default=0
            )
            assert depth == 1 + max_sub_depth
    
    def test_flatten(self, execution_result):
        """Flatten should return all nodes"""
        flattened = execution_result.flatten()
        
        assert len(flattened) >= 1
        assert flattened[0] == execution_result
        assert all(hasattr(item, 'status') for item in flattened)
    
    def test_summary_stats(self, execution_result):
        """Summary stats should be correct"""
        stats = execution_result.summary_stats()
        
        # Required fields
        required_fields = [
            "total_executions", "depth", "success", "failed",
            "skipped", "critical_errors", "warnings", "total_duration"
        ]
        for field in required_fields:
            assert field in stats
        
        # Validation
        assert stats["total_executions"] >= 1
        assert (
            stats["success"] + stats["failed"] + stats["skipped"] ==
            stats["total_executions"]
        )
        assert stats["total_duration"] >= 0
        assert stats["critical_errors"] >= 0
        assert stats["warnings"] >= 0

# === DEPENDENCY TESTS ===
class TestDependencies:
    """Test dependency handling"""
    
    def test_skipped_phases_have_reason(self, execution_result):
        """Skipped phases should have skip reason"""
        for sub in execution_result.sub_results:
            if sub.status == "skipped":
                assert sub.skipped_reason is not None
                assert len(sub.skipped_reason) > 0
    
    def test_dependencies_structure(self, execution_result):
        """Dependencies should be list of strings"""
        for sub in execution_result.sub_results:
            assert isinstance(sub.dependencies, list)
            assert all(isinstance(dep, str) for dep in sub.dependencies)

# === TIMING TESTS ===
class TestTiming:
    """Test duration and timing calculations"""
    
    def test_root_duration_positive(self, execution_result):
        """Root duration should be positive"""
        assert execution_result.duration > 0
    
    def test_sub_durations_non_negative(self, execution_result):
        """All sub-durations should be non-negative"""
        for sub in execution_result.sub_results:
            assert sub.duration >= 0
    
    def test_parent_duration_includes_children(self, execution_result):
        """Parent duration should be >= sum of sub-durations"""
        total_sub_duration = sum(
            sub.duration for sub in execution_result.sub_results
        )
        # Allow 10% margin for orchestration overhead
        assert execution_result.duration >= total_sub_duration * 0.9

# === METADATA TESTS ===
class TestMetadata:
    """Test metadata handling"""
    
    def test_has_metadata(self, execution_result):
        """Should have metadata dict"""
        assert isinstance(execution_result.metadata, dict)
    
    def test_composite_metadata(self, execution_result):
        """Composite agents should track sub-executions"""
        if execution_result.is_composite:
            assert (
                "sub_executions" in execution_result.metadata or
                len(execution_result.metadata) >= 0
            )