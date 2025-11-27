from loguru import logger
from typing import Dict, Optional, Any
from pathlib import Path

from agents.analyticsOrchestrator.analytics_orchestrator import AnalyticsOrchestrator

from agents.dashboardBuilder.dashboardBuilderConfigs.hardware_change_plotflow_config import HardwareChangePlotflowConfig
from agents.dashboardBuilder.logStrFormatters.hardware_change_plotter_formatter import build_hardware_change_plotter_log

class HardwareChangePlotter: 
    """
    Unified interface for hardware change analytics plotting.
    
    Orchestrates mold/machine-level data processors to generate
    structured analytics, plot and save reports and visualization.
    
    Architecture:
        HardwareChangePlotter (Service Layer)
            ├─ MachineLayoutPlotter
            └─ MachineMoldPairPlotter
    
    Usage:
        config = HardwareChangePlotflowConfig(
            enable_machine_layout_tracker = True
            enable_machine_mold_pair_tracker = True
        )
        plotter = HardwareChangePlotter(config)
        results = plotter.data_process()
    """
    
    def __init__(self, config: HardwareChangePlotflowConfig):
        """
        Initialize HardwareChangePlotter with configuration.
        
        Args:
            config: HardwareChangePlotflowConfig containing parameters and paths
        """
        self.logger = logger.bind(class_="HardwareChangePlotter")
        self.config = config

        self.analytics_orchestrator_config = self.config.analytics_orchestrator_config

        self.logger.info("Initialized HardwareChangePlotter")

        try:
            self.analytics_orchestrator_config.enable_hardware_change_analysis = (
                self.config.enable_machine_layout_plotter 
                or self.config.enable_machine_mold_pair_plotter),
            

            self.analytics_orchestrator_config.change_analytic_config.enable_machine_layout_tracker = (
                self.config.enable_machine_layout_plotter),
            self.analytics_orchestrator_config.change_analytic_config.enable_machine_mold_pair_tracker = (
                self.config.enable_machine_mold_pair_plotter),

            orchestrator = AnalyticsOrchestrator(self.analytics_orchestrator_config)
            
            self.orchestrator_results, self.orchestrator_log_str = orchestrator.run_analytics()

        except Exception as e:
            self.logger.error("Failed to analyze data: {}", e)
            raise
        
    def data_process(self) -> Dict[str, Optional[Dict[str, Any]]]:
        """
        Execute multi-level data processing pipeline.
        
        Conditionally runs machine/mold processors based on config.
        Machine/mold levels only run if respective dates are provided.
        """

        self.logger.info("Starting multi-level data processing pipeline")

        results = {
            "machine_level_results": self._safe_process(
                self.machine_level_process, 
                "machine"
            ) if self.config.enable_machine_layout_plotter else None,
            "mold_level_results": self._safe_process(
                self.mold_level_process, 
                "mold"
            ) if self.config.enable_machine_mold_pair_plotter else None
        }

        log_entries_str = build_hardware_change_plotter_log(self.config, results)

        # Save log
        if self.config.save_hardware_change_plotter_log:
            try:
                output_dir = Path(self.config.hardware_change_plotter_dir)
                output_dir.mkdir(parents=True, exist_ok=True)
                log_path = output_dir / "change_log.txt"
                with open(log_path, "a", encoding="utf-8") as log_file:
                    log_file.write(log_entries_str)
                self.logger.info("✓ Updated and saved change log: {}", log_path)
            except Exception as e:
                self.logger.error("✗ Failed to save change log {}: {}", log_path, e)
        
        return results, log_entries_str
    
    def machine_level_process(self) -> Dict[str, Any]:
        """
        Plot and save plots & reports with optional parallel processing for machine-level production data.
        
        Returns:
            Dictionary containing processing results
        """

        self.logger.info("Plotting machine-level data.")
        
        machine_layout_tracker_results = self.orchestrator_results['change_hardware_analysis']['results']['machine_layout_tracker']

        if machine_layout_tracker_results['has_new_layout_change']:

            machine_layout_hist_change = machine_layout_tracker_results['machine_layout_hist_change']

            from agents.dashboardBuilder.hardwareChangePlotter.machine_layout_plotter import MachineLayoutPlotter

            machine_layout_plotter = MachineLayoutPlotter(
                machine_layout_hist_change_df = machine_layout_hist_change, 
                default_dir = self.config.machine_layout_plotter_result_dir,
                visualization_config_path = self.config.machine_layout_visualization_config_path,
                enable_parallel = self.config.enable_parallel,
                max_workers = self.config.max_workers)
            
            machine_layout_plotter_log_entries = machine_layout_plotter.plot_all()

            self.logger.info("Machine-level data saved!")
        
            return {"status": "completed", 
                    "result": {
                        "machine_layout_tracker": machine_layout_tracker_results['log_entries'], 
                        "machine_layout_plotter": "".join(machine_layout_plotter_log_entries)
                        }
                    }
        
        else:
            return {"status": "skipped", 
                    "result": {
                        "machine_layout_tracker": "No changes detected.", 
                        "machine_layout_plotter": "No changes detected."
                        }
                    }
    
    def mold_level_process(self) -> Dict[str, Any]:
        """
        Plot and save plots & reports with optional parallel processing for mold-level production data.
        
        Returns:
            Dictionary containing processing results
        """

        self.logger.info("Processing mold-level data.")

        mold_layout_tracker_results = self.orchestrator_results['change_hardware_analysis']['results']['machine_mold_pair_tracker']

        if mold_layout_tracker_results['has_new_pair_change']:
            first_mold_usage = mold_layout_tracker_results['first_mold_usage']
            first_paired_mold_machine = mold_layout_tracker_results['first_paired_mold_machine']
            mold_tonnage_summary = mold_layout_tracker_results['mold_tonnage_summary']
            

            from agents.dashboardBuilder.hardwareChangePlotter.machine_mold_pair_plotter import MachineMoldPairPlotter

            mold_layout_tracker = MachineMoldPairPlotter(
                first_mold_usage = first_mold_usage, 
                first_paired_mold_machine = first_paired_mold_machine,
                mold_tonnage_summary = mold_tonnage_summary,
                default_dir = self.config.machine_mold_pair_plotter_result_dir,
                visualization_config_path = self.config.machine_mold_pair_visualization_config_path,
                enable_parallel = self.config.enable_parallel,
                max_workers = self.config.max_workers)
            
            mold_layout_plotter_log_entries = mold_layout_tracker.plot_all()
    
            self.logger.info("Mold-level data saved!")
            
            return {"status": "completed", 
                    "result": {
                        "mold_layout_tracker": mold_layout_tracker_results['log_entries'], 
                        "mold_layout_plotter": "".join(mold_layout_plotter_log_entries)
                        }
                    }
        
        else:
            return {"status": "skipped", 
                    "result": {
                        "mold_layout_tracker": "No changes detected.", 
                        "mold_layout_plotter": "No changes detected."
                        }
                    }
        
    def _safe_process(self, 
                      process_func, 
                      level_name: str) -> Optional[Dict[str, Any]]:
        """
        Execute processing function with error isolation.
        
        Args:
            process_func: Processing function to execute
            level_name: Name of processing level (for logging)
            
        Returns:
            Processing results or None if failed
        """
        try:
            result = process_func()
            self.logger.success("✓ {} level processing completed", level_name.capitalize())
            return result
        except Exception as e:
            self.logger.error("✗ {} level processing failed: {}", level_name.capitalize(), e)
            # Re-raise if you want to fail fast, or return None to continue
            return None