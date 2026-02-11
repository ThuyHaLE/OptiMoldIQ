# tests/workflows_tests/test_executor.py

import pytest
import json
import uuid
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, mock_open, call
from dataclasses import dataclass

from optiMoldMaster.workflows.executor import WorkflowExecutor, WorkflowExecutorResult
from optiMoldMaster.workflows.dependency_policies.base import (
    DependencyValidationResult,
    DependencyIssue,
    DependencyReason,
    DependencySource
)
from modules.base_module import ModuleResult


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_registry():
    """Mock ModuleRegistry"""
    registry = Mock()
    return registry


@pytest.fixture
def workflows_dir(tmp_path):
    """Create temporary workflows directory"""
    workflows = tmp_path / "workflows"
    workflows.mkdir()
    return str(workflows)


@pytest.fixture
def sample_workflow_dict():
    """Sample workflow definition"""
    return {
        "name": "test_workflow",
        "description": "Test workflow",
        "modules": [
            {
                "module": "DataPipelineModule",
                "config_file": "configs/pipeline.yaml",
                "required": True,
                "dependency_policy": "strict"
            },
            {
                "module": "AnalysisModule",
                "config_file": "configs/analysis.yaml",
                "required": False,
                "dependency_policy": {
                    "name": "flexible",
                    "params": {"max_age_days": 30}
                }
            }
        ]
    }


@pytest.fixture
def executor(mock_registry, workflows_dir):
    """Create WorkflowExecutor instance"""
    return WorkflowExecutor(
        registry=mock_registry,
        workflows_dir=workflows_dir
    )


@pytest.fixture
def create_workflow_file(workflows_dir):
    """Helper to create workflow files"""
    def _create(name: str, content: dict):
        file_path = Path(workflows_dir) / f"{name}.json"
        with open(file_path, 'w') as f:
            json.dump(content, f)
        return file_path
    return _create


@pytest.fixture
def mock_module_instance():
    """Mock module instance"""
    module = Mock()
    module.dependencies = {"dep1": "/path/to/dep1"}
    module.safe_execute.return_value = ModuleResult(
        status="success",
        data={"result": "data"},
        message="Success"
    )
    return module


# ============================================================================
# WorkflowExecutorResult TESTS
# ============================================================================

class TestWorkflowExecutorResult:
    """Test WorkflowExecutorResult dataclass"""
    
    def test_result_initialization(self):
        result = WorkflowExecutorResult(
            execution_id="abc123",
            workflow_name="test_workflow",
            status="success",
            message="Completed"
        )
        
        assert result.execution_id == "abc123"
        assert result.workflow_name == "test_workflow"
        assert result.status == "success"
        assert result.message == "Completed"
        assert result.results == {}
        assert result.execution_context == {}
    
    def test_is_success(self):
        result = WorkflowExecutorResult(
            execution_id="123",
            workflow_name="test",
            status="success",
            message="OK"
        )
        assert result.is_success() is True
        assert result.is_failed() is False
        assert result.is_skipped() is False
    
    def test_is_failed(self):
        result = WorkflowExecutorResult(
            execution_id="123",
            workflow_name="test",
            status="failed",
            message="Error"
        )
        assert result.is_success() is False
        assert result.is_failed() is True
        assert result.is_skipped() is False
    
    def test_is_skipped(self):
        result = WorkflowExecutorResult(
            execution_id="123",
            workflow_name="test",
            status="skipped",
            message="Skipped"
        )
        assert result.is_success() is False
        assert result.is_failed() is False
        assert result.is_skipped() is True
    
    def test_with_results_and_context(self):
        result = WorkflowExecutorResult(
            execution_id="123",
            workflow_name="test",
            status="success",
            message="OK",
            results={"module1": {"status": "success"}},
            execution_context={"cached": ["module1"]}
        )
        
        assert "module1" in result.results
        assert "cached" in result.execution_context


# ============================================================================
# WORKFLOW LOADING TESTS
# ============================================================================

