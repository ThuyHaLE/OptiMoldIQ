### Adding a New Dependency Policy

#### Step 1: Create Policy Class
```python
# workflows/dependency_policies/my_policy.py
from workflows.dependency_policies.base import DependencyPolicy, DependencyValidationResult
from typing import Dict, List

class MyPolicy(DependencyPolicy):
    def __init__(self, my_param: str = None):
        super().__init__()
        self.my_param = my_param

    def validate(
        self,
        dependencies: Dict[str, str],
        workflow_modules: List[str] = None
    ) -> DependencyValidationResult:
        result = DependencyValidationResult(workflow_modules=workflow_modules or [])
        # Your validation logic here
        return result
```

#### Step 2: Register in `__init__.py`
```python
# workflows/dependency_policies/__init__.py
from workflows.dependency_policies.my_policy import MyPolicy

AVAILABLE_POLICIES = {
    ...,
    "my_policy": MyPolicy,
}

POLICY_SCHEMAS = {
    ...,
    "my_policy": PolicySchema(
        policy_class=MyPolicy,
        required_params=[],
        optional_params={
            'my_param': {
                'type': str,
                'default': None,
                'description': 'Description of my_param'
            }
        },
        description="Description of what my policy does"
    ),
}
```

#### Step 3: Use in Workflow Config

**String format** (uses all defaults):
```json
{
  "dependency_policy": "my_policy"
}
```

**Dict format** (with params):
```json
{
  "dependency_policy": {
    "name": "my_policy",
    "params": {
      "my_param": "some_value"
    }
  }
}
```

#### Notes
- `errors` in `DependencyValidationResult` is blocking — workflow will not run if there are errors.
- `warnings` is non-blocking.
- Using helper `_check_in_workflow()` and `_check_in_database()` from base class if nessesary.
- To see schema of a policy: `DependencyPolicyFactory.get_schema("my_policy")`
- To list all available policies: `DependencyPolicyFactory.list_policies()`