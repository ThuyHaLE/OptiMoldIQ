from dataclasses import dataclass, field
from typing import Optional
from configs.shared.shared_source_config import SharedSourceConfig

class RequiredColumns:
    # Select available columns
    PRODUCING_BASE_COLS = ['poNo', 'itemCode', 'itemName', 'poETA', 'moldNo',
                           'itemQuantity', 'itemRemain', 'machineNo', 'startedDate']
    PENDING_BASE_COLS = ['poNo', 'itemCode', 'itemName', 'poETA', 'itemRemain']
    
@dataclass
class ProducingProcessorConfig:
    """Configuration class for producing processor parameters"""

    # Shared source configs
    shared_source_config: SharedSourceConfig = field(default_factory=SharedSourceConfig)
    efficiency: Optional[float] = None
    loss: Optional[float] = None

    # Default values
    DEFAULT_EFFICIENCY = 0.85
    DEFAULT_LOSS = 0.03

    def __post_init__(self):
        """Apply default values for None fields"""
        self.efficiency = self._get_default(self.efficiency, self.DEFAULT_EFFICIENCY)
        self.loss = self._get_default(self.loss, self.DEFAULT_LOSS)

    @staticmethod
    def _get_default(value, default):
        """Return default if value is None"""
        return default if value is None else value