class TestWorkflowLoading:
    """Test workflow loading functionality"""
    
    def test_load_workflow_success(self, executor, create_workflow_file, sample_workflow_dict):
        """Test successfully loading a workflow"""
        create_workflow_file("test_workflow", sample_workflow_dict)
        
        workflow = executor._load_workflow("test_workflow")
        
        assert workflow["name"] == "test_workflow"
        assert len(workflow["modules"]) == 2
        assert workflow["modules"][0]["module"] == "DataPipelineModule"
    
    def test_load_workflow_not_found(self, executor):
        """Test loading non-existent workflow raises error"""
        with pytest.raises(FileNotFoundError, match="Workflow file not found"):
            executor._load_workflow("nonexistent_workflow")
    
    def test_get_workflow_info(self, executor, create_workflow_file, sample_workflow_dict):
        """Test get_workflow_info returns workflow definition"""
        create_workflow_file("test_workflow", sample_workflow_dict)
        
        info = executor.get_workflow_info("test_workflow")
        
        assert info == sample_workflow_dict
    
    def test_load_workflow_invalid_json(self, executor, workflows_dir):
        """Test loading workflow with invalid JSON"""
        file_path = Path(workflows_dir) / "invalid.json"
        file_path.write_text("{ invalid json }")
        
        with pytest.raises(json.JSONDecodeError):
            executor._load_workflow("invalid")


# ============================================================================
# DEPENDENCY VALIDATION TESTS
# ============================================================================

class TestDependencyValidation:
    """Test dependency validation"""
    
    def test_validate_dependencies_with_strict_policy(self, executor):
        """Test dependency validation with strict policy"""
        from optiMoldMaster.workflows.dependency_policies.strict import StrictWorkflowPolicy
        
        module = Mock()
        module.dependencies = {"dep1": "/path/dep1"}
        
        policy = StrictWorkflowPolicy()
        requested_modules = ["dep1"]
        
        result = executor.validate_dependencies(
            module_instance=module,
            requested_modules=requested_modules,
            dependency_policy=policy
        )
        
        assert result.valid is True
        assert "dep1" in result.resolved
    
    def test_validate_dependencies_missing_dependency(self, executor):
        """Test validation with missing dependency"""
        from optiMoldMaster.workflows.dependency_policies.strict import StrictWorkflowPolicy
        
        module = Mock()
        module.dependencies = {"dep1": "/path/dep1"}
        
        policy = StrictWorkflowPolicy()
        requested_modules = []  # dep1 not in workflow
        
        result = executor.validate_dependencies(
            module_instance=module,
            requested_modules=requested_modules,
            dependency_policy=policy
        )
        
        assert result.valid is False
        assert "dep1" in result.errors
    
    def test_validate_dependencies_default_strict_policy(self, executor):
        """Test that default policy is StrictWorkflowPolicy"""
        module = Mock()
        module.dependencies = {"dep1": "/path/dep1"}
        
        # Don't pass policy - should use default
        result = executor.validate_dependencies(
            module_instance=module,
            requested_modules=["dep1"],
            dependency_policy=None
        )
        
        assert result.valid is True
    
    def test_validate_dependencies_flexible_policy(self, executor, tmp_path):
        """Test validation with flexible policy"""
        from optiMoldMaster.workflows.dependency_policies.flexible import FlexibleDependencyPolicy
        
        # Create test file
        test_file = tmp_path / "data.txt"
        test_file.write_text("data")
        
        module = Mock()
        module.dependencies = {"dep1": str(test_file)}
        
        policy = FlexibleDependencyPolicy()
        requested_modules = []
        
        result = executor.validate_dependencies(
            module_instance=module,
            requested_modules=requested_modules,
            dependency_policy=policy
        )
        
        # Flexible policy should allow missing workflow deps
        assert result.valid is True


# ============================================================================
# MODULE EXECUTION TESTS
# ============================================================================

