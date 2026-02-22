# BaseModule Detailed API

## Overview

`BaseModule` is the abstract base class for all modules in the system. Each module wraps a sub-agent and exposes a standardized interface so the workflow executor can orchestrate it.

```
BaseModule (ABC)
├── load_config()        # classmethod
├── module_name          # abstract property
├── dependencies         # property
├── execute()            # abstract method
└── safe_execute()       # wrapper with error handling
```

---

## Class Attributes

### `DEFAULT_CONFIG_PATH`

```python
DEFAULT_CONFIG_PATH: str = None
```

Class-level path to the default YAML config file. Used as a fallback when `config_path` is not provided to `__init__` or when the file does not exist.

|          |                                                     |
| -------- | --------------------------------------------------- |
| Type     | `str \| None`                                       |
| Required | Not required, but **recommended** for each subclass |
| Default  | `None` — will return empty config `{}` if not set   |

**Example:**

```python
class MyNewModule(BaseModule):
    DEFAULT_CONFIG_PATH = "configs/modules/my_new_module.yaml"
```

---

## Constructor

### `__init__(config_path=None)`

```python
def __init__(self, config_path: Optional[str] = None)
```

Initializes the module, loads configuration, and binds the logger.

| Parameter     | Type          | Default | Description                                                |
| ------------- | ------------- | ------- | ---------------------------------------------------------- |
| `config_path` | `str \| None` | `None`  | Path to config file. If `None`, uses `DEFAULT_CONFIG_PATH` |

**Config loading priority:**

1. `config_path` if provided and the file exists
2. `DEFAULT_CONFIG_PATH` if `config_path` does not exist
3. `{}` if neither exists or is set

**Attributes set:**

| Attribute     | Type     | Description                                   |
| ------------- | -------- | --------------------------------------------- |
| `self.config` | `Dict`   | Config dictionary loaded from YAML            |
| `self.logger` | `Logger` | Loguru logger bound with `module=module_name` |

---

## Class Methods

### `load_config(config_path=None)`

```python
@classmethod
def load_config(cls, config_path: Optional[str] = None) -> Dict
```

Loads module configuration from a YAML file. Automatically called by `__init__`.

| Parameter     | Type          | Description              |
| ------------- | ------------- | ------------------------ |
| `config_path` | `str \| None` | Path to YAML config file |

**Returns:** `Dict` — configuration dictionary, or `{}` if loading fails.

**Behavior:**

```
config_path provided?
├── Yes → file exists? → load it
│              └── No  → fallback to DEFAULT_CONFIG_PATH
└── No  → DEFAULT_CONFIG_PATH set?
               ├── Yes → load DEFAULT_CONFIG_PATH
               └── No  → warning + return {}
```

**Exceptions:** Does not raise exceptions — logs the error and returns `{}` if loading fails.

---

## Abstract Properties

### `module_name`

```python
@property
@abstractmethod
def module_name(self) -> str
```

Unique identifier of the module. Used to:

* Bind to the logger (`self.logger`)
* Identify the module in the workflow executor
* Map within the `AVAILABLE_MODULES` registry

**Must be implemented in each subclass.**

```python
@property
def module_name(self) -> str:
    return "MyNewModule"
```

---

## Properties

### `dependencies`

```python
@property
def dependencies(self) -> Dict[str, str]
```

Declares the dependencies required before this module can execute.

**Returns:** `Dict[str, str]` mapping `dep_name -> resource_path`.

| Key                                                   | Value                                   |
| ----------------------------------------------------- | --------------------------------------- |
| Dependency name (usually the module that produces it) | Path to resource in filesystem/database |

**Default:** `{}` — no dependencies.

```python
@property
def dependencies(self) -> Dict[str, str]:
    return {
        'DataPipelineModule': './DataPipelineOrchestrator/DataLoaderAgent/newest/path_annotations.json',
        'ValidationModule': './ValidationOrchestrator/change_log.txt'
    }
```

> **Note:** `dependencies` are read by the workflow executor and validated via `DependencyPolicy` before `execute()` is called. See: `dependency_policies.md`.

---

## Abstract Methods

### `execute()`

```python
@abstractmethod
def execute(self) -> ModuleResult
```

Contains the full processing logic of the module. **Must be implemented in each subclass.**

**Returns:** `ModuleResult`

**Expected implementation pattern:**

