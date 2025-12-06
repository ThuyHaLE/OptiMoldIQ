from dataclasses import dataclass
from agents.utils import validate_path
from agents.autoPlanner.initialPlanner.optimizer.compatibility_based_mold_machine_optimizer import PriorityOrder
from typing import Dict, List

@dataclass
class ExcelSheetMapping:
    """Configuration for Excel sheet loading"""

    producing_status_data: str = 'producing_status_data'
    pending_status_data: str = 'pending_status_data'
    mold_machine_priority_matrix: str = 'mold_machine_priority_matrix'
    mold_estimated_capacity_df: str = 'mold_estimated_capacity_df'
    invalid_molds: str = 'invalid_molds'
    
    def get_sheet_mappings(self) -> Dict[str, str]:
        """Get dictionary mapping of sheet names to attribute names"""
        return {
            self.producing_status_data: 'producing_status_data',
            self.pending_status_data: 'pending_status_data', 
            self.mold_machine_priority_matrix: 'mold_machine_priority_matrix',
            self.mold_estimated_capacity_df: 'mold_estimated_capacity_df',
            self.invalid_molds: 'invalid_molds'
        }
    
    def get_sheets_requiring_index(self) -> List[str]:
        """Get list of sheets that need special index processing"""
        return [self.mold_machine_priority_matrix]
    
@dataclass
class PendingProcessorConfig:
    """Configuration class for pending processor parameters"""

    source_path: str = 'agents/shared_db/DataLoaderAgent/newest'
    annotation_name: str = "path_annotations.json"
    databaseSchemas_path: str = 'database/databaseSchemas.json'
    sharedDatabaseSchemas_path: str = 'database/sharedDatabaseSchemas.json'

    default_dir: str = "agents/shared_db/AutoPlanner/InitialPlanner"

    producing_processor_folder_path: str = 'agents/shared_db/AutoPlanner/InitialPlanner/ProducingProcessor'
    producing_processor_target_name: str = "change_log.txt"

    max_load_threshold: int = 30
    priority_order: PriorityOrder = PriorityOrder.PRIORITY_1
    log_progress_interval: int = 5
    verbose: bool = True
    use_sample_data: bool = False

    def __post_init__(self):
        """Validate directory settings when saving is enabled."""
        validate_path("source_path", self.source_path)
        validate_path("producing_processor_folder_path", self.producing_processor_folder_path)