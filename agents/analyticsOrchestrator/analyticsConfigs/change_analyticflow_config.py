from dataclasses import dataclass
from agents.utils import validate_path

@dataclass
class ChangeAnalyticflowConfig:
    """Configuration class for analyticflow parameters"""
    
    enable_machine_layout_tracker: bool = False
    enable_machine_mold_pair_tracker: bool = False
    
    # Shared paths
    source_path: str = 'agents/shared_db/DataLoaderAgent/newest'
    annotation_name: str = "path_annotations.json"
    databaseSchemas_path: str = 'database/databaseSchemas.json'

    save_hardware_change_analyzer_log: bool = True
    hardware_change_analyzer_dir: str = "agents/shared_db/HardwareChangeAnalyzer"

    machine_layout_tracker_dir: str = "agents/shared_db/HardwareChangeAnalyzer/MachineLayoutTracker"
    machine_layout_tracker_change_log_name: str = "change_log.txt"

    machine_mold_pair_tracker_dir: str = "agents/shared_db/HardwareChangeAnalyzer/MachineMoldPairTracker"
    machine_mold_pair_tracker_change_log_name: str = "change_log.txt"

    def __post_init__(self):
        """Validate directory settings when saving is enabled."""
        validate_path("machine_layout_tracker_dir", self.machine_layout_tracker_dir)
        validate_path("machine_mold_pair_tracker_dir", self.machine_mold_pair_tracker_dir)
        if self.save_hardware_change_analyzer_log:
            validate_path("hardware_change_analyzer_dir", self.hardware_change_analyzer_dir)