```python
def execute(self) -> ModuleResult:
    # 1. Read input from shared database/filesystem
    input_data = self._read_from_db()

    # 2. Process
    result = self._process(input_data)

    # 3. Write output to shared database/filesystem
    self._write_to_db(result)

    # 4. Return metadata/summary — NOT full data
    return ModuleResult(
        status='success',
        data={'rows_processed': len(result)},
        message="Completed successfully"
    )
```

> **Important:** `ModuleResult.data` should only contain metadata or summary information. Full data must be stored in the shared database, not returned.

---

## Methods

### `safe_execute()`

```python
def safe_execute(self) -> ModuleResult
```

Wrapper around `execute()` with automatic error handling.
**The workflow executor should call this method instead of `execute()` directly.**

**Returns:** `ModuleResult`

**Behavior:**

* Calls `execute()` inside a try/except block
* Logs results (success/warning/error)
* If `execute()` raises an exception → catches it and returns `ModuleResult(status='failed', ...)`

```
safe_execute()
├── try → execute()
│     ├── success  → log info  → return ModuleResult(status='success')
│     └── other    → log warn  → return ModuleResult(status=result.status)
└── except Exception
          └── log error → return ModuleResult(status='failed', errors=[str(e)])
```

---

## ModuleResult

```python
@dataclass
class ModuleResult:
    status:  str                    # 'success' | 'failed' | 'skipped'
    data:    Any                    # metadata/summary only
    message: str                    # human-readable message
    errors:  Optional[List[str]]    # list of error strings, default None
```

### Fields

| Field     | Type                | Required | Description                                         |
| --------- | ------------------- | -------- | --------------------------------------------------- |
| `status`  | `str`               | ✅        | `'success'`, `'failed'`, or `'skipped'`             |
| `data`    | `Any`               | ✅        | Metadata/summary. Should not contain full data      |
| `message` | `str`               | ✅        | Human-readable result description                   |
| `errors`  | `List[str] \| None` | ❌        | List of error messages, used when `status='failed'` |

### Helper Methods

| Method         | Returns | Description           |
| -------------- | ------- | --------------------- |
| `is_success()` | `bool`  | `status == 'success'` |
| `is_failed()`  | `bool`  | `status == 'failed'`  |
| `is_skipped()` | `bool`  | `status == 'skipped'` |

---

## Module Registry

Modules are registered in two places:

**`modules/__init__.py`** — Python registry:

```python
AVAILABLE_MODULES: Dict[str, Type[BaseModule]] = {
    'MyNewModule': MyNewModule,
    ...
}
```

**`configs/module_registry.yaml`** — Config registry:

```yaml
MyNewModule:
  config_path: configs/modules/my_new_module.yaml
  enabled: true
  description: "..."
```

---

### `get_module(name)`

```python
def get_module(name: str) -> Type[BaseModule]
```

Factory function that retrieves a module class by name.
Returns the **class**, not an instance.

```python
module_cls = get_module('MyNewModule')
module = module_cls(config_path='configs/modules/my_new_module.yaml')
result = module.safe_execute()
```

Raises `ValueError` if `name` does not exist in `AVAILABLE_MODULES`.

---

### `list_available_modules()`

```python
def list_available_modules() -> list[str]
```

Returns a list of all registered module names.

---

## Full Subclass Example

```python
# modules/my_new_module.py
from modules.base_module import BaseModule, ModuleResult
from typing import Dict, Optional

class MyNewModule(BaseModule):
    
    DEFAULT_CONFIG_PATH = "configs/modules/my_new_module.yaml"

    def __init__(self, config_path: Optional[str] = None):
        super().__init__(config_path)
        # Access config via self.config
        self.timeout = self.config.get('timeout', 300)

    @property
    def module_name(self) -> str:
        return "MyNewModule"

    @property
    def dependencies(self) -> Dict[str, str]:
        return {
            'DataPipelineModule': './DataPipelineOrchestrator/output.json'
        }

    def execute(self) -> ModuleResult:
        try:
            # Read → Process → Write
            data = self._read_input()
            result = self._process(data)
            self._write_output(result)

            return ModuleResult(
                status='success',
                data={'processed': len(result)},
                message=f"Processed {len(result)} records"
            )
        except FileNotFoundError as e:
            return ModuleResult(
                status='failed',
                data=None,
                message="Input not found",
                errors=[str(e)]
            )
```

---

## Adding a New Module

See [Adding a New Module](docs/v3/guides/adding_modules.md) for the step-by-step guide.