# tests/workflows_tests/test_orchestrator.py

import pytest
import json
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, call

from optiMoldMaster.opti_mold_master import OptiMoldIQ
from optiMoldMaster.workflows.executor import WorkflowExecutor, WorkflowExecutorResult
from optiMoldMaster.workflows.registry.registry import ModuleRegistry
from modules.base_module import ModuleResult


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_module_registry():
    """Mock ModuleRegistry"""
    registry = Mock(spec=ModuleRegistry)
    registry.available_modules = {
        "Module1": Mock(),
        "Module2": Mock(),
        "Module3": Mock()
    }
    return registry


@pytest.fixture
def workflows_dir(tmp_path):
    """Create temporary workflows directory with sample workflows"""
    workflows = tmp_path / "workflows"
    workflows.mkdir()
    return workflows


@pytest.fixture
def create_workflow_file(workflows_dir):
    """Helper to create workflow definition files"""
    def _create(name: str, content: dict):
        file_path = workflows_dir / f"{name}.json"
        with open(file_path, 'w') as f:
            json.dump(content, f)
        return file_path
    return _create


@pytest.fixture
def sample_workflows(create_workflow_file):
    """Create sample workflow files"""
    workflows = {
        "workflow1": {
            "name": "workflow1",
            "modules": [
                {
                    "module": "Module1",
                    "required": False,
                    "dependency_policy": "strict"
                }
            ]
        },
        "workflow2": {
            "name": "workflow2",
            "modules": [
                {
                    "module": "Module2",
                    "required": True,
                    "dependency_policy": {
                        "name": "flexible",
                        "params": {"max_age_days": 30}
                    }
                }
            ]
        },
        "workflow3": {
            "name": "workflow3",
            "modules": [
                {
                    "module": "Module3",
                    "required": False,
                    "dependency_policy": None
                }
            ]
        }
    }
    
    for name, content in workflows.items():
        create_workflow_file(name, content)
    
    return workflows


@pytest.fixture
def orchestrator(mock_module_registry, workflows_dir):
    """Create OptiMoldIQ orchestrator instance"""
    return OptiMoldIQ(
        module_registry=mock_module_registry,
        workflows_dir=str(workflows_dir)
    )


@pytest.fixture
def orchestrator_with_workflows(mock_module_registry, workflows_dir, sample_workflows):
    """Create orchestrator with pre-loaded workflows"""
    return OptiMoldIQ(
        module_registry=mock_module_registry,
        workflows_dir=str(workflows_dir)
    )


# ============================================================================
# INITIALIZATION TESTS
# ============================================================================

class TestOrchestratorInitialization:
    """Test OptiMoldIQ initialization"""
    
    def test_initialization_with_valid_workflows(
        self,
        mock_module_registry,
        workflows_dir,
        sample_workflows
    ):
        """Test successful initialization with valid workflows"""
        orchestrator = OptiMoldIQ(
            module_registry=mock_module_registry,
            workflows_dir=str(workflows_dir)
        )
        
        assert orchestrator.module_registry == mock_module_registry
        assert orchestrator.workflows_dir == workflows_dir
        assert len(orchestrator._available_workflows) == 3
        assert "workflow1" in orchestrator._available_workflows
        assert "workflow2" in orchestrator._available_workflows
        assert "workflow3" in orchestrator._available_workflows
    
    def test_initialization_with_empty_directory(
        self,
        mock_module_registry,
        workflows_dir
    ):
        """Test initialization with empty workflows directory"""
        orchestrator = OptiMoldIQ(
            module_registry=mock_module_registry,
            workflows_dir=str(workflows_dir)
        )
        
        assert len(orchestrator._available_workflows) == 0
        assert orchestrator._executors == {}
    
    def test_initialization_creates_empty_executor_cache(
        self,
        mock_module_registry,
        workflows_dir
    ):
        """Test that executor cache is initialized empty"""
        orchestrator = OptiMoldIQ(
            module_registry=mock_module_registry,
            workflows_dir=str(workflows_dir)
        )
        
        assert orchestrator._executors == {}


# ============================================================================
# WORKFLOW DISCOVERY TESTS
# ============================================================================

