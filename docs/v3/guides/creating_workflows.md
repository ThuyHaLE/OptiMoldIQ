# Workflow Design Guide

### Adding a New Workflow

#### Create Workflow Definition
```json
// workflows/definitions/my_workflow.json
{
  "workflow_name": "my_workflow",
  "description": "My custom workflow",
  "modules": [
    {
      "module": "DataPipelineModule",
      "config_file": "configs/modules/data_pipeline.yaml",
      "dependency_policy": "strict",
      "required": true
    },
    {
      "module": "MyNewModule",
      "config_file": "configs/modules/my_new_module.yaml",
      "dependency_policy": {"name": "hybrid", "params": {"max_age_days": 7}},
      "required": false
    }
  ]
}
```

**Module fields:**

| Field | Required | Description |
|-------|----------|-------------|
| `module` | ✅ | Module name — must match key in `AVAILABLE_MODULES` |
| `config_file` | ✅ | Path to module's YAML config |
| `dependency_policy` | ❌ | String or dict. Default: `strict` if omitted |
| `required` | ❌ | If `true`, workflow stops on failure. Default: `false` |

`dependency_policy` accepts two formats:
```json
"dependency_policy": "strict"

"dependency_policy": {"name": "hybrid", "params": {"max_age_days": 7}}
```

#### Execute Workflow
```python
from optiMoldMaster.opti_mold_master import OptiMoldIQ, ModuleRegistry

registry = ModuleRegistry()
orchestrator = OptiMoldIQ(
    module_registry=registry,
    workflows_dir="workflows/definitions"
)

# List available workflows (auto-discovered from workflows/definitions/)
orchestrator.list_workflows()

# Execute single workflow
result = orchestrator.execute("my_workflow")

# Execute with fresh cache (re-runs all modules)
result = orchestrator.execute("my_workflow", clear_cache=True)

# Execute multiple workflows in sequence
results = orchestrator.execute_chain(
    ["data_pipeline_workflow", "analytics_workflow"],
    stop_on_failure=True
)
```

#### Workflow Discovery

Workflows are **auto-discovered** at startup from `workflows/definitions/*.json`. No registration needed — just drop the JSON file in and restart the orchestrator.

Each workflow is validated on load: missing `modules` field or invalid `dependency_policy` will log an error and skip that workflow.

#### Execution Cache

Each workflow has its own execution cache. If a module already ran in the same session, its result is reused automatically. Use `clear_cache=True` to force re-execution, or `orchestrator.clear_all_caches()` to reset all.