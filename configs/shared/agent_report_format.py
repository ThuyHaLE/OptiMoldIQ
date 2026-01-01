# configs/shared/agent_report_format.py

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from enum import Enum
from abc import ABC, abstractmethod
from datetime import datetime
import traceback
from pathlib import Path
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
    SUCCESS = "success"        # Fully successful
    DEGRADED = "degraded"      # Successful, but fallback was used
    WARNING = "warning"        # Successful with warnings
    PARTIAL = "partial"        # Some sub-phases failed
    FAILED = "failed"          # Completely failed
    SKIPPED = "skipped"        # Skipped due to unmet dependencies

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
    Base class for atomic execution phases.
    
    Attributes:
        RECOVERABLE_ERRORS: Tuple of exceptions that can be recovered via fallback
        CRITICAL_ERRORS: Tuple of exceptions that are always critical
        FALLBACK_FAILURE_IS_CRITICAL: If True, fallback failure returns CRITICAL severity
    """
    
    # Define in subclass
    RECOVERABLE_ERRORS: tuple = ()
    CRITICAL_ERRORS: tuple = ()
    FALLBACK_FAILURE_IS_CRITICAL = False  # Default: ERROR for most phases

    def __init__(self, name: str):
        self.name = name
    
    def get_name(self) -> str:
        return self.name
    
    @abstractmethod
    def _execute_impl(self) -> Any:
        """
        Implementation of phase logic.
        Should be overridden by subclasses.
        
        Raises:
            Exception: Any error that occurs during execution
        """
        raise NotImplementedError("Subclasses must implement _execute_impl()")
    
    @abstractmethod
    def _fallback(self) -> Any:
        """
        Fallback implementation when _execute_impl fails with RECOVERABLE_ERRORS.
        Should be overridden by subclasses if fallback is possible.
        
        Default behavior: raise error (no fallback available)
        
        Raises:
            Exception: If fallback is not possible or fails
        """
        raise NotImplementedError(
            f"Phase {self.name} has no fallback implementation. "
            "Override _fallback() if recovery is possible."
        )
    
    def execute(self) -> ExecutionResult:
        """
        Execute phase with comprehensive error handling.
        
        Never raises exceptions - always returns ExecutionResult.
        
        Returns:
            ExecutionResult: Result with status, duration, and any errors
        """

        start_time = datetime.now()
        
        try:
            # Attempt normal execution
            result = self._execute_impl()
            
            return ExecutionResult(
                name=self.name,
                type="phase",
                status=ExecutionStatus.SUCCESS.value,
                duration=(datetime.now() - start_time).total_seconds(),
                data={"result": result}
            )
            
        except self.RECOVERABLE_ERRORS as e:
            # Try fallback for recoverable errors
            logger.warning(f"Phase {self.name} attempting fallback: {str(e)}")
            
            try:
                result = self._fallback()
                return ExecutionResult(
                    name=self.name,
                    type="phase",
                    status=ExecutionStatus.DEGRADED.value,  # ⭐ Degraded!
                    duration=(datetime.now() - start_time).total_seconds(),
                    severity=PhaseSeverity.WARNING.value,
                    data={
                        "result": result, 
                        "fallback_used": True,
                        "original_error": str(e)
                    },
                    warnings=[{
                        "message": f"Fallback used due to: {str(e)}",
                        "severity": PhaseSeverity.WARNING.value,
                        "phase": self.name
                    }]
                )
            
            except Exception as fallback_error:
                # ⭐ KEY FEATURE: Use FALLBACK_FAILURE_IS_CRITICAL to determine severity
                severity = (
                    PhaseSeverity.CRITICAL.value 
                    if self.FALLBACK_FAILURE_IS_CRITICAL
                    else PhaseSeverity.ERROR.value
                )
                
                logger.error(
                    f"Phase {self.name} fallback failed with severity={severity}"
                )
                
                return ExecutionResult(
                    name=self.name,
                    type="phase",
                    status=ExecutionStatus.FAILED.value,
                    duration=(datetime.now() - start_time).total_seconds(),
                    severity=severity,
                    error=f"Fallback failed: {str(fallback_error)}",
                    traceback=traceback.format_exc(),
                    metadata={
                        "original_error": str(e),
                        "fallback_error": str(fallback_error)
                    }
                )
        
        except self.CRITICAL_ERRORS as e:
            # Critical errors always return CRITICAL severity
            logger.critical(f"Phase {self.name} critical failure: {str(e)}")
            
            return ExecutionResult(
                name=self.name,
                type="phase",
                status=ExecutionStatus.FAILED.value,
                duration=(datetime.now() - start_time).total_seconds(),
                severity=PhaseSeverity.CRITICAL.value,
                error=str(e),
                traceback=traceback.format_exc()
            )
        
        except Exception as e:
            # Unexpected errors return ERROR severity
            logger.error(f"Phase {self.name} unexpected error: {str(e)}")
            
            return ExecutionResult(
                name=self.name,
                type="phase",
                status=ExecutionStatus.FAILED.value,
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
    Agent that contains sub-phases or sub-agents.
    Automatically handles execution, aggregation, and error handling.
    """
    
    def __init__(self, name: str, executables: List[Executable]):
        self.name = name
        self.executables = executables
    
    def get_name(self) -> str:
        return self.name
    
    def execute(self) -> ExecutionResult:
        """Execute all sub-executables with automatic aggregation"""
        start_time = datetime.now()
        sub_results = []
        warnings = []
        
        for executable in self.executables:
            result = executable.execute()
            sub_results.append(result)
            warnings.extend(result.warnings)
            
            # ⭐ CRITICAL failure → stop immediately
            if result.has_critical_errors():
                logger.error(
                    f"Critical failure in {executable.get_name()}, "
                    f"stopping {self.name}"
                )
                
                # Mark remaining executables as skipped
                for remaining in self.executables[len(sub_results):]:
                    sub_results.append(ExecutionResult(
                        name=remaining.get_name(),
                        type="phase" if isinstance(remaining, AtomicPhase) else "agent",
                        status=ExecutionStatus.SKIPPED.value,
                        duration=0.0,
                        skipped_reason=f"Dependency {executable.get_name()} failed critically"
                    ))
                break
            
            # Non-critical failures → log warning and continue
            if result.status == ExecutionStatus.FAILED.value:
                warnings.append({
                    "message": f"{executable.get_name()} failed but continuing",
                    "severity": result.severity
                })
        
        duration = (datetime.now() - start_time).total_seconds()
        
        # ✨ Use updated aggregation logic with DEGRADED support
        status, severity = self._aggregate_status(sub_results)
        
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
    
    def _aggregate_status(self, results: List[ExecutionResult]) -> tuple[str, str]:
        """
        Compute overall status with degraded tracking.
        
        Priority:
        1. CRITICAL errors → FAILED
        2. Any failures → PARTIAL
        3. Any degraded (fallback used) → DEGRADED
        4. Any warnings → WARNING
        5. All success → SUCCESS
        """
        # Check for critical errors
        if any(r.has_critical_errors() for r in results):
            return ExecutionStatus.FAILED.value, PhaseSeverity.CRITICAL.value
        
        # Check for failures
        if any(r.status == ExecutionStatus.FAILED.value for r in results):
            return ExecutionStatus.PARTIAL.value, PhaseSeverity.ERROR.value
        
        # ✨ Check for degraded (fallback used)
        if any(r.status == ExecutionStatus.DEGRADED.value for r in results):
            return ExecutionStatus.DEGRADED.value, PhaseSeverity.WARNING.value
        
        # Check for warnings
        if any(r.severity == PhaseSeverity.WARNING.value for r in results):
            return ExecutionStatus.WARNING.value, PhaseSeverity.WARNING.value
        
        # All good
        return ExecutionStatus.SUCCESS.value, PhaseSeverity.INFO.value

