from dataclasses import dataclass, field
from agents.utils import validate_path
from agents.analyticsOrchestrator.analyticsConfigs.change_analyticflow_config import ChangeAnalyticflowConfig
from agents.analyticsOrchestrator.analyticsConfigs.performance_analyticflow_config import PerformanceAnalyticflowConfig

@dataclass
class AnalyticsOrchestratorConfig:
    """Configuration class for analytics orchestrator parameters"""

    # Enable AnalyticsOrchestrator components
    enable_hardware_change_analysis: bool = False #HardwareChangeAnalyzer
    enable_multi_level_analysis: bool = False #MultiLevelPerformanceAnalyzer

    save_analytics_orchestrator_log: bool = True
    analytics_orchestrator_dir: str = 'agents/shared_db/AnalyticsOrchestrator'
    
    change_config: ChangeAnalyticflowConfig = field(default_factory=ChangeAnalyticflowConfig)
    performance_config: PerformanceAnalyticflowConfig = field(default_factory=PerformanceAnalyticflowConfig)

    def __post_init__(self):
        """Validate directory settings when saving is enabled."""
        if self.save_analytics_orchestrator_log:
            validate_path("analytics_orchestrator_dir", self.analytics_orchestrator_dir)