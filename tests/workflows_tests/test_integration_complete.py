# tests/workflows_tests/test_integration_complete.py

"""
Complete integration tests for the entire workflow system:
- Registry -> Executor -> Orchestrator
- Real file operations
- End-to-end workflow execution
"""

import pytest
import json
import yaml
from pathlib import Path
from unittest.mock import Mock, patch

from workflows.registry.registry import ModuleRegistry
from workflows.executor import WorkflowExecutor
from optiMoldMaster.opti_mold_master import OptiMoldIQ
from modules.base_module import ModuleResult


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def temp_project_structure(tmp_path):
    """Create complete project structure"""
    structure = {
        "workflows_dir": tmp_path / "workflows",
        "configs_dir": tmp_path / "configs",
        "data_dir": tmp_path / "data",
        "registry_file": tmp_path / "configs" / "registry.yaml"
    }
    
    # Create directories
    for key, path in structure.items():
        if key != "registry_file":
            path.mkdir(parents=True, exist_ok=True)
    
    return structure


@pytest.fixture
def mock_modules():
    """Create mock module classes"""
    class MockModule1:
        def __init__(self, config_path=None):
            self.config_path = config_path
            self.dependencies = {}
        
        def safe_execute(self):
            return ModuleResult(
                status="success",
                data={"module1": "result"},
                message="Module1 executed"
            )
    
    class MockModule2:
        def __init__(self, config_path=None):
            self.config_path = config_path
            self.dependencies = {"Module1": "/path/module1"}
        
        def safe_execute(self):
            return ModuleResult(
                status="success",
                data={"module2": "result"},
                message="Module2 executed"
            )
    
    class MockModule3:
        def __init__(self, config_path=None):
            self.config_path = config_path
            self.dependencies = {}
        
        def safe_execute(self):
            return ModuleResult(
                status="failed",
                data=None,
                message="Module3 failed",
                errors=["Intentional failure"]
            )
    
    return {
        "Module1": MockModule1,
        "Module2": MockModule2,
        "Module3": MockModule3
    }


# ============================================================================
# COMPLETE INTEGRATION TESTS
# ============================================================================

