from dataclasses import dataclass
from typing import Literal, Dict, Optional
from copy import deepcopy

@dataclass
class FeatureWeightConfig:
    """Configuration class for mold-machine feature weight calculator parameters"""
    efficiency: Optional[float] = None
    loss: Optional[float] = None
    scaling: Optional[Literal['absolute', 'relative']] = None
    confidence_weight: Optional[float] = None
    n_bootstrap: Optional[int] = None
    confidence_level: Optional[float] = None
    min_sample_size: Optional[int] = None
    sample_size_threshold: Optional[int] = None
    feature_weights: Optional[Dict[str, float]] = None
    targets: Optional[Dict[str, float]] = None
    
    DEFAULTS = {
        'efficiency': 0.85,
        'loss': 0.03,
        'scaling': 'absolute',
        'confidence_weight': 0.3,
        'n_bootstrap': 500,
        'confidence_level': 0.95,
        'min_sample_size': 10,
        'sample_size_threshold': 50,
        'feature_weights': None,
        'targets': {
            'shiftNGRate': 'minimize',
            'shiftCavityRate': 1.0,
            'shiftCycleTimeRate': 1.0,
            'shiftCapacityRate': 1.0,
        }
    }
    
    def __post_init__(self):
        """Apply defaults for None values with deep copy for mutable types"""
        for field_name, default_value in self.DEFAULTS.items():
            if getattr(self, field_name) is None:
                if isinstance(default_value, (dict, list)):
                    setattr(self, field_name, deepcopy(default_value))
                else:
                    setattr(self, field_name, default_value)
        # Validate scaling value
        if self.scaling not in ['absolute', 'relative']:
            raise ValueError(f"scaling must be 'absolute' or 'relative', got '{self.scaling}'")