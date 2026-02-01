from loguru import logger
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import List, Optional
import traceback
from configs.shared.config_report_format import ConfigReportMixin
from configs.shared.dict_based_report_generator import DictBasedReportGenerator
from agents.dashboardBuilder.dashboard_builder_config import ComponentConfig, DashboardBuilderConfig

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

# Import unified ExecutableWrapper
from configs.shared.executable_wrapper import ExecutableWrapper

# ============================================
# DASHBOARD BUILDER
# ============================================
class DashboardBuilder(ConfigReportMixin):
    """
    Orchestrates visualization services using data from AnalyticsOrchestrator.
    
    Key improvements:
    - Uses ExecutableWrapper to bridge services into Executable interface
    - No wrapper phases needed
    - Clean execution tree structure
    - Properly handles data dependency from AnalyticsOrchestrator
    """

    REQUIRED_FIELDS = {
        'config': {
            'shared_source_config': {
                'annotation_path': str,
                'databaseSchemas_path': str,
                'multi_level_performance_visualization_service_dir': str,
                'multi_level_performance_visualization_service_log_path': str,
                'day_level_visualization_pipeline_dir': str,
                'day_level_visualization_pipeline_log_path': str,
                'month_level_visualization_pipeline_dir': str,
                'month_level_visualization_pipeline_log_path': str,
                'year_level_visualization_pipeline_dir': str,
                'year_level_visualization_pipeline_log_path': str,
                'hardware_change_visualization_service_dir': str,
                'hardware_change_visualization_service_log_path': str,
                'machine_layout_visualization_pipeline_dir': str,
                'machine_layout_visualization_pipeline_change_log_path': str,
                'mold_machine_pair_visualization_pipeline_dir': str,
                'mold_machine_pair_visualization_pipeline_change_log_path': str,
                'dashboard_builder_log_path': str
                },
            'machine_layout_visualization_service': {
                'enabled': bool,
                'save_result': bool
                },
            'mold_machine_pair_visualization_service': {
                'enabled': bool,
                'save_result': bool
                },

            'day_level_visualization_service': {
                'enabled': bool,
                'save_result': bool,
                'requested_timestamp': bool,
                },
            'month_level_visualization_service': {
                'enabled': bool,
                'save_result': bool,
                'requested_timestamp': bool,
                'analysis_date': bool
                },
            'year_level_visualization_service': {
                'enabled': bool,
                'save_result': bool,
                'requested_timestamp': bool,
                'analysis_date': bool
                },
        
            'save_builder_log': bool
            }
        }

    def __init__(self, 
                 config: DashboardBuilderConfig):
        
        """
        Initialize DashboardBuilder with configuration.
        
        Args:        
            config: DashboardBuilderConfig containing processing parameters
        """
        
        # Capture initialization arguments for reporting
        self._capture_init_args()

        # Initialize logger with class name for better tracking
        self.logger = logger.bind(class_="DashboardBuilder")

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
        
        # Store orchestrator result for visualization services
        self._orchestrator_result: Optional[ExecutionResult] = None

    def build_dashboard(self) -> ExecutionResult:
        """
        Execute the complete dashboard builder pipeline.
        
        This method:
        1. Runs AnalyticsOrchestrator to get analysis data
        2. Creates ExecutableWrappers for each enabled visualization service
        3. Uses CompositeAgent to execute them with automatic aggregation
        4. Saves pipeline log if requested
        5. Returns unified ExecutionResult
        
        Returns:
            ExecutionResult containing all sub-service results
        """
        
        self.logger.info("Starting DashboardBuilder ...")

        agent_id = self.__class__.__name__

        timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        config_header = self._generate_config_report(timestamp_str, required_only=True)
        
        # ============================================
        # STEP 1: RUN ANALYTICS ORCHESTRATOR
        # ============================================
        if self.config.enable_analytics_orchestrator:
            self.logger.info("📊 Running AnalyticsOrchestrator to generate data...")
            
            try:
                from agents.analyticsOrchestrator.analytics_orchestrator import AnalyticsOrchestrator
                orchestrator = AnalyticsOrchestrator(
                    config=self.config.get_analytics_orchestrator_config()
                )
                self._orchestrator_result = orchestrator.run_analyzing()
                
                self.logger.info(
                    f"✓ AnalyticsOrchestrator completed: {self._orchestrator_result.status}"
                )
                
                # Check if orchestrator failed critically
                if self._orchestrator_result.has_critical_errors():
                    self.logger.error(
                        "❌ AnalyticsOrchestrator failed critically - "
                        "cannot proceed with visualization"
                    )
                    return ExecutionResult(
                        name="DashboardBuilder",
                        type="agent",
                        status=ExecutionStatus.FAILED.value,
                        duration=self._orchestrator_result.duration,
                        severity=PhaseSeverity.CRITICAL.value,
                        error="AnalyticsOrchestrator failed critically",
                        metadata={
                            "orchestrator_status": self._orchestrator_result.status,
                            "orchestrator_errors": self._orchestrator_result.get_failed_paths()
                        }
                    )
                
            except Exception as e:
                self.logger.error(f"❌ Failed to run AnalyticsOrchestrator: {e}")
                return ExecutionResult(
                    name="DashboardBuilder",
                    type="agent",
                    status=ExecutionStatus.FAILED.value,
                    duration=0.0,
                    severity=PhaseSeverity.CRITICAL.value,
                    error=f"Failed to run AnalyticsOrchestrator: {str(e)}",
                    traceback=traceback.format_exc()
                )
        else:
            self.logger.warning(
                "⚠️ AnalyticsOrchestrator is disabled - "
                "no data available for visualization"
            )
            return ExecutionResult(
                name="DashboardBuilder",
                type="agent",
                status=ExecutionStatus.SKIPPED.value,
                duration=0.0,
                severity=PhaseSeverity.WARNING.value,
                skipped_reason="AnalyticsOrchestrator disabled in configuration"
            )
        
        # ============================================
        # STEP 2: BUILD VISUALIZATION SERVICE LIST
        # ============================================
        executables: List[Executable] = []
        
        # Service 1: Hardware Change Visualization (wrapped)
        if self.config.enable_change_visualization_service:
            def run_hardware_visualization() -> ExecutionResult:
                """Factory function to create and run HardwareChangeVisualizationService"""
                from agents.dashboardBuilder.visualizationServices.hardware_change_visualization import HardwareChangeVisualizationService
                
                # Extract data from orchestrator result
                hardware_data = self._orchestrator_result.get_path("HardwareChangeAnalyzer")
                
                if hardware_data is None:
                    self.logger.warning(
                        "⚠️ HardwareChangeAnalyzer data not found in orchestrator result"
                    )
                    return ExecutionResult(
                        name="HardwareChangeVisualizationService",
                        type="agent",
                        status=ExecutionStatus.SKIPPED.value,
                        duration=0.0,
                        severity=PhaseSeverity.WARNING.value,
                        skipped_reason="HardwareChangeAnalyzer data not available"
                    )
                
                service = HardwareChangeVisualizationService(
                    config=self.config.get_change_visualization_config(),
                    data=hardware_data
                )
                return service.run_visualizing()
            
            executables.append(
                ExecutableWrapper(
                    name="HardwareChangeVisualizationService",
                    factory=run_hardware_visualization,
                    on_error_severity=PhaseSeverity.ERROR.value  # Non-critical
                )
            )
            self.logger.info("✓ HardwareChangeVisualizationService enabled")
        
        # Service 2: Multi-Level Performance Visualization (wrapped)
        if self.config.enable_performance_visualization_service:
            def run_performance_visualization() -> ExecutionResult:
                """Factory function to create and run MultiLevelPerformanceVisualizationService"""
                from agents.dashboardBuilder.visualizationServices.multi_level_performance_visualization import MultiLevelPerformanceVisualizationService
                
                # Extract data from orchestrator result
                performance_data = self._orchestrator_result.get_path("MultiLevelPerformanceAnalyzer")
                
                if performance_data is None:
                    self.logger.warning(
                        "⚠️ MultiLevelPerformanceAnalyzer data not found in orchestrator result"
                    )
                    return ExecutionResult(
                        name="MultiLevelPerformanceVisualizationService",
                        type="agent",
                        status=ExecutionStatus.SKIPPED.value,
                        duration=0.0,
                        severity=PhaseSeverity.WARNING.value,
                        skipped_reason="MultiLevelPerformanceAnalyzer data not available"
                    )
                
                service = MultiLevelPerformanceVisualizationService(
                    config=self.config.get_performance_visualization_config(),
                    data=performance_data
                )
                return service.run_visualizing()
            
            executables.append(
                ExecutableWrapper(
                    name="MultiLevelPerformanceVisualizationService",
                    factory=run_performance_visualization,
                    on_error_severity=PhaseSeverity.ERROR.value  # Non-critical
                )
            )
            self.logger.info("✓ MultiLevelPerformanceVisualizationService enabled")
        
        # Check if any services are enabled
        if not executables:
            self.logger.warning("⚠️ No visualization services enabled!")
            return ExecutionResult(
                name="DashboardBuilder",
                type="agent",
                status=ExecutionStatus.SKIPPED.value,
                duration=0.0,
                severity=PhaseSeverity.WARNING.value,
                skipped_reason="No visualization services enabled in configuration",
                metadata={
                    "enable_change_visualization_service": self.config.enable_change_visualization_service,
                    "enable_performance_visualization_service": self.config.enable_performance_visualization_service
                }
            )
        
        # ============================================
        # STEP 3: EXECUTE USING COMPOSITE AGENT
        # ============================================
        self.logger.info(f"🚀 Executing {len(executables)} visualization service(s)...")
        
        agent = CompositeAgent("DashboardBuilder", executables)
        result = agent.execute()
        
        # ============================================
        # STEP 4: SAVE PIPELINE LOG IF REQUESTED
        # ============================================
        if self.config.save_builder_log:
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
                    Path(self.config.shared_source_config.dashboard_builder_log_path)
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
        # STEP 5: PRINT EXECUTION TREE & ANALYSIS
        # ============================================
        self.logger.info(
            "✅ DashboardBuilder completed in {:.2f}s! Status: {}",
            result.duration,
            result.status
        )
        
        # Print execution tree for visibility
        print_execution_summary(result)
        
        return result