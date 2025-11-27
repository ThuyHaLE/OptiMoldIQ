from dataclasses import dataclass
from typing import Optional
from agents.utils import validate_path

@dataclass
class PerformancePlotflowConfig:
    """Configuration class for plotflow parameters"""
    
    # Shared paths
    source_path: str = 'agents/shared_db/DataLoaderAgent/newest'
    annotation_name: str = "path_annotations.json"
    databaseSchemas_path: str = 'database/databaseSchemas.json'

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
    save_analytics_orchestrator_log: bool = False
    analytics_orchestrator_dir: str = 'agents/shared_db/DashboardBuilder'

    save_multi_level_performance_analyzer_log: bool = True
    multi_level_performance_analyzer_dir: str = "agents/shared_db/DashboardBuilder/MultiLevelPerformanceAnalyzer"

    # Day level
    record_date: Optional[str] = None
    
    # Month level
    record_month: Optional[str] = None
    month_analysis_date: Optional[str] = None
    
    # Year level
    record_year: Optional[str] = None
    year_analysis_date: Optional[str] = None

    def __post_init__(self):
        """Validate directory settings when saving is enabled."""

        if self.save_multi_level_performance_plotter_log:
            validate_path("multi_level_performance_plotter_dir", self.multi_level_performance_plotter_dir)

        if self.save_analytics_orchestrator_log:
            validate_path("analytics_orchestrator_dir", self.analytics_orchestrator_dir)
        
        if self.save_multi_level_performance_analyzer_log:
            validate_path("multi_level_performance_analyzer_dir", self.multi_level_performance_analyzer_dir)