from loguru import logger
from typing import Dict, Optional, Any
from pathlib import Path

from agents.analyticsOrchestrator.analyticsConfigs.analytics_orchestrator_config import AnalyticsOrchestratorConfig
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
        self.logger.info("Initialized MultiLevelPerformancePlotter")

        try:
            orchestrator = AnalyticsOrchestrator(
                AnalyticsOrchestratorConfig(
                # Enable AnalyticsOrchestrator components
                enable_multi_level_analysis = (self.config.record_date is not None 
                                               or self.config.record_month is not None
                                               or self.config.record_year is not None),

                # Database sources
                source_path = self.config.source_path,
                annotation_name = self.config.annotation_name,
                databaseSchemas_path = self.config.databaseSchemas_path,

                save_analytics_orchestrator_log = self.config.save_analytics_orchestrator_log,
                analytics_orchestrator_dir = self.config.analytics_orchestrator_dir,

                # MultiLevelPerformanceAnalyzer config
                record_date=self.config.record_date,
                day_save_output = self.config.record_date is not None,

                record_month=self.config.record_month,
                month_analysis_date=self.config.month_analysis_date,
                month_save_output = self.config.record_month is not None,

                record_year=self.config.record_year,
                year_analysis_date=self.config.year_analysis_date,
                year_save_output = self.config.record_year is not None,

                save_multi_level_performance_analyzer_log = self.config.save_multi_level_performance_analyzer_log,
                multi_level_performance_analyzer_dir = self.config.multi_level_performance_analyzer_dir
                )
            )

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
            "day_level_results": self._safe_process(
                self.day_level_process, 
                "day"
            ) if self.config.record_date is not None else None,

            "month_level_results": self._safe_process(
                self.month_level_process, 
                "month"
            ) if self.config.record_month is not None else None,

            "year_level_results": self._safe_process(
                self.year_level_process, 
                "year"
            ) if self.config.record_year is not None else None,
        }

        log_entries_str = build_multi_level_performance_plotter_log(self.config, results)

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
            source_path = self.config.source_path, 
            annotation_name = self.config.annotation_name,
            databaseSchemas_path = self.config.databaseSchemas_path,
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
                    "day_level_plotter": "".join(day_level_log_entries)
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
            source_path = self.config.source_path, 
            annotation_name = self.config.annotation_name,
            databaseSchemas_path = self.config.databaseSchemas_path,
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
                    "month_level_plotter": "".join(month_level_log_entries)
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
            source_path = self.config.source_path, 
            annotation_name = self.config.annotation_name,
            databaseSchemas_path = self.config.databaseSchemas_path,
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
                    "year_level_plotter": "".join(year_level_log_entries)
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