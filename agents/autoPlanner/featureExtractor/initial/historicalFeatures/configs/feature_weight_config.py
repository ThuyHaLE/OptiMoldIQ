from dataclasses import dataclass, field
from agents.utils import validate_path
from typing import Literal, Dict, Optional

@dataclass
class FeatureWeightConfig:
    """Configuration class for mold-machine feature weight calculator parameters"""

    source_path: str = 'agents/shared_db/DataLoaderAgent/newest'
    annotation_name: str = "path_annotations.json"
    databaseSchemas_path: str = 'database/databaseSchemas.json'
    sharedDatabaseSchemas_path: str = 'database/sharedDatabaseSchemas.json'

    folder_path: str = 'agents/shared_db/OrderProgressTracker'
    target_name: str = "change_log.txt"

    default_dir: str = "agents/shared_db/HistoricalFeatures"

    mold_stability_index_folder = 'agents/shared_db/HistoricalFeatures/MoldStabilityIndexCalculator'
    mold_stability_index_target_name = "change_log.txt"

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

    def __post_init__(self):
        """Validate directory settings when saving is enabled."""
        validate_path("source_path", self.source_path)
        validate_path("folder_path", self.folder_path)
        validate_path("mold_stability_index_folder", self.mold_stability_index_folder)