class TestModuleExecution:
    """Test individual module execution within workflow"""
    
    def test_execute_single_module_success(
        self, 
        executor, 
        mock_registry,
        create_workflow_file,
        mock_module_instance
    ):
        """Test successful execution of single module"""
        workflow = {
            "modules": [
                {
                    "module": "TestModule",
                    "required": False,
                    "dependency_policy": None
                }
            ]
        }
        create_workflow_file("single_module", workflow)
        
        mock_registry.get_module_instance.return_value = mock_module_instance
        mock_module_instance.dependencies = {}
        
        result = executor.execute("single_module")
        
        assert result.is_success()
        assert "TestModule" in result.results
        assert result.results["TestModule"]["status"] == "success"
    
    def test_execute_module_with_config(
        self,
        executor,
        mock_registry,
        create_workflow_file,
        mock_module_instance
    ):
        """Test module execution with config file"""
        workflow = {
            "modules": [
                {
                    "module": "TestModule",
                    "config_file": "configs/test.yaml",
                    "required": False,
                    "dependency_policy": None
                }
            ]
        }
        create_workflow_file("with_config", workflow)
        
        mock_registry.get_module_instance.return_value = mock_module_instance
        mock_module_instance.dependencies = {}
        
        result = executor.execute("with_config")
        
        # Verify config_file was passed to registry
        mock_registry.get_module_instance.assert_called_once_with(
            "TestModule",
            "configs/test.yaml"
        )
        assert result.is_success()
    
    def test_execute_required_module_failure_stops_workflow(
        self,
        executor,
        mock_registry,
        create_workflow_file,
        mock_module_instance
    ):
        """Test that required module failure stops workflow"""
        workflow = {
            "modules": [
                {
                    "module": "RequiredModule",
                    "required": True,
                    "dependency_policy": None
                },
                {
                    "module": "NeverExecutedModule",
                    "required": False,
                    "dependency_policy": None
                }
            ]
        }
        create_workflow_file("required_fail", workflow)
        
        # First module fails
        failed_module = Mock()
        failed_module.dependencies = {}
        failed_module.safe_execute.return_value = ModuleResult(
            status="failed",
            data=None,
            message="Module failed",
            errors=["Error occurred"]
        )
        
        mock_registry.get_module_instance.return_value = failed_module
        
        result = executor.execute("required_fail")
        
        assert result.is_failed()
        assert "RequiredModule" in result.results
        assert "NeverExecutedModule" not in result.results
        assert "Module RequiredModule failed" in result.message
    
    def test_execute_optional_module_failure_continues(
        self,
        executor,
        mock_registry,
        create_workflow_file
    ):
        """Test that optional module failure allows workflow to continue"""
        workflow = {
            "modules": [
                {
                    "module": "OptionalModule",
                    "required": False,
                    "dependency_policy": None
                },
                {
                    "module": "SecondModule",
                    "required": False,
                    "dependency_policy": None
                }
            ]
        }
        create_workflow_file("optional_fail", workflow)
        
        # First module fails, second succeeds
        call_count = [0]
        def get_module_side_effect(name, config):
            call_count[0] += 1
            module = Mock()
            module.dependencies = {}
            if call_count[0] == 1:
                # First call - failed module
                module.safe_execute.return_value = ModuleResult(
                    status="failed",
                    data=None,
                    message="Failed"
                )
            else:
                # Second call - success
                module.safe_execute.return_value = ModuleResult(
                    status="success",
                    data={"result": "ok"},
                    message="Success"
                )
            return module
        
        mock_registry.get_module_instance.side_effect = get_module_side_effect
        
        result = executor.execute("optional_fail")
        
        # Workflow should succeed because failures are optional
        assert result.is_success()
        assert len(result.results) == 2
        assert result.results["OptionalModule"]["status"] == "failed"
        assert result.results["SecondModule"]["status"] == "success"
    
    def test_execute_module_dependency_validation_failure(
        self,
        executor,
        mock_registry,
        create_workflow_file
    ):
        """Test module skipped when dependency validation fails"""
        workflow = {
            "modules": [
                {
                    "module": "TestModule",
                    "required": False,
                    "dependency_policy": "strict"
                }
            ]
        }
        create_workflow_file("dep_fail", workflow)
        
        module = Mock()
        module.dependencies = {"missing_dep": "/path/missing"}
        mock_registry.get_module_instance.return_value = module
        
        result = executor.execute("dep_fail")
        
        # Module should be skipped
        assert result.is_success()  # Workflow succeeds but module skipped
        assert result.results["TestModule"]["status"] == "skipped"
        assert "Dependencies not met" in result.results["TestModule"]["message"]
    
    def test_execute_required_module_dependency_failure_stops(
        self,
        executor,
        mock_registry,
        create_workflow_file
    ):
        """Test required module with dependency failure stops workflow"""
        workflow = {
            "modules": [
                {
                    "module": "RequiredModule",
                    "required": True,
                    "dependency_policy": "strict"
                }
            ]
        }
        create_workflow_file("required_dep_fail", workflow)
        
        module = Mock()
        module.dependencies = {"missing_dep": "/path/missing"}
        mock_registry.get_module_instance.return_value = module
        
        result = executor.execute("required_dep_fail")
        
        assert result.is_failed()
        assert "Dependency validation failed" in result.message


