from dataclasses import dataclass, field
from agents.utils import validate_path
from agents.dashboardBuilder.dashboardBuilderConfigs.performance_plotflow_config import PerformancePlotflowConfig
from agents.dashboardBuilder.dashboardBuilderConfigs.hardware_change_plotflow_config import HardwareChangePlotflowConfig

@dataclass
class DashboardBuilderConfig:
    """Configuration class for dashboard builder parameters"""

    # Enable DashboardBuilder components
    # HardwareChangePlotter
    enable_hardware_change_plotter: bool = False  
    enable_hardware_change_machine_layout_plotter: bool = False # MachineLayoutPlotter
    enable_hardware_change_machine_mold_pair_plotter: bool = False # MachineMoldPairPlotter
    
    # MultiLevelPerformancePlotter
    enable_multi_level_plotter: bool = False  
    enable_multi_level_day_level_plotter: bool = False # DayLevelDataPlotter
    enable_multi_level_month_level_plotter: bool = False # MonthLevelDataPlotter
    enable_multi_level_year_level_plotter: bool = False # YearLevelDataPlotter

    save_dashboard_builder_log: bool = True
    dashboard_builder_dir: str = 'agents/shared_db/DashboardBuilder'
    
    performance_plotflow_config: PerformancePlotflowConfig = field(default_factory=PerformancePlotflowConfig)
    hardware_change_plotflow_config: HardwareChangePlotflowConfig = field(default_factory=HardwareChangePlotflowConfig)

    def __post_init__(self):
        """Validate directory settings when saving is enabled."""
        if self.save_dashboard_builder_log:
            validate_path("dashboard_builder_dir", self.dashboard_builder_dir)