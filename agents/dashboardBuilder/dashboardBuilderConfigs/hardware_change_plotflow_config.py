from dataclasses import dataclass
from typing import Optional
from agents.utils import validate_path

@dataclass
class HardwareChangePlotflowConfig:
    """Configuration class for plotflow parameters"""

    enable_machine_layout_plotter: bool = False
    enable_machine_mold_pair_plotter: bool = False
    
    # Shared paths
    source_path: str = 'agents/shared_db/DataLoaderAgent/newest'
    annotation_name: str = "path_annotations.json"
    databaseSchemas_path: str = 'database/databaseSchemas.json'

    # HardwareChangePlotter config
    save_hardware_change_plotter_log: bool = True
    hardware_change_plotter_dir: str = "agents/shared_db/DashboardBuilder/HardwareChangePlotter"

    machine_layout_plotter_result_dir: str = "agents/shared_db/DashboardBuilder/HardwareChangePlotter/MachineLayoutPlotter"
    machine_layout_visualization_config_path: Optional[str] = None

    machine_mold_pair_plotter_result_dir: str = "agents/shared_db/DashboardBuilder/HardwareChangePlotter/MachineMoldPairPlotter"
    machine_mold_pair_visualization_config_path: Optional[str] = None

    # Optimal Processing
    enable_parallel: bool = True  # Enable parallel processing
    max_workers: Optional[int] = None  # Auto-detect optimal worker count

    # AnalyticsOrchestrator config
    save_analytics_orchestrator_log: bool = False
    analytics_orchestrator_dir: str = 'agents/shared_db/DashboardBuilder'

    save_hardware_change_analyzer_log: bool = True
    hardware_change_analyzer_dir: str = "agents/shared_db/DashboardBuilder/HardwareChangeAnalyzer"

    machine_layout_tracker_result_dir: str = "agents/shared_db/DashboardBuilder/HardwareChangePlotter/MachineLayoutTracker"
    machine_layout_tracker_change_log_name: str = "change_log.txt"

    machine_mold_pair_tracker_result_dir: str = "agents/shared_db/DashboardBuilder/HardwareChangePlotter/MachineMoldPairTracker"
    machine_mold_pair_tracker_change_log_name: str = "change_log.txt"

    def __post_init__(self):
        """Validate directory settings when saving is enabled."""

        validate_path("machine_layout_plotter_result_dir", self.machine_layout_plotter_result_dir)
        validate_path("machine_mold_pair_plotter_result_dir", self.machine_mold_pair_plotter_result_dir)
        validate_path("machine_layout_tracker_result_dir", self.machine_layout_tracker_result_dir)
        validate_path("machine_mold_pair_tracker_result_dir", self.machine_mold_pair_tracker_result_dir)

        if self.save_hardware_change_plotter_log:
            validate_path("hardware_change_plotter_dir", self.hardware_change_plotter_dir)

        if self.save_analytics_orchestrator_log:
            validate_path("analytics_orchestrator_dir", self.analytics_orchestrator_dir)

        if self.save_hardware_change_analyzer_log:
            validate_path("hardware_change_analyzer_dir", self.hardware_change_analyzer_dir)