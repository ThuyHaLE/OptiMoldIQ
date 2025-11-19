from loguru import logger
from dataclasses import dataclass
from typing import Dict, Optional, Any
from pathlib import Path
from datetime import datetime

from agents.dashboardBuilder.plotters.day_level_data_plotter import DayLevelDataPlotter
from agents.dashboardBuilder.plotters.month_level_data_plotter import MonthLevelDataPlotter
from agents.dashboardBuilder.plotters.year_level_data_plotter import YearLevelDataPlotter

@dataclass
class PlotflowConfig:
    """Configuration class for plotflow parameters"""

    # Day level
    record_date: Optional[str] = None
    day_visualization_config_path: Optional[str] = None
    
    # Month level
    record_month: Optional[str] = None
    month_analysis_date: Optional[str] = None
    month_visualization_config_path: Optional[str] = None
    
    # Year level
    record_year: Optional[str] = None
    year_analysis_date: Optional[str] = None
    year_visualization_config_path: Optional[str] = None
    
    # Shared paths
    source_path: str = 'agents/shared_db/DataLoaderAgent/newest'
    annotation_name: str = "path_annotations.json"
    databaseSchemas_path: str = 'database/databaseSchemas.json'
    default_dir: str = "agents/shared_db"

    # Optimal Processing
    enable_parallel: bool = True  # Enable parallel processing
    max_workers: Optional[int] = None  # Auto-detect optimal worker count


