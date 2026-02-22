# Config File Reference

## Directory Structure
```
OptiMoldIQ/
└── configs/
    ├── shared/
    |   └── shared_source_config.py    # SharedSourceConfig dataclass - defines all shared paths
    ├── module_registry.yaml           # Maps module names to their config files
    └── modules/
        ├── analytics.yaml
        ├── dashboard.yaml
        ├── data_pipeline.yaml
        ├── features_extracting.yaml
        ├── initial_planning.yaml
        ├── progress_tracking.yaml
        └── validation.yaml
```

---

## `module_registry.yaml`

Maps each module to its config file. Used by the workflow executor to load module configs.
```yaml
ModuleName:
  config_path: configs/modules/module.yaml
  enabled: true         # Whether module is active
  description: "..."    # Human-readable description
```

---

## `configs/shared/shared_source_config.py`

Defines `SharedSourceConfig` — a dataclass centralizing all shared paths across modules (database dirs, change logs, agent output dirs, etc.).

All path fields follow a hierarchy: most paths are derived from `db_dir` and `default_dir`, so typically only these two base fields need to be set. Individual paths can be overridden if needed.

**Base fields:**
| Field | Default | Description |
|-------|---------|-------------|
| `db_dir` | `database` | Root directory for database files |
| `default_dir` | `agents/shared_db` | Root directory for agent shared outputs |

**Validation behavior:**
- `strict_validation: bool = False` — if `True`, raises error when paths don't exist
- `auto_create_dirs: bool = False` — if `True`, auto-creates missing `_dir` paths

---

## Module Config Files

Each module config is a YAML file loaded by `BaseModule.load_config()`. All path values are resolved relative to `project_root`.

### Common structure
```yaml
project_root: "."     # All relative paths are resolved against this

<module_key>:
  shared_source_config:
    db_dir: "..."         # Required: root for database files
    default_dir: "..."    # Required: root for agent shared outputs
    
    # All other SharedSourceConfig fields are optional.
    # If omitted, paths are auto-derived from db_dir and default_dir.
    # Override only when you need non-default locations.
    # Full list of available fields: configs/shared/shared_source_config.py
  
  # Module-specific settings...
```

### `validation.yaml`
```yaml
project_root: "."

validation:
  shared_source_config:
    db_dir: "database"        # Required
    default_dir: "agents/shared_db"  # Required

    # Optional overrides (defaults shown as comments)
    # validation_df_name: ["productRecords", "purchaseOrders"]
    # databaseSchemas_path: "{db_dir}/databaseSchemas.json"
    # annotation_path: "{default_dir}/DataPipelineOrchestrator/DataCollector/newest/path_annotations.json"
    # validation_dir: "{default_dir}/ValidationOrchestrator"
    # validation_change_log_path: "{default_dir}/ValidationOrchestrator/change_log.txt"

  enable_parallel: true
  max_workers: null       # null = auto
```

**Module-specific required fields** (beyond `db_dir` / `default_dir`):

| Field | Type | Description |
|-------|------|-------------|
| `validation_df_name` | `List[str]` | DataFrames to validate. Supported: `productRecords`, `purchaseOrders` |
| `enable_parallel` | `bool` | Enable parallel validation |
| `max_workers` | `Optional[int]` | Worker count for parallel mode (`null` = auto) |

> Each module only requires the `shared_source_config` fields it actually uses. Check each module's `dependencies` property and `_build_shared_config()` to see which fields are accessed.