class TestWorkflowDiscovery:
    """Test workflow auto-discovery functionality"""
    
    def test_discover_all_valid_workflows(
        self,
        orchestrator_with_workflows
    ):
        """Test discovering all valid workflows"""
        workflows = orchestrator_with_workflows._available_workflows
        
        assert len(workflows) == 3
        assert all(isinstance(path, Path) for path in workflows.values())
        assert all(path.suffix == ".json" for path in workflows.values())
    
    def test_discover_workflows_ignores_non_json(
        self,
        mock_module_registry,
        workflows_dir
    ):
        """Test that non-JSON files are ignored"""
        # Create JSON and non-JSON files
        (workflows_dir / "valid.json").write_text('{"modules": []}')
        (workflows_dir / "ignored.txt").write_text("not json")
        (workflows_dir / "ignored.yaml").write_text("not json")
        
        orchestrator = OptiMoldIQ(
            module_registry=mock_module_registry,
            workflows_dir=str(workflows_dir)
        )
        
        assert len(orchestrator._available_workflows) == 1
        assert "valid" in orchestrator._available_workflows
        assert "ignored" not in orchestrator._available_workflows
    
    def test_discover_workflows_handles_invalid_json(
        self,
        mock_module_registry,
        workflows_dir
    ):
        """Test that invalid JSON files are skipped with error log"""
        (workflows_dir / "valid.json").write_text('{"modules": []}')
        (workflows_dir / "invalid.json").write_text('{ invalid json }')
        
        with patch('optiMoldMaster.optim_mold_master.logger') as mock_logger:
            orchestrator = OptiMoldIQ(
                module_registry=mock_module_registry,
                workflows_dir=str(workflows_dir)
            )
            
            # Should discover valid, skip invalid
            assert len(orchestrator._available_workflows) == 1
            assert "valid" in orchestrator._available_workflows
            
            # Should log error for invalid
            assert mock_logger.error.called
    
    def test_discover_workflows_with_subdirectories(
        self,
        mock_module_registry,
        workflows_dir
    ):
        """Test that only top-level JSON files are discovered"""
        # Top level
        (workflows_dir / "top_level.json").write_text('{"modules": []}')
        
        # Subdirectory
        subdir = workflows_dir / "subdir"
        subdir.mkdir()
        (subdir / "nested.json").write_text('{"modules": []}')
        
        orchestrator = OptiMoldIQ(
            module_registry=mock_module_registry,
            workflows_dir=str(workflows_dir)
        )
        
        # Should only find top-level workflow
        assert len(orchestrator._available_workflows) == 1
        assert "top_level" in orchestrator._available_workflows
        assert "nested" not in orchestrator._available_workflows


# ============================================================================
# WORKFLOW VALIDATION TESTS
# ============================================================================