class TestCompleteIntegration:
    """Test complete workflow system integration"""
    
    @patch('workflows.registry.registry.AVAILABLE_MODULES')
    @patch('workflows.registry.registry.get_module')
    def test_end_to_end_workflow_execution(
        self,
        mock_get_module,
        mock_available_modules,
        temp_project_structure,
        mock_modules
    ):
        """Test complete end-to-end workflow execution"""
        # Setup
        mock_available_modules.return_value = mock_modules
        mock_get_module.side_effect = lambda name: mock_modules[name]
        
        # Create registry
        registry_data = {
            "Module1": {
                "config_path": str(temp_project_structure["configs_dir"] / "module1.yaml"),
                "enabled": True
            },
            "Module2": {
                "config_path": str(temp_project_structure["configs_dir"] / "module2.yaml"),
                "enabled": True
            }
        }
        with open(temp_project_structure["registry_file"], 'w') as f:
            yaml.dump(registry_data, f)
        
        # Create workflow
        workflow_def = {
            "name": "test_workflow",
            "modules": [
                {
                    "module": "Module1",
                    "required": True,
                    "dependency_policy": None
                },
                {
                    "module": "Module2",
                    "required": False,
                    "dependency_policy": "strict"
                }
            ]
        }
        workflow_file = temp_project_structure["workflows_dir"] / "test_workflow.json"
        with open(workflow_file, 'w') as f:
            json.dump(workflow_def, f)
        
        # Initialize system
        registry = ModuleRegistry(registry_path=str(temp_project_structure["registry_file"]))
        orchestrator = OptiMoldIQ(
            module_registry=registry,
            workflows_dir=str(temp_project_structure["workflows_dir"])
        )
        
        # Execute workflow
        result = orchestrator.execute("test_workflow")
        
        # Verify
        assert result.is_success()
        assert "Module1" in result.results
        assert "Module2" in result.results
        assert result.results["Module1"]["status"] == "success"
        assert result.results["Module2"]["status"] == "success"
    
    @patch('workflows.registry.registry.AVAILABLE_MODULES')
    @patch('workflows.registry.registry.get_module')
    def test_workflow_chain_execution(
        self,
        mock_get_module,
        mock_available_modules,
        temp_project_structure,
        mock_modules
    ):
        """Test executing multiple workflows in chain"""
        mock_available_modules.return_value = mock_modules
        mock_get_module.side_effect = lambda name: mock_modules[name]
        
        # Create registry
        registry_data = {
            "Module1": {"enabled": True},
            "Module2": {"enabled": True}
        }
        with open(temp_project_structure["registry_file"], 'w') as f:
            yaml.dump(registry_data, f)
        
        # Create multiple workflows
        workflow1 = {
            "name": "workflow1",
            "modules": [{"module": "Module1", "required": False, "dependency_policy": None}]
        }
        workflow2 = {
            "name": "workflow2",
            "modules": [{"module": "Module2", "required": False, "dependency_policy": None}]
        }
        
        workflows_dir = temp_project_structure["workflows_dir"]
        with open(workflows_dir / "workflow1.json", 'w') as f:
            json.dump(workflow1, f)
        with open(workflows_dir / "workflow2.json", 'w') as f:
            json.dump(workflow2, f)
        
        # Initialize and execute chain
        registry = ModuleRegistry(registry_path=str(temp_project_structure["registry_file"]))
        orchestrator = OptiMoldIQ(
            module_registry=registry,
            workflows_dir=str(workflows_dir)
        )
        
        results = orchestrator.execute_chain(["workflow1", "workflow2"])
        
        assert len(results) == 2
        assert results["workflow1"].is_success()
        assert results["workflow2"].is_success()
    
    @patch('workflows.registry.registry.AVAILABLE_MODULES')
    @patch('workflows.registry.registry.get_module')
    def test_workflow_with_failed_required_module(
        self,
        mock_get_module,
        mock_available_modules,
        temp_project_structure,
        mock_modules
    ):
        """Test workflow stops when required module fails"""
        mock_available_modules.return_value = mock_modules
        mock_get_module.side_effect = lambda name: mock_modules[name]
        
        # Create registry
        registry_data = {"Module3": {"enabled": True}}
        with open(temp_project_structure["registry_file"], 'w') as f:
            yaml.dump(registry_data, f)
        
        # Create workflow with failing required module
        workflow_def = {
            "name": "fail_workflow",
            "modules": [
                {
                    "module": "Module3",
                    "required": True,
                    "dependency_policy": None
                }
            ]
        }
        workflow_file = temp_project_structure["workflows_dir"] / "fail_workflow.json"
        with open(workflow_file, 'w') as f:
            json.dump(workflow_def, f)
        
        # Initialize and execute
        registry = ModuleRegistry(registry_path=str(temp_project_structure["registry_file"]))
        orchestrator = OptiMoldIQ(
            module_registry=registry,
            workflows_dir=str(temp_project_structure["workflows_dir"])
        )
        
        result = orchestrator.execute("fail_workflow")
        
        assert result.is_failed()
        assert "Module3" in result.results
        assert result.results["Module3"]["status"] == "failed"


