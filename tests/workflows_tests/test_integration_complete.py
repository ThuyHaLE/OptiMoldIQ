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
        "Module3": MockModule3,
    }


# ============================================================================
# COMPLETE INTEGRATION TESTS
# ============================================================================

class TestCompleteIntegration:

    @patch('modules.get_module')
    @patch('modules.AVAILABLE_MODULES', new_callable=dict)
    def test_end_to_end_workflow_execution(
        self,
        mock_available_modules,
        mock_get_module,
        temp_project_structure,
        mock_modules,
    ):
        mock_available_modules.update(mock_modules)
        mock_get_module.side_effect = lambda name: mock_modules[name]

        registry_data = {
            "Module1": {
                "config_path": str(temp_project_structure["configs_dir"] / "module1.yaml"),
                "enabled": True,
            },
            "Module2": {
                "config_path": str(temp_project_structure["configs_dir"] / "module2.yaml"),
                "enabled": True,
            },
        }
        with open(temp_project_structure["registry_file"], "w") as f:
            yaml.dump(registry_data, f)

        workflow_def = {
            "name": "test_workflow",
            "modules": [
                {"module": "Module1", "required": True, "dependency_policy": None},
                {"module": "Module2", "required": False, "dependency_policy": "strict"},
            ],
        }
        with open(temp_project_structure["workflows_dir"] / "test_workflow.json", "w") as f:
            json.dump(workflow_def, f)

        registry = ModuleRegistry(registry_path=str(temp_project_structure["registry_file"]))
        orchestrator = OptiMoldIQ(
            module_registry=registry,
            workflows_dir=str(temp_project_structure["workflows_dir"]),
        )

        result = orchestrator.execute("test_workflow")

        assert result.is_success()
        assert result.results["Module1"]["status"] == "success"
        assert result.results["Module2"]["status"] == "success"

    @patch('modules.get_module')
    @patch('modules.AVAILABLE_MODULES', new_callable=dict)
    def test_workflow_chain_execution(
        self,
        mock_available_modules,
        mock_get_module,
        temp_project_structure,
        mock_modules,
    ):
        mock_available_modules.update(mock_modules)
        mock_get_module.side_effect = lambda name: mock_modules[name]

        registry_data = {"Module1": {"enabled": True}, "Module2": {"enabled": True}}
        with open(temp_project_structure["registry_file"], "w") as f:
            yaml.dump(registry_data, f)

        workflows_dir = temp_project_structure["workflows_dir"]
        for name, mod in [("workflow1", "Module1"), ("workflow2", "Module2")]:
            with open(workflows_dir / f"{name}.json", "w") as f:
                json.dump(
                    {"name": name, "modules": [{"module": mod, "required": False, "dependency_policy": None}]},
                    f,
                )

        registry = ModuleRegistry(registry_path=str(temp_project_structure["registry_file"]))
        orchestrator = OptiMoldIQ(
            module_registry=registry,
            workflows_dir=str(workflows_dir),
        )

        results = orchestrator.execute_chain(["workflow1", "workflow2"])

        assert len(results) == 2
        assert results["workflow1"].is_success()
        assert results["workflow2"].is_success()

    @patch('modules.get_module')
    @patch('modules.AVAILABLE_MODULES', new_callable=dict)
    def test_workflow_with_failed_required_module(
        self,
        mock_available_modules,
        mock_get_module,
        temp_project_structure,
        mock_modules,
    ):
        mock_available_modules.update(mock_modules)
        mock_get_module.side_effect = lambda name: mock_modules[name]

        registry_data = {"Module3": {"enabled": True}}
        with open(temp_project_structure["registry_file"], "w") as f:
            yaml.dump(registry_data, f)

        workflow_def = {
            "name": "fail_workflow",
            "modules": [{"module": "Module3", "required": True, "dependency_policy": None}],
        }
        with open(temp_project_structure["workflows_dir"] / "fail_workflow.json", "w") as f:
            json.dump(workflow_def, f)

        registry = ModuleRegistry(registry_path=str(temp_project_structure["registry_file"]))
        orchestrator = OptiMoldIQ(
            module_registry=registry,
            workflows_dir=str(temp_project_structure["workflows_dir"]),
        )

        result = orchestrator.execute("fail_workflow")

        assert result.is_failed()
        assert result.results["Module3"]["status"] == "failed"


