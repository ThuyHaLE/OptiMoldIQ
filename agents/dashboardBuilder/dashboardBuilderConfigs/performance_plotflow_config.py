from dataclasses import dataclass, field
from typing import Optional
from agents.utils import validate_path
from agents.analyticsOrchestrator.analyticsConfigs.analytics_orchestrator_config import AnalyticsOrchestratorConfig

@dataclass
class PerformancePlotflowConfig:
    """Configuration class for plotflow parameters"""
    
    enable_day_level_plotter: bool = False
    enable_month_level_plotter: bool = False
    enable_year_level_plotter: bool = False

    # MultiLevelPerformancePlotter config
    save_multi_level_performance_plotter_log: bool = True
    multi_level_performance_plotter_dir: str = "agents/shared_db/DashboardBuilder/MultiLevelPerformancePlotter"

    day_level_visualization_config_path: Optional[str] = None
    month_level_visualization_config_path: Optional[str] = None
    year_level_visualization_config_path: Optional[str] = None

    # Optimal Processing
    enable_parallel: bool = True  # Enable parallel processing
    max_workers: Optional[int] = None  # Auto-detect optimal worker count

    # AnalyticsOrchestrator config
    analytics_orchestrator_config: AnalyticsOrchestratorConfig = field(default_factory=AnalyticsOrchestratorConfig)

    def __post_init__(self):
        """Validate directory settings when saving is enabled."""
        if self.save_multi_level_performance_plotter_log:
            validate_path("multi_level_performance_plotter_dir", self.multi_level_performance_plotter_dir)
        if self.day_level_visualization_config_path is not None:
            validate_path("analytics_orchestrator_dir", self.day_level_visualization_config_path)
        if self.month_level_visualization_config_path is not None:
            validate_path("analytics_orchestrator_dir", self.month_level_visualization_config_path)
        if self.year_level_visualization_config_path is not None:
            validate_path("analytics_orchestrator_dir", self.year_level_visualization_config_path)