class TestDependencyPolicyIntegration:
    """Test dependency policies in complete workflow"""
    
    @patch('workflows.registry.registry.AVAILABLE_MODULES')
    @patch('workflows.registry.registry.get_module')
    def test_strict_policy_blocks_missing_dependencies(
        self,
        mock_get_module,
        mock_available_modules,
        temp_project_structure,
        mock_modules
    ):
        """Test strict policy prevents execution with missing deps"""
        mock_available_modules.return_value = mock_modules
        mock_get_module.side_effect = lambda name: mock_modules[name]
        
        # Create workflow where Module2 depends on Module1 (strict policy)
        workflow_def = {
            "name": "strict_test",
            "modules": [
                {
                    "module": "Module2",
                    "required": False,
                    "dependency_policy": "strict"
                }
            ]
        }
        workflow_file = temp_project_structure["workflows_dir"] / "strict_test.json"
        with open(workflow_file, 'w') as f:
            json.dump(workflow_def, f)
        
        # Initialize
        registry_data = {"Module2": {"enabled": True}}
        with open(temp_project_structure["registry_file"], 'w') as f:
            yaml.dump(registry_data, f)
        
        registry = ModuleRegistry(registry_path=str(temp_project_structure["registry_file"]))
        orchestrator = OptiMoldIQ(
            module_registry=registry,
            workflows_dir=str(temp_project_structure["workflows_dir"])
        )
        
        result = orchestrator.execute("strict_test")
        
        # Module2 should be skipped due to missing dependency
        assert result.is_success()  # Workflow succeeds but module skipped
        assert result.results["Module2"]["status"] == "skipped"
    
    @patch('workflows.registry.registry.AVAILABLE_MODULES')
    @patch('workflows.registry.registry.get_module')
    def test_flexible_policy_allows_execution(
        self,
        mock_get_module,
        mock_available_modules,
        temp_project_structure,
        mock_modules,
        tmp_path
    ):
        """Test flexible policy allows execution with missing optional deps"""
        mock_available_modules.return_value = mock_modules
        
        # Create module with file dependency
        class FlexibleModule:
            def __init__(self, config_path=None):
                self.dependencies = {"data_file": str(tmp_path / "data.txt")}
            
            def safe_execute(self):
                return ModuleResult(
                    status="success",
                    data={"result": "ok"},
                    message="Executed"
                )
        
        modules_with_flexible = {**mock_modules, "FlexibleModule": FlexibleModule}
        mock_get_module.side_effect = lambda name: modules_with_flexible[name]
        
        # Create data file
        (tmp_path / "data.txt").write_text("test data")
        
        # Create workflow with flexible policy
        workflow_def = {
            "name": "flexible_test",
            "modules": [
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
        workflow_file = temp_project_structure["workflows_dir"] / "flexible_test.json"
        with open(workflow_file, 'w') as f:
            json.dump(workflow_def, f)
        
        # Initialize
        registry_data = {"FlexibleModule": {"enabled": True}}
        with open(temp_project_structure["registry_file"], 'w') as f:
            yaml.dump(registry_data, f)
        
        registry = ModuleRegistry(registry_path=str(temp_project_structure["registry_file"]))
        orchestrator = OptiMoldIQ(
            module_registry=registry,
            workflows_dir=str(temp_project_structure["workflows_dir"])
        )
        
        result = orchestrator.execute("flexible_test")
        
        # Should execute successfully
        assert result.is_success()
        assert result.results["FlexibleModule"]["status"] == "success"


class TestCacheIntegration:
    """Test execution caching across workflows"""
    
    @patch('workflows.registry.registry.AVAILABLE_MODULES')
    @patch('workflows.registry.registry.get_module')
    def test_cache_persists_within_workflow(
        self,
        mock_get_module,
        mock_available_modules,
        temp_project_structure,
        mock_modules
    ):
        """Test cache persists for duplicate modules in workflow"""
        mock_available_modules.return_value = mock_modules
        
        execution_count = {"count": 0}
        
        class CountedModule:
            def __init__(self, config_path=None):
                self.dependencies = {}
            
            def safe_execute(self):
                execution_count["count"] += 1
                return ModuleResult(
                    status="success",
                    data={"count": execution_count["count"]},
                    message="OK"
                )
        
        modules_with_counted = {**mock_modules, "CountedModule": CountedModule}
        mock_get_module.side_effect = lambda name: modules_with_counted[name]
        
        # Create workflow with duplicate module
        workflow_def = {
            "name": "cache_test",
            "modules": [
                {"module": "CountedModule", "required": False, "dependency_policy": None},
                {"module": "CountedModule", "required": False, "dependency_policy": None}
            ]
        }
        workflow_file = temp_project_structure["workflows_dir"] / "cache_test.json"
        with open(workflow_file, 'w') as f:
            json.dump(workflow_def, f)
        
        # Initialize
        registry_data = {"CountedModule": {"enabled": True}}
        with open(temp_project_structure["registry_file"], 'w') as f:
            yaml.dump(registry_data, f)
        
        registry = ModuleRegistry(registry_path=str(temp_project_structure["registry_file"]))
        orchestrator = OptiMoldIQ(
            module_registry=registry,
            workflows_dir=str(temp_project_structure["workflows_dir"])
        )
        
        result = orchestrator.execute("cache_test")
        
        # Module should only execute once due to caching
        assert execution_count["count"] == 1
        assert result.is_success()
    
    @patch('workflows.registry.registry.AVAILABLE_MODULES')
    @patch('workflows.registry.registry.get_module')
    def test_cache_cleared_between_executions(
        self,
        mock_get_module,
        mock_available_modules,
        temp_project_structure,
        mock_modules
    ):
        """Test cache can be cleared between executions"""
        mock_available_modules.return_value = mock_modules
        
        execution_count = {"count": 0}
        
        class CountedModule:
            def __init__(self, config_path=None):
                self.dependencies = {}
            
            def safe_execute(self):
                execution_count["count"] += 1
                return ModuleResult(
                    status="success",
                    data={"count": execution_count["count"]},
                    message="OK"
                )
        
        modules_with_counted = {**mock_modules, "CountedModule": CountedModule}
        mock_get_module.side_effect = lambda name: modules_with_counted[name]
        
        # Create workflow
        workflow_def = {
            "name": "clear_cache_test",
            "modules": [
                {"module": "CountedModule", "required": False, "dependency_policy": None}
            ]
        }
        workflow_file = temp_project_structure["workflows_dir"] / "clear_cache_test.json"
        with open(workflow_file, 'w') as f:
            json.dump(workflow_def, f)
        
        # Initialize
        registry_data = {"CountedModule": {"enabled": True}}
        with open(temp_project_structure["registry_file"], 'w') as f:
            yaml.dump(registry_data, f)
        
        registry = ModuleRegistry(registry_path=str(temp_project_structure["registry_file"]))
        orchestrator = OptiMoldIQ(
            module_registry=registry,
            workflows_dir=str(temp_project_structure["workflows_dir"])
        )
        
        # Execute twice with clear_cache
        orchestrator.execute("clear_cache_test", clear_cache=False)
        orchestrator.execute("clear_cache_test", clear_cache=True)
        
        # Should execute twice (once per execution call)
        assert execution_count["count"] == 2


class TestErrorPropagation:
    """Test error handling across system layers"""
    
    @patch('workflows.registry.registry.AVAILABLE_MODULES')
    @patch('workflows.registry.registry.get_module')
    def test_module_error_propagates_correctly(
        self,
        mock_get_module,
        mock_available_modules,
        temp_project_structure,
        mock_modules
    ):
        """Test that module errors propagate through system"""
        mock_available_modules.return_value = mock_modules
        mock_get_module.side_effect = lambda name: mock_modules[name]
        
        # Create workflow with failing module
        workflow_def = {
            "name": "error_test",
            "modules": [
                {"module": "Module3", "required": True, "dependency_policy": None}
            ]
        }
        workflow_file = temp_project_structure["workflows_dir"] / "error_test.json"
        with open(workflow_file, 'w') as f:
            json.dump(workflow_def, f)
        
        # Initialize
        registry_data = {"Module3": {"enabled": True}}
        with open(temp_project_structure["registry_file"], 'w') as f:
            yaml.dump(registry_data, f)
        
        registry = ModuleRegistry(registry_path=str(temp_project_structure["registry_file"]))
        orchestrator = OptiMoldIQ(
            module_registry=registry,
            workflows_dir=str(temp_project_structure["workflows_dir"])
        )
        
        result = orchestrator.execute("error_test")
        
        # Error should propagate
        assert result.is_failed()
        assert result.results["Module3"]["errors"] == ["Intentional failure"]