# ============================================
# UTILITY FUNCTIONS
# ============================================
def print_execution_summary(final_result):
    # Print execution tree for visibility
    print("\n" + "="*60)
    print("EXECUTION TREE")
    print("="*60)
    print_execution_tree(final_result)
    print("="*60 + "\n")
    
    # Print analysis
    analysis = analyze_execution(final_result)
    print("EXECUTION ANALYSIS:")
    print(f"  Status: {analysis['status']}")
    print(f"  Duration: {analysis['duration']:.2f}s")
    print(f"  Complete: {analysis['complete']}")
    print(f"  All Successful: {analysis['all_successful']}")
    print(f"  Statistics: {analysis['statistics']}")
    if analysis['failed_paths']:
        print(f"  Failed Paths: {analysis['failed_paths']}")
    print("="*60 + "\n")

def print_execution_tree(result: ExecutionResult, indent: int = 0) -> None:
    """Print execution tree with degraded status indicator"""
    prefix = "  " * indent
    icon = "📦" if result.type == "agent" else "⚙️"
    
    status_icons = {
        ExecutionStatus.SUCCESS.value: "✓",
        ExecutionStatus.DEGRADED.value: "⚠️",  # ✨ New icon
        ExecutionStatus.WARNING.value: "⚡",
        ExecutionStatus.FAILED.value: "✗",
        ExecutionStatus.SKIPPED.value: "⊘",
        ExecutionStatus.PARTIAL.value: "◐"
    }
    status_icon = status_icons.get(result.status, "?")
    
    severity_colors = {
        PhaseSeverity.CRITICAL.value: "🔴",
        PhaseSeverity.ERROR.value: "🟠",
        PhaseSeverity.WARNING.value: "🟡",
        PhaseSeverity.INFO.value: ""
    }
    severity_icon = severity_colors.get(result.severity, "")
    
    # Show fallback indicator
    fallback_indicator = ""
    if result.data.get("fallback_used"):
        fallback_indicator = " [FALLBACK]"
    
    print(
        f"{prefix}{icon} {result.name} {status_icon}{fallback_indicator} "
        f"{severity_icon} ({result.duration:.2f}s)"
    )
    
    # Show original error if fallback was used
    if result.data.get("fallback_used"):
        original_error = result.data.get("original_error", "Unknown")
        print(f"{prefix}   └─ Recovered from: {original_error}")
    
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

