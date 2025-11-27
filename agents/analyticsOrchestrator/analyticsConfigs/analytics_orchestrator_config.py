from dataclasses import dataclass
from typing import Optional
from agents.utils import validate_path

@dataclass
class AnalyticsOrchestratorConfig:
    """Configuration class for analytics orchestrator parameters"""

    # Enable AnalyticsOrchestrator components
    enable_hardware_change_analysis: bool = False #HardwareChangeAnalyzer
    enable_multi_level_analysis: bool = False #MultiLevelPerformanceAnalyzer

    # Database sources
    source_path: str = 'agents/shared_db/DataLoaderAgent/newest'
    annotation_name: str = "path_annotations.json"
    databaseSchemas_path: str = 'database/databaseSchemas.json'

    save_analytics_orchestrator_log: bool = False
    analytics_orchestrator_dir: str = 'agents/shared_db/AnalyticsOrchestrator'
    
    # HardwareChangeAnalyzer config
    enable_machine_layout_tracker: bool = False
    enable_machine_mold_pair_tracker: bool = False

    save_hardware_change_analyzer_log: bool = True
    hardware_change_analyzer_dir: str = "agents/shared_db/AnalyticsOrchestrator/HardwareChangeAnalyzer"

    machine_layout_tracker_dir: str = "agents/shared_db/AnalyticsOrchestrator/HardwareChangeAnalyzer/UpdateMachineLayout"
    machine_layout_tracker_change_log_name: str = "change_log.txt"

    machine_mold_pair_tracker_dir: str = "agents/shared_db/AnalyticsOrchestrator/HardwareChangeAnalyzer/UpdateMoldOverview"
    machine_mold_pair_tracker_change_log_name: str = "change_log.txt"
            
    # MultiLevelPerformanceAnalyzer config
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

    # Output directory
    save_multi_level_performance_analyzer_log: bool = False
    multi_level_performance_analyzer_dir: str = "agents/shared_db/AnalyticsOrchestrator/MultiLevelPerformanceAnalyzer"

    def __post_init__(self):
        """Validate directory settings when saving is enabled."""

        validate_path("machine_layout_tracker_dir", self.machine_layout_tracker_dir)
        validate_path("machine_mold_pair_tracker_dir", self.machine_mold_pair_tracker_dir)

        if self.save_analytics_orchestrator_log:
            validate_path("analytics_orchestrator_dir", self.analytics_orchestrator_dir)

        if self.save_hardware_change_analyzer_log:
            validate_path("hardware_change_analyzer_dir", self.hardware_change_analyzer_dir)

        if self.save_multi_level_performance_analyzer_log:
            validate_path("multi_level_performance_analyzer_dir", self.multi_level_performance_analyzer_dir)