class MultiLevelDataPlotter: 
    """
    Unified interface for multi-level data analytics plotting.
    
    Orchestrates day/month/year-level data processors to generate
    structured analytics, plot and save reports and visualization.
    
    Architecture:
        MultiLevelDataPlotter (Service Layer)
            ├─ DayLevelDataPlotter
            ├─ MonthLevelDataPlotter
            └─ YearLevelDataPlotter
    
    Usage:
        config = PlotflowConfig(
            record_date="2025-11-16",
            record_month="2025-11",
            record_year="2025"
        )
        plotter = MultiLevelDataPlotter(config)
        results = plotter.data_process()
    """
    
    def __init__(self, config: PlotflowConfig):
        """
        Initialize MultiLevelDataPlotter with configuration.
        
        Args:
            config: PlotflowConfig containing time parameters and paths
        """
        self.logger = logger.bind(class_="MultiLevelDataPlotter")
        self.config = config
        self.logger.info("Initialized MultiLevelDataPlotter")

        # Setup directories
        self.default_dir = Path(self.config.default_dir)
        self.output_dir = self.default_dir / "MultiLevelDataPlotter"
        
    def data_process(self) -> Dict[str, Optional[Dict[str, Any]]]:
        """
        Execute multi-level data processing pipeline.
        
        Conditionally runs day/month/year processors based on config.
        Day/Month/year levels only run if respective dates are provided.
        """

        self.logger.info("Starting multi-level data processing pipeline")
        
        # Check if all dates are None
        if not any([self.config.record_date, 
                    self.config.record_month, 
                    self.config.record_year]):
            self.logger.warning("No dates configured - skipping all processing")
            return {
                "day_level_results": None,
                "month_level_results": None,
                "year_level_results": None
            }
        
        results = {
            "day_level_results": self._safe_process(
                self.day_level_process, 
                "day"
            ) if self.config.record_date else None,
            "month_level_results": self._safe_process(
                self.month_level_process, 
                "month"
            ) if self.config.record_month else None,
            "year_level_results": self._safe_process(
                self.year_level_process, 
                "year"
            ) if self.config.record_year else None
        }

        self.update_change_logs(results)

        return results
    
    def update_change_logs(self, results: Dict[str, Optional[Dict]]):
        """
        Update change log file with processing results and configuration.
        
        Args:
            results: Dictionary containing processing results for each level
        """
        timestamp_now = datetime.now()
        timestamp_str = timestamp_now.strftime("%Y-%m-%d %H:%M:%S")
        
        log_path = self.output_dir / "change_log.txt"
        log_entries = []

        # Prepare log entries
        log_entries.append(f"[{timestamp_str}] MultiLevelDataPlotter Run")
        log_entries.append("")

        # Configuration section
        log_entries.append("--Configuration--")

        log_entries.append(f"⤷ Output Directory: {self.output_dir}")
        log_entries.append(f"⤷ Source Path: {self.config.source_path}")
        log_entries.append(f"⤷ Parallel Enabled: {self.config.enable_parallel}")
        log_entries.append(f"⤷ Max Workers: {self.config.max_workers or 'Auto'}")

        if self.config.record_date != None:
            log_entries.append(f"Day Level:")
            log_entries.append(f"⤷ Record Date: {self.config.record_date}")
            log_entries.append(f"⤷ Viz Config: {self.config.day_visualization_config_path or 'Default'}")
        if self.config.record_month != None:
            log_entries.append(f"Month Level:")
            log_entries.append(f"⤷ Record Month: {self.config.record_month}")
            log_entries.append(f"⤷ Analysis Date: {self.config.month_analysis_date or 'Not set'}")
            log_entries.append(f"⤷ Viz Config: {self.config.month_visualization_config_path or 'Default'}")
        if self.config.record_year != None:
            log_entries.append(f"Year Level:")
            log_entries.append(f"⤷ Record Year: {self.config.record_year or 'Not set'}")
            log_entries.append(f"⤷ Analysis Date: {self.config.year_analysis_date or 'Not set'}")
            log_entries.append(f"⤷ Viz Config: {self.config.year_visualization_config_path or 'Default'}")

        log_entries.append("")
        
        # Processing summary
        log_entries_dict = self._log_processing_summary(results)
        
        log_entries.append("--Processing Summary--")
        
        # Skipped levels
        if 'Skipped' in log_entries_dict['Processing Summary']:
            log_entries.append(f"⤷ Skipped: {log_entries_dict['Processing Summary']['Skipped']}")
        
        # Completed levels
        if 'Completed' in log_entries_dict['Processing Summary']:
            completed_str = log_entries_dict['Processing Summary']['Completed']
            log_entries.append(f"⤷ Completed: {completed_str}")
        log_entries.append("")
        
        # Detailed results
        if log_entries_dict.get('Details'):
            log_entries.append("--Details--")
            for level_name, level_result in log_entries_dict['Details'].items():
                log_entries.append(f"⤷ {level_name}:")
                log_entries.append(''.join(level_result))
            log_entries.append("")
        
        # Write to file
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)

            with open(log_path, "a", encoding="utf-8") as log_file:
                log_file.write("\n".join(log_entries))
            
            self.logger.info("✓ Updated change log: {}", log_path)
            
        except Exception as e:
            self.logger.error("✗ Failed to update change log {}: {}", log_path, e)
            raise OSError(f"Failed to update change log {log_path}: {e}")
    
    def _log_processing_summary(self, results: Dict[str, Optional[Dict]]):
        """Log summary of processing results."""

        log_entries = {
            'Processing Summary': {},
            'Details': {}
        }

        self.logger.info("Processing Summary:")
        
        skipped = [k for k, v in results.items() if v is None]

        if skipped:
            skipped_info = ", ".join(skipped)
            self.logger.info("  ⊘ Skipped: {}", skipped_info)
            log_entries['Processing Summary']['Skipped'] = skipped_info

        completed = [k for k, v in results.items() if v is not None]
        completed_info = ", ".join(completed) if completed else "None"
    
        self.logger.info("  ✓ Completed: {}", completed_info)
        log_entries['Processing Summary']['Completed'] = completed_info
        
        for lv in completed:
            log_entries['Details'][lv] = results[lv]['result']

        return log_entries
    
    def day_level_process(self) -> Dict[str, Any]:
        """
        Plot and save plots & reports with optional parallel processing for day-level production data.
        
        Returns:
            Dictionary containing processing results
        """

        self.logger.info("Plotting day-level data for date: {}", self.config.record_date or "default")
        
        day_level_plotter = DayLevelDataPlotter(
            self.config.record_date,
            self.config.source_path,
            self.config.annotation_name,
            self.config.databaseSchemas_path,
            self.output_dir,
            self.config.day_visualization_config_path,
            self.config.enable_parallel,
            self.config.max_workers
        )
        
        log_entries = day_level_plotter.plot_all()

        self.logger.info("Day-level data for date: {} saved!", self.config.record_date or "default")
        
        return {"status": "completed", "date": self.config.record_date, "result": log_entries}
    
    def month_level_process(self) -> Dict[str, Any]:
        """
        Plot and save plots & reports with optional parallel processing for month-level production data.
        
        Returns:
            Dictionary containing processing results
        """

        self.logger.info("Processing month-level data for month: {}", self.config.record_month)
        
        month_level_plotter = MonthLevelDataPlotter(
            self.config.record_month,
            self.config.month_analysis_date,
            self.config.source_path,
            self.config.annotation_name,
            self.config.databaseSchemas_path,
            self.output_dir,
            self.config.month_visualization_config_path,
            self.config.enable_parallel,
            self.config.max_workers
        )

        log_entries = month_level_plotter.plot_all()

        # FIXED: Changed to use record_month instead of record_date
        self.logger.info("Month-level data for month: {} saved!", self.config.record_month)
        
        return {"status": "completed", "month": self.config.record_month, "result": log_entries}
        
    def year_level_process(self) -> Dict[str, Any]:
        """
        Plot and save plots & reports with optional parallel processing for year-level production data.
        
        Returns:
            Dictionary containing processing results
        """

        self.logger.info("Processing year-level data for year: {}", self.config.record_year)
        
        year_level_plotter = YearLevelDataPlotter(
            self.config.record_year,
            self.config.year_analysis_date,
            self.config.source_path,
            self.config.annotation_name,
            self.config.databaseSchemas_path,
            self.output_dir,
            self.config.year_visualization_config_path,
            self.config.enable_parallel,
            self.config.max_workers
        )
        
        log_entries = year_level_plotter.plot_all()

        # FIXED: Changed to use record_year instead of record_date
        self.logger.info("Year-level data for year: {} saved!", self.config.record_year)
        
        return {"status": "completed", "year": self.config.record_year, "result": log_entries}
    
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