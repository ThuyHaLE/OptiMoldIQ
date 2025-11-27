from dataclasses import dataclass, field
from agents.utils import validate_path
from agents.dashboardBuilder.dashboardBuilderConfigs.performance_plotflow_config import PerformancePlotflowConfig
from agents.dashboardBuilder.dashboardBuilderConfigs.hardware_change_plotflow_config import HardwareChangePlotflowConfig

@dataclass
class DashboardBuilderConfig:
    """Configuration class for dashboard builder parameters"""

    # Enable DashboardBuilder components
    enable_multi_level_plotter: bool = False  # MultiLevelPerformancePlotter
    enable_hardware_change_plotter: bool = False  # HardwareChangePlotter

    save_dashboard_builder_log: bool = False
    dashboard_builder_dir: str = 'agents/shared_db/DashboardBuilder'
    
    performance_plotflow_config: PerformancePlotflowConfig = field(default_factory=PerformancePlotflowConfig)
    hardware_change_plotflow_config: HardwareChangePlotflowConfig = field(default_factory=HardwareChangePlotflowConfig)

    def __post_init__(self):
        """Validate directory settings when saving is enabled."""
        if self.save_dashboard_builder_log:
            validate_path("dashboard_builder_dir", self.dashboard_builder_dir)