# ============================================================================
# EXECUTION CACHE TESTS
# ============================================================================

class TestExecutionCache:
    """Test execution caching functionality"""
    
    def test_module_executed_once_with_cache(
        self,
        executor,
        mock_registry,
        create_workflow_file,
        mock_module_instance
    ):
        """Test that module is only executed once when cached"""
        workflow = {
            "modules": [
                {"module": "CachedModule", "required": False, "dependency_policy": None},
                {"module": "CachedModule", "required": False, "dependency_policy": None}
            ]
        }
        create_workflow_file("cached", workflow)
        
        mock_registry.get_module_instance.return_value = mock_module_instance
        mock_module_instance.dependencies = {}
        
        result = executor.execute("cached")
        
        # Module should only be instantiated once
        assert mock_registry.get_module_instance.call_count == 1
        # safe_execute should only be called once
        assert mock_module_instance.safe_execute.call_count == 1
        
        assert result.is_success()
        assert result.execution_context["total_modules"] == 2
        assert "CachedModule" in result.execution_context["cached_modules"]
    
    def test_cache_persists_across_workflow_executions(
        self,
        executor,
        mock_registry,
        create_workflow_file,
        mock_module_instance
    ):
        """Test cache persists across multiple workflow executions"""
        workflow = {
            "modules": [
                {"module": "Module1", "required": False, "dependency_policy": None}
            ]
        }
        create_workflow_file("persist", workflow)
        
        mock_registry.get_module_instance.return_value = mock_module_instance
        mock_module_instance.dependencies = {}
        
        # Execute twice
        result1 = executor.execute("persist")
        result2 = executor.execute("persist")
        
        # Should only execute once total
        assert mock_module_instance.safe_execute.call_count == 1
        
        assert result1.is_success()
        assert result2.is_success()
    
    def test_cache_stores_module_results(
        self,
        executor,
        mock_registry,
        create_workflow_file,
        mock_module_instance
    ):
        """Test that cache stores actual module results"""
        workflow = {
            "modules": [
                {"module": "Module1", "required": False, "dependency_policy": None}
            ]
        }
        create_workflow_file("cache_result", workflow)
        
        expected_result = ModuleResult(
            status="success",
            data={"key": "value"},
            message="Cached result"
        )
        mock_module_instance.safe_execute.return_value = expected_result
        mock_module_instance.dependencies = {}
        mock_registry.get_module_instance.return_value = mock_module_instance
        
        result = executor.execute("cache_result")
        
        # Check cache contains the result
        assert "Module1" in executor._execution_cache
        cached_result = executor._execution_cache["Module1"]
        assert cached_result.status == "success"
        assert cached_result.data == {"key": "value"}


