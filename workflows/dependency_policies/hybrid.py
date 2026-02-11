# workflows/dependency_policies/hybrid.py

from workflows.dependency_policies.base import (
    DependencyPolicy, DependencyValidationResult, DependencyIssue, 
    DependencyReason, DependencySource)
from datetime import datetime

class HybridDependencyPolicy(DependencyPolicy):

    def __init__(self, max_age_days: int = None, prefer_workflow: bool = True):
        super().__init__()
        self.max_age_days = max_age_days
        self.prefer_workflow = prefer_workflow

    def validate(self, dependencies, workflow_modules=None):
        
        workflow_modules = workflow_modules or []

        errors = {}
        warnings = {}
        resolved = {}

        for dep_name, resource_path in dependencies.items():

            # 1️⃣ Try workflow
            if self._check_in_workflow(dep_name, workflow_modules):
                resolved[dep_name] = DependencySource.WORKFLOW
                continue

            # 2️⃣ Fallback to database
            exists, modified_time = self._check_in_database(resource_path)

            if not exists:
                errors[dep_name] = DependencyIssue(
                    dep_name=dep_name,
                    reason=DependencyReason.NOT_FOUND,
                    source=DependencySource.DATABASE,
                    required=True
                )
                continue

            # 3️⃣ Age check
            if self.max_age_days is not None and modified_time:
                age_days = (datetime.now() - modified_time).days
                if age_days > self.max_age_days:
                    errors[dep_name] = DependencyIssue(
                        dep_name=dep_name,
                        reason=DependencyReason.TOO_OLD,
                        source=DependencySource.DATABASE,
                        required=True,
                        metadata={
                            "age_days": age_days,
                            "max_age_days": self.max_age_days
                        }
                    )
                    continue

            # 4️⃣ Database OK
            resolved[dep_name] = DependencySource.DATABASE

            if self.prefer_workflow:
                warnings[dep_name] = DependencyIssue(
                    dep_name=dep_name,
                    reason=DependencyReason.WORKFLOW_VIOLATION,
                    source=DependencySource.DATABASE,
                    required=False
                )

        return DependencyValidationResult(
            errors=errors,
            warnings=warnings,
            resolved=resolved,
            workflow_modules=workflow_modules
        )