# modules/dependency_policies/flexible.py

from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from modules.dependency_policies.base import DependencyPolicy, DependencyValidationResult

class FlexibleDependencyPolicy(DependencyPolicy):
    """
    Flexible policy: Dependencies are optional.
    Module can run with partial or no dependencies.
    
    Args:
        required_deps: List of dependency names that are required
        max_age_days: Max age for database data
    """
    
    def __init__(self, required_deps: List[str] = None, max_age_days: int = None):
        super().__init__()
        self.required_deps = set(required_deps or [])
        self.max_age_days = max_age_days
    
    def validate(self, dependencies, context, workflow_modules=None):
        missing = []
        resolved_from = {}
        warnings = []
        
        for dep_name, resource_path in dependencies.items():
            is_required = dep_name in self.required_deps
            
            # Try context
            if self._check_in_context(dep_name, context):
                resolved_from[dep_name] = 'context'
                self.logger.debug(f"✅ {dep_name}: found in context")
                continue
            
            # Try database
            exists, modified_time = self._check_in_database(resource_path)
            
            if not exists:
                if is_required:
                    missing.append(f"{dep_name} (required but not found)")
                    self.logger.warning(f"❌ {dep_name}: required but not found")
                else:
                    warnings.append(f"{dep_name} not found but optional")
                    self.logger.info(f"⚠️  {dep_name}: not found but optional")
                continue
            
            # Check age
            if self.max_age_days is not None and modified_time:
                age_days = (datetime.now() - modified_time).days
                if age_days > self.max_age_days:
                    if is_required:
                        missing.append(f"{dep_name} (required but too old: {age_days} days)")
                    else:
                        warnings.append(f"{dep_name} data old ({age_days} days) but optional")
                    continue
            
            resolved_from[dep_name] = 'database'
            self.logger.info(f"✅ {dep_name}: found in database")
        
        return DependencyValidationResult(
            workflow_modules = workflow_modules,
            is_valid=len(missing) == 0,
            missing=missing,
            resolved_from=resolved_from,
            warnings=warnings
        )
