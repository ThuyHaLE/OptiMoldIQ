from loguru import logger
from typing import Dict, Optional, Any
from pathlib import Path

from agents.analyticsOrchestrator.multiLevelPerformanceAnalyzer.day_level_data_processor import DayLevelDataProcessor
from agents.analyticsOrchestrator.multiLevelPerformanceAnalyzer.month_level_data_processor import MonthLevelDataProcessor
from agents.analyticsOrchestrator.multiLevelPerformanceAnalyzer.year_level_data_processor import YearLevelDataProcessor

from agents.analyticsOrchestrator.analyticsConfigs.performance_analyticflow_config import PerformanceAnalyticflowConfig
from agents.analyticsOrchestrator.logStrFormatters.multi_level_performance_analyzer_formatter import build_multi_level_performance_analyzer_log

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
        
        log_entries_str = build_multi_level_performance_analyzer_log(self.config, results)

        # Save log
        if self.config.save_multi_level_performance_analyzer_log:
            try:
                output_dir = Path(self.config.multi_level_performance_analyzer_dir)
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
            self.config.multi_level_performance_analyzer_dir
        )
        
        (adjusted_record_date, processed_df, 
         mold_based_record_df, item_based_record_df, 
         summary_stats, analysis_summary, log_entries) = day_level_processor.data_process(
            self.config.day_save_output)
        
        return {
            "record_date": adjusted_record_date,
            "processed_records": processed_df,
            "mold_based_records": mold_based_record_df,
            "item_based_records": item_based_record_df,
            "summary_stats": summary_stats,
            "analysis_summary": analysis_summary,
            "log_entries": "".join(log_entries) if log_entries else None
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
            self.config.multi_level_performance_analyzer_dir
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
            "log_entries": "".join(log_entries) if log_entries else None
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
            self.config.multi_level_performance_analyzer_dir
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
            "log_entries": "".join(log_entries) if log_entries else None
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