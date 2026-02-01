from loguru import logger
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Callable
import traceback
from configs.shared.config_report_format import ConfigReportMixin
from agents.analyticsOrchestrator.analytics_orchestrator_config import ComponentConfig, AnalyticsOrchestratorConfig
from configs.shared.dict_based_report_generator import DictBasedReportGenerator

# Import agent report format components
from configs.shared.agent_report_format import (
    Executable,
    ExecutionResult,
    ExecutionStatus,
    PhaseSeverity,
    CompositeAgent,
    print_execution_summary,
    format_execution_tree,
    update_change_log,
    extract_export_metadata)

# ============================================
# EXECUTABLE WRAPPER - Bridge pattern
# ============================================
class ExecutableWrapper(Executable):
    """
    Wraps an analyzer that returns ExecutionResult.
    Allows CompositeAgent to orchestrate analyzers seamlessly.
    
    This is a bridge between the Executable interface and analyzers that
    already return ExecutionResult objects.
    """
    
    def __init__(self, 
                 name: str,
                 analyzer_factory: Callable[[], ExecutionResult],
                 on_error_severity: str = PhaseSeverity.CRITICAL.value):
        """
        Args:
            name: Name for this executable (will appear in execution tree)
            analyzer_factory: Function that creates and runs analyzer.
                             Must return ExecutionResult.
            on_error_severity: Severity level if analyzer crashes unexpectedly
        """
        self.name = name
        self.analyzer_factory = analyzer_factory
        self.on_error_severity = on_error_severity
    
    def get_name(self) -> str:
        return self.name
    
    def execute(self) -> ExecutionResult:
        """
        Execute analyzer and return its ExecutionResult directly.
        
        Returns:
            ExecutionResult from analyzer, or a failed ExecutionResult
            if the analyzer crashes unexpectedly
        """
        start_time = datetime.now()
        
        try:
            logger.info(f"🔄 Executing {self.name}...")
            
            # Call the analyzer factory
            result = self.analyzer_factory()
            
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
            # If analyzer crashes, wrap in failed ExecutionResult
            duration = (datetime.now() - start_time).total_seconds()
            logger.error(f"❌ {self.name} crashed: {e}")
            
            return ExecutionResult(
                name=self.name,
                type="agent",  # Wrapped analyzers are treated as agents
                status=ExecutionStatus.FAILED.value,
                duration=duration,
                severity=self.on_error_severity,
                error=f"Analyzer crashed: {str(e)}",
                traceback=traceback.format_exc(),
                metadata={
                    "crash_type": type(e).__name__,
                    "crash_message": str(e)
                }
            )


