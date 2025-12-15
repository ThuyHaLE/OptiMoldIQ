# configs/shared/agent_report_format.py

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from enum import Enum
from abc import ABC, abstractmethod
from datetime import datetime
import traceback
from loguru import logger

# ============================================
# ENUMS
# ============================================
class PhaseSeverity(Enum):
    """Severity levels for phases"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ExecutionStatus(Enum):
    """Execution status values"""
    SUCCESS = "success"
    WARNING = "warning"
    PARTIAL = "partial"
    FAILED = "failed"


# ============================================
# BASE EXECUTABLE - Common interface
# ============================================
class Executable(ABC):
    """
    Base interface for both Phase and Agent
    """
    
    @abstractmethod
    def execute(self) -> 'ExecutionResult':
        """Execute and return result - never raises"""
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Get the name of this executable"""
        pass


# ============================================
# EXECUTION RESULT - Unified result format
# ============================================
@dataclass
class ExecutionResult:
    """
    Unified result format for both Phase and Agent
    Agent report IS-A ExecutionResult with sub_results
    """
    name: str
    type: str  # "phase" or "agent"
    status: str
    duration: float
    severity: str = PhaseSeverity.INFO.value
    
    # Error info
    error: Optional[str] = None
    traceback: Optional[str] = None
    
    # Data
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Hierarchical structure - KEY PART
    sub_results: List['ExecutionResult'] = field(default_factory=list)
    total_sub_executions: int = 0  # Expected sub-phases/sub-agents
    
    # Dependencies
    dependencies: List[str] = field(default_factory=list)
    skipped_reason: Optional[str] = None
    
    # Warnings
    warnings: List[Dict[str, str]] = field(default_factory=list)
    
    # ===== COMPUTED PROPERTIES =====
    @property
    def is_leaf(self) -> bool:
        """Is this an atomic phase (no sub-results)?"""
        return len(self.sub_results) == 0
    
    @property
    def is_composite(self) -> bool:
        """Is this a composite (has sub-results)?"""
        return len(self.sub_results) > 0
    
    def is_complete(self) -> bool:
        """All expected sub-executions completed?"""
        if self.is_leaf:
            return True
        return len(self.sub_results) == self.total_sub_executions
    
    def all_successful(self) -> bool:
        """All sub-executions successful?"""
        if self.is_leaf:
            return self.status == "success"
        
        return (
            self.is_complete() and
            all(sub.all_successful() for sub in self.sub_results)
        )
    
    def has_critical_errors(self) -> bool:
        """Has critical errors (recursive check)?"""
        if self.status == "failed" and self.severity == PhaseSeverity.CRITICAL.value:
            return True
        
        return any(sub.has_critical_errors() for sub in self.sub_results)
    
    def get_failed_paths(self) -> List[str]:
        """Get all failed execution paths (recursive)"""
        paths = []
        
        if self.status == "failed":
            paths.append(self.name)
        
        for sub in self.sub_results:
            sub_paths = sub.get_failed_paths()
            paths.extend([f"{self.name}.{path}" for path in sub_paths])
        
        return paths
    
    def get_depth(self) -> int:
        """Get tree depth"""
        if self.is_leaf:
            return 1
        return 1 + max((sub.get_depth() for sub in self.sub_results), default=0)
    
    def flatten(self) -> List['ExecutionResult']:
        """Flatten tree to list (DFS)"""
        result = [self]
        for sub in self.sub_results:
            result.extend(sub.flatten())
        return result
    
    def summary_stats(self) -> Dict[str, Any]:
        """Recursive statistics"""
        all_results = self.flatten()
        
        return {
            "total_executions": len(all_results),
            "depth": self.get_depth(),
            "success": sum(1 for r in all_results if r.status == "success"),
            "failed": sum(1 for r in all_results if r.status == "failed"),
            "skipped": sum(1 for r in all_results if r.status == "skipped"),
            "critical_errors": sum(1 for r in all_results if r.has_critical_errors()),
            "warnings": sum(len(r.warnings) for r in all_results),
            "total_duration": sum(r.duration for r in all_results)
        }


# ============================================
# ATOMIC PHASE - Leaf node
# ============================================
class AtomicPhase(Executable):
    """
    Simple phase - no sub-phases
    Atomic unit of work
    """
    
    # Define in subclass
    RECOVERABLE_ERRORS: tuple = ()
    CRITICAL_ERRORS: tuple = ()
    
    def __init__(self, name: str):
        self.name = name
    
    def get_name(self) -> str:
        return self.name
    
    @abstractmethod
    def _execute_impl(self) -> Any:
        """Implement actual logic here - can raise freely"""
        pass
    
    @abstractmethod
    def _fallback(self) -> Any:
        """Fallback logic if main execution fails - can raise if no fallback"""
        pass
    
    def execute(self) -> ExecutionResult:
        """Execute phase - never raises"""
        start_time = datetime.now()
        
        try:
            result = self._execute_impl()
            
            return ExecutionResult(
                name=self.name,
                type="phase",
                status="success",
                duration=(datetime.now() - start_time).total_seconds(),
                data={"result": result}
            )
            
        except self.RECOVERABLE_ERRORS as e:
            # Try fallback
            logger.warning(f"Phase {self.name} attempting fallback: {str(e)}")
            
            try:
                result = self._fallback()
                return ExecutionResult(
                    name=self.name,
                    type="phase",
                    status="success",
                    duration=(datetime.now() - start_time).total_seconds(),
                    severity=PhaseSeverity.WARNING.value,
                    data={"result": result, "fallback_used": True},
                    warnings=[{
                        "message": f"Fallback used: {str(e)}",
                        "severity": PhaseSeverity.WARNING.value
                    }]
                )
            except Exception as fallback_error:
                return ExecutionResult(
                    name=self.name,
                    type="phase",
                    status="failed",
                    duration=(datetime.now() - start_time).total_seconds(),
                    severity=PhaseSeverity.ERROR.value,
                    error=f"Fallback failed: {str(fallback_error)}",
                    traceback=traceback.format_exc()
                )
        
        except self.CRITICAL_ERRORS as e:
            logger.critical(f"Phase {self.name} critical failure: {str(e)}")
            
            return ExecutionResult(
                name=self.name,
                type="phase",
                status="failed",
                duration=(datetime.now() - start_time).total_seconds(),
                severity=PhaseSeverity.CRITICAL.value,
                error=str(e),
                traceback=traceback.format_exc()
            )
        
        except Exception as e:
            logger.error(f"Phase {self.name} unexpected error: {str(e)}")
            
            return ExecutionResult(
                name=self.name,
                type="phase",
                status="failed",
                duration=(datetime.now() - start_time).total_seconds(),
                severity=PhaseSeverity.ERROR.value,
                error=str(e),
                traceback=traceback.format_exc()
            )