def generate_execution_tree_as_str(result: ExecutionResult) -> str:
    """Generate a string representation of the execution tree."""   
    import io
    import sys
    old_stdout = sys.stdout
    sys.stdout = buffer = io.StringIO()
    print_execution_tree(result)
    sys.stdout = old_stdout
    return "\n".join(["EXECUTION TREE:", buffer.getvalue()])

def update_change_log(agent_id: str,
                      config_header: str,
                      result: ExecutionResult,
                      summary: str,
                      export_log: str, 
                      log_path: str | Path) -> str:
        
    """Generate change log content."""

    try:  
        # Initialize validation log entries for entire processing run
        log_content = [
            "=" * 60,
            config_header,
            "--Processing Summary--",
            f"⤷ {agent_id} results:",
            generate_execution_tree_as_str(result),
            generate_summary_export_log(summary, export_log),
        ]
        log_str = "\n".join(log_content)
        logger.info("✓ Change log generated successfully")
        message = append_change_log(log_path, log_str)
        return message
        
    except Exception as e:
        logger.error("✗ Failed to generate change log: {}", e)
        raise

def generate_summary_export_log(summary: str, export_log: str) -> str:
    """Generate a summary export log string."""
    log_content = [
        "="*60,
        "--Summary & Export Log--",
        "",
        "SUMMARY:",
        summary,
        "",
        "EXPORT LOG:",
        export_log,
        "",
        "="*60,
        ""
    ]
    return "\n".join(log_content)

def append_change_log(log_path: str | Path, log_str: str) -> str:
    """
    Append a change log string to a file.

    Args:
        log_path: Path to the log file.
        log_str: Content to append (must be non-empty).

    Returns:
        Confirmation message.

    Raises:
        ValueError: If log_str is empty or whitespace.
        OSError: If writing to file fails.
    """
    if not log_str or not log_str.strip():
        logger.error("❌ Nothing to append. Log string is empty.")
        raise ValueError("Log string must not be empty.")
    log_path = Path(log_path)
    try:
        with log_path.open("a", encoding="utf-8") as f:
            f.write(log_str.rstrip() + "\n")
        message = f"✓ Updated and saved change log: {log_path}"
        logger.info(message)
        return message
    except OSError as e:
        logger.error("✗ Failed to save change log {}: {}", log_path, e)
        raise 