# ============================================================================
# WORKFLOW EXECUTION TESTS
# ============================================================================

class TestWorkflowExecution:
    """Test complete workflow execution"""
    
    def test_execute_empty_workflow(
        self,
        executor,
        create_workflow_file
    ):
        """Test executing workflow with no modules"""
        workflow = {"modules": []}
        create_workflow_file("empty", workflow)
        
        result = executor.execute("empty")
        
        assert result.is_success()
        assert len(result.results) == 0
        assert result.message == "Workflow completed successfully"
    
    def test_execute_multi_module_workflow(
        self,
        executor,
        mock_registry,
        create_workflow_file
    ):
        """Test executing workflow with multiple modules"""
        workflow = {
            "modules": [
                {"module": "Module1", "required": False, "dependency_policy": None},
                {"module": "Module2", "required": False, "dependency_policy": None},
                {"module": "Module3", "required": False, "dependency_policy": None}
            ]
        }
        create_workflow_file("multi", workflow)
        
        def get_module(name, config):
            module = Mock()
            module.dependencies = {}
            module.safe_execute.return_value = ModuleResult(
                status="success",
                data={f"{name}_data": "value"},
                message=f"{name} completed"
            )
            return module
        
        mock_registry.get_module_instance.side_effect = get_module
        
        result = executor.execute("multi")
        
        assert result.is_success()
        assert len(result.results) == 3
        assert all(
            result.results[f"Module{i}"]["status"] == "success"
            for i in range(1, 4)
        )
    
    def test_execute_workflow_generates_execution_id(
        self,
        executor,
        mock_registry,
        create_workflow_file,
        mock_module_instance
    ):
        """Test that each execution generates unique ID"""
        workflow = {
            "modules": [
                {"module": "Module1", "required": False, "dependency_policy": None}
            ]
        }
        create_workflow_file("unique_id", workflow)
        
        mock_registry.get_module_instance.return_value = mock_module_instance
        mock_module_instance.dependencies = {}
        
        result1 = executor.execute("unique_id")
        
        # Clear cache for second execution
        executor._execution_cache.clear()
        
        result2 = executor.execute("unique_id")
        
        # IDs should be different
        assert result1.execution_id != result2.execution_id
        # IDs should be 8 characters (hex)
        assert len(result1.execution_id) == 8
        assert len(result2.execution_id) == 8
    
    def test_execute_workflow_with_mixed_policies(
        self,
        executor,
        mock_registry,
        create_workflow_file,
        tmp_path
    ):
        """Test workflow with different dependency policies per module"""
        # Create test file
        test_file = tmp_path / "data.txt"
        test_file.write_text("test data")
        
        workflow = {
            "modules": [
                {
                    "module": "StrictModule",
                    "required": False,
                    "dependency_policy": "strict"
                },
                {
                    "module": "FlexibleModule",
                    "required": False,
                    "dependency_policy": {
                        "name": "flexible",
                        "params": {"max_age_days": 30}
                    }
                }
            ]
        }
        create_workflow_file("mixed_policies", workflow)
        
        call_count = [0]
        def get_module_side_effect(name, config):
            call_count[0] += 1
            module = Mock()
            if call_count[0] == 1:
                # StrictModule - dependency in workflow
                module.dependencies = {"dep1": "/path/dep1"}
            else:
                # FlexibleModule - dependency in filesystem
                module.dependencies = {"dep2": str(test_file)}
            
            module.safe_execute.return_value = ModuleResult(
                status="success",
                data={},
                message="OK"
            )
            return module
        
        mock_registry.get_module_instance.side_effect = get_module_side_effect
        
        result = executor.execute("mixed_policies")
        
        assert result.is_success()
        assert len(result.results) == 2


# ============================================================================
# RESPONSE BUILDER TESTS
# ============================================================================

