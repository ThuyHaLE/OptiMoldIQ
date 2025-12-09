from dataclasses import dataclass, field

from configs.shared.shared_source_config import SharedSourceConfig
from agents.autoPlanner.featureExtractor.initial.historicalFeaturesExtractor.configs.feature_weight_config import FeatureWeightConfig
from agents.autoPlanner.featureExtractor.initial.historicalFeaturesExtractor.configs.mold_stability_config import MoldStabilityConfig

@dataclass
class FeaturesExtractorConfig:
    """Configuration class for historical features extractor parameters"""

    # Shared source configs
    shared_source_config: SharedSourceConfig = field(default_factory=SharedSourceConfig)

    # Phase - MoldStabilityIndexCalculator configs
    mold_stability_config: MoldStabilityConfig = field(default_factory=MoldStabilityConfig)

    # Phase - MoldMachineFeatureWeightCalculator configs
    feature_weight_config: FeatureWeightConfig = field(default_factory=FeatureWeightConfig)