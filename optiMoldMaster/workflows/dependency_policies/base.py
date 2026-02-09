# optiMoldMaster/workflows/dependency_policies/base.py

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Any
from datetime import datetime
from loguru import logger
from enum import Enum


class DependencyReason(str, Enum):
    NONE = "none"
    NOT_FOUND = "not_found"
    TOO_OLD = "too_old"
    WORKFLOW_VIOLATION = "workflow_violation"

class DependencySource(str, Enum):
    WORKFLOW = "workflow"
    DATABASE = "database"
    WORKFLOW_DATABASE = "workflow+database"
    NONE = "none"

@dataclass
class DependencyIssue:
    dep_name: str
    reason: DependencyReason = DependencyReason.NONE
    source: DependencySource = DependencySource.NONE
    required: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self):
        return {
            "dep_name": self.dep_name,
            "reason": self.reason.value,
            "source": self.source.value,
            "required": self.required,
            "metadata": self.metadata
        }

@dataclass
class DependencyValidationResult:
    """
    Canonical dependency validation result.
    This is the ONLY contract between:
    - DependencyPolicy
    - WorkflowExecutor
    """
    errors: Dict[str, DependencyIssue] = field(default_factory=dict)     # blocking issues
    warnings: Dict[str, DependencyIssue] = field(default_factory=dict)   # non-blocking issues
    resolved: Dict[str, DependencySource] = field(default_factory=dict)  # successfully resolved deps (dep_name -> source)
    workflow_modules: List[str] = field(default_factory=list)

    @property
    def valid(self) -> bool:
        return not self.errors
    
    def has_errors(self) -> bool:
        return len(self.errors) > 0
    
    def has_warnings(self) -> bool:
        return len(self.warnings) > 0
    
    def should_block(self) -> bool:
        return any(issue.required for issue in self.errors.values())

    def summary(self) -> Dict:
        return {
            "valid": self.valid,
            "errors": {k: v.reason.value for k, v in self.errors.items()},
            "warnings": {k: v.reason.value for k, v in self.warnings.items()},
            "resolved": {k: v.value for k, v in self.resolved.items()}
        }
    
class DependencyPolicy(ABC):
    """Base class for dependency validation policies"""
    
    def __init__(self):
        self.logger = logger.bind(policy=self.__class__.__name__)
    
    @abstractmethod
    def validate(self,
                 dependencies: Dict[str, str],
                 workflow_modules: List[str] = None
                 ) -> DependencyValidationResult:
        """
        Validate dependencies according to policy.
        
        Args:
            dependencies: Dict mapping dep_name -> resource_path
            workflow_modules: List of modules in current workflow
            
        Returns:
            DependencyValidationResult with validation details
        """
        pass
    
    def _check_in_workflow(self, dep_name: str, workflow_modules: List) -> bool:
        """Helper: Check if dependency exists in workflow"""
        return dep_name in workflow_modules
    
    def _check_in_database(self, resource_path: str) -> Tuple[bool, datetime]:
        """
        Helper: Check if resource exists in database/filesystem.
        
        Returns:
            (exists, last_modified_time)
        """
        from pathlib import Path
        path = Path(resource_path)
        
        if not path.exists():
            return False, None
        
        try:
            stat = path.stat()
            modified_time = datetime.fromtimestamp(stat.st_mtime)
            return True, modified_time
        except Exception as e:
            self.logger.error(f"Error checking {resource_path}: {e}")
            return False, None