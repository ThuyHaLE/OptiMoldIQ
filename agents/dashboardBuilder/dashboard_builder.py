from loguru import logger
from typing import Dict, Optional, Any
from pathlib import Path

from agents.dashboardBuilder.dashboardBuilderConfigs.dashboard_builder_config import DashboardBuilderConfig
from agents.dashboardBuilder.logStrFormatters.dashboard_builder_formatter import build_dashboard_builder_log

class DashboardBuilder:
    """
    Unified interface for dashboard visualization operations.
    
    Orchestrates multi-level performance plotting and hardware change visualization components,
    providing a clean public interface for other agents.
    
    Architecture:
        DashboardBuilder (Facade Layer)
            ├─ MultiLevelPerformancePlotter (Day/Month/Year visualizations)
            └─ HardwareChangePlotter (Change visualizations)
    
    Usage:
        config = DashboardBuilderConfig(
            enable_multi_level_plotter=True,
            enable_hardware_change_plotter=True
        )
        builder = DashboardBuilder(config)
        results = builder.build_dashboards()
    """
    
    def __init__(self, 
                 config: DashboardBuilderConfig):
        """
        Initialize DashboardBuilder with configuration.
        
        Args:
            config: DashboardBuilderConfig containing visualization parameters
        """
        self.logger = logger.bind(class_="DashboardBuilder")
        self.config = config
        self.logger.info("Initialized DashboardBuilder")
        
    def build_dashboards(self):
        """
        Executes visualization modules based on enable flags:
        - If both disabled → do nothing
        - If only one enabled → run that module
        - If both enabled → run both modules
        """
        results = {
            "multi_level_plotter": None, 
            "hardware_change_plotter": None
        }
        
        # Nothing enabled
        if not self.config.enable_hardware_change_plotter and not self.config.enable_multi_level_plotter:
            self.logger.info("No plotters enabled. Nothing to run.")
        
        # Run Hardware Change Plotter
        if self.config.enable_hardware_change_plotter:
            results["hardware_change_plotter"] = self._safe_process(
                self.process_hardware_change_plotter,
                "hardware change plotter")

        # Run Multi-Level Performance Plotter
        if self.config.enable_multi_level_plotter:
            results["multi_level_plotter"] = self._safe_process(
                self.process_multi_level_plotter,
                "multi-level performance plotter")
        
        log_entries_str = build_dashboard_builder_log(self.config, results)

        # Save log
        if self.config.save_dashboard_builder_log:
            try:
                output_dir = Path(self.config.dashboard_builder_dir)
                output_dir.mkdir(parents=True, exist_ok=True)
                log_path = output_dir / "dashboard_log.txt"
                with open(log_path, "a", encoding="utf-8") as log_file:
                    log_file.write(log_entries_str)
                self.logger.info("✓ Updated and saved dashboard log: {}", log_path)
            except Exception as e:
                self.logger.error("✗ Failed to save dashboard log {}: {}", log_path, e)

        return results, log_entries_str
    
    def process_multi_level_plotter(self) -> Dict[str, Any]:
        """
        Execute multi-level performance plotting.
        
        Returns:
            Dictionary containing plotting results
        """
        self.logger.info("Processing multi-level performance plotter")

        from agents.dashboardBuilder.multiLevelPerformancePlotter.multi_level_performance_plotter import (
            MultiLevelPerformancePlotter)
        
        # Execute plotting
        plotter = MultiLevelPerformancePlotter(self.config.performance_plotflow_config)
        results, log_entries_str = plotter.data_process()
        
        self.logger.success("✓ Multi-level performance plotter completed")
        
        return {
            "results": results, 
            "log_entries_str": log_entries_str
        }
    
    def process_hardware_change_plotter(self) -> Dict[str, Any]:
        """
        Execute hardware change visualization.
        
        Returns:
            Dictionary containing hardware change plotter results
        """
        self.logger.info("Processing hardware change plotter")

        from agents.dashboardBuilder.hardwareChangePlotter.hardware_change_plotter import (
            HardwareChangePlotter)

        # Execute plotting
        plotter = HardwareChangePlotter(self.config.hardware_change_plotflow_config)
        results, log_entries_str = plotter.data_process()
        
        self.logger.success("✓ Hardware change plotter completed")
        
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