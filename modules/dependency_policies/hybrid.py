# modules/dependency_policies/hybrid.py

from modules.dependency_policies.base import DependencyPolicy, DependencyValidationResult
from datetime import datetime, timedelta

class HybridDependencyPolicy(DependencyPolicy):
    """
    Hybrid policy: Try context first, fallback to database.
    
    Args:
        max_age_days: Maximum age for database data (None = no limit)
        prefer_context: If True, warn when using database fallback
    """
    
    def __init__(self, max_age_days: int = None, prefer_context: bool = True):
        super().__init__()
        self.max_age_days = max_age_days
        self.prefer_context = prefer_context
    
    def validate(self, dependencies, context, workflow_modules=None):
        missing = []
        resolved_from = {}
        warnings = []
        
        for dep_name, resource_path in dependencies.items():
            # 1️⃣ Try context first
            if self._check_in_context(dep_name, context):
                resolved_from[dep_name] = 'context'
                self.logger.debug(f"✅ {dep_name}: found in context")
                continue
            
            # 2️⃣ Fallback to database
            exists, modified_time = self._check_in_database(resource_path)
            
            if not exists:
                missing.append(f"{dep_name} (not in context and not in database)")
                self.logger.warning(f"❌ {dep_name}: not found anywhere")
                continue
            
            # 3️⃣ Check age constraint
            if self.max_age_days is not None and modified_time:
                age_days = (datetime.now() - modified_time).days
                if age_days > self.max_age_days:
                    missing.append(f"{dep_name} (database data too old: {age_days} > {self.max_age_days} days)")
                    self.logger.warning(f"❌ {dep_name}: data too old ({age_days} days)")
                    continue
            
            # 4️⃣ Database data is valid
            resolved_from[dep_name] = 'database'
            self.logger.info(f"✅ {dep_name}: found in database (modified: {modified_time})")
            
            if self.prefer_context:
                warnings.append(f"{dep_name} using database fallback instead of fresh context data")
        
        return DependencyValidationResult(
            workflow_modules = workflow_modules,
            is_valid=len(missing) == 0,
            missing=missing,
            resolved_from=resolved_from,
            warnings=warnings
        )