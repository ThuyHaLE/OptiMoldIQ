from loguru import logger
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
from configs.shared.config_report_format import ConfigReportMixin
from agents.analyticsOrchestrator.analytics_orchestrator_config import ComponentConfig, AnalyticsOrchestratorConfig
from configs.shared.dict_based_report_generator import DictBasedReportGenerator

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
# PHASE: HARDWARE CHANGE ANALYZING
# ============================================
class  HardwareChangeAnalyzingPhase(AtomicPhase):
    """Phase for running the actual hardware change analyzer logic"""
    
    RECOVERABLE_ERRORS = (KeyError, ValueError, pd.errors.MergeError)
    CRITICAL_ERRORS = (MemoryError, KeyboardInterrupt)
    FALLBACK_FAILURE_IS_CRITICAL = False
    
    def __init__(self, 
                 config: AnalyticsOrchestratorConfig):
        super().__init__("HardwareChangeAnalyzer")

        self.config = config

    def _execute_impl(self) -> Dict[str, Any]:
        """Run hardware change analyzer logic"""
        logger.info("🔄 Running hardware change analyzer...")

        # Initialize hardware change analyzer
        from agents.analyticsOrchestrator.analyzers.hardware_change_analyzer import HardwareChangeAnalyzer

        analyzer = HardwareChangeAnalyzer(
            config = self.config.get_change_analyzer_config())
        
        result = analyzer.run_analyzing()
                
        return {
            "payload": result,
            "savable": True
        }

    def _fallback(self) -> Dict[str, Any]:
        """Fallback: return empty analyzing results"""
        logger.warning("Using fallback for HardwareChangeAnalyzingPhase - returning empty results")
        return {
            "payload": None,
            "savable": False
        }
    
# ============================================
# PHASE: MULTI-LEVEL PERFORMANCE ANALYZING
# ============================================
class  MultiLevelPerformanceAnalyzingPhase(AtomicPhase):
    """Phase for running the actual multi-level performance analyzer logic"""
    
    RECOVERABLE_ERRORS = (KeyError, ValueError, pd.errors.MergeError)
    CRITICAL_ERRORS = (MemoryError, KeyboardInterrupt)
    FALLBACK_FAILURE_IS_CRITICAL = False
    
    def __init__(self, 
                 config: AnalyticsOrchestratorConfig):
        super().__init__("MultiLevelPerformanceAnalyzer")

        self.config = config

    def _execute_impl(self) -> Dict[str, Any]:
        """Run multi-level performance analyzer logic"""
        logger.info("🔄 Running multi-level performance analyzer...")

        # Initialize multi-level performance analyzer
        from agents.analyticsOrchestrator.analyzers.multi_level_performance_analyzer import MultiLevelPerformanceAnalyzer

        analyzer = MultiLevelPerformanceAnalyzer(
            config = self.config.get_performance_analyzer_config())

        result = analyzer.run_analyzing()
                
        return {
            "payload": result,
            "savable": True
        }

    def _fallback(self) -> Dict[str, Any]:
        """Fallback: return empty analyzing results"""
        logger.warning("Using fallback for MultiLevelPerformanceAnalyzingPhase - returning empty results")
        return {
            "payload": None,
            "savable": False
        }

class AnalyticsOrchestrator(ConfigReportMixin):

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
        Initialize HardwareChangeAnalyzer with configuration.
        
        Args:        
            config: AnalyticsOrchestratorConfig containing processing parameters, including:
                - shared_source_config:
                    - annotation_path (str): Path to the JSON file containing path annotations.
                    - databaseSchemas_path (str): Path to database schema for validation.
                    - machine_layout_tracker_dir (str): Base directory for storing reports.
                    - machine_layout_tracker_change_log_path (str): Path to the MachineLayoutTracker change log.
                    - mold_machine_pair_tracker_dir (str): Base directory for storing reports.
                    - mold_machine_pair_tracker_change_log_path (str): Path to the MoldMachinePairTracker change log.
                    - hardware_change_analyzer_log_path (str): Path to the HardwareChangeAnalyzer change log.
                    - day_level_processor_dir (str): Base directory for storing reports.
                    - day_level_processor_log_path (str): Path to the DayLevelDataProcessor change log.
                    - month_level_processor_dir (str): Base directory for storing reports.
                    - month_level_processor_log_path (str): Path to the MonthLevelDataProcessor change log.
                    - year_level_processor_dir (str): Base directory for storing reports.
                    - year_level_processor_log_path (str): Path to the YearLevelDataProcessor change log.
                    - multi_level_performance_analyzer_log_path (str): Path to the MultiLevelPerformanceAnalyzer change log.
                    - analytics_orchestrator_log_path (str): Path to the AnalyticsOrchestrator change log.
                - machine_layout_tracker (ComponentConfig): Component config for MachineLayoutTracker
                - mold_machine_pair_tracker (ComponentConfig): Component config for MoldMachinePairTracker 
                - day_level_processor (ComponentConfig): Component config for DayLevelDataProcessor 
                - month_level_processor (ComponentConfig): Component config for MonthLevelDataProcessor
                - year_level_processor (ComponentConfig): Component config for YearLevelDataProcessor
                - save_orchestrator_log (bool): Save AnalyticsOrchestrator change log
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
        """Execute the complete hardware change analyzer pipeline."""
        
        self.logger.info("Starting AnalyticsOrchestrator ...")

        agent_id = self.__class__.__name__

        timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        config_header = self._generate_config_report(timestamp_str, required_only=True)
        
        # ============================================
        # BUILD PHASE LIST WITH SHARED CONTAINER
        # ============================================
        phases: List[Executable] = []
        
        # Phase 1: Machine Layout Tracking (optional)
        if self.config.enable_change_analysis:
            phases.append(HardwareChangeAnalyzingPhase(self.config))
        
        # Phase 2: Multi-Level Performance Analyzing (optional)
        if self.config.enable_performance_analysis:
            phases.append(MultiLevelPerformanceAnalyzingPhase(self.config))
        
        # ============================================
        # EXECUTE USING COMPOSITE AGENT
        # ============================================
        agent = CompositeAgent("AnalyticsOrchestrator", phases)
        result = agent.execute()

        # ============================================
        # SAVE PIPELINE LOG IF REQUESTED
        # ============================================
        if self.config.save_orchestrator_log:

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
                Path(self.config.shared_source_config.analytics_orchestrator_log_path)
            )
            
            self.logger.info(f"Pipeline log saved: {message}")

        # ============================================
        # PRINT EXECUTION TREE & ANALYSIS
        # ============================================
        self.logger.info("✅ AnalyticsOrchestrator completed in {:.2f}s!", result.duration)
        
        # Print execution tree for visibility
        print_execution_summary(result)
        
        return result