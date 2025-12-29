# modules/dependency_policies/__init__.py

from modules.dependency_policies.strict import StrictContextPolicy
from modules.dependency_policies.flexible import FlexibleDependencyPolicy
from modules.dependency_policies.hybrid import HybridDependencyPolicy
from modules.dependency_policies.workflow_aware import WorkflowAwareDependencyPolicy
from modules.dependency_policies.base import DependencyPolicy

# Registry of availble policies
AVAILABLE_POLICIES = {
    "StrictContextPolicy": StrictContextPolicy,
    "FlexibleDependencyPolicy": FlexibleDependencyPolicy,
    "HybridDependencyPolicy": HybridDependencyPolicy,
    "WorkflowAwareDependencyPolicy": WorkflowAwareDependencyPolicy,
}

__all__ = [
    "StrictContextPolicy",
    "FlexibleDependencyPolicy",
    "HybridDependencyPolicy",
    "WorkflowAwareDependencyPolicy",
]