from loguru import logger
from typing import Dict, Optional, Any
from pathlib import Path

from agents.analyticsOrchestrator.analytics_orchestrator import AnalyticsOrchestrator

from agents.dashboardBuilder.dashboardBuilderConfigs.performance_plotflow_config import PerformancePlotflowConfig
from agents.dashboardBuilder.logStrFormatters.multi_level_performance_plotter_formatter import build_multi_level_performance_plotter_log

class MultiLevelPerformancePlotter: 
    """
    Unified interface for multi-level data analytics plotting.
    
    Orchestrates day/month/year-level data processors to generate
    structured analytics, plot and save reports and visualization.
    
    Architecture:
        MultiLevelPerformancePlotter (Service Layer)
            ├─ DayLevelDataPlotter
            ├─ MonthLevelDataPlotter
            └─ YearLevelDataPlotter
    
    Usage:
        config = PerformancePlotflowConfig(
            record_date="2025-11-16",
            record_month="2025-11",
            record_year="2025"
        )
        plotter = MultiLevelDataPlotter(config)
        results = plotter.data_process()
    """
    
    def __init__(self, config: PerformancePlotflowConfig):
        """
        Initialize MultiLevelPerformancePlotter with configuration.
        
        Args:
            config: PerformancePlotflowConfig containing parameters and paths
        """
        self.logger = logger.bind(class_="MultiLevelPerformancePlotter")
        self.config = config

        self.analytics_orchestrator_config = self.config.analytics_orchestrator_config

        self.logger.info("Initialized MultiLevelPerformancePlotter")

        try:
            # Apply auto-configuration and get summary string
            self.auto_configuration_str = self._apply_auto_configuration()
            
            # Log the auto-config summary to console
            self.logger.info("{}", self.auto_configuration_str)
            
            orchestrator = AnalyticsOrchestrator(self.analytics_orchestrator_config)
            self.orchestrator_results, self.orchestrator_log_str = orchestrator.run_analytics()

        except Exception as e:
            self.logger.error("Failed to analyze data: {}", e)
            raise

    def _apply_auto_configuration(self) -> str:
        """
        Apply auto-configuration rules to analytics_orchestrator_config.
        This modifies the config in-place based on plotter enable flags.
        
        Returns:
            str: Summary string of auto-configuration changes
        """
        log_lines = []
        log_lines.append("--Auto-Configuration--")
        log_lines.append(f"⤷ Input Configs:")
        log_lines.append(f"   ⤷ enable_day_level_plotter: {self.enable_day_level_plotter}")
        log_lines.append(f"   ⤷ enable_month_level_plotter: {self.enable_month_level_plotter}")
        log_lines.append(f"   ⤷ enable_year_level_plotter: {self.enable_year_level_plotter}")
        log_lines.append(f"   ⤷ record_date: {self.analytics_orchestrator_config.performance_config.record_date}")
        log_lines.append(f"   ⤷ record_month: {self.analytics_orchestrator_config.performance_config.record_month}")
        log_lines.append(f"   ⤷ record_year: {self.analytics_orchestrator_config.performance_config.record_year}")
        log_lines.append("")
        
        log_lines.append("⤷ Applied Changes:")
        
        # Enable AnalyticsOrchestrator components: 
        # DayLevelDataPlotter or MonthLevelDataPlotter or YearLevelDataPlotter -> MultiLevelPerformanceAnalyzer
        new_multi_level_analysis = (
            self.enable_day_level_plotter or self.enable_month_level_plotter or self.enable_year_level_plotter)
        self.analytics_orchestrator_config.enable_multi_level_analysis = new_multi_level_analysis
        log_lines.append(
            f"   ⤷ enable_multi_level_analysis (day OR month OR year): {new_multi_level_analysis}"
        )
        
        # Enable PerformanceAnalyticflowConfig components: 
        # Enable DayLevelDataPlotter/MonthLevelDataPlotter/YearLevelDataPlotter out-saving option
        # record_date/record_month/year_save_output is not None -> day_save_output/month_save_output/year_save_output = True
        new_day_save = (self.analytics_orchestrator_config.performance_config.record_date is not None)
        self.analytics_orchestrator_config.performance_config.day_save_output = new_day_save
        log_lines.append(
            f"   ⤷ day_save_output (record_date is not None): {new_day_save}"
        )
        
        new_month_save = (self.analytics_orchestrator_config.performance_config.record_month is not None)
        self.analytics_orchestrator_config.performance_config.month_save_output = new_month_save
        log_lines.append(
            f"   ⤷ month_save_output (record_month is not None): {new_month_save}"
        )
        
        new_year_save = (self.analytics_orchestrator_config.performance_config.record_year is not None)
        self.analytics_orchestrator_config.performance_config.year_save_output = new_year_save
        log_lines.append(
            f"   ⤷ year_save_output (record_year is not None): {new_year_save}"
        )
        
        # Enable PerformanceAnalyticflowConfig change log
        self.analytics_orchestrator_config.performance_config.save_multi_level_performance_analyzer_log = True
        log_lines.append(
            f"   ⤷ save_multi_level_performance_analyzer_log: True (force enabled)"
        )
        log_lines.append("")
        
        return "\n".join(log_lines)

    def data_process(self) -> Dict[str, Optional[Dict[str, Any]]]:
        """
        Execute multi-level data processing pipeline.
        
        Conditionally runs machine/mold processors based on config.
        Machine/mold levels only run if respective dates are provided.
        """

        self.logger.info("Starting multi-level data processing pipeline")

        results = {
            "day_level_results": self._safe_process(
                self.day_level_process, 
                "day"
            ) if self.enable_day_level_plotter else None,

            "month_level_results": self._safe_process(
                self.month_level_process, 
                "month"
            ) if self.enable_month_level_plotter else None,

            "year_level_results": self._safe_process(
                self.year_level_process, 
                "year"
            ) if self.enable_year_level_plotter else None,
        }

        log_entries_str = build_multi_level_performance_plotter_log(self.config, 
                                                                    results, 
                                                                    self.auto_configuration_str)

        # Save log
        if self.config.save_multi_level_performance_plotter_log:
            try:
                output_dir = Path(self.config.multi_level_performance_plotter_dir)
                output_dir.mkdir(parents=True, exist_ok=True)
                log_path = output_dir / "change_log.txt"
                with open(log_path, "a", encoding="utf-8") as log_file:
                    log_file.write(log_entries_str)
                self.logger.info("✓ Updated and saved change log: {}", log_path)
            except Exception as e:
                self.logger.error("✗ Failed to save change log {}: {}", log_path, e)
        
        return results, log_entries_str
    
    def day_level_process(self) -> Dict[str, Any]:
        """
        Plot and save plots & reports with optional parallel processing for day-level production data.
        
        Returns:
            Dictionary containing processing results
        """

        self.logger.info("Plotting day-level data.")
        
        day_level_results = self.orchestrator_results['multi_level_analytics']['results']['day_level_results']

        from agents.dashboardBuilder.multiLevelPerformancePlotter.day_level_data_plotter import DayLevelDataPlotter
        
        day_level_plotter = DayLevelDataPlotter(
            day_level_results = day_level_results,
            source_path = self.analytics_orchestrator_config.performance_config.source_path, 
            annotation_name = self.analytics_orchestrator_config.performance_config.annotation_name,
            databaseSchemas_path = self.analytics_orchestrator_config.performance_config.databaseSchemas_path,
            default_dir = self.config.multi_level_performance_plotter_dir,
            visualization_config_path = self.config.day_level_visualization_config_path,
            enable_parallel = self.config.enable_parallel,
            max_workers = self.config.max_workers
        )
        
        day_level_log_entries = day_level_plotter.plot_all()

        self.logger.info("Day-level data saved!")
    
        return {"status": "completed", 
                "result": {
                    "day_level_processor": day_level_results['log_entries'], 
                    "day_level_plotter": "".join(day_level_log_entries) if day_level_log_entries else None
                    }
                }

    def month_level_process(self) -> Dict[str, Any]:
        """
        Plot and save plots & reports with optional parallel processing for month-level production data.
        
        Returns:
            Dictionary containing processing results
        """

        self.logger.info("Plotting day-level data.")
        
        month_level_results = self.orchestrator_results['multi_level_analytics']['results']['month_level_results']

        from agents.dashboardBuilder.multiLevelPerformancePlotter.month_level_data_plotter import MonthLevelDataPlotter
        
        month_level_plotter = MonthLevelDataPlotter(
            month_level_results = month_level_results,
            source_path = self.analytics_orchestrator_config.performance_config.source_path, 
            annotation_name = self.analytics_orchestrator_config.performance_config.annotation_name,
            databaseSchemas_path = self.analytics_orchestrator_config.performance_config.databaseSchemas_path,
            default_dir = self.config.multi_level_performance_plotter_dir,
            visualization_config_path = self.config.day_level_visualization_config_path,
            enable_parallel = self.config.enable_parallel,
            max_workers = self.config.max_workers
        )
        
        month_level_log_entries = month_level_plotter.plot_all()

        self.logger.info("Month-level data saved!")
    
        return {"status": "completed", 
                "result": {
                    "month_level_processor": month_level_results['log_entries'], 
                    "month_level_plotter": "".join(month_level_log_entries) if month_level_log_entries else None
                    }
                }
    
    def year_level_process(self) -> Dict[str, Any]:
        """
        Plot and save plots & reports with optional parallel processing for year-level production data.
        
        Returns:
            Dictionary containing processing results
        """

        self.logger.info("Plotting day-level data.")
        
        year_level_results = self.orchestrator_results['multi_level_analytics']['results']['year_level_results']

        from agents.dashboardBuilder.multiLevelPerformancePlotter.year_level_data_plotter import YearLevelDataPlotter
        
        year_level_plotter = YearLevelDataPlotter(
            year_level_results = year_level_results,
            source_path = self.analytics_orchestrator_config.performance_config.source_path, 
            annotation_name = self.analytics_orchestrator_config.performance_config.annotation_name,
            databaseSchemas_path = self.analytics_orchestrator_config.performance_config.databaseSchemas_path,
            default_dir = self.config.multi_level_performance_plotter_dir,
            visualization_config_path = self.config.day_level_visualization_config_path,
            enable_parallel = self.config.enable_parallel,
            max_workers = self.config.max_workers
        )
        
        year_level_log_entries = year_level_plotter.plot_all()

        self.logger.info("Year-level data saved!")
    
        return {"status": "completed", 
                "result": {
                    "year_level_processor": year_level_results['log_entries'], 
                    "year_level_plotter": "".join(year_level_log_entries) if year_level_log_entries else None
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