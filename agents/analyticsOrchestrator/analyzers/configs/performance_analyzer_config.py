from dataclasses import dataclass, field
from typing import Optional
from configs.shared.shared_source_config import SharedSourceConfig

@dataclass
class PerformanceAnalyzerConfig:
    """Configuration class for analyticflow parameters"""
    
    # Shared source configs
    shared_source_config: SharedSourceConfig = field(default_factory=SharedSourceConfig)

    # Day level
    record_date: Optional[str] = None
    save_day_result: Optional[bool] = None
    
    # Month level
    record_month: Optional[str] = None
    month_analysis_date: Optional[str] = None
    save_month_result: Optional[bool] = None
    
    # Year level
    record_year: Optional[str] = None
    year_analysis_date: Optional[str] = None
    save_year_result: Optional[bool] = None

    # Save MultiLevelPerformanceAnalyzer change log
    save_multi_level_performance_analyzer_log: Optional[bool] = None

    # Class-level defaults
    SAVE_DAY_RESULT = False
    SAVE_MONTH_RESULT = False
    SAVE_YEAR_RESULT = False

    def __post_init__(self):
        """Apply default values with conditional logic"""
        # Save flags: True if record_* is set, otherwise use default
        self.save_day_result = self._get_conditional_default(
            self.save_day_result,
            self.record_date is not None,
            self.SAVE_DAY_RESULT
        )
        
        self.save_month_result = self._get_conditional_default(
            self.save_month_result,
            self.record_month is not None,
            self.SAVE_MONTH_RESULT
        )
        
        self.save_year_result = self._get_conditional_default(
            self.save_year_result,
            self.record_year is not None,
            self.SAVE_YEAR_RESULT
        )
        
        # Multi-level log: True if any level is being saved
        self.save_multi_level_performance_analyzer_log = self._get_default(
            self.save_multi_level_performance_analyzer_log,
            self.save_day_result or self.save_month_result or self.save_year_result
        )

    @staticmethod
    def _get_conditional_default(value, condition, default):
        """Return condition result if value is None, otherwise return value"""
        if value is not None:
            return value
        return condition if condition else default
    
    @staticmethod
    def _get_default(value, default):
        """Return default if value is None"""
        return default if value is None else value