class TestWorkflowValidation:
    """Test workflow definition validation"""
    
    def test_validate_workflow_missing_modules_field(
        self,
        orchestrator
    ):
        """Test validation fails when modules field is missing"""
        workflow_def = {"name": "broken"}
        
        with pytest.raises(ValueError, match="Missing 'modules' field"):
            orchestrator._validate_workflow_definition(workflow_def, "broken")
    
    def test_validate_workflow_module_missing_name(
        self,
        orchestrator
    ):
        """Test validation fails when module is missing 'module' field"""
        workflow_def = {
            "modules": [
                {"required": False}  # Missing 'module' field
            ]
        }
        
        with pytest.raises(ValueError, match="Missing 'module' field"):
            orchestrator._validate_workflow_definition(workflow_def, "broken")
    
    def test_validate_workflow_invalid_dependency_policy(
        self,
        orchestrator
    ):
        """Test validation fails with invalid dependency policy"""
        workflow_def = {
            "modules": [
                {
                    "module": "TestModule",
                    "dependency_policy": {
                        "name": "flexible",
                        "params": {"invalid_param": "value"}
                    }
                }
            ]
        }
        
        with pytest.raises(ValueError, match="Unknown parameters"):
            orchestrator._validate_workflow_definition(workflow_def, "broken")
    
    def test_validate_workflow_unknown_policy_name(
        self,
        orchestrator
    ):
        """Test validation fails with unknown policy name"""
        workflow_def = {
            "modules": [
                {
                    "module": "TestModule",
                    "dependency_policy": "unknown_policy"
                }
            ]
        }
        
        with pytest.raises(ValueError, match="Unknown dependency policy"):
            orchestrator._validate_workflow_definition(workflow_def, "broken")
    
    def test_validate_valid_workflow(
        self,
        orchestrator
    ):
        """Test validation succeeds with valid workflow"""
        workflow_def = {
            "modules": [
                {
                    "module": "Module1",
                    "required": True,
                    "dependency_policy": "strict"
                },
                {
                    "module": "Module2",
                    "dependency_policy": {
                        "name": "flexible",
                        "params": {"max_age_days": 30}
                    }
                }
            ]
        }
        
        # Should not raise
        orchestrator._validate_workflow_definition(workflow_def, "valid")
    
    def test_validate_workflow_multiple_errors(
        self,
        orchestrator
    ):
        """Test validation reports multiple errors"""
        workflow_def = {
            "modules": [
                {"required": False},  # Missing 'module'
                {
                    "module": "Module1",
                    "dependency_policy": "invalid_policy"
                }
            ]
        }
        
        with pytest.raises(ValueError) as exc_info:
            orchestrator._validate_workflow_definition(workflow_def, "broken")
        
        error_msg = str(exc_info.value)
        assert "Missing 'module' field" in error_msg
        assert "Unknown dependency policy" in error_msg


# ============================================================================
# WORKFLOW LISTING TESTS
# ============================================================================

class TestWorkflowListing:
    """Test workflow listing functionality"""
    
    def test_list_workflows(
        self,
        orchestrator_with_workflows
    ):
        """Test listing all available workflows"""
        workflows = orchestrator_with_workflows.list_workflows()
        
        assert isinstance(workflows, list)
        assert len(workflows) == 3
        assert "workflow1" in workflows
        assert "workflow2" in workflows
        assert "workflow3" in workflows
    
    def test_list_workflows_empty(
        self,
        orchestrator
    ):
        """Test listing when no workflows exist"""
        workflows = orchestrator.list_workflows()
        
        assert isinstance(workflows, list)
        assert len(workflows) == 0
    
    def test_get_workflow_info(
        self,
        orchestrator_with_workflows
    ):
        """Test getting workflow definition"""
        info = orchestrator_with_workflows.get_workflow_info("workflow1")
        
        assert info["name"] == "workflow1"
        assert "modules" in info
        assert len(info["modules"]) == 1
    
    def test_get_workflow_info_not_found(
        self,
        orchestrator_with_workflows
    ):
        """Test getting info for non-existent workflow"""
        with pytest.raises(ValueError, match="not found"):
            orchestrator_with_workflows.get_workflow_info("nonexistent")


# ============================================================================
# EXECUTOR MANAGEMENT TESTS
# ============================================================================

class TestExecutorManagement:
    """Test executor creation and caching"""
    
    def test_get_or_create_executor_creates_new(
        self,
        orchestrator_with_workflows
    ):
        """Test creating new executor"""
        executor = orchestrator_with_workflows._get_or_create_executor("workflow1")
        
        assert isinstance(executor, WorkflowExecutor)
        assert "workflow1" in orchestrator_with_workflows._executors
    
    def test_get_or_create_executor_reuses_cached(
        self,
        orchestrator_with_workflows
    ):
        """Test reusing cached executor"""
        executor1 = orchestrator_with_workflows._get_or_create_executor("workflow1")
        executor2 = orchestrator_with_workflows._get_or_create_executor("workflow1")
        
        assert executor1 is executor2
        assert len(orchestrator_with_workflows._executors) == 1
    
    def test_get_or_create_executor_different_workflows(
        self,
        orchestrator_with_workflows
    ):
        """Test creating different executors for different workflows"""
        executor1 = orchestrator_with_workflows._get_or_create_executor("workflow1")
        executor2 = orchestrator_with_workflows._get_or_create_executor("workflow2")
        
        assert executor1 is not executor2
        assert len(orchestrator_with_workflows._executors) == 2
    
    def test_get_or_create_executor_not_found(
        self,
        orchestrator_with_workflows
    ):
        """Test error when workflow doesn't exist"""
        with pytest.raises(ValueError, match="Workflow 'nonexistent' not found"):
            orchestrator_with_workflows._get_or_create_executor("nonexistent")


