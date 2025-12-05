from dataclasses import dataclass
from agents.utils import validate_path

@dataclass
class MoldStabilityConfig:
    """Configuration class for mold stability index calculator parameters"""

    source_path: str = 'agents/shared_db/DataLoaderAgent/newest'
    annotation_name: str = "path_annotations.json"
    databaseSchemas_path: str = 'database/databaseSchemas.json'
    default_dir: str = "agents/shared_db/HistoricalFeatures"

    efficiency: float = 0.85
    loss: float = 0.03
    cavity_stability_threshold: float  = 0.6
    cycle_stability_threshold: float  = 0.4
    total_records_threshold: int = 30

    def __post_init__(self):
        """Validate directory settings when saving is enabled."""
        validate_path("analytics_orchestrator_dir", self.source_path)