from dataclasses import dataclass, field
from agents.utils import validate_path

from agents.autoPlanner.featureExtractor.initial.historicalFeatures.configs.feature_weight_config import FeatureWeightConfig
from agents.autoPlanner.featureExtractor.initial.historicalFeatures.configs.mold_stability_config import MoldStabilityConfig

@dataclass
class FeaturesExtractorConfig:
    """Configuration class for historical features extractor parameters"""

    # Phase 1 - MoldStabilityIndexCalculator configs
    mold_stability_config: MoldStabilityConfig = field(default_factory=MoldStabilityConfig)

    # Phase 2 - OrderProgressTracker configs
    source_path: str = 'agents/shared_db/DataLoaderAgent/newest'
    annotation_name: str = "path_annotations.json"
    databaseSchemas_path: str = 'tests/mock_database/databaseSchemas.json'

    folder_path: str = "agents/shared_db/ValidationOrchestrator"
    target_name: str = "change_log.txt"
    default_dir: str = "agents/shared_db"
    
    # Phase 3 - MoldMachineFeatureWeightCalculator configs
    feature_weight_config: FeatureWeightConfig = field(default_factory=FeatureWeightConfig)

    def __post_init__(self):
        """Validate directory settings when saving is enabled."""
        validate_path("source_path", self.source_path)
        validate_path("folder_path", self.folder_path)