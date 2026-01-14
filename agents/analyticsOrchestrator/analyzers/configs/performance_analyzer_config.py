from dataclasses import dataclass, field
from typing import Optional, Dict, List
from configs.shared.shared_source_config import SharedSourceConfig

@dataclass
class LevelConfig:
    """Configuration for a single processing level"""
    requested_timestamp: Optional[str] = None
    analysis_date: Optional[str] = None
    save_result: Optional[bool] = None

@dataclass
class PerformanceAnalyzerConfig:
    """Configuration class for multi-level performance analysis
    
    This class manages configuration for day, month, and year level processors.
    Each level can be independently enabled/disabled and configured with specific
    timestamps and save settings.
    """
    
    # Shared source configs
    shared_source_config: SharedSourceConfig = field(default_factory=SharedSourceConfig)

    # Day level configuration
    enable_day_level_processor: Optional[bool] = None
    day_level_processor_params: LevelConfig = field(default_factory=LevelConfig)

    # Month level configuration
    enable_month_level_processor: Optional[bool] = None
    month_level_processor_params: LevelConfig = field(default_factory=LevelConfig)

    # Year level configuration
    enable_year_level_processor: Optional[bool] = None
    year_level_processor_params: LevelConfig = field(default_factory=LevelConfig)

    # Multi-level analyzer logging
    save_multi_level_performance_analyzer_log: Optional[bool] = None

    # Class-level defaults
    DEFAULT_ENABLE_DAY_LEVEL_PROCESSOR = False
    DEFAULT_ENABLE_MONTH_LEVEL_PROCESSOR = False
    DEFAULT_ENABLE_YEAR_LEVEL_PROCESSOR = False
    
    DEFAULT_SAVE_DAY_RESULT = True
    DEFAULT_SAVE_MONTH_YEAR_RESULT = True

    def __post_init__(self):
        """Apply default values and validate configuration"""
        
        # Apply default enable/disable values
        if self.enable_day_level_processor is None:
            self.enable_day_level_processor = self.DEFAULT_ENABLE_DAY_LEVEL_PROCESSOR
        
        if self.enable_month_level_processor is None:
            self.enable_month_level_processor = self.DEFAULT_ENABLE_MONTH_LEVEL_PROCESSOR
        
        if self.enable_year_level_processor is None:
            self.enable_year_level_processor = self.DEFAULT_ENABLE_YEAR_LEVEL_PROCESSOR

        # Apply default values for each level's parameters
        self._apply_level_defaults()
        
        # Enable multi-level logging if any processor is enabled
        if self.save_multi_level_performance_analyzer_log is None:
            self.save_multi_level_performance_analyzer_log = (
                self.enable_day_level_processor or 
                self.enable_month_level_processor or 
                self.enable_year_level_processor
            )

    def _apply_level_defaults(self) -> None:
        """Apply default values for each level's parameters
        
        Day level: Uses DEFAULT_SAVE_DAY_RESULT when save_result is None
        Month/Year levels: Uses DEFAULT_SAVE_MONTH_YEAR_RESULT when save_result is None
                          AND requested_timestamp is provided
        """
        if self.enable_day_level_processor: 
            if self.day_level_processor_params.save_result is None:
                self.day_level_processor_params.save_result = self.DEFAULT_SAVE_DAY_RESULT
        
        if self.enable_month_level_processor: 
            if self.month_level_processor_params.save_result is None:
                has_timestamp = self.month_level_processor_params.requested_timestamp is not None
                self.month_level_processor_params.save_result = (
                    self.DEFAULT_SAVE_MONTH_YEAR_RESULT if has_timestamp else False
                )
        
        if self.enable_year_level_processor: 
            if self.year_level_processor_params.save_result is None:
                has_timestamp = self.year_level_processor_params.requested_timestamp is not None
                self.year_level_processor_params.save_result = (
                    self.DEFAULT_SAVE_MONTH_YEAR_RESULT if has_timestamp else False
                )

    def validate(self) -> None:
        """Validate configuration consistency
        
        Raises:
            ValueError: If month/year processors are enabled without timestamps
        """
        if self.enable_month_level_processor:
            if self.month_level_processor_params.requested_timestamp is None:
                raise ValueError(
                    "Month level processor requires requested_timestamp to be set"
                )
        
        if self.enable_year_level_processor:
            if self.year_level_processor_params.requested_timestamp is None:
                raise ValueError(
                    "Year level processor requires requested_timestamp to be set"
                )

    def get_enabled_levels(self) -> List[str]:
        """Get list of enabled processing levels
        
        Returns:
            List of enabled level names (e.g., ['DAY', 'MONTH'])
        """
        levels = []
        if self.enable_day_level_processor: 
            levels.append("DAY")
        if self.enable_month_level_processor: 
            levels.append("MONTH")
        if self.enable_year_level_processor: 
            levels.append("YEAR")
        return levels
    
    def get_level_params(self) -> Dict[str, Dict]:
        """Get parameters for all enabled levels
        
        Returns:
            Dictionary mapping level names to their parameter dictionaries
        """
        params = {}
        if self.enable_day_level_processor: 
            params["DAY"] = self.day_level_processor_params
        if self.enable_month_level_processor: 
            params["MONTH"] = self.month_level_processor_params
        if self.enable_year_level_processor: 
            params["YEAR"] = self.year_level_processor_params
        return params