class TestDependencyPolicyIntegration:

    @patch('modules.get_module')
    @patch('modules.AVAILABLE_MODULES', new_callable=dict)
    def test_strict_policy_blocks_missing_dependencies(
        self,
        mock_available_modules,
        mock_get_module,
        temp_project_structure,
        mock_modules,
    ):
        mock_available_modules.update(mock_modules)
        mock_get_module.side_effect = lambda name: mock_modules[name]

        registry_data = {"Module2": {"enabled": True}}
        with open(temp_project_structure["registry_file"], "w") as f:
            yaml.dump(registry_data, f)

        workflow_def = {
            "name": "strict_test",
            "modules": [{"module": "Module2", "required": False, "dependency_policy": "strict"}],
        }
        with open(temp_project_structure["workflows_dir"] / "strict_test.json", "w") as f:
            json.dump(workflow_def, f)

        registry = ModuleRegistry(registry_path=str(temp_project_structure["registry_file"]))
        orchestrator = OptiMoldIQ(
            module_registry=registry,
            workflows_dir=str(temp_project_structure["workflows_dir"]),
        )

        result = orchestrator.execute("strict_test")

        assert result.is_success()
        assert result.results["Module2"]["status"] == "skipped"

    @patch('modules.get_module')
    @patch('modules.AVAILABLE_MODULES', new_callable=dict)
    def test_flexible_policy_allows_execution(
        self,
        mock_available_modules,
        mock_get_module,
        temp_project_structure,
        mock_modules,
        tmp_path,
    ):
        class FlexibleModule:
            def __init__(self, config_path=None):
                self.dependencies = {"data_file": str(tmp_path / "data.txt")}

            def safe_execute(self):
                return ModuleResult(status="success", data={"result": "ok"}, message="Executed")

        all_modules = {**mock_modules, "FlexibleModule": FlexibleModule}
        mock_available_modules.update(all_modules)
        mock_get_module.side_effect = lambda name: all_modules[name]

        (tmp_path / "data.txt").write_text("test data")

        registry_data = {"FlexibleModule": {"enabled": True}}
        with open(temp_project_structure["registry_file"], "w") as f:
            yaml.dump(registry_data, f)

        workflow_def = {
            "name": "flexible_test",
            "modules": [
                {
                    "module": "FlexibleModule",
                    "required": False,
                    "dependency_policy": {"name": "flexible", "params": {"max_age_days": 30}},
                }
            ],
        }
        with open(temp_project_structure["workflows_dir"] / "flexible_test.json", "w") as f:
            json.dump(workflow_def, f)

        registry = ModuleRegistry(registry_path=str(temp_project_structure["registry_file"]))
        orchestrator = OptiMoldIQ(
            module_registry=registry,
            workflows_dir=str(temp_project_structure["workflows_dir"]),
        )

        result = orchestrator.execute("flexible_test")

        assert result.is_success()
        assert result.results["FlexibleModule"]["status"] == "success"


