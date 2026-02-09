# optiMoldMaster/workflows/dependency_policies/__init__.py

from optiMoldMaster.workflows.dependency_policies.base import DependencyPolicy
from optiMoldMaster.workflows.dependency_policies.strict import StrictWorkflowPolicy
from optiMoldMaster.workflows.dependency_policies.flexible import FlexibleDependencyPolicy
from optiMoldMaster.workflows.dependency_policies.hybrid import HybridDependencyPolicy

# ------------------------------------------------------------------
# Policy registry (canonical names)
# ------------------------------------------------------------------
AVAILABLE_POLICIES = {
    "strict": StrictWorkflowPolicy,
    "flexible": FlexibleDependencyPolicy,
    "hybrid": HybridDependencyPolicy,

    # backward compatible aliases
    "StrictWorkflowPolicy": StrictWorkflowPolicy,
    "FlexibleDependencyPolicy": FlexibleDependencyPolicy,
    "HybridDependencyPolicy": HybridDependencyPolicy,
}

__all__ = [
    "DependencyPolicy",
    "StrictWorkflowPolicy",
    "FlexibleDependencyPolicy",
    "HybridDependencyPolicy",
    "AVAILABLE_POLICIES",
]