from dataclasses import dataclass
from agents.utils import validate_path

@dataclass
class ProducingProcessorConfig:
    """Configuration class for producing processor parameters"""

    source_path: str = 'agents/shared_db/DataLoaderAgent/newest'
    annotation_name: str = "path_annotations.json"
    databaseSchemas_path: str = 'database/databaseSchemas.json'
    sharedDatabaseSchemas_path: str = 'database/sharedDatabaseSchemas.json'

    folder_path: str = 'agents/shared_db/OrderProgressTracker'
    target_name: str = "change_log.txt"

    default_dir: str = "agents/shared_db/AutoPlanner/InitialPlanner"

    mold_stability_index_folder: str = "agents/shared_db/HistoricalFeaturesExtractor/MoldStabilityIndexCalculator"
    mold_stability_index_target_name: str = "change_log.txt"

    mold_machine_weights_hist_path: str = "agents/shared_db/HistoricalFeaturesExtractor/MoldMachineFeatureWeightCalculator/weights_hist.xlsx"

    efficiency: float = 0.85
    loss: float = 0.03

    def __post_init__(self):
        """Validate directory settings when saving is enabled."""
        validate_path("source_path", self.source_path)
        validate_path("folder_path", self.folder_path)
        validate_path("mold_stability_index_folder", self.mold_stability_index_folder)