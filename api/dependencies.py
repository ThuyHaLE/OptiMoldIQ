from typing import Optional
from optiMoldMaster.opti_mold_master import OptiMoldIQ

_orchestrator: Optional[OptiMoldIQ] = None

def init_orchestrator(instance: OptiMoldIQ):
    global _orchestrator
    _orchestrator = instance

def get_orchestrator() -> OptiMoldIQ:
    if _orchestrator is None:
        raise RuntimeError("Orchestrator not initialized")
    return _orchestrator