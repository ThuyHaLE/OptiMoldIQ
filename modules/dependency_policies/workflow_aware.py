# modules/dependency_policies/workflow_aware.py

from datetime import datetime, timedelta
from modules.dependency_policies.base import DependencyPolicy, DependencyValidationResult

class WorkflowAwareDependencyPolicy(DependencyPolicy):
    """
    Workflow-aware policy: Validates based on what should run in workflow.
    
    - If dependency in workflow_modules → must be in context
    - If not in workflow_modules → can use database fallback
    
    Args:
        max_age_days: Max age for database data
        strict_workflow: If True, deps in workflow MUST succeed
    """
    
    def __init__(self, max_age_days: int = None, strict_workflow: bool = True):
        super().__init__()
        self.max_age_days = max_age_days
        self.strict_workflow = strict_workflow
    
    def validate(self, dependencies, context, workflow_modules=None):
        missing = []
        resolved_from = {}
        warnings = []
        
        workflow_modules = set(workflow_modules or [])
        
        for dep_name, resource_path in dependencies.items():
            in_workflow = dep_name in workflow_modules
            
            # Check context
            if self._check_in_context(dep_name, context):
                resolved_from[dep_name] = 'context'
                self.logger.debug(f"✅ {dep_name}: found in context")
                continue
            
            # If should be in workflow but not found/failed
            if in_workflow and self.strict_workflow:
                status = "failed" if dep_name in context else "not found"
                missing.append(f"{dep_name} (in workflow but {status})")
                self.logger.warning(f"❌ {dep_name}: in workflow but {status}")
                continue
            
            # Try database fallback (only if not in workflow)
            if not in_workflow:
                exists, modified_time = self._check_in_database(resource_path)
                
                if not exists:
                    missing.append(f"{dep_name} (not in workflow and not in database)")
                    self.logger.warning(f"❌ {dep_name}: not found")
                    continue
                
                # Check age
                if self.max_age_days is not None and modified_time:
                    age_days = (datetime.now() - modified_time).days
                    if age_days > self.max_age_days:
                        missing.append(f"{dep_name} (database data too old: {age_days} days)")
                        continue
                
                resolved_from[dep_name] = 'database'
                self.logger.info(f"✅ {dep_name}: found in database")
            else:
                missing.append(f"{dep_name} (in workflow but execution failed)")
        
        return DependencyValidationResult(
            workflow_modules = workflow_modules,
            is_valid=len(missing) == 0,
            missing=missing,
            resolved_from=resolved_from,
            warnings=warnings
        )