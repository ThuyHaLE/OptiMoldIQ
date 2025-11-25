from loguru import logger
from dataclasses import dataclass
from typing import Dict, Optional, Any
from pathlib import Path
from datetime import datetime

@dataclass
class AnalyticsOrchestratorConfig:
    """Configuration class for analytics orchestrator parameters"""

    # Enable AnalyticsOrchestrator components
    enable_hardware_change_analysis: bool = False #HardwareChangeAnalyzer
    enable_multi_level_analysis: bool = False #MultiLevelPerformanceAnalyzer

    # Database sources
    source_path: str = 'agents/shared_db/DataLoaderAgent/newest'
    annotation_name: str = "path_annotations.json"
    databaseSchemas_path: str = 'database/databaseSchemas.json'
    default_dir: str = 'agents/shared_db/AnalyticsOrchestrator'

    # HardwareChangeAnalyzer config
    enable_machine_layout_tracker: bool = False
    enable_machine_mold_pair_tracker: bool = False
    change_tracker_output_dir: str = "agents/shared_db/AnalyticsOrchestrator/HardwareChangeAnalyzer"
    machine_layout_tracker_dir: str = "agents/shared_db/AnalyticsOrchestrator/HardwareChangeAnalyzer/UpdateMachineLayout/tracker_results"
    machine_layout_tracker_change_log_name: str = "change_log.txt"
    machine_mold_pair_tracker_dir: str = "agents/shared_db/AnalyticsOrchestrator/HardwareChangeAnalyzer/UpdateMoldOverview/tracker_results"
    machine_mold_pair_tracker_change_log_name: str = "change_log.txt"

    # MultiLevelPerformanceAnalyzer config
    # Day level 
    record_date: Optional[str] = None
    day_save_output: bool = False
    # Month level
    record_month: Optional[str] = None
    month_analysis_date: Optional[str] = None
    month_save_output: bool = False
    # Year level
    record_year: Optional[str] = None
    year_analysis_date: Optional[str] = None
    year_save_output: bool = False

    # Output directory
    multi_level_output_dir: str = "agents/shared_db/AnalyticsOrchestrator/MultiLevelDataAnalytics"
    
