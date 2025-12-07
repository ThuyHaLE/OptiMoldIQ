# configs/shared/shared_source_config.py
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Optional, Type

@dataclass
class SharedSourceConfig:
    """Configuration class for shared source"""
    
    # Base directories
    db_dir: str = 'database'
    default_dir: str = "agents/shared_db"

    # Optional override-able fields
    dynamic_db_dir: Optional[str] = None
    databaseSchemas_path: Optional[str] = None
    sharedDatabaseSchemas_path: Optional[str] = None
    annotation_path: Optional[str] = None

    validation_dir: Optional[str] = None
    validation_change_log_path: Optional[str] = None

    progress_tracker_dir: Optional[str] = None
    progress_tracker_change_log_path: Optional[str] = None

    features_extractor_dir: Optional[str] = None
    mold_stability_index_dir: Optional[str] = None
    mold_stability_index_change_log_path: Optional[str] = None
    mold_machine_weights_dir: Optional[str] = None
    mold_machine_weights_hist_path: Optional[str] = None
    
    def __post_init__(self):

        """Fill defaults when None"""
        
        self.dynamic_db_dir = (
            self.dynamic_db_dir or f"{self.db_dir}/dynamicDatabase")
        self.databaseSchemas_path = (
            self.databaseSchemas_path or f"{self.db_dir}/databaseSchemas.json")
        self.sharedDatabaseSchemas_path = (
            self.sharedDatabaseSchemas_path or f"{self.db_dir}/sharedDatabaseSchemas.json")

        self.annotation_path = (
            self.annotation_path or f"{self.default_dir}/DataLoaderAgent/newest/path_annotations.json")
        
        self.validation_dir = (
            self.validation_dir or f"{self.default_dir}/ValidationOrchestrator")
        self.validation_change_log_path = (
            self.validation_change_log_path or f"{self.validation_dir}/change_log.txt")

        self.progress_tracker_dir = (
            self.progress_tracker_dir or f"{self.default_dir}/OrderProgressTracker")
        self.progress_tracker_change_log_path = (
            self.progress_tracker_change_log_path or f"{self.progress_tracker_dir}/change_log.txt")

        self.features_extractor_dir = (
            self.features_extractor_dir or f"{self.default_dir}/HistoricalFeaturesExtractor")
        self.mold_stability_index_dir = (
            self.mold_stability_index_dir or f"{self.features_extractor_dir}/MoldStabilityIndexCalculator")
        self.mold_stability_index_change_log_path = (
            self.mold_stability_index_change_log_path or f"{self.mold_stability_index_dir}/change_log.txt")
        self.mold_machine_weights_dir = (
            self.mold_machine_weights_dir or f"{self.features_extractor_dir}/MoldMachineFeatureWeightCalculator")
        self.mold_machine_weights_hist_path = (
            self.mold_machine_weights_hist_path or f"{self.mold_machine_weights_dir}/weights_hist.xlsx")
        
        # Validate critical paths
        self.dynamic_db_dir = self.validate_path("dynamic_db_dir", self.dynamic_db_dir)

    def validate_path(self, name: str, value: str) -> str:
        """
        Ensure value is a non-empty path-like string and normalize it.
        
        Returns:
            Normalized path string
        """
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{name} must be a non-empty string.")

        # Check path-like
        if "/" not in value and "\\" not in value:
            raise ValueError(f"{name} must look like a path (contain '/' or '\\').")

        # Normalize path: convert to POSIX, remove trailing spaces
        path = Path(value).as_posix().strip().rstrip("/")

        # Return normalized path (without trailing slash for consistency)
        return path

    def validate_requirements(
        self, 
        required_fields: Dict[str, Type]
    ) -> tuple[bool, Optional[List[str]]]:
        """
        Validate whether the configuration satisfies the required constraints.
        
        Args:
            required_fields: Dict mapping field name -> expected type
                Example: {'source_dir': str, 'default_dir': str}
            
        Returns:
            (is_valid, errors)
        """
        errors = []
        
        for field, expected_type in required_fields.items():
            # Check existence
            if not hasattr(self, field):
                errors.append(f"{field}: not exists in config")
                continue
            
            # Check value
            value = getattr(self, field)
            if value is None or value == "":
                errors.append(f"{field}: is empty")
                continue

            # Check type
            if not isinstance(value, expected_type):
                errors.append(
                    f"{field}: expected {expected_type.__name__}, "
                    f"got {type(value).__name__}"
                )
        
        is_valid = len(errors) == 0
        return is_valid, errors if not is_valid else None
    
    def get_available_fields(self) -> List[str]:
        """Get all available field names"""
        return list(self.__dataclass_fields__.keys())