# Step-by-step module creation

### Adding a New Module

#### Step 1: Create Module Class
```python
# modules/my_new_module.py
from modules.base_module import BaseModule, ModuleResult
from typing import Dict, Optional

class MyNewModule(BaseModule):
    
    DEFAULT_CONFIG_PATH: str = "configs/modules/my_new_module.yaml"
    
    def __init__(self, config_path: Optional[str] = None):
        super().__init__(config_path)
    
    @property
    def module_name(self) -> str:
        return "MyNewModule"
    
    @property
    def dependencies(self) -> Dict[str, str]:
        return {
            'DataPipelineModule': './path/to/expected/output.json'
        }
    
    def execute(self) -> ModuleResult:
        # 1. Read data from shared database
        # 2. Process data
        # 3. Write results back to shared database
        # 4. Return ModuleResult with status/metadata only (not the actual data)
        return ModuleResult(
            status='success',
            data={'summary': 'metadata only'},
            message="Completed"
        )
```

#### Step 2: Register in `modules/__init__.py`
```python
# modules/__init__.py
from modules.my_new_module import MyNewModule

AVAILABLE_MODULES = {
    ...,
    'MyNewModule': MyNewModule,  # ADD THIS
}

# Also add to __all__
__all__ = [
    ...,
    'MyNewModule',
]
```

#### Step 3: Add to Module Registry
```yaml
# configs/module_registry.yaml
MyNewModule:
  config_path: configs/modules/my_new_module.yaml
  enabled: true
  description: Description of what your module does
```

#### Step 4: Create Config File
```yaml
# configs/modules/my_new_module.yaml
module_settings:
  timeout: 300
  retries: 3

custom_params:
  param1: value1
```

#### Step 5: Use in Workflow
```json
{
  "workflow_name": "my_workflow",
  "modules": [
    {
      "module": "DataPipelineModule",
      "config_file": "configs/modules/data_pipeline.yaml",
      "required": true
    },
    {
      "module": "MyNewModule",
      "config_file": "configs/modules/my_new_module.yaml",
      "dependency_policy": {"name": "hybrid"},
      "required": true
    }
  ]
}
```

#### Step 6: Test
```bash
pytest tests/modules_tests/test_modules_auto.py -k "MyNewModule" -v
```

---

### Notes

**`execute()`** does not receive `context` nor return `context_updates` — data is shared between modules via the shared database, not through return values.

**`ModuleResult.data`** only contains metadata/summary information. The actual data is written to the shared database inside `execute()`.

**`safe_execute()`** is a wrapper that automatically handles exceptions — the workflow executor calls this method instead of calling `execute()` directly.

**Config loading** follows this priority order:
1. `config_path` passed to the constructor
2. `DEFAULT_CONFIG_PATH` defined on the class
3. Returns `{}` if no configuration is found

To get a module instance by name: `get_module("MyNewModule")()`  
To list all available modules: `list_available_modules()`