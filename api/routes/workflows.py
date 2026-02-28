from fastapi import APIRouter, Depends, HTTPException
from api.dependencies import get_orchestrator

router = APIRouter(prefix="/api", tags=["workflows"])

@router.get("/workflows")
def list_workflows(orc=Depends(get_orchestrator)):
    result = []
    for name in orc.list_workflows():
        try:
            result.append(orc.get_workflow_info(name))
        except Exception as e:
            # Don't crash entire list if one workflow fails
            result.append({"workflow_name": name, "error": str(e)})
    return result