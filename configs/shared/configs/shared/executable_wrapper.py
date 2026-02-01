# configs/shared/executable_wrapper.py
"""
Unified ExecutableWrapper for use across all agents.

This wrapper allows agents/services that return ExecutionResult to be 
composed using CompositeAgent pattern.
"""

from typing import Callable
from datetime import datetime
import traceback
from loguru import logger

from configs.shared.agent_report_format import (
    Executable,
    ExecutionResult,
    ExecutionStatus,
    PhaseSeverity
)


class ExecutableWrapper(Executable):
    """
    Wraps a component (analyzer/service/etc) that returns ExecutionResult.
    Allows CompositeAgent to orchestrate components seamlessly.
    
    This is a bridge between the Executable interface and components that
    already return ExecutionResult objects.
    
    Usage:
        # For analyzers
        wrapper = ExecutableWrapper(
            name="HardwareChangeAnalyzer",
            factory=lambda: HardwareChangeAnalyzer(config).run_analyzing()
        )
        
        # For services
        wrapper = ExecutableWrapper(
            name="VisualizationService",
            factory=lambda: VisualizationService(config).run_visualizing()
        )
    """
    
    def __init__(self, 
                 name: str,
                 factory: Callable[[], ExecutionResult],
                 on_error_severity: str = PhaseSeverity.CRITICAL.value):
        """
        Args:
            name: Name for this executable (will appear in execution tree)
            factory: Function that creates and runs the component.
                    Must return ExecutionResult.
            on_error_severity: Severity level if component crashes unexpectedly
        """
        self.name = name
        self.factory = factory
        self.on_error_severity = on_error_severity
    
    def get_name(self) -> str:
        return self.name
    
    def execute(self) -> ExecutionResult:
        """
        Execute component and return its ExecutionResult directly.
        
        Returns:
            ExecutionResult from component, or a failed ExecutionResult
            if the component crashes unexpectedly
        """
        start_time = datetime.now()
        
        try:
            logger.info(f"🔄 Executing {self.name}...")
            
            # Call the factory function
            result = self.factory()
            
            # Validate that we got an ExecutionResult
            if not isinstance(result, ExecutionResult):
                raise TypeError(
                    f"{self.name} must return ExecutionResult, "
                    f"got {type(result).__name__}"
                )
            
            logger.info(
                f"✓ {self.name} completed: {result.status} "
                f"in {result.duration:.2f}s"
            )
            
            return result
            
        except Exception as e:
            # If component crashes, wrap in failed ExecutionResult
            duration = (datetime.now() - start_time).total_seconds()
            logger.error(f"❌ {self.name} crashed: {e}")
            
            return ExecutionResult(
                name=self.name,
                type="agent",  # Wrapped components are treated as agents
                status=ExecutionStatus.FAILED.value,
                duration=duration,
                severity=self.on_error_severity,
                error=f"Component crashed: {str(e)}",
                traceback=traceback.format_exc(),
                metadata={
                    "crash_type": type(e).__name__,
                    "crash_message": str(e)
                }
            )