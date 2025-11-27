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
        
        log_entries_str = build_analytics_orchestrator_log(self.config, results)

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