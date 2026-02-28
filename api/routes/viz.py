from fastapi import APIRouter, Depends
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from api.dependencies import get_orchestrator
import math

def sanitize(obj):
    if isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
        return None
    if isinstance(obj, dict):
        return {k: sanitize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [sanitize(v) for v in obj]
    return obj

router = APIRouter(prefix="/api", tags=["viz"])

@router.get("/viz")
def get_all_viz(orc=Depends(get_orchestrator)):
    output = {}
    for name in orc.list_workflows():
        latest = orc.get_latest_run(name)
        if latest:
            output[name] = sanitize(latest.to_dict())
    return JSONResponse(content=output)