# configs/shared/agent_report_format.py

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, TypedDict, Callable, Tuple
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

class SaveDecision(Enum):
    """Why a phase result was saved or skipped"""
    SAVED = "saved"
    SKIPPED_NO_RESULT = "skipped_no_result"
    SKIPPED_NOT_ROUTED = "skipped_not_routed"
    SKIPPED_DISABLED = "skipped_disabled"
    SKIPPED_NOT_SAVABLE = "skipped_not_savable"
    SKIPPED_DISABLED_SAVABLE = "skipped_disabled_savable"
    SKIPPED_NO_SAVE_FN = "skipped_no_save_fn"
    SKIPPED_INVALID_PATHS = "skipped_invalid_paths"  # ✨ New
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
        if self.severity == PhaseSeverity.CRITICAL.value:
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
    
    def get_path(self, path: str) -> Optional['ExecutionResult']:
        """
        Get nested result by dot-separated path.
        Automatically handles nested payloads.
        
        Args:
            path: Dot-separated path like "Agent.SubAgent.Phase"
            
        Returns:
            ExecutionResult if found, None otherwise
            
        Example:
            >>> tracker = result.get_path("HardwareChangeAnalyzer.MachineLayoutTracker")
            >>> payload = tracker.data['result']['payload']
        """
        parts = path.split('.')
        current = self
        
        for part in parts:
            # Try sub_results first
            next_node = next(
                (r for r in current.sub_results if r.name == part), 
                None
            )
            
            # If not found, try diving into payload
            if next_node is None and hasattr(current, 'data'):
                payload = current.data.get('result', {}).get('payload')
                # Duck typing: check if payload has sub_results
                if hasattr(payload, 'sub_results'):
                    next_node = next(
                        (r for r in payload.sub_results if r.name == part),
                        None
                    )
            
            if next_node is None:
                logger.warning(f"Path not found: {path} (stopped at {part})")
                return None
            
            current = next_node
        
        return current
    
    def get_path_data(self, path: str, *keys) -> Any:
        """
        Get data from nested result by path.
        
        Args:
            path: Dot-separated path to result
            *keys: Keys to traverse in data dict
            
        Returns:
            Value if found, None otherwise
            
        Example:
            >>> payload = result.get_path_data(
            ...     "HardwareChangeAnalyzer.MachineLayoutTracker",
            ...     'result', 'payload'
            ... )
            >>> # Equivalent to:
            >>> # result.get_path("...").data['result']['payload']
        """
        node = self.get_path(path)
        if node is None:
            return None
        
        data = node.data
        for key in keys:
            if not isinstance(data, dict):
                return None
            data = data.get(key)
            if data is None:
                return None
        
        return data
    
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
class SaveRoute(TypedDict, total=False):
    """Configuration for saving a phase result"""
    enabled: bool
    savable: bool
    should_save: bool
    save_fn: Optional[Callable[[Dict], Dict]]
    input_dict: Optional[Dict]

@dataclass
class SaveResult:
    """Result of attempting to save a phase"""
    decision: SaveDecision
    message: str
    metadata: Optional[Dict] = None
    error: Optional[Exception] = None
    log_entries: list[str] = field(default_factory=list)
    
    def add_log(self, msg: str) -> None:
        """Add log entry and update message"""
        self.log_entries.append(msg)
        self.message = "\n".join(self.log_entries)

# ============================================
# PRINT EXECUTION SUMMARY
# ============================================
def print_execution_summary(final_result: ExecutionResult) -> None:
    """Print execution summary (thin wrapper for logging)"""
    print(format_execution_summary(final_result))

def format_execution_summary(final_result: ExecutionResult) -> str:
    """Format complete execution summary as string"""
    analysis = analyze_execution(final_result)
    
    lines = [
        "=" * 60,
        "EXECUTION TREE",
        "=" * 60,
        format_execution_tree(final_result),
        "=" * 60,
        "",
        "EXECUTION ANALYSIS:",
        f"  Status: {analysis['status']}",
        f"  Duration: {analysis['duration']:.2f}s",
        f"  Complete: {analysis['complete']}",
        f"  All Successful: {analysis['all_successful']}",
        f"  Statistics: {analysis['statistics']}"
    ]
    
    if analysis['failed_paths']:
        lines.append(f"  Failed Paths: {analysis['failed_paths']}")
    
    lines.append("=" * 60)
    return "\n".join(lines)

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