class AnalyticsOrchestrator:
    """
    Unified interface for analytics operations.
    
    Orchestrates multi-level data analytics and change analysis components,
    providing a clean public interface for other agents.
    
    Architecture:
        AnalyticsOrchestrator (Facade Layer)
            ├─ MultiLevelPerformanceAnalyzer (Day/Month/Year processing)
            └─ HardwareChangeAnalyzer (Change detection)
    
    Usage:
        config = AnalyticsOrchestratorConfig(
            record_date="2025-11-16",
            record_month="2025-11",
            enable_multi_level_analysis=True
        )
        orchestrator = AnalyticsOrchestrator(config)
        results = orchestrator.process()
    """
    
    def __init__(self, 
                 config: AnalyticsOrchestratorConfig):
        """
        Initialize AnalyticsOrchestrator with configuration.
        
        Args:
            config: AnalyticsOrchestratorConfig containing processing parameters
        """
        self.logger = logger.bind(class_="AnalyticsOrchestrator")
        self.config = config
        self.logger.info("Initialized AnalyticsOrchestrator")
        
    def run_analytics(self, save_log = False):
        """
        Executes analytics modules based on enable flags:
        - If both disabled → do nothing
        - If only one enabled → run that module
        - If both enabled → run ChangeAnalysis then MultiLevelAnalysis
        """
        results =  {
            "multi_level_analytics": None, 
            "change_hardware_analysis": None
            }
        
        # Nothing enabled
        if not self.config.enable_hardware_change_analysis and not self.config.enable_multi_level_analysis:
            self.logger.info("No analytics enabled. Nothing to run.")
        
        # Run Multi-Level analytics
        if self.config.enable_hardware_change_analysis:
            results["change_hardware_analysis"] = self._safe_process(
                self.process_change_analysis,
                "change hardware analysis")

        # Run Change Analysis
        if self.config.enable_multi_level_analysis:
            results["multi_level_analytics"] = self._safe_process(
                self.process_multi_level_analytics,
                "multi-level analytics")
        
        log_entries_str = self.update_change_logs(results)

        # Save log
        if save_log:
            try:
                output_dir = Path(self.config.default_dir)
                output_dir.mkdir(parents=True, exist_ok=True)
                log_path = output_dir / "change_log.txt"
                with open(log_path, "a", encoding="utf-8") as log_file:
                    log_file.write(log_entries_str)
                self.logger.info("✓ Updated and saved change log: {}", log_path)
            except Exception as e:
                self.logger.error("✗ Failed to save change log {}: {}", log_path, e)

        return results, log_entries_str
    
    def process_multi_level_analytics(self) -> Dict[str, Any]:
        """
        Execute multi-level data analytics processing.
        
        Returns:
            Dictionary containing analytics results
        """
        # Check if any date is configured
        if not any([
            self.config.record_date,
            self.config.record_month,
            self.config.record_year
        ]):
            self.logger.warning("No dates configured - skipping analytics")
            return None
        
        self.logger.info("Processing multi-level analytics")

        from agents.analyticsOrchestrator.multiLevelPerformanceAnalyzer.multi_level_performance_analyzer import (
            PerformanceAnalyticflowConfig, MultiLevelPerformanceAnalyzer)
        
        # Build analytics config
        analytics_config = PerformanceAnalyticflowConfig(
            record_date=self.config.record_date,
            day_save_output = self.config.day_save_output,
            record_month=self.config.record_month,
            month_analysis_date=self.config.month_analysis_date,
            month_save_output = self.config.month_save_output,
            record_year=self.config.record_year,
            year_analysis_date=self.config.year_analysis_date,
            year_save_output = self.config.year_save_output,
            source_path=self.config.source_path,
            annotation_name=self.config.annotation_name,
            databaseSchemas_path=self.config.databaseSchemas_path,
            default_dir=self.config.multi_level_output_dir
        )
        
        # Execute analytics
        analytics = MultiLevelPerformanceAnalyzer(analytics_config)
        results, log_entries_str = analytics.data_process()
        
        self.logger.success("✓ Multi-level analytics completed")
        
        return {
            "results": results, 
            "log_entries_str": log_entries_str
            }
    
    def process_change_analysis(self) -> Dict[str, Any]:
        """
        Execute data change analysis.
        
        Returns:
            Dictionary containing change analysis summary
        """
        self.logger.info("Processing data change analysis")

        from agents.analyticsOrchestrator.hardwareChangeAnalyzer.hardware_change_analyzer import (
            ChangeAnalyticflowConfig, HardwareChangeAnalyzer)

        # Build analytics config
        analytics_config = ChangeAnalyticflowConfig(
            enable_machine_layout_tracker = self.config.enable_machine_layout_tracker,
            enable_machine_mold_pair_tracker = self.config.enable_machine_mold_pair_tracker,
            source_path = self.config.source_path,
            annotation_name = self.config.annotation_name,
            databaseSchemas_path = self.config.databaseSchemas_path,
            default_dir = self.config.change_tracker_output_dir,
            machine_layout_tracker_dir = self.config.machine_layout_tracker_dir,
            machine_layout_tracker_change_log_name = self.config.machine_layout_tracker_change_log_name,
            machine_mold_pair_tracker_dir = self.config.machine_mold_pair_tracker_dir,
            machine_mold_pair_tracker_change_log_name = self.config.machine_mold_pair_tracker_change_log_name
            )

        # Execute analytics
        analyzer = HardwareChangeAnalyzer(analytics_config)
        results, log_entries_str = analyzer.analyze_changes()
        
        self.logger.success("✓ Change analysis completed")
        
        return {
                "results": results, 
                "log_entries_str": log_entries_str
                }
    
    def _safe_process(
        self,
        process_func,
        component_name: str) -> Optional[Dict[str, Any]]:
        """
        Execute processing function with error isolation.
        
        Args:
            process_func: Processing function to execute
            component_name: Name of component (for logging)
            
        Returns:
            Processing results or None if failed
        """
        try:
            result = process_func()
            self.logger.success("✓ {} completed", component_name)
            return result
        except Exception as e:
            self.logger.error("✗ {} failed: {}", component_name, e)
            return None
        
    def update_change_logs(self, results: Dict[str, Optional[Dict]]):
        """
        Update change_log.txt with run configuration and processing results.
        Clean, consistent, and corrected version.
        """

        timestamp_now = datetime.now()
        timestamp_str = timestamp_now.strftime("%Y-%m-%d %H:%M:%S")

        log_entries = []

        # HEADER
        log_entries.append(f"[{timestamp_str}] AnalyticsOrchestrator Run")
        log_entries.append("")

        # CONFIGURATION
        log_entries.append("--Configuration--")

        # Database sources
        log_entries.append(f"⤷ Database Annotation: {self.config.source_path}/{self.config.annotation_name}")
        log_entries.append(f"⤷ Database Schemas: {self.config.databaseSchemas_path}")
        log_entries.append(f"⤷ Default Directory: {self.config.default_dir}")

        # Change Analysis
        if self.config.enable_hardware_change_analysis:
            log_entries.append("⤷ Change Analysis: Enable")
            log_entries.append(f"   ⤷ Output Directory: {self.config.change_tracker_output_dir}")
            log_entries.append("--DataChangeAnalyzer Configuration--")
            # Machine layout tracker
            if self.config.enable_machine_layout_tracker:
                log_entries.append("⤷ Machine layout tracker: Enable")
                log_entries.append("--MachineLayoutTracker Configuration--")
                log_entries.append(f"   ⤷ Machine Layout Output Directory: {self.config.machine_layout_tracker_dir}")
                log_entries.append(f"   ⤷ Machine Layout Change Log Name: {self.config.machine_layout_tracker_change_log_name}")
            else:
                log_entries.append("⤷ Machine layout tracker: Disable")

            # Machine mold pair tracker
            if self.config.enable_machine_mold_pair_tracker:
                log_entries.append("⤷ Machine mold pair tracker: Enable")
                log_entries.append("--MachineMoldPairTrackerr Configuration--")
                log_entries.append(f"   ⤷ Mold Overview Output Directory: {self.config.machine_mold_pair_tracker_dir}")
                log_entries.append(f"   ⤷ Mold Overview Change Log Name: {self.config.machine_mold_pair_tracker_change_log_name}")
            else:
                log_entries.append("⤷ Machine mold pair tracker: Disable")
        else:
            log_entries.append("⤷ Change Analysis: Disable")

        # Multi-Level Analysis
        if self.config.enable_multi_level_analysis:
            log_entries.append("⤷ Multi-level Analysis: Enable")
            log_entries.append(f"   ⤷ Output Directory: {self.config.multi_level_output_dir}")
            log_entries.append("--MultiLevelDataAnalytics Configuration--")

            # Day Level
            if self.config.record_date is None:
                log_entries.append("   ⤷ Day level: Disable")
            else:
                log_entries.append("   ⤷ Day level")
                log_entries.append(f"      ⤷ Record Date: {self.config.record_date}")
                log_entries.append(f"      ⤷ Save Output: {self.config.day_save_output}")

            # Month Level
            if self.config.record_month is None:
                log_entries.append("   ⤷ Month level: Disable")
            else:
                log_entries.append("   ⤷ Month level")
                log_entries.append(f"      ⤷ Record Month: {self.config.record_month}")
                log_entries.append(f"      ⤷ Analysis Date: {self.config.month_analysis_date}")
                log_entries.append(f"      ⤷ Save Output: {self.config.month_save_output}")

            # Year Level
            if self.config.record_year is None:
                log_entries.append("   ⤷ Year level: Disable")
            else:
                log_entries.append("   ⤷ Year level")
                log_entries.append(f"      ⤷ Record Year: {self.config.record_year}")
                log_entries.append(f"      ⤷ Analysis Date: {self.config.year_analysis_date}")
                log_entries.append(f"      ⤷ Save Output: {self.config.year_save_output}")

        else:
            log_entries.append("⤷ Multi-level Analysis: Disable")

        log_entries.append("")

        # PROCESSING SUMMARY
        log_entries.append("--Processing Summary--")

        # Skipped tasks
        skipped_components = [k for k, v in results.items() if v is None]
        if skipped_components:
            skipped_info = ", ".join(skipped_components)
            log_entries.append("⤷ Skipped")
            log_entries.append(f"   ⤷ {skipped_info}")
            self.logger.info("  ⊘ Skipped: {}", skipped_info)

        # Completed tasks
        completed_components = [k for k, v in results.items() if v is not None]
        completed_info = ", ".join(completed_components) if completed_components else "None"

        log_entries.append("⤷ Completed")
        log_entries.append(f"   ⤷ {completed_info}")
        self.logger.info("  ✓ Completed: {}", completed_info)

        # Detailed results
        if completed_components:
            log_entries.append("--Component Details--")
            for component in completed_components:
                log_entries.append(f"⤷ {component}")
                component_details = results[component]["log_entries_str"]
                log_entries.append(f"      ⤷ Log Entries:\n{component_details}")

        log_entries.append("")

        return "\n".join(log_entries)