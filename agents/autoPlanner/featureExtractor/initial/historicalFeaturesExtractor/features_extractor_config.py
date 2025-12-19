from dataclasses import dataclass, field
from typing import Optional

from configs.shared.shared_source_config import SharedSourceConfig
from agents.autoPlanner.calculators.configs.feature_weight_config import FeatureWeightConfig
from agents.autoPlanner.calculators.configs.mold_stability_config import MoldStabilityConfig

@dataclass
class FeaturesExtractorConfig:
    """Configuration class for historical features extractor parameters"""

    efficiency: Optional[float] = None
    loss: Optional[float] = None

    # Shared source configs
    shared_source_config: SharedSourceConfig = field(default_factory=SharedSourceConfig)

    # Phase - MoldStabilityIndexCalculator configs
    mold_stability_config: MoldStabilityConfig = field(default_factory=MoldStabilityConfig)

    # Phase - MoldMachineFeatureWeightCalculator configs
    feature_weight_config: FeatureWeightConfig = field(default_factory=FeatureWeightConfig)

    DEFAULT_EFFICIENCY = 0.85
    DEFAULT_LOSS = 0.03

    def __post_init__(self):
        """Apply default values for None fields"""
        self.efficiency = self._get_default(self.efficiency, self.DEFAULT_EFFICIENCY)
        self.loss = self._get_default(self.loss, self.DEFAULT_LOSS)

        for cfg in (self.mold_stability_config, self.feature_weight_config):
            cfg.efficiency = self.efficiency
            cfg.loss = self.loss

    @staticmethod
    def _get_default(value, default):
        """Return default if value is None"""
        return default if value is None else value