# ============================================
# COMPOSITE AGENT - Branch node
# ============================================
class CompositeAgent(Executable):
    """
    Agent that contains sub-phases or sub-agents
    Can be used as a phase in parent agent
    """
    
    def __init__(self, name: str, executables: List[Executable]):
        self.name = name
        self.executables = executables  # Can be phases or agents!
    
    def get_name(self) -> str:
        return self.name
    
    def execute(self) -> ExecutionResult:
        """
        Execute all sub-executables
        NEVER raises - always returns ExecutionResult
        """
        start_time = datetime.now()
        sub_results = []
        warnings = []
        
        for executable in self.executables:
            # Execute sub-phase/sub-agent
            result = executable.execute()  # No try-catch needed!
            sub_results.append(result)
            
            # Collect warnings
            warnings.extend(result.warnings)
            
            # Check if should stop
            if result.has_critical_errors():
                logger.error(
                    f"Critical failure in {executable.get_name()}, "
                    f"stopping {self.name}"
                )
                
                # Skip remaining executables
                for remaining in self.executables[len(sub_results):]:
                    sub_results.append(ExecutionResult(
                        name=remaining.get_name(),
                        type="phase" if isinstance(remaining, AtomicPhase) else "agent",
                        status="skipped",
                        duration=0.0,
                        skipped_reason=f"Dependency {executable.get_name()} failed critically"
                    ))
                break
            
            # Non-critical failures - log and continue
            if result.status == "failed":
                warnings.append({
                    "message": f"{executable.get_name()} failed but continuing",
                    "severity": result.severity
                })
        
        # Determine overall status
        duration = (datetime.now() - start_time).total_seconds()
        
        # Auto-compute status from sub-results
        if any(r.has_critical_errors() for r in sub_results):
            status = ExecutionStatus.FAILED.value
            severity = PhaseSeverity.CRITICAL.value
        elif not all(r.status == "success" for r in sub_results):
            status = ExecutionStatus.PARTIAL.value
            severity = PhaseSeverity.ERROR.value
        elif warnings:
            status = ExecutionStatus.SUCCESS.value
            severity = PhaseSeverity.WARNING.value
        else:
            status = ExecutionStatus.SUCCESS.value
            severity = PhaseSeverity.INFO.value
        
        return ExecutionResult(
            name=self.name,
            type="agent",
            status=status,
            duration=duration,
            severity=severity,
            sub_results=sub_results,
            total_sub_executions=len(self.executables),
            warnings=warnings,
            metadata={
                "sub_executions": len(sub_results),
                "expected_executions": len(self.executables)
            }
        )


# ============================================
# UTILITY FUNCTIONS
# ============================================
def print_execution_tree(result: ExecutionResult, indent: int = 0) -> None:
    """
    Print execution result as a tree
    
    Args:
        result: ExecutionResult to print
        indent: Current indentation level
    """
    prefix = "  " * indent
    icon = "📦" if result.type == "agent" else "⚙️"
    
    status_icons = {
        "success": "✓",
        "failed": "✗",
        "skipped": "⊘",
        "partial": "⚡"
    }
    status_icon = status_icons.get(result.status, "?")
    
    severity_colors = {
        PhaseSeverity.CRITICAL.value: "🔴",
        PhaseSeverity.ERROR.value: "🟠",
        PhaseSeverity.WARNING.value: "🟡",
        PhaseSeverity.INFO.value: ""
    }
    severity_icon = severity_colors.get(result.severity, "")
    
    print(f"{prefix}{icon} {result.name} {status_icon} {severity_icon} ({result.duration:.2f}s)")
    
    if result.error:
        print(f"{prefix}   └─ Error: {result.error}")
    
    for sub in result.sub_results:
        print_execution_tree(sub, indent + 1)


def analyze_execution(result: ExecutionResult) -> Dict[str, Any]:
    """
    Analyze execution result and return comprehensive report
    
    Args:
        result: ExecutionResult to analyze
    
    Returns:
        Dictionary with analysis details
    """
    stats = result.summary_stats()
    failed_paths = result.get_failed_paths()
    
    return {
        "name": result.name,
        "status": result.status,
        "duration": result.duration,
        "complete": result.is_complete(),
        "all_successful": result.all_successful(),
        "statistics": stats,
        "failed_paths": failed_paths,
        "has_critical_errors": result.has_critical_errors(),
        "depth": result.get_depth()
    }