from loguru import logger
from dataclasses import dataclass
from typing import Dict, Optional, Any

from agents.analyticsOrchestrator.multiLevelDataAnalytics.day_level_data_processor import DayLevelDataProcessor
from agents.analyticsOrchestrator.multiLevelDataAnalytics.month_level_data_processor import MonthLevelDataProcessor
from agents.analyticsOrchestrator.multiLevelDataAnalytics.year_level_data_processor import YearLevelDataProcessor


@dataclass
class AnalyticflowConfig:
    """Configuration class for analyticflow parameters"""
    
    # Day level
    record_date: Optional[str] = None
    
    # Month level
    record_month: Optional[str] = None
    month_analysis_date: Optional[str] = None
    
    # Year level
    record_year: Optional[str] = None
    year_analysis_date: Optional[str] = None
    
    # Shared paths
    source_path: str = 'agents/shared_db/DataLoaderAgent/newest'
    annotation_name: str = "path_annotations.json"
    databaseSchemas_path: str = 'database/databaseSchemas.json'
    default_dir: str = "agents/shared_db"


class MultiLevelDataAnalytics:
    """
    Unified interface for multi-level data analytics processing.
    
    Orchestrates day/month/year-level data processors to generate
    structured analytics outputs for consumption by dashboard builders
    and future agents (planRefiner, taskOrchestrator).
    
    Architecture:
        MultiLevelDataAnalytics (Service Layer)
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
    
    def __init__(self, config: AnalyticflowConfig):
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
        
        self._log_processing_summary(results)

        return results
    
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
        """
        self.logger.info("Processing day-level data for date: {}", 
                        self.config.record_date or "default")
        
        day_level_processor = DayLevelDataProcessor(
            self.config.record_date,
            self.config.source_path,
            self.config.annotation_name,
            self.config.databaseSchemas_path,
            self.config.default_dir
        )
        
        (processed_df, mold_based_record_df, 
         item_based_record_df, summary_stats) = day_level_processor.product_record_processing()
        
        return {
            "processed_records": processed_df,
            "mold_based_records": mold_based_record_df,
            "item_based_records": item_based_record_df,
            "summary_stats": summary_stats
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
                - summary_stats: Monthly summary statistics
        """
        self.logger.info("Processing month-level data for month: {}", 
                        self.config.record_month)
        
        month_level_processor = MonthLevelDataProcessor(
            self.config.record_month,
            self.config.month_analysis_date,
            self.config.source_path,
            self.config.annotation_name,
            self.config.databaseSchemas_path,
            self.config.default_dir
        )
        
        (analysis_timestamp, adjusted_record_month, 
         finished_df, unfinished_df, 
         final_summary) = month_level_processor.product_record_processing()
        
        return {
            "record_month": adjusted_record_month,
            "month_analysis_date": analysis_timestamp,
            "finished_records": finished_df,
            "unfinished_records": unfinished_df,
            "summary_stats": final_summary
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
                - summary_stats: Yearly summary statistics
        """
        self.logger.info("Processing year-level data for year: {}", 
                        self.config.record_year)
        
        year_level_processor = YearLevelDataProcessor(
            self.config.record_year,
            self.config.year_analysis_date,
            self.config.source_path,
            self.config.annotation_name,
            self.config.databaseSchemas_path,
            self.config.default_dir
        )
        
        (analysis_timestamp, adjusted_record_year, 
         finished_df, unfinished_df, 
         final_summary) = year_level_processor.product_record_processing()
        
        return {
            "record_year": adjusted_record_year,
            "year_analysis_date": analysis_timestamp,
            "finished_records": finished_df,
            "unfinished_records": unfinished_df,
            "summary_stats": final_summary
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
    
    def _log_processing_summary(self, results: Dict[str, Optional[Dict]]):
        
        """Log summary of processing results."""
        completed = [k for k, v in results.items() if v is not None]
        skipped = [k for k, v in results.items() if v is None]
        
        self.logger.info("Processing Summary:")
        self.logger.info("  ✓ Completed: {}", ", ".join(completed) if completed else "None")
        if skipped:
            self.logger.info("  ⊘ Skipped: {}", ", ".join(skipped))