# ============================================
# ANALYTICS ORCHESTRATOR
# ============================================
class AnalyticsOrchestrator(ConfigReportMixin):
    """
    Orchestrates multiple analytics agents (HardwareChangeAnalyzer, 
    MultiLevelPerformanceAnalyzer, etc.) using CompositeAgent pattern.
    
    Key difference from previous implementation:
    - Uses ExecutableWrapper to bridge analyzers into Executable interface
    - No more nested payload wrapping
    - Clean execution tree structure
    """

    REQUIRED_FIELDS = {
        'config': {
            'shared_source_config': {
                'annotation_path': str,
                'databaseSchemas_path': str,
                'machine_layout_tracker_dir': str,
                'machine_layout_tracker_change_log_path': str,
                'mold_machine_pair_tracker_dir': str,
                'mold_machine_pair_tracker_change_log_path': str,
                'hardware_change_analyzer_log_path': str,
                'day_level_processor_dir': str,
                'day_level_processor_log_path': str,
                'month_level_processor_dir': str,
                'month_level_processor_log_path': str,
                'year_level_processor_dir': str,
                'year_level_processor_log_path': str,
                'multi_level_performance_analyzer_log_path': str,
                'performance_analyzer_constant_config_path': str,
                'analytics_orchestrator_log_path': str
                },

            'machine_layout_tracker': {
                'enabled': bool,
                'save_result': bool
                },
            'mold_machine_pair_tracker': {
                'enabled': bool,
                'save_result': bool
                },

            'day_level_processor': {
                'enabled': bool,
                'save_result': bool,
                'requested_timestamp': bool,
                },
            'month_level_processor': {
                'enabled': bool,
                'save_result': bool,
                'requested_timestamp': bool,
                'analysis_date': bool
                },
            'year_level_processor': {
                'enabled': bool,
                'save_result': bool,
                'requested_timestamp': bool,
                'analysis_date': bool
                },
        
            'save_orchestrator_log': bool
            }
        }

    def __init__(self, 
                 config: AnalyticsOrchestratorConfig):
        
        """
        Initialize AnalyticsOrchestrator with configuration.
        
        Args:        
            config: AnalyticsOrchestratorConfig containing processing parameters, including:
                - shared_source_config: Paths for all sub-components
                - machine_layout_tracker (ComponentConfig): Component config
                - mold_machine_pair_tracker (ComponentConfig): Component config 
                - day_level_processor (ComponentConfig): Component config 
                - month_level_processor (ComponentConfig): Component config
                - year_level_processor (ComponentConfig): Component config
                - save_orchestrator_log (bool): Save orchestrator change log
        """
        
        # Capture initialization arguments for reporting
        self._capture_init_args()

        # Initialize logger with class name for better tracking
        self.logger = logger.bind(class_="AnalyticsOrchestrator")

        # Store configuration
        self.config = config

        # Validate required configs
        is_valid, errors = self.config.shared_source_config.validate_requirements(
            self.REQUIRED_FIELDS['config']['shared_source_config'])
        if not is_valid:
            raise ValueError(
                f"{self.__class__.__name__} config validation failed:\n" +
                "\n".join(f"  - {e}" for e in errors)
            )

    def run_analyzing(self) -> ExecutionResult:
        """
        Execute the complete analytics orchestrator pipeline.
        
        This method:
        1. Creates ExecutableWrappers for each enabled analyzer
        2. Uses CompositeAgent to execute them with automatic aggregation
        3. Saves pipeline log if requested
        4. Returns unified ExecutionResult
        
        Returns:
            ExecutionResult containing all sub-analyzer results
        """
        
        self.logger.info("Starting AnalyticsOrchestrator ...")

        agent_id = self.__class__.__name__

        timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        config_header = self._generate_config_report(timestamp_str, required_only=True)
        
        # ============================================
        # BUILD EXECUTABLE LIST WITH WRAPPERS
        # ============================================
        executables: List[Executable] = []
        
        # 1. Hardware Change Analyzer (wrapped)
        if self.config.enable_change_analysis:
            def run_hardware_analyzer() -> ExecutionResult:
                """Factory function to create and run HardwareChangeAnalyzer"""
                from agents.analyticsOrchestrator.analyzers.hardware_change_analyzer import HardwareChangeAnalyzer
                
                analyzer = HardwareChangeAnalyzer(
                    config=self.config.get_change_analyzer_config()
                )
                return analyzer.run_analyzing()
            
            executables.append(
                ExecutableWrapper(
                    name="HardwareChangeAnalyzer",
                    analyzer_factory=run_hardware_analyzer,
                    on_error_severity=PhaseSeverity.ERROR.value  # Non-critical
                )
            )
            self.logger.info("✓ HardwareChangeAnalyzer enabled")
        
        # 2. Multi-Level Performance Analyzer (wrapped)
        if self.config.enable_performance_analysis:
            def run_performance_analyzer() -> ExecutionResult:
                """Factory function to create and run MultiLevelPerformanceAnalyzer"""
                from agents.analyticsOrchestrator.analyzers.multi_level_performance_analyzer import MultiLevelPerformanceAnalyzer
                
                analyzer = MultiLevelPerformanceAnalyzer(
                    config=self.config.get_performance_analyzer_config()
                )
                return analyzer.run_analyzing()
            
            executables.append(
                ExecutableWrapper(
                    name="MultiLevelPerformanceAnalyzer",
                    analyzer_factory=run_performance_analyzer,
                    on_error_severity=PhaseSeverity.ERROR.value  # Non-critical
                )
            )
            self.logger.info("✓ MultiLevelPerformanceAnalyzer enabled")
        
        # Check if any analyzers are enabled
        if not executables:
            self.logger.warning("⚠️ No analyzers enabled!")
            return ExecutionResult(
                name="AnalyticsOrchestrator",
                type="agent",
                status=ExecutionStatus.SKIPPED.value,
                duration=0.0,
                severity=PhaseSeverity.WARNING.value,
                skipped_reason="No analyzers enabled in configuration",
                metadata={
                    "enable_change_analysis": self.config.enable_change_analysis,
                    "enable_performance_analysis": self.config.enable_performance_analysis
                }
            )
        
        # ============================================
        # EXECUTE USING COMPOSITE AGENT
        # ============================================
        self.logger.info(f"🚀 Executing {len(executables)} analyzer(s)...")
        
        agent = CompositeAgent("AnalyticsOrchestrator", executables)
        result = agent.execute()
        
        # ============================================
        # SAVE PIPELINE LOG IF REQUESTED
        # ============================================
        if self.config.save_orchestrator_log:
            try:
                # Generate summary report
                reporter = DictBasedReportGenerator(use_colors=False)
                summary = "\n".join(reporter.export_report(self.config.get_summary()))
                
                # Extract export metadata from all sub-results
                export_metadata_dict = extract_export_metadata(result)
                export_metadata = "\n".join(reporter.export_report(export_metadata_dict))
                
                # Save pipeline change log
                message = update_change_log(
                    agent_id, 
                    config_header, 
                    format_execution_tree(result), 
                    summary, 
                    export_metadata, 
                    Path(self.config.shared_source_config.analytics_orchestrator_log_path)
                )
                
                self.logger.info(f"📝 {message}")
                
            except Exception as e:
                self.logger.error(f"❌ Failed to save pipeline log: {e}")
                # Don't fail the entire pipeline just because log saving failed
                result.warnings.append({
                    "message": f"Failed to save pipeline log: {str(e)}",
                    "severity": PhaseSeverity.WARNING.value
                })

        # ============================================
        # PRINT EXECUTION TREE & ANALYSIS
        # ============================================
        self.logger.info(
            "✅ AnalyticsOrchestrator completed in {:.2f}s! "
            "Status: {}",
            result.duration,
            result.status
        )
        
        # Print execution tree for visibility
        print_execution_summary(result)
        
        return result