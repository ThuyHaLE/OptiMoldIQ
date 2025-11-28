from loguru import logger
from typing import Dict, Optional, Any
from pathlib import Path

from agents.analyticsOrchestrator.analyticsConfigs.analytics_orchestrator_config import AnalyticsOrchestratorConfig
from agents.analyticsOrchestrator.logStrFormatters.analytics_orchestrator_formatter import build_analytics_orchestrator_log

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
        
    def run_analytics(self):
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
        
        # Apply auto-configuration and get summary string
        self.auto_configuration_str = self._apply_auto_configuration()

        # Log the auto-config summary to console
        self.logger.info(f"\n{self.auto_configuration_str}")
        
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

        log_entries_str = build_analytics_orchestrator_log(self.config, 
                                                           results,
                                                           self.auto_configuration_str
                                                           )

        # Save log
        if self.config.save_analytics_orchestrator_log:
            try:
                output_dir = Path(self.config.analytics_orchestrator_dir)
                output_dir.mkdir(parents=True, exist_ok=True)
                log_path = output_dir / "change_log.txt"
                with open(log_path, "a", encoding="utf-8") as log_file:
                    log_file.write(log_entries_str)
                self.logger.info("✓ Updated and saved change log: {}", log_path)
            except Exception as e:
                self.logger.error("✗ Failed to save change log {}: {}", log_path, e)

        return results, log_entries_str
    
    def _apply_auto_configuration(self) -> str:
        """
        Apply auto-configuration rules to analytics configs.
        This modifies the configs in-place based on analytics orchestrator enable flags.
        
        Returns:
            str: Summary string of auto-configuration changes
        """
        log_lines = []
        log_lines.append("--Auto-Configuration--")
        log_lines.append(f"⤷ Input Configs:")
        log_lines.append(f"   ⤷ enable_hardware_change_analysis: {self.config.enable_hardware_change_analysis}")
        log_lines.append(f"   ⤷ enable_multi_level_analysis: {self.config.enable_multi_level_analysis}")
        
        if self.config.enable_hardware_change_analysis:
            log_lines.append(f"   ⤷ enable_hardware_change_machine_layout_tracker: {self.config.enable_hardware_change_machine_layout_tracker}")
            log_lines.append(f"   ⤷ enable_hardware_change_machine_mold_pair_tracker: {self.config.enable_hardware_change_machine_mold_pair_tracker}")
        
        if self.config.enable_multi_level_analysis:
            log_lines.append(f"   ⤷ enable_multi_level_day_level_processor: {self.config.enable_multi_level_day_level_processor}")
            log_lines.append(f"   ⤷ enable_multi_level_month_level_processor: {self.config.enable_multi_level_month_level_processor}")
            log_lines.append(f"   ⤷ enable_multi_level_year_level_processor: {self.config.enable_multi_level_year_level_processor}")
        
        log_lines.append("")
        log_lines.append("⤷ Applied Changes:")
        
        # Hardware Change Analysis Configuration
        if self.config.enable_hardware_change_analysis:
            log_lines.append("   ⤷ ChangeAnalyticflowConfig:")
            
            self.config.change_config.enable_machine_layout_tracker = (
                self.config.enable_hardware_change_machine_layout_tracker
            )
            log_lines.append(
                f"      ⤷ enable_machine_layout_tracker (=hardware_change_machine_layout_tracker): "
                f"{self.config.enable_hardware_change_machine_layout_tracker}"
            )
            
            self.config.change_config.enable_machine_mold_pair_tracker = (
                self.config.enable_hardware_change_machine_mold_pair_tracker
            )
            log_lines.append(
                f"      ⤷ enable_machine_mold_pair_tracker (=hardware_change_machine_mold_pair_tracker): "
                f"{self.config.enable_hardware_change_machine_mold_pair_tracker}"
            )
            
            self.config.change_config.save_hardware_change_analyzer_log = True
            log_lines.append(f"      ⤷ save_hardware_change_analyzer_log: True (force enabled)")
        
        # Multi-Level Performance Analysis Configuration
        if self.config.enable_multi_level_analysis:
            log_lines.append("   ⤷ PerformanceAnalyticflowConfig:")
            
            self.config.performance_config.enable_day_level_processor = (
                self.config.enable_multi_level_day_level_processor
            )
            log_lines.append(
                f"      ⤷ enable_day_level_processor (=multi_level_day_level_processor): "
                f"{self.config.enable_multi_level_day_level_processor}"
            )
            
            self.config.performance_config.enable_month_level_processor = (
                self.config.enable_multi_level_month_level_processor
            )
            log_lines.append(
                f"      ⤷ enable_month_level_processor (=multi_level_month_level_processor): "
                f"{self.config.enable_multi_level_month_level_processor}"
            )
            
            self.config.performance_config.enable_year_level_processor = (
                self.config.enable_multi_level_year_level_processor
            )
            log_lines.append(
                f"      ⤷ enable_year_level_processor (=multi_level_year_level_processor): "
                f"{self.config.enable_multi_level_year_level_processor}"
            )
            
            self.config.performance_config.save_multi_level_performance_analyzer_log = True
            log_lines.append(f"      ⤷ save_multi_level_performance_analyzer_log: True (force enabled)")
        
        if not self.config.enable_hardware_change_analysis and not self.config.enable_multi_level_analysis:
            log_lines.append("   ⤷ No analytics enabled - no changes applied")
        
        log_lines.append("")
        
        return "\n".join(log_lines)

    def process_multi_level_analytics(self) -> Dict[str, Any]:
        """
        Execute multi-level data analytics processing.
        
        Returns:
            Dictionary containing analytics results
        """
        # Check if any date is configured
        if not any([
            self.config.performance_config.record_date,
            self.config.performance_config.record_month,
            self.config.performance_config.record_year
        ]):
            self.logger.warning("No dates configured - skipping analytics")
            return None
        
        self.logger.info("Processing multi-level analytics")

        from agents.analyticsOrchestrator.multiLevelPerformanceAnalyzer.multi_level_performance_analyzer import (
            MultiLevelPerformanceAnalyzer)
        
        # Execute analytics
        analytics = MultiLevelPerformanceAnalyzer(self.config.performance_config)
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
            HardwareChangeAnalyzer)

        # Execute analytics
        analyzer = HardwareChangeAnalyzer(self.config.change_config)
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