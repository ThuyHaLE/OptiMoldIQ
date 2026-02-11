# workflows/dependency_policies/flexible.py

from datetime import datetime
from typing import List
from workflows.dependency_policies.base import (
    DependencyPolicy, DependencyValidationResult, DependencyIssue, 
    DependencyReason, DependencySource)
 
class FlexibleDependencyPolicy(DependencyPolicy):
    """
    Flexible policy: Dependencies are optional.
    Module can run with partial or no dependencies.

    Rules:
    - Required deps:
        - Must exist (workflow OR database)
        - Must satisfy age constraint
    - Optional deps:
        - Missing or stale → warning only

    Args:
        required_deps: List of dependency names that are required
        max_age_days: Max age for database data
    """

    def __init__(self, 
                 required_deps: List[str] = None, 
                 max_age_days: int = None):
        super().__init__()
        self.required_deps = set(required_deps or [])
        self.max_age_days = max_age_days

    def validate(self, dependencies, workflow_modules=None):

        workflow_modules = workflow_modules or []

        errors = {}
        warnings = {}
        resolved = {}

        for dep_name, resource_path in dependencies.items():
            is_required = dep_name in self.required_deps

            # --------------------------------------------------
            # 1️⃣ Try workflow
            # --------------------------------------------------
            if self._check_in_workflow(dep_name, workflow_modules):
                resolved[dep_name] = DependencySource.WORKFLOW
                self.logger.debug(f"✅ {dep_name}: resolved from workflow")
                continue

            # --------------------------------------------------
            # 2️⃣ Try database
            # --------------------------------------------------
            exists, modified_time = self._check_in_database(resource_path)

            if not exists:
                issue = DependencyIssue(
                    dep_name=dep_name,
                    reason=DependencyReason.NOT_FOUND, 
                    source=DependencySource.WORKFLOW_DATABASE, 
                    required=is_required
                )

                if is_required:
                    errors[dep_name] = issue
                    self.logger.warning(f"❌ {dep_name}: required but not found")
                else:
                    warnings[dep_name] = issue
                    self.logger.info(f"⚠️  {dep_name}: optional and not found")
                continue

            # --------------------------------------------------
            # 3️⃣ Age validation
            # --------------------------------------------------
            if self.max_age_days is not None and modified_time:
                age_days = (datetime.now() - modified_time).days
                if age_days > self.max_age_days:
                    issue = DependencyIssue(
                        dep_name=dep_name,
                        reason=DependencyReason.TOO_OLD,
                        source=DependencySource.DATABASE,
                        required=is_required,
                        metadata={
                            "age_days": age_days,
                            "max_age_days": self.max_age_days,
                            "last_modified": modified_time.isoformat()
                        }
                    )

                    if is_required:
                        errors[dep_name] = issue
                        self.logger.warning(
                            f"❌ {dep_name}: required but too old ({age_days} days)"
                        )
                    else:
                        warnings[dep_name] = issue
                        self.logger.info(
                            f"⚠️  {dep_name}: optional but data is old ({age_days} days)"
                        )
                    continue

            # --------------------------------------------------
            # 4️⃣ Database dependency resolved
            # --------------------------------------------------
            resolved[dep_name] = DependencySource.DATABASE
            self.logger.info(f"✅ {dep_name}: resolved from database")

        return DependencyValidationResult(
            errors=errors,
            warnings=warnings,
            resolved=resolved,
            workflow_modules=workflow_modules
        )