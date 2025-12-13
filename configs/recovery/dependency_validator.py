# configs/recovery/dependency_validator.py
from dataclasses import dataclass, field
from typing import Dict, Callable, Optional, List, Any
from enum import Enum
from pathlib import Path
from loguru import logger
import pandas as pd
from agents.utils import read_change_log

class DependencyStatus(Enum):
    AVAILABLE = "available"
    MISSING = "missing"
    HEALING_FAILED = "healing_failed"

@dataclass
class Dependency:
    """Defines a data dependency with healing capability"""
    name: str
    change_log_path: str
    healing_agent: Optional[Callable] = None
    required: bool = True
    description: str = ""
    file_type: str = "excel"
    validate_content: Optional[Callable] = None
    load_fn: Optional[Callable[[str], Any]] = None

@dataclass
class DependencyValidationResult:
    """Result of dependency validation"""
    dependency_name: str
    status: DependencyStatus
    path: Optional[str] = None
    data: Optional[Any] = None
    error: Optional[str] = None
    healed: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

class DependencyValidator:
    """Validates and heals agent dependencies"""
    
    def __init__(self, shared_source_config):
        self.shared_source_config = shared_source_config
        self.logger = logger.bind(class_=self.__class__.__name__)
        self._healing_stack = []
        self._change_log_cache = {}
    
    def validate_dependencies(
        self, 
        dependencies: List[Dependency],
        auto_heal: bool = True,
        load_data: bool = False
    ) -> Dict[str, DependencyValidationResult]:
        """Validate all dependencies upfront."""
        results = {}
        
        self.logger.info("=" * 60)
        self.logger.info("DEPENDENCY VALIDATION PHASE")
        self.logger.info("=" * 60)
        
        for dep in dependencies:
            self.logger.info(f"\n📋 Validating: {dep.name}")
            if dep.description:
                self.logger.info(f"   Description: {dep.description}")
            
            result = self._validate_single_dependency(dep, auto_heal, load_data)
            results[dep.name] = result
            
            self._log_validation_result(dep, result)
            
            # Fail fast for required dependencies
            if dep.required and result.status != DependencyStatus.AVAILABLE:
                self._log_dependency_summary(results)
                raise ValueError(
                    f"Required dependency '{dep.name}' failed validation: {result.error}"
                )
        
        self._log_dependency_summary(results)
        return results
    
    def _read_change_log(self, change_log_path):
        """Helper function to get latest file path from a change log."""
        return  read_change_log(
            Path(change_log_path).parent,
            Path(change_log_path).name
        )
    
    def _validate_single_dependency(
        self, 
        dep: Dependency, 
        auto_heal: bool,
        load_data: bool
    ) -> DependencyValidationResult:
        """Validate a single dependency"""
        
        # Read change log
        latest_path = self._read_change_log(dep.change_log_path)
        
        if latest_path is not None:
            # Validate file exists
            if not self._validate_file_exists(latest_path):
                self.logger.warning(f"Path in change log doesn't exist: {latest_path}")
                latest_path = None
        
        # Handle missing or invalid path
        if latest_path is None:
            if not auto_heal or dep.healing_agent is None:
                return DependencyValidationResult(
                    dependency_name=dep.name,
                    status=DependencyStatus.MISSING,
                    error="No valid path found and no healing agent available"
                )
            
            # Attempt healing
            heal_result = self._attempt_healing(dep)
            if heal_result.status != DependencyStatus.AVAILABLE:
                return heal_result
            
            latest_path = heal_result.path
        
        # Path is valid, create result
        result = DependencyValidationResult(
            dependency_name=dep.name,
            status=DependencyStatus.AVAILABLE,
            path=latest_path,
            metadata={'file_type': dep.file_type}
        )
        
        # Load data if requested
        if load_data:
            try:
                result.data = self._load_data(latest_path, dep)
                
                # Run custom validation if provided
                if dep.validate_content:
                    validation_error = dep.validate_content(result.data)
                    if validation_error:
                        return DependencyValidationResult(
                            dependency_name=dep.name,
                            status=DependencyStatus.MISSING,
                            path=latest_path,
                            error=f"Content validation failed: {validation_error}"
                        )
            
            except Exception as e:
                return DependencyValidationResult(
                    dependency_name=dep.name,
                    status=DependencyStatus.MISSING,
                    path=latest_path,
                    error=f"Failed to load data: {str(e)}"
                )
        
        return result
    
    def _attempt_healing(self, dep: Dependency) -> DependencyValidationResult:
        """Attempt to heal a missing dependency"""
        
        # Check for circular dependency
        if dep.name in self._healing_stack:
            cycle = " → ".join(self._healing_stack + [dep.name])
            return DependencyValidationResult(
                dependency_name=dep.name,
                status=DependencyStatus.HEALING_FAILED,
                error=f"Circular dependency detected: {cycle}"
            )
        
        self._healing_stack.append(dep.name)
        
        try:
            self.logger.info(f"🔧 Attempting to heal dependency: {dep.name}")
            
            # Run healing agent
            dep.healing_agent()
            
            # Clear cache for this change log
            self._change_log_cache.pop(dep.change_log_path, None)
            
            # Verify healing worked
            latest_path = self._read_change_log(dep.change_log_path)
            
            if latest_path and self._validate_file_exists(latest_path):
                self.logger.info(f"✓ Healing successful for {dep.name}")
                return DependencyValidationResult(
                    dependency_name=dep.name,
                    status=DependencyStatus.AVAILABLE,
                    path=latest_path,
                    healed=True
                )
            else:
                return DependencyValidationResult(
                    dependency_name=dep.name,
                    status=DependencyStatus.HEALING_FAILED,
                    error="Healing agent ran but path still not available"
                )
        
        except Exception as e:
            self.logger.error(f"✗ Healing failed for {dep.name}: {e}", exc_info=True)
            return DependencyValidationResult(
                dependency_name=dep.name,
                status=DependencyStatus.HEALING_FAILED,
                error=str(e)
            )
        
        finally:
            self._healing_stack.pop()
    
    def _validate_file_exists(self, path: str) -> bool:
        """Check if file actually exists"""
        return Path(path).exists()
    
    def _load_data(self, path: str, dep: Dependency) -> Any:
        """Load data based on file type or custom load function"""
        
        # Use custom load function if provided
        if dep.load_fn is not None:
            self.logger.debug(f"Using custom load function for {dep.name}")
            return dep.load_fn(path)
        
        # Default loading logic
        if dep.file_type == 'excel':
            return pd.read_excel(path)
        elif dep.file_type == 'csv':
            return pd.read_csv(path)
        elif dep.file_type == 'json':
            import json
            with open(path, 'r') as f:
                return json.load(f)
        elif dep.file_type == 'pickle':
            import pickle
            with open(path, 'rb') as f:
                return pickle.load(f)
        else:
            raise ValueError(f"Unsupported file type: {dep.file_type}")
    
    def _log_validation_result(self, dep: Dependency, result: DependencyValidationResult):
        """Log validation result"""
        status_emoji = {
            DependencyStatus.AVAILABLE: "✓",
            DependencyStatus.MISSING: "✗",
            DependencyStatus.HEALING_FAILED: "✗"
        }
        
        emoji = status_emoji.get(result.status, "?")
        
        if result.status == DependencyStatus.AVAILABLE:
            healed_str = " (healed)" if result.healed else ""
            required_str = "" if dep.required else " [optional]"
            self.logger.info(f"   {emoji} Status: AVAILABLE{healed_str}{required_str}")
            self.logger.info(f"   📁 Path: {result.path}")
            if result.data is not None:
                self.logger.info(f"   📊 Data: {self._get_data_summary(result.data)}")
        else:
            required_str = " [REQUIRED]" if dep.required else " [optional]"
            self.logger.warning(f"   {emoji} Status: {result.status.value.upper()}{required_str}")
            if result.error:
                self.logger.warning(f"   ⚠️  Error: {result.error}")
    
    def _get_data_summary(self, data: Any) -> str:
        """Get summary of loaded data"""
        if isinstance(data, pd.DataFrame):
            return f"DataFrame ({len(data)} rows × {len(data.columns)} cols)"
        elif isinstance(data, dict):
            return f"Dict ({len(data)} keys)"
        elif isinstance(data, list):
            return f"List ({len(data)} items)"
        else:
            return f"{type(data).__name__}"
    
    def _log_dependency_summary(self, results: Dict[str, DependencyValidationResult]):
        """Log summary of all dependencies"""
        self.logger.info("\n" + "=" * 60)
        self.logger.info("DEPENDENCY VALIDATION SUMMARY")
        self.logger.info("=" * 60)

        available = sum(1 for r in results.values() 
                       if r.status == DependencyStatus.AVAILABLE)
        healed = sum(1 for r in results.values() if r.healed)
        failed = sum(1 for r in results.values() 
                    if r.status in [DependencyStatus.MISSING, DependencyStatus.HEALING_FAILED])
        
        self.logger.info(f"📊 Total: {len(results)} | ✓ Available: {available} | 🔧 Healed: {healed} | ✗ Failed: {failed}")
        
        if failed > 0:
            self.logger.warning("\n⚠️  Failed dependencies:")
            for name, result in results.items():
                if result.status != DependencyStatus.AVAILABLE:
                    self.logger.warning(f"   - {name}: {result.error}")
        
        self.logger.info("=" * 60 + "\n")

def get_dependency_data(validation_results: Dict[str, DependencyValidationResult], name: str) -> Any:
    """Helper to get data from validation results"""
    result = validation_results.get(name)
    if not result:
        raise KeyError(f"Dependency '{name}' not found")
    if result.status != DependencyStatus.AVAILABLE:
        raise ValueError(f"Dependency '{name}' not available: {result.error}")
    return result.data

def get_dependency_path(validation_results: Dict[str, DependencyValidationResult], name: str) -> str:
    """Helper to get path from validation results"""
    result = validation_results.get(name)
    if not result:
        raise KeyError(f"Dependency '{name}' not found")
    if result.status != DependencyStatus.AVAILABLE:
        raise ValueError(f"Dependency '{name}' not available: {result.error}")
    return result.path