def format_execution_tree(result: ExecutionResult, 
                          indent: int = 0) -> str:
    """Format execution tree as string (pure function)"""
    lines = []
    prefix = "  " * indent
    icon = "📦" if result.type == "agent" else "⚙️"
    
    status_icons = {
        ExecutionStatus.SUCCESS.value: "✓",
        ExecutionStatus.DEGRADED.value: "⚠️",
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
    
    fallback_indicator = " [FALLBACK]" if result.data.get("fallback_used") else ""
    
    lines.append(
        f"{prefix}{icon} {result.name} {status_icon}{fallback_indicator} "
        f"{severity_icon} ({result.duration:.2f}s)"
    )
    
    if result.data.get("fallback_used"):
        original_error = result.data.get("original_error", "Unknown")
        lines.append(f"{prefix}   └─ Recovered from: {original_error}")
    
    if result.error:
        lines.append(f"{prefix}   └─ Error: {result.error}")
    
    for sub in result.sub_results:
        lines.append(format_execution_tree(sub, indent + 1))
    
    return "\n".join(lines)

# ============================================
# SAVE PHASE RESULTS
# ============================================
def save_result(save_routing: Dict[str, SaveRoute],
                result: 'ExecutionResult'
                ) -> Tuple[Dict[str, SaveRoute], Dict[str, Dict]]:
    """
    Save phase results based on routing configuration.
    
    Args:
        save_routing: Mapping of phase names to save configurations.
                      Will be modified in-place to add runtime state.
    
    Returns:
        Tuple of:
        - save_routing: Updated with runtime state for each phase:
            - savable (bool): Whether phase result is savable
            - phase_result (dict): Payload from phase execution
            - should_save (bool): Final decision to save
            - save_input_dict (dict, optional): Input passed to save_fn if saved
        - export_metadata: Summary of save outcomes per phase
    
    Note:
        save_routing is modified in-place. Config fields (enabled, save_fn, 
        save_paths) remain unchanged, but runtime fields are added.
    """
    export_metadata = {}
    
    for phase_result in result.sub_results:
        phase_name = phase_result.name
        
        # Skip if not in routing
        if phase_name not in save_routing:
            logger.debug(f"[SAVE][{phase_name}] skipped: not in save_routing")
            continue
        
        # Initialize export metadata
        export_metadata[phase_name] = {
            "metadata": None,
            "export_log": None,
        }
        
        route = save_routing[phase_name]
        
        # Process save
        save_outcome = process_phase_save(phase_name, phase_result, route)
        
        # Record outcome
        export_metadata[phase_name]["metadata"] = save_outcome.metadata
        export_metadata[phase_name]["export_log"] = save_outcome.message

    return save_routing, export_metadata

def process_phase_save(phase_name: str,
                       phase_result: 'ExecutionResult',
                       route: SaveRoute
                       ) -> SaveResult:
    """
    Process save logic for a single phase.
    
    Args:
        phase_name: Name of the phase
        phase_result: ExecutionResult from phase execution
        route: Save routing configuration
    
    Returns:
        SaveResult with outcome and logs
    """
    # Extract result data from phase
    result_data = (phase_result.data or {}).get("result", {})

    if not result_data:
        msg = f"[SAVE][{phase_name}] skipped: result is not available"
        logger.warning(msg)
        return SaveResult(
            decision=SaveDecision.SKIPPED_NO_RESULT,
            message=msg,
            log_entries=[msg],
            metadata={
                'status': 'skipped', 
                'reason': 'no_result'}
        )
    
    # Update route with runtime flags
    route["savable"] = result_data.get("savable", False)
    route["phase_result"] = result_data.get("payload", {})

    # Determine if should save
    enabled = route.get("enabled", False)
    savable = route.get("savable", False)
    should_save, decision, reason = evaluate_save_flags(enabled, savable)
    
    if not should_save:
        msg = f"[SAVE][{phase_name}] skipped: {reason}"
        log_level = logger.warning if enabled and not savable else logger.info
        log_level(msg)
        route["should_save"] = False
        return SaveResult(
            decision=decision,
            message=msg,
            log_entries=[msg],
            metadata={
                'status': 'skipped',
                'reason': reason,
                'enabled': enabled,
                'savable': savable
            }
        )
    
    # Validate paths early
    save_paths = route.get("save_paths", {})
    paths_valid, path_error, validated_paths = validate_save_paths(save_paths)
    
    if not paths_valid:
        msg = f"[SAVE][{phase_name}] skipped: invalid paths - {path_error}"
        logger.warning(msg)
        route["should_save"] = False
        return SaveResult(
            decision=SaveDecision.SKIPPED_INVALID_PATHS,  # ✨ New decision
            message=msg,
            log_entries=[msg],
            metadata={
                'status': 'skipped',
                'reason': 'invalid_paths',
                'error': path_error
            }
        )
    
    # Validate save function
    save_fn = route.get("save_fn")
    if not callable(save_fn):
        msg = f"[SAVE][{phase_name}] skipped: save_fn is not callable"
        logger.warning(msg)
        route["should_save"] = False
        return SaveResult(
            decision=SaveDecision.SKIPPED_NO_SAVE_FN,
            message=msg,
            log_entries=[msg],
            metadata={
                'status': 'skipped',
                'reason': 'no_save_fn'
            }
        )
    
    # Execute save
    # Build save input dict with validated paths
    save_input_dict = {
        "name": phase_result.name,
        "status": phase_result.status,
        "result": result_data.get("payload", {}),
        "execution_summary": format_execution_summary(phase_result),
        "output_dir": validated_paths["output_dir"],
        "change_log_path": validated_paths["change_log_path"],
        "change_log_header": route.get("change_log_header", "")
    }

    # Update route with save decision
    route["should_save"] = True
    route["save_input_dict"] = save_input_dict 

    acceptance_msg = f"[SAVE][{phase_name}] accepted: {reason}"
    logger.info(acceptance_msg)
    
    save_outcome = save_phase_result(
        phase_name,
        route["save_input_dict"],
        save_fn
    )
    
    # Prepend acceptance message
    save_outcome.add_log(acceptance_msg)
    
    return save_outcome

def validate_save_paths(save_paths: Dict[str, Any]
                        ) -> Tuple[bool, Optional[str], Dict[str, Path]]:
    """Simple path validation - just convert and check not None"""
    if not save_paths:
        return False, "save_paths not provided", {}
    
    required = ["output_dir", "change_log_path"]
    validated = {}
    
    for key in required:
        if key not in save_paths or save_paths[key] is None:
            return False, f"missing or None: {key}", {}
        
        try:
            path = Path(save_paths[key])
            # Create parent dirs
            if key.endswith("_dir"):
                path.mkdir(parents=True, exist_ok=True)
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
            
            validated[key] = path
        except Exception as e:
            return False, f"invalid {key}: {e}", {}
    
    return True, None, validated

def evaluate_save_flags(enabled: bool, 
                        savable: bool
                        ) -> Tuple[bool, SaveDecision, str]:
    """
    Determine if phase should be saved based on configuration flags.
    
    Args:
        enabled: Whether saving is enabled by user input
        savable: Whether phase allows saving
    
    Returns:
        (should_save, decision_reason, human_readable_message)
    """
    if not enabled and not savable:
        return (
            False,
            SaveDecision.SKIPPED_DISABLED,
            "disabled by input & not savable by phase"
        )
    
    if not enabled and savable:
        return (
            False,
            SaveDecision.SKIPPED_DISABLED_SAVABLE,
            "disabled by input (phase allows saving)"
        )
    
    if enabled and not savable:
        return (
            False,
            SaveDecision.SKIPPED_NOT_SAVABLE,
            "enabled by input but phase marked unsavable"
        )
    
    return (
        True,
        SaveDecision.SAVED,
        "enabled by input & savable by phase"
    )

def save_phase_result(phase_name: str,
                      phase_data: Dict,
                      save_fn: Callable[[Dict], Dict]
                      ) -> SaveResult:
    """
    Execute save function for a phase.
    
    Args:
        phase_name: Name of the phase being saved
        phase_data: Processed phase data dict with keys:
            - name: Phase name
            - status: Execution status
            - result: Payload data
            - execution_summary: Formatted summary
        save_fn: Save function that processes phase_data
    
    Returns:
        SaveResult with outcome and metadata
    """

    try:
        # Call user-provided save_fn
        metadata = save_fn(phase_data)
        status = metadata.get('status', 'unknown')
        
        # Check if save reported failure
        if status == 'failed':
            return SaveResult(
                decision=SaveDecision.FAILED,
                message=metadata.get('export_log', f"[SAVE][{phase_name}] failed"),
                metadata=metadata,
                log_entries=[f"[SAVE][{phase_name}] failed: {metadata.get('export_log')}"]
            )
        
        # ✨ Handle business logic skips (no changes, etc.)
        elif status.startswith('skipped'):
            reason = metadata.get('reason', status.replace('skipped_', ''))
            return SaveResult(
                decision=SaveDecision.SKIPPED_NO_RESULT,
                message=metadata.get('export_log', f"[SAVE][{phase_name}] skipped: {reason}"),
                metadata=metadata,
                log_entries=[f"[SAVE][{phase_name}] ⊘ skipped: {reason}"]
            )
        
        elif status == 'success':
            return SaveResult(
                decision=SaveDecision.SAVED,
                message=metadata.get('export_log', f"[SAVE][{phase_name}] succeeded"),
                metadata=metadata,
                log_entries=[f"[SAVE][{phase_name}] completed"]
            )
        
        else:
            logger.warning(f"Unknown save status '{status}' for {phase_name}")
            return SaveResult(
                decision=SaveDecision.SAVED,
                message=metadata.get('export_log', f"Completed (status: {status})"),
                metadata=metadata,
                log_entries=[f"[SAVE][{phase_name}] ⚠️ {status}"]
            )
        
    except Exception as e:
        # Catch unexpected exceptions from save_fn
        error_msg = f"Exception in save_fn: {str(e)}"
        logger.error(f"[SAVE][{phase_name}] {error_msg}", exc_info=True)
        
        return SaveResult(
            decision=SaveDecision.FAILED,
            message=error_msg,
            metadata={
                'status': 'failed',
                'export_log': error_msg,
                'error': str(e)
            },
            log_entries=[f"[SAVE][{phase_name}] exception: {error_msg}"]
        )

def update_change_log(agent_id: str,
                      config_header: str,
                      format_execution_tree: str,
                      summary: str,
                      export_log: str,
                      log_path: str | Path) -> str:
    """Update change log file with new entry"""
    try:
        log_content = format_change_log_entry(
            agent_id, config_header, format_execution_tree, summary, export_log)
        logger.info("✓ Change log generated successfully")
        return append_change_log(log_path, log_content)
    except Exception as e:
        logger.error("✗ Failed to generate change log: {}", e)
        raise

def format_change_log_entry(agent_id: str,
                            config_header: str,
                            format_execution_tree: str,
                            summary: str,
                            export_log: str) -> str:
    """Generate change log content as string"""
    sections = [
        "=" * 60,
        config_header,
        "",
        "--Processing Summary--",
        "",
        f"⤷ {agent_id} results:",
        "",
        "EXECUTION TREE:",
        "",
        format_execution_tree,
        "=" * 60,
        "",
        "--Summary & Export Log--",
        "",
        "SUMMARY:",
        "",
        summary,
        "",
        "EXPORT LOG:",
        "",
        export_log,
        "",
        "=" * 60,
        ""
    ]
    return "\n".join(sections)

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
    log_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with log_path.open("a", encoding="utf-8") as f:
            f.write(log_str.rstrip() + "\n")
        message = f"✓ Updated and saved change log: {log_path}"
        logger.info(message)
        return message
    except OSError as e:
        logger.error("✗ Failed to save change log {}: {}", log_path, e)
        raise 

def format_export_logs(export_metadata: Dict[str, Dict]) -> List[str]:
    """
    Format export metadata into readable log lines.
    
    Args:
        export_metadata: Dictionary mapping phase names to export results:
            {
                "phase_name": {
                    "metadata": {"status": "success", ...},
                    "export_log": "..."
                }
            }
    
    Returns:
        List of formatted log lines ready to append to pipeline logs
    """
    log_lines = []
    
    # Status to icon/label mapping
    status_map = {
        'success': ('✅', 'success'),
        'failed': ('❌', 'failed'),
        'skipped_no_changes': ('⊘', 'no changes'),
        'skipped': ('⊘', 'skipped'),
        'unknown': ('⚠️', 'unknown')
    }
    
    for phase_name, phase_export in export_metadata.items():
        phase_metadata = phase_export.get('metadata') or {}
        status = phase_metadata.get('status', 'unknown')
        
        # Get icon and label for status
        icon, label = status_map.get(status, ('❓', status))
        
        # Header with status
        log_lines.append(f"⤷ Phase: {phase_name} {icon} {label}")
        
        # Export log details (indented)
        export_log = phase_export.get('export_log', 'No export log')
        for line in export_log.split('\n'):
            if line.strip():
                log_lines.append(f"  {line}")
    
    return log_lines

def extract_export_metadata(result: ExecutionResult):
    """Recursively extract with nested structure"""

    def extract_single_phase_metadata(phase_detail):
        try:
            if not hasattr(phase_detail, 'metadata'):
                return f"⚠️ No metadata attribute"
            export_metadata = phase_detail.metadata.get('export_metadata')
            if not export_metadata:
                return f"⚠️ No export_metadata"
            return export_metadata
        except Exception as e:
            return f"❌ {type(e).__name__}: {e}"
        
    all_export_metadata = {}

    for phase_detail in result.sub_results:

        all_export_metadata[phase_detail.name] = extract_single_phase_metadata(phase_detail)
        
    return all_export_metadata