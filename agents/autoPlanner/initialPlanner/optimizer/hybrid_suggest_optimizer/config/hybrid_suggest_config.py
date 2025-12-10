from dataclasses import dataclass, field
from typing import Optional
from configs.shared.shared_source_config import SharedSourceConfig

class MoldCapacityColumns:
    """Required columns for mold capacity estimation output."""
    REQUIRED = [
        'moldNo', 'moldName', 'acquisitionDate', 'machineTonnage',
        'moldCavityStandard', 'moldSettingCycle', 'cavityStabilityIndex',
        'cycleStabilityIndex', 'theoreticalMoldHourCapacity', 
        'effectiveMoldHourCapacity', 'estimatedMoldHourCapacity',
        'balancedMoldHourCapacity', 'totalRecords', 'totalCavityMeasurements',
        'totalCycleMeasurements', 'firstRecordDate', 'lastRecordDate'
    ]

class FeatureWeights:
    """Constants for feature weights used in optimization."""
    
    # Default weights for different performance metrics
    DEFAULTS = {
        'shiftNGRate_weight': 0.1,       # Defect rate (10%)
        'shiftCavityRate_weight': 0.25,  # Cavity utilization (25%)  
        'shiftCycleTimeRate_weight': 0.25, # Cycle time efficiency (25%)
        'shiftCapacityRate_weight': 0.4   # Overall capacity (40% - highest priority)
    }
    
    # Required columns for feature weight calculations
    REQUIRED_COLUMNS = [
        'shiftNGRate', 'shiftCavityRate', 'shiftCycleTimeRate', 'shiftCapacityRate'
    ]

@dataclass
class HybridSuggestConfig:
    """Configuration class for historical features extractor parameters"""

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