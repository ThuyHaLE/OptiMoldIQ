from loguru import logger
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
from configs.shared.config_report_format import ConfigReportMixin
from configs.shared.dict_based_report_generator import DictBasedReportGenerator
from agents.dashboardBuilder.dashboard_builder_config import ComponentConfig, DashboardBuilderConfig

# Import agent report format components
from configs.shared.agent_report_format import (
    Executable,
    ExecutionResult,
    AtomicPhase,
    CompositeAgent,
    print_execution_summary,
    format_execution_tree,
    update_change_log,
    extract_export_metadata)

# ============================================
# PHASE: HARDWARE CHANGE VISUALIZATION
# ============================================
class  HardwareChangeVisualizationPhase(AtomicPhase):
    """Phase for running the actual hardware change visualization logic"""
    
    RECOVERABLE_ERRORS = (KeyError, ValueError, pd.errors.MergeError)
    CRITICAL_ERRORS = (MemoryError, KeyboardInterrupt)
    FALLBACK_FAILURE_IS_CRITICAL = False
    
    def __init__(self, 
                 config: DashboardBuilderConfig,
                 orchestrator_result: ExecutionResult):
        super().__init__("HardwareChangeVisualizationService")

        self.config = config
        self.data = orchestrator_result

    def _execute_impl(self) -> Dict[str, Any]:
        """Run hardware change visualization logic"""
        logger.info("🔄 Running hardware change visualization...")

        # Initialize hardware change visualization service
        from agents.dashboardBuilder.visualizationServices.hardware_change_visualization import HardwareChangeVisualizationService
        service = HardwareChangeVisualizationService(
            config = self.config.get_change_visualization_config(),
            data = self.data.get_path("HardwareChangeAnalyzer")
        )
        result = service.run_visualizing()
                
        return {
            "payload": result,
            "savable": True
        }

    def _fallback(self) -> Dict[str, Any]:
        """Fallback: return empty visualization results"""
        logger.warning("Using fallback for HardwareChangeVisualizationPhase - returning empty results")
        return {
            "payload": None,
            "savable": False
        }

# ============================================
# PHASE: MULTI-LEVEL PERFORMANCE VISUALIZATION
# ============================================
class  MultiLevelPerformanceVisualizationPhase(AtomicPhase):
    """Phase for running the actual multi-level performance visualization logic"""
    
    RECOVERABLE_ERRORS = (KeyError, ValueError, pd.errors.MergeError)
    CRITICAL_ERRORS = (MemoryError, KeyboardInterrupt)
    FALLBACK_FAILURE_IS_CRITICAL = False
    
    def __init__(self, 
                 config: DashboardBuilderConfig,
                 orchestrator_result: ExecutionResult):
        super().__init__("MultiLevelPerformanceVisualizationService")

        self.config = config
        self.data = orchestrator_result

    def _execute_impl(self) -> Dict[str, Any]:
        """Run multi-level performance visualization logic"""
        logger.info("🔄 Running multi-level performance visualization...")

        # Initialize multi-level performance visualization service
        from agents.dashboardBuilder.visualizationServices.multi_level_performance_visualization import MultiLevelPerformanceVisualizationService
        service = MultiLevelPerformanceVisualizationService(
            config = self.config.get_performance_visualization_config(),
            data = self.data.get_path("MultiLevelPerformanceAnalyzer")
        )
        result = service.run_visualizing()
                
        return {
            "payload": result,
            "savable": True
        }

    def _fallback(self) -> Dict[str, Any]:
        """Fallback: return empty visualization results"""
        logger.warning("Using fallback for MultiLevelPerformanceVisualizationPhase - returning empty results")
        return {
            "payload": None,
            "savable": False
        }