class TestResponseBuilder:
    """Test response building functionality"""
    
    def test_build_response_success(self, executor):
        """Test building successful response"""
        module_results = {
            "Module1": ModuleResult(
                status="success",
                data={"key": "value"},
                message="Success"
            )
        }
        
        response = executor._build_response(
            workflow_name="test_workflow",
            execution_id="abc123",
            status="success",
            message="Completed",
            results=module_results
        )
        
        assert isinstance(response, WorkflowExecutorResult)
        assert response.execution_id == "abc123"
        assert response.workflow_name == "test_workflow"
        assert response.status == "success"
        assert "Module1" in response.results
        assert response.results["Module1"]["status"] == "success"
        assert response.results["Module1"]["data"] == {"key": "value"}
    
    def test_build_response_with_execution_context(self, executor):
        """Test response includes execution context"""
        executor._execution_cache["CachedModule"] = ModuleResult(
            status="success",
            data={},
            message="Cached"
        )
        
        module_results = {
            "Module1": ModuleResult(status="success", data={}, message="OK")
        }
        
        response = executor._build_response(
            workflow_name="test",
            execution_id="123",
            status="success",
            message="OK",
            results=module_results
        )
        
        assert "cached_modules" in response.execution_context
        assert "CachedModule" in response.execution_context["cached_modules"]
        assert response.execution_context["total_modules"] == 1
    
    def test_build_response_with_errors(self, executor):
        """Test building response with module errors"""
        module_results = {
            "FailedModule": ModuleResult(
                status="failed",
                data=None,
                message="Module failed",
                errors=["Error 1", "Error 2"]
            )
        }
        
        response = executor._build_response(
            workflow_name="test",
            execution_id="123",
            status="failed",
            message="Workflow failed",
            results=module_results
        )
        
        assert response.status == "failed"
        assert response.results["FailedModule"]["errors"] == ["Error 1", "Error 2"]


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestExecutorIntegration:
    """Integration tests for complete execution flows"""
    
    def test_complete_workflow_execution_flow(
        self,
        executor,
        mock_registry,
        create_workflow_file,
        tmp_path
    ):
        """Test complete realistic workflow execution"""
        # Create data files
        input_file = tmp_path / "input.dat"
        input_file.write_text("input data")
        
        workflow = {
            "name": "data_pipeline",
            "description": "Complete data pipeline",
            "modules": [
                {
                    "module": "DataIngestion",
                    "config_file": "configs/ingestion.yaml",
                    "required": True,
                    "dependency_policy": {
                        "name": "flexible",
                        "params": {
                            "required_deps": ["input_data"],
                            "max_age_days": 7
                        }
                    }
                },
                {
                    "module": "DataTransform",
                    "config_file": "configs/transform.yaml",
                    "required": True,
                    "dependency_policy": "strict"
                },
                {
                    "module": "DataExport",
                    "config_file": None,
                    "required": False,
                    "dependency_policy": "hybrid"
                }
            ]
        }
        create_workflow_file("data_pipeline", workflow)
        
        # Setup mock modules
        module_count = [0]
        def create_mock_module(name, config):
            module_count[0] += 1
            module = Mock()
            
            if module_count[0] == 1:
                # DataIngestion - has file dependency
                module.dependencies = {"input_data": str(input_file)}
            elif module_count[0] == 2:
                # DataTransform - depends on DataIngestion
                module.dependencies = {"DataIngestion": "/path/ingestion"}
            else:
                # DataExport - depends on DataTransform
                module.dependencies = {"DataTransform": "/path/transform"}
            
            module.safe_execute.return_value = ModuleResult(
                status="success",
                data={f"{name}_output": f"data_{module_count[0]}"},
                message=f"{name} completed successfully"
            )
            return module
        
        mock_registry.get_module_instance.side_effect = create_mock_module
        
        result = executor.execute("data_pipeline")
        
        assert result.is_success()
        assert len(result.results) == 3
        assert result.results["DataIngestion"]["status"] == "success"
        assert result.results["DataTransform"]["status"] == "success"
        assert result.results["DataExport"]["status"] == "success"
        
        # Verify all configs were passed correctly
        calls = mock_registry.get_module_instance.call_args_list
        assert calls[0] == call("DataIngestion", "configs/ingestion.yaml")
        assert calls[1] == call("DataTransform", "configs/transform.yaml")
        assert calls[2] == call("DataExport", None)


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

