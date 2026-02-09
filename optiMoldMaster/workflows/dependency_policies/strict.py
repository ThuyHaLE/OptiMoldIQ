# optiMoldMaster/workflows/dependency_policies/strict.py

from optiMoldMaster.workflows.dependency_policies.base import (
    DependencyPolicy, DependencyValidationResult, DependencyIssue, 
    DependencyReason, DependencySource)

class StrictWorkflowPolicy(DependencyPolicy):

    def validate(self, dependencies, workflow_modules = None):
        
        workflow_modules = workflow_modules or []

        errors = {}
        resolved = {}

        for dep_name, resource_path in dependencies.items():
            if self._check_in_workflow(dep_name, workflow_modules):
                resolved[dep_name] = DependencySource.WORKFLOW
            else:
                errors[dep_name] = DependencyIssue(
                    dep_name=dep_name,
                    reason=DependencyReason.WORKFLOW_VIOLATION,
                    source=DependencySource.WORKFLOW,
                    required=True,
                    metadata={
                        "expected_in_workflow": True,
                        "workflow_modules": workflow_modules
                    }
                )

        return DependencyValidationResult(
            errors=errors,
            resolved=resolved,
            workflow_modules=workflow_modules
        )