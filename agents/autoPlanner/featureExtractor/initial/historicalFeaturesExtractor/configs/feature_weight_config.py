from dataclasses import dataclass, field
from typing import Literal, Dict, Optional

@dataclass
class FeatureWeightConfig:
    """Configuration class for mold-machine feature weight calculator parameters"""
    efficiency: float = 0.85
    loss: float = 0.03

    scaling: Literal['absolute', 'relative'] = 'absolute'
    confidence_weight: float = 0.3
    n_bootstrap: int = 500
    confidence_level: float = 0.95
    min_sample_size: int = 10
    feature_weights: Optional[Dict[str, float]] = None

    targets: Dict[str, float] = field(
        default_factory=lambda: {
            'shiftNGRate': 'minimize',
            'shiftCavityRate': 1.0,
            'shiftCycleTimeRate': 1.0,
            'shiftCapacityRate': 1.0,
        }
    )