class TestErrorHandling:
    """Test error handling and edge cases"""
    
    def test_module_instantiation_failure(
        self,
        executor,
        mock_registry,
        create_workflow_file
    ):
        """Test handling when module instantiation fails"""
        workflow = {
            "modules": [
                {"module": "FailModule", "required": True, "dependency_policy": None}
            ]
        }
        create_workflow_file("inst_fail", workflow)
        
        mock_registry.get_module_instance.side_effect = ValueError("Module not found")
        
        with pytest.raises(ValueError, match="Module not found"):
            executor.execute("inst_fail")
    
    def test_module_execution_exception(
        self,
        executor,
        mock_registry,
        create_workflow_file
    ):
        """Test handling when module.safe_execute raises exception"""
        workflow = {
            "modules": [
                {"module": "ExceptionModule", "required": False, "dependency_policy": None}
            ]
        }
        create_workflow_file("exec_exception", workflow)
        
        module = Mock()
        module.dependencies = {}
        module.safe_execute.side_effect = RuntimeError("Execution failed")
        mock_registry.get_module_instance.return_value = module
        
        with pytest.raises(RuntimeError, match="Execution failed"):
            executor.execute("exec_exception")
    
    def test_invalid_dependency_policy_config(
        self,
        executor,
        mock_registry,
        create_workflow_file
    ):
        """Test handling invalid dependency policy configuration"""
        workflow = {
            "modules": [
                {
                    "module": "TestModule",
                    "required": False,
                    "dependency_policy": {
                        "name": "flexible",
                        "params": {"invalid_param": "value"}
                    }
                }
            ]
        }
        create_workflow_file("invalid_policy", workflow)
        
        module = Mock()
        module.dependencies = {}
        mock_registry.get_module_instance.return_value = module
        
        with pytest.raises(ValueError, match="Unknown parameters"):
            executor.execute("invalid_policy")


# ============================================================================
# EDGE CASES
# ============================================================================

class TestEdgeCases:
    """Test edge cases and boundary conditions"""
    
    def test_workflow_with_no_modules_field(
        self,
        executor,
        create_workflow_file
    ):
        """Test workflow missing modules field"""
        workflow = {"name": "broken"}
        create_workflow_file("broken", workflow)
        
        with pytest.raises(KeyError):
            executor.execute("broken")
    
    def test_module_with_none_config(
        self,
        executor,
        mock_registry,
        create_workflow_file,
        mock_module_instance
    ):
        """Test module with explicit None config"""
        workflow = {
            "modules": [
                {"module": "Module1", "config_file": None, "required": False, "dependency_policy": None}
            ]
        }
        create_workflow_file("none_config", workflow)
        
        mock_registry.get_module_instance.return_value = mock_module_instance
        mock_module_instance.dependencies = {}
        
        result = executor.execute("none_config")
        
        mock_registry.get_module_instance.assert_called_once_with("Module1", None)
        assert result.is_success()
    
    def test_module_with_empty_dependencies(
        self,
        executor,
        mock_registry,
        create_workflow_file,
        mock_module_instance
    ):
        """Test module with no dependencies"""
        workflow = {
            "modules": [
                {"module": "IndependentModule", "required": False, "dependency_policy": "strict"}
            ]
        }
        create_workflow_file("no_deps", workflow)
        
        mock_module_instance.dependencies = {}
        mock_registry.get_module_instance.return_value = mock_module_instance
        
        result = executor.execute("no_deps")
        
        assert result.is_success()
        assert result.results["IndependentModule"]["status"] == "success"