class DashboardBuilder(ConfigReportMixin):

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
        
            'save_orchestrator_log': bool
            }
        }

    def __init__(self, 
                 config: DashboardBuilderConfig):
        
        """
        Initialize DashboardBuilder with configuration.
        
        Args:        
            config: DashboardBuilderConfig containing processing parameters, including:
                - shared_source_config:
                    - annotation_path (str): Path to the JSON file containing path annotations.
                    - databaseSchemas_path (str): Path to database schema for validation.
                    - day_level_visualization_pipeline_dir (str): Base directory for storing reports.
                    - day_level_visualization_pipeline_log_path (str): Path to the DayLevelVisualizationPipeline change log.
                    - month_level_visualization_pipeline_dir (str): Base directory for storing reports.
                    - month_level_visualization_pipeline_log_path (str): Path to the MonthLevelVisualizationPipeline change log.
                    - year_level_visualization_pipeline_dir (str): Base directory for storing reports.
                    - year_level_visualization_pipeline_log_path (str): Path to the YearLevelVisualizationPipeline change log.
                    - multi_level_performance_visualization_service_log_path (str): Path to the MultiLevelPerformanceVisualizationService change log.
                    - hardware_change_visualization_service_dir (str): Base directory for storing reports/visualizations.
                    - hardware_change_visualization_service_log_path (str): Path to the HardwareChangeVisualizationService change log.
                    - machine_layout_visualization_pipeline_dir (str): Base directory for storing reports/visualizations.
                    - machine_layout_visualization_pipeline_change_log_path (str): Path to the MachineLayoutVisualizationPipeline change log.
                    - mold_machine_pair_visualization_pipeline_dir (str): Base directory for storing reports/visualizations.
                    - mold_machine_pair_visualization_pipeline_change_log_path (str): Path to the MoldMachinePairVisualizationPipeline change log.
                    - dashboard_builder_log_path (str): Path to save the DashboardBuilder change log.
                - machine_layout_visualization_service: (ComponentConfig): Component config for MachineLayoutVisualizationPipeline
                - mold_machine_pair_visualization_service: Component config for MoldMachinePairVisualizationPipeline
                - day_level_visualization_service (ComponentConfig): Component config for DayLevelVisualizationPipeline
                - month_level_visualization_service (ComponentConfig): Component config for MonthLevelVisualizationPipeline
                - year_level_visualization_service (ComponentConfig): Component config for YearLevelVisualizationPipeline
                - save_builder_log (bool): Save DashboardBuilder change log
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

    def build_dashboard(self) -> ExecutionResult:
        """Execute the complete dashboard builder pipeline."""
        
        self.logger.info("Starting DashboardBuilder ...")

        agent_id = self.__class__.__name__

        timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        config_header = self._generate_config_report(timestamp_str, required_only=True)
        
        # ============================================
        # BUILD PHASE LIST WITH SHARED CONTAINER
        # ============================================
        phases: List[Executable] = []

        # Execute Analytics Orchestrator to get data for visualization phases
        if self.config.enable_analytics_orchestrator:
            from agents.analyticsOrchestrator.analytics_orchestrator_v1 import AnalyticsOrchestrator
            orchestrator = AnalyticsOrchestrator(
                config = self.config.get_analytics_orchestrator_config())
            orchestrator_result = orchestrator.run_analyzing()
        
            # Phase 1: Hardware Change Visualization Service (optional)
            if self.config.enable_change_visualization_service:
                phases.append(HardwareChangeVisualizationPhase(self.config, orchestrator_result))
            
            # Phase 2: Multi-Level Performance Visualization Service (optional)
            if self.config.enable_performance_visualization_service:
                phases.append(MultiLevelPerformanceVisualizationPhase(self.config, orchestrator_result))
            
        # ============================================
        # EXECUTE USING COMPOSITE AGENT
        # ============================================
        agent = CompositeAgent("DashboardBuilder", phases)
        result = agent.execute()

        # ============================================
        # SAVE PIPELINE LOG IF REQUESTED
        # ============================================
        if self.config.save_builder_log:

            # Generate summary report
            reporter = DictBasedReportGenerator(use_colors=False)
            summary = "\n".join(reporter.export_report(self.config.get_summary()))
            export_metadata = "\n".join(reporter.export_report(extract_export_metadata(result)))
            
            # Save pipeline change log
            message = update_change_log(
                agent_id, 
                config_header, 
                format_execution_tree(result), 
                summary, 
                export_metadata, 
                Path(self.config.shared_source_config.dashboard_builder_log_path)
            )
            
            self.logger.info(f"Pipeline log saved: {message}")

        # ============================================
        # PRINT EXECUTION TREE & ANALYSIS
        # ============================================
        self.logger.info("✅ DashboardBuilder completed in {:.2f}s!", result.duration)
        
        # Print execution tree for visibility
        print_execution_summary(result)
        
        return result