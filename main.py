# optiMoldMaster/main.py

from optiMoldMaster.optim_mold_master import OptiMoldIQ
from optiMoldMaster.workflows.registry.registry import ModuleRegistry

# Initialize
registry = ModuleRegistry()
registry.auto_discover("optiMoldMaster/modules")

orchestrator = OptiMoldIQ(
    module_registry=registry,
    workflows_dir="optiMoldMaster/workflows/definitions"
)

# List available workflows
print(orchestrator.list_workflows())
# ['update_database', 'full_pipeline', 'validate_only']

# Execute by name
result = orchestrator.execute("update_database")

# Execute with fresh cache
result = orchestrator.execute("update_database", clear_cache=True)