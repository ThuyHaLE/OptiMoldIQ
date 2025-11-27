from dataclasses import dataclass
from typing import Optional
from agents.utils import validate_path

@dataclass
class DashboardBuilderConfig:
    """Configuration class for dashboard builder parameters"""

    # Enable DashboardBuilder components
    enable_hardware_change_plotter: bool = False  # HardwareChangePlotter
    enable_multi_level_plotter: bool = False  # MultiLevelPerformancePlotter

    # Database sources
    source_path: str = 'agents/shared_db/DataLoaderAgent/newest'
    annotation_name: str = "path_annotations.json"
    databaseSchemas_path: str = 'database/databaseSchemas.json'

    save_dashboard_builder_log: bool = True
    dashboard_builder_dir: str = 'agents/shared_db/DashboardBuilder'
    
    # HardwareChangePlotter config
    enable_machine_layout_plotter: bool = False
    enable_machine_mold_pair_plotter: bool = False

    save_hardware_change_plotter_log: bool = True
    hardware_change_plotter_dir: str = "agents/shared_db/DashboardBuilder/HardwareChangePlotter"

    machine_layout_plotter_result_dir: str = "agents/shared_db/DashboardBuilder/HardwareChangePlotter/MachineLayoutPlotter"
    machine_layout_visualization_config_path: Optional[str] = None

    machine_mold_pair_plotter_result_dir: str = "agents/shared_db/DashboardBuilder/HardwareChangePlotter/MachineMoldPairPlotter"
    machine_mold_pair_visualization_config_path: Optional[str] = None
            
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

    # HardwareChangeAnalyzer config
    save_hardware_change_analyzer_log: bool = False
    hardware_change_analyzer_dir: str = "agents/shared_db/DashboardBuilder/HardwareChangeAnalyzer"

    machine_layout_tracker_result_dir: str = "agents/shared_db/DashboardBuilder/HardwareChangePlotter/MachineLayoutTracker"
    machine_layout_tracker_change_log_name: str = "change_log.txt"

    machine_mold_pair_tracker_result_dir: str = "agents/shared_db/DashboardBuilder/HardwareChangePlotter/MachineMoldPairTracker"
    machine_mold_pair_tracker_change_log_name: str = "change_log.txt"

    # MultiLevelPerformanceAnalyzer config
    save_multi_level_performance_analyzer_log: bool = False
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

        validate_path("machine_layout_plotter_result_dir", self.machine_layout_plotter_result_dir)
        validate_path("machine_mold_pair_plotter_result_dir", self.machine_mold_pair_plotter_result_dir)
        validate_path("machine_layout_tracker_result_dir", self.machine_layout_tracker_result_dir)
        validate_path("machine_mold_pair_tracker_result_dir", self.machine_mold_pair_tracker_result_dir)

        if self.save_dashboard_builder_log:
            validate_path("dashboard_builder_dir", self.dashboard_builder_dir)

        if self.save_hardware_change_plotter_log:
            validate_path("hardware_change_plotter_dir", self.hardware_change_plotter_dir)

        if self.save_multi_level_performance_plotter_log:
            validate_path("multi_level_performance_plotter_dir", self.multi_level_performance_plotter_dir)

        if self.save_analytics_orchestrator_log:
            validate_path("analytics_orchestrator_dir", self.analytics_orchestrator_dir)

        if self.save_hardware_change_analyzer_log:
            validate_path("hardware_change_analyzer_dir", self.hardware_change_analyzer_dir)

        if self.save_multi_level_performance_analyzer_log:
            validate_path("multi_level_performance_analyzer_dir", self.multi_level_performance_analyzer_dir)