# ============================================================================
# WORKFLOW EXECUTION TESTS
# ============================================================================

class TestWorkflowExecution:
    """Test workflow execution"""
    
    @patch('optiMoldMaster.optim_mold_master.WorkflowExecutor')
    def test_execute_workflow_success(
        self,
        MockWorkflowExecutor,
        orchestrator_with_workflows
    ):
        """Test successful workflow execution"""
        # Setup mock executor
        mock_executor = Mock()
        mock_result = WorkflowExecutorResult(
            execution_id="abc123",
            workflow_name="workflow1",
            status="success",
            message="Completed"
        )
        mock_executor.execute.return_value = mock_result
        MockWorkflowExecutor.return_value = mock_executor
        
        result = orchestrator_with_workflows.execute("workflow1")
        
        assert result.is_success()
        assert result.workflow_name == "workflow1"
        mock_executor.execute.assert_called_once_with(workflow_name="workflow1")
    
    @patch('optiMoldMaster.optim_mold_master.WorkflowExecutor')
    def test_execute_workflow_not_found(
        self,
        MockWorkflowExecutor,
        orchestrator_with_workflows
    ):
        """Test executing non-existent workflow"""
        with pytest.raises(ValueError, match="not found"):
            orchestrator_with_workflows.execute("nonexistent")
    
    @patch('optiMoldMaster.optim_mold_master.WorkflowExecutor')
    def test_execute_workflow_with_clear_cache(
        self,
        MockWorkflowExecutor,
        orchestrator_with_workflows
    ):
        """Test executing workflow with cache clearing"""
        mock_executor = Mock()
        mock_executor._execution_cache = {"Module1": Mock()}
        mock_executor.execute.return_value = WorkflowExecutorResult(
            execution_id="123",
            workflow_name="workflow1",
            status="success",
            message="OK"
        )
        MockWorkflowExecutor.return_value = mock_executor
        
        result = orchestrator_with_workflows.execute("workflow1", clear_cache=True)
        
        # Cache should be cleared
        mock_executor._execution_cache.clear.assert_called_once()
        assert result.is_success()
    
    @patch('optiMoldMaster.optim_mold_master.WorkflowExecutor')
    def test_execute_workflow_without_clear_cache(
        self,
        MockWorkflowExecutor,
        orchestrator_with_workflows
    ):
        """Test executing workflow without clearing cache"""
        mock_executor = Mock()
        mock_executor._execution_cache = {"Module1": Mock()}
        mock_executor.execute.return_value = WorkflowExecutorResult(
            execution_id="123",
            workflow_name="workflow1",
            status="success",
            message="OK"
        )
        MockWorkflowExecutor.return_value = mock_executor
        
        result = orchestrator_with_workflows.execute("workflow1", clear_cache=False)
        
        # Cache should NOT be cleared
        mock_executor._execution_cache.clear.assert_not_called()
        assert result.is_success()
    
    @patch('optiMoldMaster.optim_mold_master.WorkflowExecutor')
    def test_execute_reuses_cached_executor(
        self,
        MockWorkflowExecutor,
        orchestrator_with_workflows
    ):
        """Test that multiple executions reuse same executor"""
        mock_executor = Mock()
        mock_executor.execute.return_value = WorkflowExecutorResult(
            execution_id="123",
            workflow_name="workflow1",
            status="success",
            message="OK"
        )
        MockWorkflowExecutor.return_value = mock_executor
        
        # Execute twice
        orchestrator_with_workflows.execute("workflow1")
        orchestrator_with_workflows.execute("workflow1")
        
        # Executor should only be created once
        assert MockWorkflowExecutor.call_count == 1
        # But execute should be called twice
        assert mock_executor.execute.call_count == 2


# ============================================================================
# WORKFLOW CHAINING TESTS
# ============================================================================

