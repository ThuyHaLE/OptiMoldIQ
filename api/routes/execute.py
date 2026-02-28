from fastapi import APIRouter, Depends, HTTPException
from api.dependencies import get_orchestrator
import threading
import uuid

router = APIRouter(prefix="/api", tags=["execute"])

# In-memory job store — fine for single-process local tool
_jobs: dict = {}
_jobs_lock = threading.Lock()


def _run_job(job_id: str, workflow_name: str, orc):
    with _jobs_lock:
        _jobs[job_id]["status"] = "running"
    try:
        record = orc.execute(workflow_name)
        with _jobs_lock:
            _jobs[job_id].update({
                "status": record.status,
                "modules": record.summary.get("modules", {}),
                "execution_id": record.execution_id,
            })
    except Exception as e:
        with _jobs_lock:
            _jobs[job_id].update({
                "status": "failed",
                "error": str(e),
            })


@router.post("/execute/{workflow_name}")
def execute_workflow(workflow_name: str, orc=Depends(get_orchestrator)):
    # Validate workflow exists before spawning thread
    if workflow_name not in orc.list_workflows():
        raise HTTPException(status_code=404, detail=f"Workflow '{workflow_name}' not found")

    job_id = uuid.uuid4().hex[:8]
    with _jobs_lock:
        _jobs[job_id] = {"status": "pending", "modules": {}}

    thread = threading.Thread(
        target=_run_job,
        args=(job_id, workflow_name, orc),
        daemon=True  # won't block process shutdown
    )
    thread.start()
    return {"job_id": job_id}


@router.get("/execute/{job_id}/status")
def job_status(job_id: str):
    with _jobs_lock:
        job = _jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job