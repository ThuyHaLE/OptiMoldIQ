from loguru import logger
from dataclasses import dataclass
from typing import Dict, Optional, Any

from agents.analyticsOrchestrator.multiLevelPerformanceAnalyzer.day_level_data_processor import DayLevelDataProcessor
from agents.analyticsOrchestrator.multiLevelPerformanceAnalyzer.month_level_data_processor import MonthLevelDataProcessor
from agents.analyticsOrchestrator.multiLevelPerformanceAnalyzer.year_level_data_processor import YearLevelDataProcessor
from pathlib import Path
from datetime import datetime

@dataclass
class PerformanceAnalyticflowConfig:
    """Configuration class for analyticflow parameters"""
    
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
    
    # Shared paths
    source_path: str = 'agents/shared_db/DataLoaderAgent/newest'
    annotation_name: str = "path_annotations.json"
    databaseSchemas_path: str = 'database/databaseSchemas.json'
    default_dir: str = "agents/shared_db/AnalyticsOrchestrator/MultiLevelDataAnalytics"


class MultiLevelPerformanceAnalyzer:
    """
    Unified interface for multi-level data analytics processing.
    
    Orchestrates day/month/year-level data processors to generate
    structured analytics outputs for consumption by dashboard builders
    and future agents (planRefiner, taskOrchestrator).
    
    Architecture:
        MultiLevelPerformanceAnalyzer (Service Layer)
            ├─ DayLevelDataProcessor
            ├─ MonthLevelDataProcessor  
            └─ YearLevelDataProcessor
    
    Usage:
        config = AnalyticflowConfig(
            record_date="2025-11-16",
            record_month="2025-11",
            record_year="2025"
        )
        analytics = MultiLevelDataAnalytics(config)
        results = analytics.data_process()
    """
    
    def __init__(self, config: PerformanceAnalyticflowConfig):
        """
        Initialize MultiLevelDataAnalytics with configuration.
        
        Args:
            config: AnalyticflowConfig containing time parameters and paths
        """
        self.logger = logger.bind(class_="MultiLevelDataAnalytics")
        self.config = config
        self.logger.info("Initialized MultiLevelDataAnalytics")

        self.output_dir = Path(self.config.default_dir)
        
    def data_process(self) -> Dict[str, Optional[Dict[str, Any]]]:
        """
        Execute multi-level data processing pipeline.
        
        Conditionally runs day/month/year processors based on config.
        Day-level always runs (supports default date if not specified).
        Month/year levels only run if respective dates are provided.
        
        Returns:
            Dict containing results from each level:
            {
                "day_level_results": {...},
                "month_level_results": {...} or None,
                "year_level_results": {...} or None
            }
        """

        self.logger.info("Starting multi-level data processing pipeline")
        
        results = {
            "day_level_results": self._safe_process(
                self.day_level_process, 
                "day"
            ),
            "month_level_results": self._safe_process(
                self.month_level_process, 
                "month"
            ) if self.config.record_month else None,
            "year_level_results": self._safe_process(
                self.year_level_process, 
                "year"
            ) if self.config.record_year else None
        }
        
        log_entries_str = self.update_change_logs(results)

        return results, log_entries_str
    
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
        log_entries.append(f"[{timestamp_str}] multiLevelDataAnalytics Run")
        log_entries.append("")

        # Configuration section
        log_entries.append("--Configuration--")

        log_entries.append(f"⤷ Output Directory: {self.config.default_dir}")
        log_entries.append(f"⤷ Source Path: {self.config.source_path}")

        if self.config.record_date is not None:
            log_entries.append(f"Day Level:")
            log_entries.append(f"⤷ Record Date: {self.config.record_date}")
            log_entries.append(f"⤷ Save output: {self.config.day_save_output}")
        if self.config.record_month is not None:
            log_entries.append(f"Month Level:")
            log_entries.append(f"⤷ Record Month: {self.config.record_month}")
            log_entries.append(f"⤷ Analysis Date: {self.config.month_analysis_date or 'Not set'}")
            log_entries.append(f"⤷ Save output: {self.config.month_save_output}")
        if self.config.record_year is not None:
            log_entries.append(f"Year Level:")
            log_entries.append(f"⤷ Record Year: {self.config.record_year or 'Not set'}")
            log_entries.append(f"⤷ Analysis Date: {self.config.year_analysis_date or 'Not set'}")
            log_entries.append(f"⤷ Save output: {self.config.year_save_output}")

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

        return "\n".join(log_entries)
    
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
            if results[lv]["log_entries"] is not None:
                log_entries['Details'][lv] = results[lv]["log_entries"]
            else: 
                log_entries['Details'][lv] = [f"Only process the data without saving any results.\n-{lv}_summary:\n", results[lv]['analysis_summary']]

        return log_entries

    def day_level_process(self) -> Dict[str, Any]:
        """
        Process day-level production data.
        
        Supports default date if record_date not specified.
        
        Returns:
            Dict containing:
                - processed_records: Main processed DataFrame
                - mold_based_records: Mold-aggregated data
                - item_based_records: Item-aggregated data
                - summary_stats: Statistical summary
                - analysis_summary: Analysis summary
        """
        self.logger.info("Processing day-level data for date: {}", 
                        self.config.record_date or "default")
        
        day_level_processor = DayLevelDataProcessor(
            self.config.record_date,
            self.config.source_path,
            self.config.annotation_name,
            self.config.databaseSchemas_path,
            self.output_dir
        )
        
        (processed_df, mold_based_record_df, 
        item_based_record_df, summary_stats, analysis_summary, log_entries) = day_level_processor.data_process(
            self.config.day_save_output)
        
        return {
            "processed_records": processed_df,
            "mold_based_records": mold_based_record_df,
            "item_based_records": item_based_record_df,
            "summary_stats": summary_stats,
            "analysis_summary": analysis_summary,
            "log_entries": log_entries
        }
    
    def month_level_process(self) -> Dict[str, Any]:
        """
        Process month-level production data.
        
        Requires record_month to be specified in config.
        
        Returns:
            Dict containing:
                - record_month: Adjusted month string
                - month_analysis_date: Timestamp of analysis
                - finished_records: Completed orders DataFrame
                - unfinished_records: In-progress orders DataFrame
                - analysis_summary: Analysis summary
        """
        self.logger.info("Processing month-level data for month: {}", 
                        self.config.record_month)
        
        month_level_processor = MonthLevelDataProcessor(
            self.config.record_month,
            self.config.month_analysis_date,
            self.config.source_path,
            self.config.annotation_name,
            self.config.databaseSchemas_path,
            self.output_dir
        )
        
        (analysis_timestamp, adjusted_record_month, 
        finished_df, unfinished_df, 
        analysis_summary, log_entries) = month_level_processor.data_process(
                self.config.month_save_output)
    
        return {
            "record_month": adjusted_record_month,
            "month_analysis_date": analysis_timestamp,
            "finished_records": finished_df,
            "unfinished_records": unfinished_df,
            "analysis_summary": analysis_summary,
            "log_entries": log_entries
        }
    
    def year_level_process(self) -> Dict[str, Any]:
        """
        Process year-level production data.
        
        Requires record_year to be specified in config.
        
        Returns:
            Dict containing:
                - record_year: Adjusted year string
                - year_analysis_date: Timestamp of analysis
                - finished_records: Completed orders DataFrame
                - unfinished_records: In-progress orders DataFrame
                - analysis_summary: Analysis summary
        """
        self.logger.info("Processing year-level data for year: {}", 
                        self.config.record_year)
        
        year_level_processor = YearLevelDataProcessor(
            self.config.record_year,
            self.config.year_analysis_date,
            self.config.source_path,
            self.config.annotation_name,
            self.config.databaseSchemas_path,
            self.output_dir
        )

        (analysis_timestamp, adjusted_record_year, 
        finished_df, unfinished_df, 
        analysis_summary, log_entries) = year_level_processor.data_process(
                self.config.year_save_output)
    
        return {
            "record_year": adjusted_record_year,
            "year_analysis_date": analysis_timestamp,
            "finished_records": finished_df,
            "unfinished_records": unfinished_df,
            "analysis_summary": analysis_summary,
            "log_entries": log_entries
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
            return None