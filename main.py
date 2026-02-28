# main.py

from workflows.registry.registry import ModuleRegistry
from optiMoldMaster.opti_mold_master import OptiMoldIQ
from api.server import create_app

registry = ModuleRegistry()
orchestrator = OptiMoldIQ(
    module_registry=registry,
    workflows_dir="workflows/definitions"
)

app = create_app(orchestrator)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)