class TestWorkflowChaining:
    """Test workflow chaining functionality"""
    
    @patch('optiMoldMaster.optim_mold_master.WorkflowExecutor')
    def test_execute_chain_success(
        self,
        MockWorkflowExecutor,
        orchestrator_with_workflows
    ):
        """Test successful execution of workflow chain"""
        mock_executor = Mock()
        
        def execute_side_effect(workflow_name):
            return WorkflowExecutorResult(
                execution_id="123",
                workflow_name=workflow_name,
                status="success",
                message="OK"
            )
        
        mock_executor.execute.side_effect = execute_side_effect
        MockWorkflowExecutor.return_value = mock_executor
        
        results = orchestrator_with_workflows.execute_chain(
            ["workflow1", "workflow2", "workflow3"]
        )
        
        assert len(results) == 3
        assert all(result.is_success() for result in results.values())
        assert "workflow1" in results
        assert "workflow2" in results
        assert "workflow3" in results
    
    @patch('optiMoldMaster.optim_mold_master.WorkflowExecutor')
    def test_execute_chain_stops_on_failure(
        self,
        MockWorkflowExecutor,
        orchestrator_with_workflows
    ):
        """Test chain stops when workflow fails"""
        mock_executor = Mock()
        
        call_count = [0]
        def execute_side_effect(workflow_name):
            call_count[0] += 1
            if call_count[0] == 2:
                # Second workflow fails
                return WorkflowExecutorResult(
                    execution_id="123",
                    workflow_name=workflow_name,
                    status="failed",
                    message="Failed"
                )
            return WorkflowExecutorResult(
                execution_id="123",
                workflow_name=workflow_name,
                status="success",
                message="OK"
            )
        
        mock_executor.execute.side_effect = execute_side_effect
        MockWorkflowExecutor.return_value = mock_executor
        
        results = orchestrator_with_workflows.execute_chain(
            ["workflow1", "workflow2", "workflow3"],
            stop_on_failure=True
        )
        
        # Should only execute first 2 workflows
        assert len(results) == 2
        assert results["workflow1"].is_success()
        assert results["workflow2"].is_failed()
        assert "workflow3" not in results
    
    @patch('optiMoldMaster.optim_mold_master.WorkflowExecutor')
    def test_execute_chain_continues_on_failure(
        self,
        MockWorkflowExecutor,
        orchestrator_with_workflows
    ):
        """Test chain continues when stop_on_failure=False"""
        mock_executor = Mock()
        
        call_count = [0]
        def execute_side_effect(workflow_name):
            call_count[0] += 1
            if call_count[0] == 2:
                # Second workflow fails
                return WorkflowExecutorResult(
                    execution_id="123",
                    workflow_name=workflow_name,
                    status="failed",
                    message="Failed"
                )
            return WorkflowExecutorResult(
                execution_id="123",
                workflow_name=workflow_name,
                status="success",
                message="OK"
            )
        
        mock_executor.execute.side_effect = execute_side_effect
        MockWorkflowExecutor.return_value = mock_executor
        
        results = orchestrator_with_workflows.execute_chain(
            ["workflow1", "workflow2", "workflow3"],
            stop_on_failure=False
        )
        
        # Should execute all 3 workflows
        assert len(results) == 3
        assert results["workflow1"].is_success()
        assert results["workflow2"].is_failed()
        assert results["workflow3"].is_success()
    
    @patch('optiMoldMaster.optim_mold_master.WorkflowExecutor')
    def test_execute_chain_empty_list(
        self,
        MockWorkflowExecutor,
        orchestrator_with_workflows
    ):
        """Test executing empty workflow chain"""
        results = orchestrator_with_workflows.execute_chain([])
        
        assert len(results) == 0
        assert isinstance(results, dict)
    
    @patch('optiMoldMaster.optim_mold_master.WorkflowExecutor')
    def test_execute_chain_single_workflow(
        self,
        MockWorkflowExecutor,
        orchestrator_with_workflows
    ):
        """Test executing chain with single workflow"""
        mock_executor = Mock()
        mock_executor.execute.return_value = WorkflowExecutorResult(
            execution_id="123",
            workflow_name="workflow1",
            status="success",
            message="OK"
        )
        MockWorkflowExecutor.return_value = mock_executor
        
        results = orchestrator_with_workflows.execute_chain(["workflow1"])
        
        assert len(results) == 1
        assert results["workflow1"].is_success()


