from dataclasses import dataclass, field
from typing import Optional, Dict, List
from configs.shared.shared_source_config import SharedSourceConfig
from agents.analyticsOrchestrator.analytics_orchestrator_config import LevelConfig

@dataclass
class PerformanceVisualizationConfig:
    """Configuration class for multi-level performance visualization service.
    
    This class manages configuration for day, month, and year level services.
    Each level can be independently enabled/disabled and configured with specific timestamps and save settings.
    """

    # Shared source configs
    shared_source_config: SharedSourceConfig = field(default_factory=SharedSourceConfig)

    # Day level configuration
    enable_day_level_visualization: Optional[bool] = None
    day_level_visualization_params: LevelConfig = field(default_factory=LevelConfig)

    # Month level configuration
    enable_month_level_visualization: Optional[bool] = None
    month_level_visualization_params: LevelConfig = field(default_factory=LevelConfig)

    # Year level configuration
    enable_year_level_visualization: Optional[bool] = None
    year_level_visualization_params: LevelConfig = field(default_factory=LevelConfig)

    # Multi-level analyzer logging
    save_multi_level_performance_visualization_log: Optional[bool] = None

    # Class-level defaults
    DEFAULT_ENABLE_DAY_LEVEL_VISUALIZATION = False
    DEFAULT_ENABLE_MONTH_LEVEL_VISUALIZATION = False
    DEFAULT_ENABLE_YEAR_LEVEL_VISUALIZATION = False
    
    DEFAULT_SAVE_DAY_RESULT = True
    DEFAULT_SAVE_MONTH_YEAR_RESULT = True

    def __post_init__(self):
        """Apply default values and validate configuration"""
        
        # Apply default enable/disable values
        if self.enable_day_level_visualization is None:
            self.enable_day_level_visualization = self.DEFAULT_ENABLE_DAY_LEVEL_VISUALIZATION
        
        if self.enable_month_level_visualization is None:
            self.enable_month_level_visualization = self.DEFAULT_ENABLE_MONTH_LEVEL_VISUALIZATION
        
        if self.enable_year_level_visualization is None:
            self.enable_year_level_visualization = self.DEFAULT_ENABLE_YEAR_LEVEL_VISUALIZATION

        # Apply default values for each level's parameters
        self._apply_level_defaults()
        
        # Enable multi-level logging if any visualization is enabled
        if self.save_multi_level_performance_visualization_log is None:
            self.save_multi_level_performance_visualization_log = (
                self.enable_day_level_visualization or 
                self.enable_month_level_visualization or 
                self.enable_year_level_visualization
            )

    def _apply_level_defaults(self) -> None:
        """Apply default values for each level's parameters
        
        Day level: Uses DEFAULT_SAVE_DAY_RESULT when save_result is None
        Month/Year levels: Uses DEFAULT_SAVE_MONTH_YEAR_RESULT when save_result is None
                          AND requested_timestamp is provided
        """
        if self.enable_day_level_visualization: 
            if self.day_level_visualization_params.save_result is None:
                self.day_level_visualization_params.save_result = self.DEFAULT_SAVE_DAY_RESULT
        
        if self.enable_month_level_visualization: 
            if self.month_level_visualization_params.save_result is None:
                has_timestamp = self.month_level_visualization_params.requested_timestamp is not None
                self.month_level_visualization_params.save_result = (
                    self.DEFAULT_SAVE_MONTH_YEAR_RESULT if has_timestamp else False
                )

        if self.enable_year_level_visualization: 
            if self.year_level_visualization_params.save_result is None:
                has_timestamp = self.year_level_visualization_params.requested_timestamp is not None
                self.year_level_visualization_params.save_result = (
                    self.DEFAULT_SAVE_MONTH_YEAR_RESULT if has_timestamp else False
                )

    def validate(self) -> None:
        """Validate configuration consistency
        
        Raises:
            ValueError: If month/year processors are enabled without timestamps
        """
        if self.enable_month_level_visualization:
            if self.month_level_visualization_params.requested_timestamp is None:
                raise ValueError(
                    "Month level visualization requires requested_timestamp to be set"
                )

        if self.enable_year_level_visualization:
            if self.year_level_visualization_params.requested_timestamp is None:
                raise ValueError(
                    "Year level visualization requires requested_timestamp to be set"
                )

    def get_enabled_levels(self) -> List[str]:
        """Get list of enabled processing levels
        
        Returns:
            List of enabled level names (e.g., ['DAY', 'MONTH'])
        """
        levels = []
        if self.enable_day_level_visualization: 
            levels.append("DAY")
        if self.enable_month_level_visualization: 
            levels.append("MONTH")
        if self.enable_year_level_visualization: 
            levels.append("YEAR")
        return levels
    
    def get_level_params(self) -> Dict[str, Dict]:
        """Get parameters for all enabled levels
        
        Returns:
            Dictionary mapping level names to their parameter dictionaries
        """
        params = {}
        if self.enable_day_level_visualization: 
            params["DAY"] = self.day_level_visualization_params
        if self.enable_month_level_visualization: 
            params["MONTH"] = self.month_level_visualization_params
        if self.enable_year_level_visualization: 
            params["YEAR"] = self.year_level_visualization_params
        return params