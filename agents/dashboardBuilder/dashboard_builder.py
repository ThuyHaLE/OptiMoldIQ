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
        
        # Apply auto-configuration and get summary string
        self.auto_configuration_str = self._apply_auto_configuration()
        
        # Log the auto-config summary to console
        self.logger.info(f"\n{self.auto_configuration_str}")

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
            
        log_entries_str = build_dashboard_builder_log(self.config, 
                                                      results, 
                                                      self.auto_configuration_str)

        # Save log
        if self.config.save_dashboard_builder_log:
            try:
                output_dir = Path(self.config.dashboard_builder_dir)
                output_dir.mkdir(parents=True, exist_ok=True)
                log_path = output_dir / "change_log.txt"
                with open(log_path, "a", encoding="utf-8") as log_file:
                    log_file.write(log_entries_str)
                self.logger.info("✓ Updated and saved dashboard log: {}", log_path)
            except Exception as e:
                self.logger.error("✗ Failed to save dashboard log {}: {}", log_path, e)

        return results, log_entries_str
    
    def _apply_auto_configuration(self) -> str:
        """
        Apply auto-configuration rules to plotter configs.
        This modifies the configs in-place based on dashboard builder enable flags.
        
        Returns:
            str: Summary string of auto-configuration changes
        """
        log_lines = []
        log_lines.append("--Auto-Configuration--")
        log_lines.append(f"⤷ Input Configs:")
        log_lines.append(f"   ⤷ enable_hardware_change_plotter: {self.config.enable_hardware_change_plotter}")
        log_lines.append(f"   ⤷ enable_multi_level_plotter: {self.config.enable_multi_level_plotter}")
        
        if self.config.enable_hardware_change_plotter:
            log_lines.append(f"   ⤷ enable_hardware_change_machine_layout_plotter: {self.config.enable_hardware_change_machine_layout_plotter}")
            log_lines.append(f"   ⤷ enable_hardware_change_machine_mold_pair_plotter: {self.config.enable_hardware_change_machine_mold_pair_plotter}")
        
        if self.config.enable_multi_level_plotter:
            log_lines.append(f"   ⤷ enable_multi_level_day_level_plotter: {self.config.enable_multi_level_day_level_plotter}")
            log_lines.append(f"   ⤷ enable_multi_level_month_level_plotter: {self.config.enable_multi_level_month_level_plotter}")
            log_lines.append(f"   ⤷ enable_multi_level_year_level_plotter: {self.config.enable_multi_level_year_level_plotter}")
        
        log_lines.append("")
        log_lines.append("⤷ Applied Changes:")
        
        # Hardware Change Plotter Configuration
        if self.config.enable_hardware_change_plotter:
            log_lines.append("   ⤷ HardwareChangePlotflowConfig:")
            
            self.config.hardware_change_plotflow_config.enable_machine_layout_plotter = (
                self.config.enable_hardware_change_machine_layout_plotter
            )
            log_lines.append(
                f"      ⤷ enable_machine_layout_plotter (=hardware_change_machine_layout): "
                f"{self.config.enable_hardware_change_machine_layout_plotter}"
            )
            
            self.config.hardware_change_plotflow_config.enable_machine_mold_pair_plotter = (
                self.config.enable_hardware_change_machine_mold_pair_plotter
            )
            log_lines.append(
                f"      ⤷ enable_machine_mold_pair_plotter (=hardware_change_machine_mold_pair): "
                f"{self.config.enable_hardware_change_machine_mold_pair_plotter}"
            )
            
            self.config.hardware_change_plotflow_config.save_hardware_change_plotter_log = True
            log_lines.append(f"      ⤷ save_hardware_change_plotter_log: True (force enabled)")
        
        # Multi-Level Performance Plotter Configuration
        if self.config.enable_multi_level_plotter:
            log_lines.append("   ⤷ PerformancePlotflowConfig:")
            
            self.config.performance_plotflow_config.enable_day_level_plotter = (
                self.config.enable_multi_level_day_level_plotter
            )
            log_lines.append(
                f"      ⤷ enable_day_level_plotter (=multi_level_day_level): "
                f"{self.config.enable_multi_level_day_level_plotter}"
            )
            
            self.config.performance_plotflow_config.enable_month_level_plotter = (
                self.config.enable_multi_level_month_level_plotter
            )
            log_lines.append(
                f"      ⤷ enable_month_level_plotter (=multi_level_month_level): "
                f"{self.config.enable_multi_level_month_level_plotter}"
            )
            
            self.config.performance_plotflow_config.enable_year_level_plotter = (
                self.config.enable_multi_level_year_level_plotter
            )
            log_lines.append(
                f"      ⤷ enable_year_level_plotter (=multi_level_year_level): "
                f"{self.config.enable_multi_level_year_level_plotter}"
            )
            
            self.config.performance_plotflow_config.save_multi_level_performance_plotter_log = True
            log_lines.append(f"      ⤷ save_multi_level_performance_plotter_log: True (force enabled)")
        
        if not self.config.enable_hardware_change_plotter and not self.config.enable_multi_level_plotter:
            log_lines.append("   ⤷ No plotters enabled - no changes applied")
        
        log_lines.append("")
        
        return "\n".join(log_lines)

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