# ============================================================================
# CACHE MANAGEMENT TESTS
# ============================================================================

class TestCacheManagement:
    """Test cache management functionality"""
    
    @patch('optiMoldMaster.optim_mold_master.WorkflowExecutor')
    def test_clear_all_caches(
        self,
        MockWorkflowExecutor,
        orchestrator_with_workflows
    ):
        """Test clearing all executor caches"""
        # Create multiple executors
        mock_executor1 = Mock()
        mock_executor1._execution_cache = {"Module1": Mock()}
        mock_executor2 = Mock()
        mock_executor2._execution_cache = {"Module2": Mock()}
        
        MockWorkflowExecutor.side_effect = [mock_executor1, mock_executor2]
        
        # Trigger executor creation
        orchestrator_with_workflows._get_or_create_executor("workflow1")
        orchestrator_with_workflows._get_or_create_executor("workflow2")
        
        # Clear all caches
        orchestrator_with_workflows.clear_all_caches()
        
        # Both caches should be cleared
        mock_executor1._execution_cache.clear.assert_called_once()
        mock_executor2._execution_cache.clear.assert_called_once()
    
    @patch('optiMoldMaster.optim_mold_master.WorkflowExecutor')
    def test_clear_all_caches_no_executors(
        self,
        MockWorkflowExecutor,
        orchestrator_with_workflows
    ):
        """Test clearing caches when no executors exist"""
        # Should not raise error
        orchestrator_with_workflows.clear_all_caches()
    
    @patch('optiMoldMaster.optim_mold_master.WorkflowExecutor')
    def test_get_cache_stats(
        self,
        MockWorkflowExecutor,
        orchestrator_with_workflows
    ):
        """Test getting cache statistics"""
        mock_executor1 = Mock()
        mock_executor1._execution_cache = {"Module1": Mock(), "Module2": Mock()}
        mock_executor2 = Mock()
        mock_executor2._execution_cache = {"Module3": Mock()}
        
        MockWorkflowExecutor.side_effect = [mock_executor1, mock_executor2]
        
        # Create executors
        orchestrator_with_workflows._get_or_create_executor("workflow1")
        orchestrator_with_workflows._get_or_create_executor("workflow2")
        
        stats = orchestrator_with_workflows.get_cache_stats()
        
        assert stats["workflow1"] == 2
        assert stats["workflow2"] == 1
    
    @patch('optiMoldMaster.optim_mold_master.WorkflowExecutor')
    def test_get_cache_stats_empty(
        self,
        MockWorkflowExecutor,
        orchestrator_with_workflows
    ):
        """Test getting cache stats when no executors"""
        stats = orchestrator_with_workflows.get_cache_stats()
        
        assert isinstance(stats, dict)
        assert len(stats) == 0


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestOrchestratorIntegration:
    """Integration tests for complete orchestrator workflows"""
    
    def test_complete_orchestration_flow(
        self,
        mock_module_registry,
        workflows_dir,
        tmp_path
    ):
        """Test complete flow: discover -> validate -> execute"""
        # Create workflows
        workflow1 = {
            "name": "data_pipeline",
            "modules": [
                {
                    "module": "Module1",
                    "required": True,
                    "dependency_policy": "strict"
                }
            ]
        }
        workflow2 = {
            "name": "analysis",
            "modules": [
                {
                    "module": "Module2",
                    "required": False,
                    "dependency_policy": {
                        "name": "flexible",
                        "params": {"max_age_days": 30}
                    }
                }
            ]
        }
        
        (workflows_dir / "data_pipeline.json").write_text(json.dumps(workflow1))
        (workflows_dir / "analysis.json").write_text(json.dumps(workflow2))
        
        # Initialize orchestrator
        orchestrator = OptiMoldIQ(
            module_registry=mock_module_registry,
            workflows_dir=str(workflows_dir)
        )
        
        # Verify discovery
        assert len(orchestrator.list_workflows()) == 2
        
        # Verify info retrieval
        info = orchestrator.get_workflow_info("data_pipeline")
        assert info["name"] == "data_pipeline"
    
    def test_orchestrator_with_invalid_and_valid_workflows(
        self,
        mock_module_registry,
        workflows_dir
    ):
        """Test orchestrator handles mix of valid and invalid workflows"""
        # Valid workflow
        valid = {
            "modules": [
                {"module": "Module1", "dependency_policy": "strict"}
            ]
        }
        (workflows_dir / "valid.json").write_text(json.dumps(valid))
        
        # Invalid workflow (missing modules)
        invalid = {"name": "broken"}
        (workflows_dir / "invalid.json").write_text(json.dumps(invalid))
        
        # Invalid JSON
        (workflows_dir / "corrupt.json").write_text("{ invalid }")
        
        orchestrator = OptiMoldIQ(
            module_registry=mock_module_registry,
            workflows_dir=str(workflows_dir)
        )
        
        # Should only load valid workflow
        assert len(orchestrator.list_workflows()) == 1
        assert "valid" in orchestrator.list_workflows()


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