class TestCacheIntegration:

    @patch('modules.get_module')
    @patch('modules.AVAILABLE_MODULES', new_callable=dict)
    def test_cache_persists_within_workflow(
        self,
        mock_available_modules,
        mock_get_module,
        temp_project_structure,
        mock_modules,
    ):
        execution_count = {"count": 0}

        class CountedModule:
            def __init__(self, config_path=None):
                self.dependencies = {}

            def safe_execute(self):
                execution_count["count"] += 1
                return ModuleResult(status="success", data={"count": execution_count["count"]}, message="OK")

        all_modules = {**mock_modules, "CountedModule": CountedModule}
        mock_available_modules.update(all_modules)
        mock_get_module.side_effect = lambda name: all_modules[name]

        registry_data = {"CountedModule": {"enabled": True}}
        with open(temp_project_structure["registry_file"], "w") as f:
            yaml.dump(registry_data, f)

        workflow_def = {
            "name": "cache_test",
            "modules": [
                {"module": "CountedModule", "required": False, "dependency_policy": None},
                {"module": "CountedModule", "required": False, "dependency_policy": None},
            ],
        }
        with open(temp_project_structure["workflows_dir"] / "cache_test.json", "w") as f:
            json.dump(workflow_def, f)

        registry = ModuleRegistry(registry_path=str(temp_project_structure["registry_file"]))
        orchestrator = OptiMoldIQ(
            module_registry=registry,
            workflows_dir=str(temp_project_structure["workflows_dir"]),
        )

        result = orchestrator.execute("cache_test")

        assert execution_count["count"] == 1
        assert result.is_success()

    @patch('modules.get_module')
    @patch('modules.AVAILABLE_MODULES', new_callable=dict)
    def test_cache_cleared_between_executions(
        self,
        mock_available_modules,
        mock_get_module,
        temp_project_structure,
        mock_modules,
    ):
        execution_count = {"count": 0}

        class CountedModule:
            def __init__(self, config_path=None):
                self.dependencies = {}

            def safe_execute(self):
                execution_count["count"] += 1
                return ModuleResult(status="success", data={"count": execution_count["count"]}, message="OK")

        all_modules = {**mock_modules, "CountedModule": CountedModule}
        mock_available_modules.update(all_modules)
        mock_get_module.side_effect = lambda name: all_modules[name]

        registry_data = {"CountedModule": {"enabled": True}}
        with open(temp_project_structure["registry_file"], "w") as f:
            yaml.dump(registry_data, f)

        workflow_def = {
            "name": "clear_cache_test",
            "modules": [{"module": "CountedModule", "required": False, "dependency_policy": None}],
        }
        with open(temp_project_structure["workflows_dir"] / "clear_cache_test.json", "w") as f:
            json.dump(workflow_def, f)

        registry = ModuleRegistry(registry_path=str(temp_project_structure["registry_file"]))
        orchestrator = OptiMoldIQ(
            module_registry=registry,
            workflows_dir=str(temp_project_structure["workflows_dir"]),
        )

        orchestrator.execute("clear_cache_test", clear_cache=False)
        orchestrator.execute("clear_cache_test", clear_cache=True)

        assert execution_count["count"] == 2


class TestErrorPropagation:

    @patch('modules.get_module')
    @patch('modules.AVAILABLE_MODULES', new_callable=dict)
    def test_module_error_propagates_correctly(
        self,
        mock_available_modules,
        mock_get_module,
        temp_project_structure,
        mock_modules,
    ):
        mock_available_modules.update(all_modules := mock_modules)
        mock_get_module.side_effect = lambda name: all_modules[name]

        registry_data = {"Module3": {"enabled": True}}
        with open(temp_project_structure["registry_file"], "w") as f:
            yaml.dump(registry_data, f)

        workflow_def = {
            "name": "error_test",
            "modules": [{"module": "Module3", "required": True, "dependency_policy": None}],
        }
        with open(temp_project_structure["workflows_dir"] / "error_test.json", "w") as f:
            json.dump(workflow_def, f)

        registry = ModuleRegistry(registry_path=str(temp_project_structure["registry_file"]))
        orchestrator = OptiMoldIQ(
            module_registry=registry,
            workflows_dir=str(temp_project_structure["workflows_dir"]),
        )

        result = orchestrator.execute("error_test")

        assert result.is_failed()
        assert result.results["Module3"]["errors"] == ["Intentional failure"]