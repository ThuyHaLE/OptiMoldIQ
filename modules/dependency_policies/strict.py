# modules/dependency_policies/strict.py

from modules.dependency_policies.base import DependencyPolicy, DependencyValidationResult

class StrictContextPolicy(DependencyPolicy):
    """
    Strict policy: All dependencies MUST exist in context.
    No database fallback allowed.
    """
    
    def validate(self, dependencies, context, workflow_modules=None):
        missing = []
        resolved_from = {}
        
        for dep_name in dependencies:
            if self._check_in_context(dep_name, context):
                resolved_from[dep_name] = 'context'
                self.logger.debug(f"✅ {dep_name}: found in context")
            else:
                status = "not found" if dep_name not in context else "failed"
                missing.append(f"{dep_name} ({status})")
                self.logger.warning(f"❌ {dep_name}: {status} in context")
        
        return DependencyValidationResult(
            workflow_modules = workflow_modules,
            is_valid=len(missing) == 0,
            missing=missing,
            resolved_from=resolved_from
        )