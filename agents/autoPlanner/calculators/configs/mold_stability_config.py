from dataclasses import dataclass, asdict
from typing import Optional, Dict
import pandas as pd

@dataclass
class MoldStabilityCalculationResult:
    mold_stability_index: pd.DataFrame
    index_calculation_summary: str
    log_str: str
    def to_dict(self) -> Dict:
        """Convert dataclass to dictionary for serialization/logging."""
        return asdict(self)
    
@dataclass
class MoldStabilityConfig:
    """Configuration class for mold stability index calculator parameters"""
    efficiency: Optional[float] = None
    loss: Optional[float] = None
    cavity_stability_threshold: Optional[float] = None
    cycle_stability_threshold: Optional[float] = None
    total_records_threshold: Optional[int] = None
    
    # Default values
    DEFAULT_EFFICIENCY = 0.85
    DEFAULT_LOSS = 0.03
    DEFAULT_CAVITY_STABILITY_THRESHOLD = 0.6
    DEFAULT_CYCLE_STABILITY_THRESHOLD = 0.4
    DEFAULT_TOTAL_RECORDS_THRESHOLD = 30
    
    def __post_init__(self):
        """Apply default values for None fields"""
        self.efficiency = self._get_default(self.efficiency, self.DEFAULT_EFFICIENCY)
        self.loss = self._get_default(self.loss, self.DEFAULT_LOSS)
        self.cavity_stability_threshold = self._get_default(
            self.cavity_stability_threshold, 
            self.DEFAULT_CAVITY_STABILITY_THRESHOLD
        )
        self.cycle_stability_threshold = self._get_default(
            self.cycle_stability_threshold, 
            self.DEFAULT_CYCLE_STABILITY_THRESHOLD
        )
        self.total_records_threshold = self._get_default(
            self.total_records_threshold, 
            self.DEFAULT_TOTAL_RECORDS_THRESHOLD
        )
    
    @staticmethod
    def _get_default(value, default):
        """Return default if value is None"""
        return default if value is None else value