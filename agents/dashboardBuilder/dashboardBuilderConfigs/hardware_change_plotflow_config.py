from dataclasses import dataclass, field
from typing import Optional
from agents.utils import validate_path
from agents.analyticsOrchestrator.analyticsConfigs.analytics_orchestrator_config import AnalyticsOrchestratorConfig

@dataclass
class HardwareChangePlotflowConfig:
    """Configuration class for plotflow parameters"""

    enable_machine_layout_plotter: bool = False
    enable_machine_mold_pair_plotter: bool = False

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
    analytics_orchestrator_config: AnalyticsOrchestratorConfig = field(default_factory=AnalyticsOrchestratorConfig)

    def __post_init__(self):
        """Validate directory settings when saving is enabled."""
        validate_path("machine_layout_plotter_result_dir", self.machine_layout_plotter_result_dir)
        validate_path("machine_mold_pair_plotter_result_dir", self.machine_mold_pair_plotter_result_dir)
        if self.save_hardware_change_plotter_log:
            validate_path("hardware_change_plotter_dir", self.hardware_change_plotter_dir)