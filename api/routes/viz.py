from fastapi import APIRouter, Depends
from api.dependencies import get_orchestrator

router = APIRouter(prefix="/api", tags=["viz"])

@router.get("/viz")
def get_all_viz(orc=Depends(get_orchestrator)):
    output = {}
    for name in orc.list_workflows():
        latest = orc.get_latest_run(name)
        if latest:
            output[name] = latest.to_dict()
        # workflows with no runs are simply omitted
        # frontend vizCache only cares about workflows that have run
    return output