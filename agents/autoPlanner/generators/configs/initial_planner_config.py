from dataclasses import dataclass, field
from typing import Optional
from configs.shared.shared_source_config import SharedSourceConfig
from agents.autoPlanner.assigners.configs.assigner_config import PriorityOrder

@dataclass
class InitialPlannerConfig:
    """Configuration class for initial planner parameters"""

    # Shared source configs
    shared_source_config: SharedSourceConfig = field(default_factory=SharedSourceConfig)

    priority_order: PriorityOrder = PriorityOrder.PRIORITY_1

    max_load_threshold: Optional[int] = None
    log_progress_interval: Optional[int] = None

    efficiency: Optional[float] = None
    loss: Optional[float] = None

    # Default values
    MAX_LOAD_THRESHOLD = 30
    LOG_PROGRESS_INTERVAL = 10

    DEFAULT_EFFICIENCY = 0.85
    DEFAULT_LOSS = 0.03

    def __post_init__(self):
        """Apply default values for None fields"""
        self.max_load_threshold = self._get_default(self.max_load_threshold, self.MAX_LOAD_THRESHOLD)
        self.log_progress_interval = self._get_default(self.log_progress_interval, self.LOG_PROGRESS_INTERVAL)

        self.efficiency = self._get_default(self.efficiency, self.DEFAULT_EFFICIENCY)
        self.loss = self._get_default(self.loss, self.DEFAULT_LOSS)  

    @staticmethod
    def _get_default(value, default):
        """Return default if value is None"""
        return default if value is None else value