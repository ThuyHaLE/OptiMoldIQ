from dataclasses import dataclass, field
from agents.utils import validate_path
from agents.analyticsOrchestrator.analyticsConfigs.change_analyticflow_config import ChangeAnalyticflowConfig
from agents.analyticsOrchestrator.analyticsConfigs.performance_analyticflow_config import PerformanceAnalyticflowConfig

@dataclass
class AnalyticsOrchestratorConfig:
    """Configuration class for analytics orchestrator parameters"""

    # Enable AnalyticsOrchestrator components

    # HardwareChangeAnalyzer
    enable_hardware_change_analysis: bool = False #HardwareChangeAnalyzer
    enable_hardware_change_machine_layout_tracker: bool = False # MachineLayoutTracker
    enable_hardware_change_machine_mold_pair_tracker: bool = False # MachineMoldPairTracker
    
    # MultiLevelPerformanceAnalyzer
    enable_multi_level_analysis: bool = False  #MultiLevelPerformanceAnalyzer
    enable_multi_level_day_level_processor: bool = False # DayLevelDataProcessor
    enable_multi_level_month_level_processor: bool = False # MonthLevelDataProcessor
    enable_multi_level_year_level_processor: bool = False # YearLevelDataProcessor

    save_analytics_orchestrator_log: bool = True
    analytics_orchestrator_dir: str = 'agents/shared_db/AnalyticsOrchestrator'
    
    change_config: ChangeAnalyticflowConfig = field(default_factory=ChangeAnalyticflowConfig)
    performance_config: PerformanceAnalyticflowConfig = field(default_factory=PerformanceAnalyticflowConfig)

    def __post_init__(self):
        """Validate directory settings when saving is enabled."""
        if self.save_analytics_orchestrator_log:
            validate_path("analytics_orchestrator_dir", self.analytics_orchestrator_dir)