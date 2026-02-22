# Module Registry

The `ModuleRegistry` is the central catalogue that maps module names to their configurations. It combines two sources of truth: the **code registry** (`modules.AVAILABLE_MODULES` — what modules exist) and the **YAML registry** (`configs/module_registry.yaml` — how each module is configured).

---

## Registry Format

The registry is a YAML file at `configs/module_registry.yaml`. Each top-level key is a module class name exactly as it appears in `modules.AVAILABLE_MODULES`.

```yaml
# configs/module_registry.yaml

DataPipelineModule:
  config_path: configs/modules/data_pipeline.yaml
  enabled: true

FeatureEngineeringModule:
  config_path: configs/modules/feature_engineering.yaml
  enabled: true

ReportingModule:
  config_path: configs/modules/reporting.yaml
  enabled: false          # still registered but excluded from enabled_only lists
```

**Fields per entry:**

| Field | Type | Required | Description |
|---|---|---|---|
| `config_path` | `str` | No | Path to the module's own config file, passed to the module constructor. If omitted, the module is instantiated with `None`. |
| `enabled` | `bool` | No | Whether the module is considered active. Defaults to `true` if absent. Only affects `list_modules(enabled_only=True)`. |

Any extra fields are stored and accessible via `get_module_info()` as arbitrary metadata (e.g., `owner`, `version`, `tags`).

---

## How It Works

```
modules.AVAILABLE_MODULES          configs/module_registry.yaml
      (what exists)                      (how it's configured)
            │                                     │
            └──────────── ModuleRegistry ─────────┘
                                 │
                    get_module_instance("MyModule")
                                 │
                    module_class(config_path)   ← resolved config
```

1. `ModuleRegistry` loads the YAML on construction.
2. When you call `get_module_instance()`, it looks up the class in `modules.AVAILABLE_MODULES` and the `config_path` in the YAML registry.
3. If no YAML entry exists for a module, it is still instantiable — it just receives `None` as its config.
4. If the YAML file is missing entirely, the registry starts empty and all modules use their defaults.

---

## API

### `get_module_instance(module_name, override_config_path=None)`

Instantiates a module by name. Resolves config in this order:

1. `override_config_path` (if provided)
2. `config_path` from the YAML registry
3. `None` (module uses its own defaults)

```python
registry = ModuleRegistry()

# Standard — uses config_path from YAML
module = registry.get_module_instance("DataPipelineModule")

# Override — ignores YAML, uses the provided path
module = registry.get_module_instance(
    "DataPipelineModule",
    override_config_path="configs/modules/data_pipeline_dev.yaml"
)
```

Raises `ValueError` if `module_name` is not in `AVAILABLE_MODULES`.

---

### `list_modules(enabled_only=False)`

Returns a list of module names.

```python
# All registered modules (from AVAILABLE_MODULES)
registry.list_modules()
# → ["DataPipelineModule", "FeatureEngineeringModule", "ReportingModule"]

# Only modules where enabled != false in YAML
registry.list_modules(enabled_only=True)
# → ["DataPipelineModule", "FeatureEngineeringModule"]
```

> **Note:** `enabled_only=True` only looks at modules that have an entry in the YAML. Modules with no YAML entry are excluded from the `enabled_only` list even though they are instantiable.

---

### `get_module_info(module_name)`

Returns the raw YAML config dict for a module. Returns `{}` if the module exists in `AVAILABLE_MODULES` but has no YAML entry.

```python
registry.get_module_info("DataPipelineModule")
# → {"config_path": "configs/modules/data_pipeline.yaml", "enabled": true}

registry.get_module_info("UnregisteredModule")
# → {}
```

Raises `ValueError` if `module_name` is not in `AVAILABLE_MODULES`.

---

## Custom Registry Path

By default the registry reads from `configs/module_registry.yaml`. Pass a different path to the constructor:

```python
registry = ModuleRegistry(registry_path="configs/envs/staging_registry.yaml")
```

---

## Adding a New Module

**Step 1 — Register the class** in `modules/AVAILABLE_MODULES` (see the modules package for details).

**Step 2 — Add a YAML entry** (optional, but recommended):

```yaml
# configs/module_registry.yaml

MyNewModule:
  config_path: configs/modules/my_new_module.yaml
  enabled: true
```

**Step 3 — Use it:**

```python
registry = ModuleRegistry()
module = registry.get_module_instance("MyNewModule")
```

If you skip Step 2, the module is still instantiable but receives `None` as its config and will not appear in `list_modules(enabled_only=True)`.