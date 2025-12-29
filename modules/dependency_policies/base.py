# modules/dependency_policies/base.py

from abc import ABC, abstractmethod
from typing import Dict, List, Tuple
from dataclasses import dataclass
from datetime import datetime
from loguru import logger

@dataclass
class DependencyValidationResult:
    """Result of dependency validation"""
    workflow_modules: List[str] = None
    is_valid: bool
    missing: List[str]
    resolved_from: Dict[str, str]  # dep_name -> source ('context' | 'database')
    warnings: List[str] = None
    
    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


class DependencyPolicy(ABC):
    """Base class for dependency validation policies"""
    
    def __init__(self):
        self.logger = logger.bind(policy=self.__class__.__name__)
    
    @abstractmethod
    def validate(self,
                 dependencies: Dict[str, str],
                 context: Dict[str, "ModuleResult"],
                 workflow_modules: List[str] = None
                 ) -> DependencyValidationResult:
        """
        Validate dependencies according to policy.
        
        Args:
            dependencies: Dict mapping dep_name -> resource_path
            context: Current execution context
            workflow_modules: List of modules in current workflow
            
        Returns:
            DependencyValidationResult with validation details
        """
        pass
    
    def _check_in_context(self, dep_name: str, context: Dict) -> bool:
        """Helper: Check if dependency exists and succeeded in context"""
        return dep_name in context and context[dep_name].is_success()
    
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