from agents.autoPlanner.initialPlanner.optimizer.compatibility_based_mold_machine_optimizer import PriorityOrder
from typing import Dict, List
from dataclasses import dataclass, field
from typing import Optional
from configs.shared.shared_source_config import SharedSourceConfig

@dataclass
class ExcelSheetMapping:
    """Configuration for Excel sheet loading"""

    producing_status_data: str = 'producing_status_data'
    pending_status_data: str = 'pending_status_data'
    mold_machine_priority_matrix: str = 'mold_machine_priority_matrix'
    mold_estimated_capacity_df: str = 'mold_estimated_capacity_df'
    invalid_molds: str = 'invalid_molds'
    
    def get_sheet_mappings(self) -> Dict[str, str]:
        """Get dictionary mapping of sheet names to attribute names"""
        return {
            self.producing_status_data: 'producing_status_data',
            self.pending_status_data: 'pending_status_data', 
            self.mold_machine_priority_matrix: 'mold_machine_priority_matrix',
            self.mold_estimated_capacity_df: 'mold_estimated_capacity_df',
            self.invalid_molds: 'invalid_molds'
        }
    
    def get_sheets_requiring_index(self) -> List[str]:
        """Get list of sheets that need special index processing"""
        return [self.mold_machine_priority_matrix]
    
@dataclass
class PendingProcessorConfig:
    """Configuration class for pending processor parameters"""

    # Shared source configs
    shared_source_config: SharedSourceConfig = field(default_factory=SharedSourceConfig)
  
    priority_order: PriorityOrder = PriorityOrder.PRIORITY_1
    max_load_threshold: Optional[int] = None
    log_progress_interval: Optional[int] = None
    use_sample_data: Optional[bool] = None

    efficiency: Optional[float] = None
    loss: Optional[float] = None

    # Default values
    MAX_LOAD_THRESHOLD = 30
    LOG_PROGRESS_INTERVAL = 5
    USE_SAMPLE_DATA = False

    DEFAULT_EFFICIENCY = 0.85
    DEFAULT_LOSS = 0.03

    def __post_init__(self):
        """Apply default values for None fields"""
        self.max_load_threshold = self._get_default(self.max_load_threshold, self.MAX_LOAD_THRESHOLD)
        self.log_progress_interval = self._get_default(self.log_progress_interval, self.LOG_PROGRESS_INTERVAL)
        self.use_sample_data = self._get_default(self.use_sample_data, self.USE_SAMPLE_DATA)  

        self.efficiency = self._get_default(self.efficiency, self.DEFAULT_EFFICIENCY)
        self.loss = self._get_default(self.loss, self.DEFAULT_LOSS)  

    @staticmethod
    def _get_default(value, default):
        """Return default if value is None"""
        return default if value is None else value