class TestErrorHandling:
    """Test error handling and edge cases"""
    
    def test_workflows_dir_not_exists(
        self,
        mock_module_registry,
        tmp_path
    ):
        """Test handling when workflows directory doesn't exist"""
        nonexistent = tmp_path / "nonexistent"
        
        orchestrator = OptiMoldIQ(
            module_registry=mock_module_registry,
            workflows_dir=str(nonexistent)
        )
        
        # Should handle gracefully
        assert len(orchestrator.list_workflows()) == 0
    
    def test_workflow_file_read_permission_error(
        self,
        mock_module_registry,
        workflows_dir
    ):
        """Test handling file permission errors"""
        workflow_file = workflows_dir / "restricted.json"
        workflow_file.write_text('{"modules": []}')
        
        # Mock permission error
        with patch('builtins.open', side_effect=PermissionError("Access denied")):
            orchestrator = OptiMoldIQ(
                module_registry=mock_module_registry,
                workflows_dir=str(workflows_dir)
            )
            
            # Should handle gracefully and continue
            assert isinstance(orchestrator, OptiMoldIQ)


# ============================================================================
# EDGE CASES
# ============================================================================

class TestEdgeCases:
    """Test edge cases and boundary conditions"""
    
    def test_workflow_with_unicode_name(
        self,
        mock_module_registry,
        workflows_dir
    ):
        """Test workflow with Unicode characters in filename"""
        workflow = {"modules": []}
        unicode_file = workflows_dir / "工作流程.json"
        unicode_file.write_text(json.dumps(workflow), encoding='utf-8')
        
        orchestrator = OptiMoldIQ(
            module_registry=mock_module_registry,
            workflows_dir=str(workflows_dir)
        )
        
        assert "工作流程" in orchestrator.list_workflows()
    
    def test_workflow_with_very_long_name(
        self,
        mock_module_registry,
        workflows_dir
    ):
        """Test workflow with very long filename"""
        workflow = {"modules": []}
        long_name = "a" * 200
        long_file = workflows_dir / f"{long_name}.json"
        long_file.write_text(json.dumps(workflow))
        
        orchestrator = OptiMoldIQ(
            module_registry=mock_module_registry,
            workflows_dir=str(workflows_dir)
        )
        
        assert long_name in orchestrator.list_workflows()
    
    def test_multiple_orchestrators_same_workflows_dir(
        self,
        mock_module_registry,
        workflows_dir,
        sample_workflows
    ):
        """Test multiple orchestrator instances with same workflows"""
        orchestrator1 = OptiMoldIQ(
            module_registry=mock_module_registry,
            workflows_dir=str(workflows_dir)
        )
        orchestrator2 = OptiMoldIQ(
            module_registry=mock_module_registry,
            workflows_dir=str(workflows_dir)
        )
        
        # Both should discover same workflows
        assert orchestrator1.list_workflows() == orchestrator2.list_workflows()
        
        # But should have separate executor caches
        assert orchestrator1._executors is not orchestrator2._executors