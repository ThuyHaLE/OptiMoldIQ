## Workflow JSON Schema
```json
{
  "workflow_name": "string",       // Required. Used for logging
  "description": "string",         // Optional. Human-readable description
  "modules": [                     // Required. Ordered list of modules to execute
    {
      "module": "string",          // Required. Must match key in AVAILABLE_MODULES
      "config_file": "string",     // Required. Path to module's YAML config
      "dependency_policy": "...",  // Optional. Default: strict
      "required": true             // Optional. Default: false
    }
  ]
}
```

### `dependency_policy`

String shorthand (no params):
```json
"dependency_policy": "strict"
"dependency_policy": "flexible"
"dependency_policy": "hybrid"
```

Dict with params:
```json
"dependency_policy": {
  "name": "flexible",
  "params": {
    "required_deps": ["DataPipelineModule"],
    "max_age_days": 7
  }
}
```

If omitted, defaults to `strict`.

### Available policies

| Policy | Description | Params |
|--------|-------------|--------|
| `strict` | All dependencies must be present in current workflow | — |
| `flexible` | Optional required deps list + age check | `required_deps: list`, `max_age_days: int` |
| `hybrid` | Prefer workflow, fallback to database with age check | `max_age_days: int`, `prefer_workflow: bool` |

### `required`

| Value | Behavior on failure |
|-------|-------------------|
| `true` | Workflow stops immediately, returns `failed` |
| `false` | Module is skipped, workflow continues |

### Full example
```json
{
  "workflow_name": "analyze_production_records",
  "description": "Update and analyze production records pipeline",
  "modules": [
    {
      "module": "DataPipelineModule",
      "config_file": "configs/modules/data_pipeline.yaml",
      "dependency_policy": "strict",
      "required": true
    },
    {
      "module": "ValidationModule",
      "config_file": "configs/modules/validation.yaml",
      "dependency_policy": {
        "name": "hybrid",
        "params": {"max_age_days": 7}
      },
      "required": true
    },
    {
      "module": "AnalyticsModule",
      "config_file": "configs/modules/analytics.yaml",
      "dependency_policy": "flexible",
      "required": false
    }
  ]
}
```