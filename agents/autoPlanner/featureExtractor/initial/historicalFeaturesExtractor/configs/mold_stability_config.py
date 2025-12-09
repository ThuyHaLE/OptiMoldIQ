from dataclasses import dataclass

@dataclass
class MoldStabilityConfig:
    """Configuration class for mold stability index calculator parameters"""
    efficiency: float = 0.85
    loss: float = 0.03
    cavity_stability_threshold: float  = 0.6
    cycle_stability_threshold: float  = 0.4
    total_records_threshold: int = 30