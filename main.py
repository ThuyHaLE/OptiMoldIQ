# main.py

from optiMoldMaster.opti_mold_master import (
    OptiMoldIQ, ModuleRegistry)

# Initialize
registry = ModuleRegistry()

orchestrator = OptiMoldIQ(
    module_registry=registry,
    workflows_dir="workflows/definitions"
)

# List available workflows
print(orchestrator.list_workflows())
# ['update_database', 'full_pipeline', 'validate_only']

# Execute by name
result = orchestrator.execute("update_database_strict")

# Execute with fresh cache
result = orchestrator.execute("update_database_strict", clear_cache=True)