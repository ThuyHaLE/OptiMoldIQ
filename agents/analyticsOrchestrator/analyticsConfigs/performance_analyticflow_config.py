from dataclasses import dataclass
from typing import Optional
from agents.utils import validate_path

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

    save_multi_level_performance_analyzer_log: bool = True
    multi_level_performance_analyzer_dir: str = "agents/shared_db/AnalyticsOrchestrator/MultiLevelPerformanceAnalyzer"

    def __post_init__(self):
        """Validate directory settings when saving is enabled."""
        if self.save_multi_level_performance_analyzer_log:
            validate_path("multi_level_performance_analyzer_dir", self.multi_level_performance_analyzer_dir)