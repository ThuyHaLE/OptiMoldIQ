from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Type, Tuple
import os

@dataclass
class SharedSourceConfig:
    """Configuration class for shared source with improved validation"""
    
    # Base directories
    db_dir: str = 'database'
    default_dir: str = "agents/shared_db"

    # Optional override-able fields
    dynamic_db_dir: Optional[str] = None
    databaseSchemas_path: Optional[str] = None
    sharedDatabaseSchemas_path: Optional[str] = None

    #--------------------------#
    # DataPipelineOrchestrator #
    #--------------------------#
    data_pipeline_dir: Optional[str] = None
    data_pipeline_change_log_path: Optional[str] = None
    annotation_path: Optional[str] = None
    manual_review_notifications_dir: Optional[str] = None
    shared_database_dir: Optional[str] = None

    #------------------------#
    # ValidationOrchestrator #
    #------------------------#
    validation_dir: Optional[str] = None
    validation_df_name: List[str] = field(default_factory=lambda: ["productRecords", "purchaseOrders"])
    validation_change_log_path: Optional[str] = None

    #----------------------#
    # OrderProgressTracker #
    #----------------------#
    progress_tracker_dir: Optional[str] = None
    progress_tracker_change_log_path: Optional[str] = None
    progress_tracker_constant_config_path: Optional[str] = None

    #-------------#
    # AutoPlanner #
    #-------------#
    auto_planner_dir: Optional[str] = None
    auto_planner_change_log_path: Optional[str] = None

    #-----------------------------#
    # HistoricalFeaturesExtractor #
    #-----------------------------#
    features_extractor_dir: Optional[str] = None
    features_extractor_constant_config_path: Optional[str] = None
    features_extractor_change_log_path: Optional[str] = None
    mold_stability_index_dir: Optional[str] = None
    mold_stability_index_change_log_path: Optional[str] = None
    mold_machine_weights_dir: Optional[str] = None
    mold_machine_weights_hist_path: Optional[str] = None
    mold_machine_weights_change_log_path: Optional[str] = None

    #----------------#
    # InitialPlanner #
    #----------------#
    initial_planner_dir: Optional[str] = None
    initial_planner_constant_config_path: Optional[str] = None
    initial_planner_change_log_path: Optional[str] = None
    producing_processor_dir: Optional[str] = None
    producing_processor_change_log_path: Optional[str] = None
    pending_processor_dir: Optional[str] = None
    pending_processor_change_log_path: Optional[str] = None

    #-----------------------#
    # AnalyticsOrchestrator #
    #-----------------------#
    analytics_orchestrator_dir: Optional[str] = None
    analytics_orchestrator_log_path: Optional[str] = None

    #------------------------#
    # HardwareChangeAnalyzer #
    #------------------------#
    hardware_change_analyzer_dir: Optional[str] = None
    hardware_change_analyzer_log_path: Optional[str] = None
    machine_layout_tracker_dir: Optional[str] = None
    machine_layout_tracker_change_log_path: Optional[str] = None
    mold_machine_pair_tracker_dir: Optional[str] = None
    mold_machine_pair_tracker_change_log_path: Optional[str] = None

    #-------------------------------#
    # MultiLevelPerformanceAnalyzer #
    #-------------------------------#
    multi_level_performance_analyzer_dir: Optional[str] = None
    performance_analyzer_constant_config_path: Optional[str] = None
    multi_level_performance_analyzer_log_path: Optional[str] = None
    day_level_processor_dir: Optional[str] = None
    day_level_processor_log_path: Optional[str] = None
    month_level_processor_dir: Optional[str] = None
    month_level_processor_log_path: Optional[str] = None
    year_level_processor_dir: Optional[str] = None
    year_level_processor_log_path: Optional[str] = None

    #------------------#
    # DashboardBuilder #
    #------------------#
    dashboard_builder_dir: Optional[str] = None
    dashboard_builder_log_path: Optional[str] = None

    #------------------------------------#
    # HardwareChangeVisualizationService #
    #------------------------------------#
    hardware_change_visualization_service_dir: Optional[str] = None
    hardware_change_visualization_service_log_path: Optional[str] = None
    machine_layout_visualization_pipeline_dir: Optional[str] = None
    machine_layout_visualization_pipeline_change_log_path: Optional[str] = None
    mold_machine_pair_visualization_pipeline_dir: Optional[str] = None
    mold_machine_pair_visualization_pipeline_change_log_path: Optional[str] = None

    #-------------------------------------------#
    # MultiLevelPerformanceVisualizationService #
    #-------------------------------------------#
    multi_level_performance_visualization_service_dir: Optional[str] = None
    multi_level_performance_visualization_service_log_path: Optional[str] = None
    day_level_visualization_pipeline_dir: Optional[str] = None
    day_level_visualization_pipeline_log_path: Optional[str] = None
    month_level_visualization_pipeline_dir: Optional[str] = None
    month_level_visualization_pipeline_log_path: Optional[str] = None
    year_level_visualization_pipeline_dir: Optional[str] = None
    year_level_visualization_pipeline_log_path: Optional[str] = None

    # Control validation behavior
    strict_validation: bool = False  # If True, validate all paths exist
    auto_create_dirs: bool = False   # If True, create missing directories
    
    def __post_init__(self):
        """Fill defaults and validate paths"""
        
        # Fill defaults
        self._fill_defaults()
        
        # Validate all path fields
        self._validate_all_paths()
    
    def _fill_defaults(self):
        """Fill default values for None fields"""
        
        self.dynamic_db_dir = (
            self.dynamic_db_dir or f"{self.db_dir}/dynamicDatabase")
        self.databaseSchemas_path = (
            self.databaseSchemas_path or f"{self.db_dir}/databaseSchemas.json")
        self.sharedDatabaseSchemas_path = (
            self.sharedDatabaseSchemas_path or f"{self.db_dir}/sharedDatabaseSchemas.json")

        #--------------------------#
        # DataPipelineOrchestrator #
        #--------------------------#
        self.data_pipeline_dir = (
            self.data_pipeline_dir or f"{self.default_dir}/DataPipelineOrchestrator")
        self.data_pipeline_change_log_path = (
            self.data_pipeline_change_log_path or f"{self.default_dir}/DataPipelineOrchestrator/change_log.txt")
        self.manual_review_notifications_dir = (
            self.data_pipeline_dir or f"{self.default_dir}/DataPipelineOrchestrator/notifications")
        self.shared_database_dir = (
            self.annotation_path or f"{self.data_pipeline_dir}/DataCollector")
        self.annotation_path = (
            self.annotation_path or f"{self.data_pipeline_dir}/DataCollector/newest/path_annotations.json")
        
        #------------------------#
        # ValidationOrchestrator #
        #------------------------#
        self.validation_dir = (
            self.validation_dir or f"{self.default_dir}/ValidationOrchestrator")
        self.validation_change_log_path = (
            self.validation_change_log_path or f"{self.validation_dir}/change_log.txt")

        #----------------------#
        # OrderProgressTracker #
        #----------------------#
        self.progress_tracker_dir = (
            self.progress_tracker_dir or f"{self.default_dir}/OrderProgressTracker")
        self.progress_tracker_change_log_path = (
            self.progress_tracker_change_log_path or f"{self.progress_tracker_dir}/change_log.txt")
        self.progress_tracker_constant_config_path = (
            self.progress_tracker_constant_config_path or "agents/orderProgressTracker/pro_status_schema.json")

        #-------------#
        # AutoPlanner #
        #-------------#
        self.auto_planner_dir = (
            self.auto_planner_dir or f'{self.default_dir}/AutoPlanner')
        self.auto_planner_change_log_path = (
            self.auto_planner_change_log_path or f'{self.auto_planner_dir}/change_log.txt')

        #-----------------------------#
        # HistoricalFeaturesExtractor #
        #-----------------------------#
        self.features_extractor_dir = (
            self.features_extractor_dir or f"{self.auto_planner_dir}/HistoricalFeaturesExtractor")
        self.features_extractor_constant_config_path = (
            self.features_extractor_constant_config_path or 
            "agents/autoPlanner/featureExtractor/initial/historicalFeaturesExtractor/constant_configurations.json")
        self.features_extractor_change_log_path = (
            self.features_extractor_change_log_path or f"{self.features_extractor_dir}/change_log.txt")
        self.mold_stability_index_dir = (
            self.mold_stability_index_dir or f"{self.features_extractor_dir}/MoldStabilityIndexCalculator")
        self.mold_stability_index_change_log_path = (
            self.mold_stability_index_change_log_path or f"{self.mold_stability_index_dir}/change_log.txt")
        self.mold_machine_weights_dir = (
            self.mold_machine_weights_dir or f"{self.features_extractor_dir}/MoldMachineFeatureWeightCalculator")
        self.mold_machine_weights_hist_path = (
            self.mold_machine_weights_hist_path or f"{self.mold_machine_weights_dir}/weights_hist.xlsx")
        self.mold_machine_weights_change_log_path = (
            self.mold_machine_weights_change_log_path or f"{self.mold_machine_weights_dir}/change_log.txt")

        #----------------#
        # InitialPlanner #
        #----------------#
        self.initial_planner_dir = (
            self.initial_planner_dir or f'{self.auto_planner_dir}/InitialPlanner')
        self.initial_planner_constant_config_path = (
            self.initial_planner_constant_config_path or 
            "agents/autoPlanner/phases/initialPlanner/configs/constant_configurations.json")
        self.initial_planner_change_log_path = (
            self.initial_planner_change_log_path or f'{self.initial_planner_dir}/change_log.txt')
        self.producing_processor_dir = (
            self.producing_processor_dir or f'{self.initial_planner_dir}/ProducingProcessor')
        self.producing_processor_change_log_path = (
            self.producing_processor_change_log_path or f'{self.producing_processor_dir}/change_log.txt')
        self.pending_processor_dir = (
            self.pending_processor_dir or f'{self.initial_planner_dir}/PendingProcessor')
        self.pending_processor_change_log_path = (
            self.pending_processor_change_log_path or f'{self.pending_processor_dir}/change_log.txt')
        
        #-----------------------#
        # AnalyticsOrchestrator #
        #-----------------------#
        self.analytics_orchestrator_dir = (
            self.analytics_orchestrator_dir or f'{self.default_dir}/AnalyticsOrchestrator')
        self.analytics_orchestrator_log_path = (
            self.analytics_orchestrator_log_path or f"{self.analytics_orchestrator_dir}/change_log.txt")

        #------------------------#
        # HardwareChangeAnalyzer #
        #------------------------#
        self.hardware_change_analyzer_dir = (
            self.hardware_change_analyzer_dir or f'{self.analytics_orchestrator_dir}/HardwareChangeAnalyzer')
        self.hardware_change_analyzer_log_path = (
            self.hardware_change_analyzer_log_path or f"{self.hardware_change_analyzer_dir}/change_log.txt")

        self.machine_layout_tracker_dir = (
            self.machine_layout_tracker_dir or f'{self.hardware_change_analyzer_dir}/MachineLayoutTracker')
        self.machine_layout_tracker_change_log_path = (
            self.machine_layout_tracker_change_log_path or f"{self.machine_layout_tracker_dir}/change_log.txt")

        self.mold_machine_pair_tracker_dir = (
            self.mold_machine_pair_tracker_dir or f'{self.hardware_change_analyzer_dir}/MoldMachinePairTracker')
        self.mold_machine_pair_tracker_change_log_path = (
            self.mold_machine_pair_tracker_change_log_path or f"{self.mold_machine_pair_tracker_dir}/change_log.txt")

        #-------------------------------#
        # MultiLevelPerformanceAnalyzer #
        #-------------------------------#
        self.multi_level_performance_analyzer_dir = (
            self.multi_level_performance_analyzer_dir or f'{self.analytics_orchestrator_dir}/MultiLevelPerformanceAnalyzer')
        self.performance_analyzer_constant_config_path = (
            self.performance_analyzer_constant_config_path or 
            "agents/analyticsOrchestrator/processor/configs/constant_configurations.json")
        self.multi_level_performance_analyzer_log_path  = (
            self.multi_level_performance_analyzer_log_path  or f"{self.multi_level_performance_analyzer_dir}/change_log.txt")
        
        self.day_level_processor_dir = (
            self.day_level_processor_dir or f'{self.multi_level_performance_analyzer_dir}/DayLevelDataProcessor')
        self.day_level_processor_log_path  = (
            self.day_level_processor_log_path or f"{self.day_level_processor_dir}/change_log.txt")
        
        self.month_level_processor_dir = (
            self.month_level_processor_dir or f'{self.multi_level_performance_analyzer_dir}/MonthLevelDataProcessor')
        self.month_level_processor_log_path  = (
            self.month_level_processor_log_path or f"{self.month_level_processor_dir}/change_log.txt")
        
        self.year_level_processor_dir = (
            self.year_level_processor_dir or f'{self.multi_level_performance_analyzer_dir}/YearLevelDataProcessor')
        self.year_level_processor_log_path  = (
            self.year_level_processor_log_path  or f"{self.year_level_processor_dir}/change_log.txt")
        
        #------------------#
        # DashboardBuilder #
        #------------------#
        self.dashboard_builder_dir = (
            self.dashboard_builder_dir or f'{self.default_dir}/DashboardBuilder')
        self.dashboard_builder_log_path = (
            self.dashboard_builder_log_path or f"{self.dashboard_builder_dir}/change_log.txt")

        #------------------------------------#
        # HardwareChangeVisualizationService #
        #------------------------------------#
        self.hardware_change_visualization_service_dir = (
            self.hardware_change_visualization_service_dir or f'{self.dashboard_builder_dir}/HardwareChangeVisualizationService')
        self.hardware_change_visualization_service_log_path = (
            self.hardware_change_visualization_service_log_path or f"{self.hardware_change_visualization_service_dir}/change_log.txt")
        
        self.machine_layout_visualization_pipeline_dir = (
            self.machine_layout_visualization_pipeline_dir or f'{self.hardware_change_visualization_service_dir}/MachineLayoutVisualizationPipeline')
        self.machine_layout_visualization_pipeline_change_log_path = (
            self.machine_layout_visualization_pipeline_change_log_path or f"{self.machine_layout_visualization_pipeline_dir}/change_log.txt")

        self.mold_machine_pair_visualization_pipeline_dir = (
            self.mold_machine_pair_visualization_pipeline_dir or f'{self.hardware_change_visualization_service_dir}/MoldMachinePairVisualizationPipeline')
        self.mold_machine_pair_visualization_pipeline_change_log_path = (
            self.mold_machine_pair_visualization_pipeline_change_log_path or f"{self.mold_machine_pair_visualization_pipeline_dir}/change_log.txt")

        #-------------------------------------------#
        # MultiLevelPerformanceVisualizationService #
        #-------------------------------------------#
        self.multi_level_performance_visualization_service_dir = (
            self.multi_level_performance_visualization_service_dir or f'{self.dashboard_builder_dir}/MultiLevelPerformanceVisualizationService')
        self.multi_level_performance_visualization_service_log_path = (
            self.multi_level_performance_visualization_service_log_path or f"{self.multi_level_performance_visualization_service_dir}/change_log.txt")

        self.day_level_visualization_pipeline_dir = (
            self.day_level_visualization_pipeline_dir or f'{self.multi_level_performance_visualization_service_dir}/DayLevelVisualizationPipeline')
        self.day_level_visualization_pipeline_log_path = (
            self.day_level_visualization_pipeline_log_path or f"{self.day_level_visualization_pipeline_dir}/change_log.txt")

        self.month_level_visualization_pipeline_dir = (
            self.month_level_visualization_pipeline_dir or f'{self.multi_level_performance_visualization_service_dir}/MonthLevelVisualizationPipeline')
        self.month_level_visualization_pipeline_log_path = (
            self.month_level_visualization_pipeline_log_path or f"{self.month_level_visualization_pipeline_dir}/change_log.txt")

        self.year_level_visualization_pipeline_dir = (
            self.year_level_visualization_pipeline_dir or f'{self.multi_level_performance_visualization_service_dir}/YearLevelVisualizationPipeline')
        self.year_level_visualization_pipeline_log_path = (
            self.year_level_visualization_pipeline_log_path or f"{self.year_level_visualization_pipeline_dir}/change_log.txt")

    def _validate_all_paths(self):
        """Validate all path fields"""
        path_fields = self._get_path_fields()
        errors = []
        
        for field_name in path_fields:
            value = getattr(self, field_name)
            if value:
                try:
                    normalized = self.validate_path(field_name, value)
                    setattr(self, field_name, normalized)
                except ValueError as e:
                    errors.append(str(e))
        
        # Respect strict_validation setting
        if errors:
            if self.strict_validation:
                raise ValueError(
                    f"Path validation failed:\n" + 
                    "\n".join(f"  - {e}" for e in errors)
                )
            else:
                # Just log warnings in non-strict mode
                from loguru import logger
                logger.warning("Path validation warnings (non-strict mode):")
                for error in errors:
                    logger.warning(f"  - {error}")

    def _get_path_fields(self) -> List[str]:
        """Get all field names that represent paths"""
        path_indicators = ['_dir', '_path']
        return [
            name for name in self.__dataclass_fields__.keys()
            if any(indicator in name for indicator in path_indicators)
        ]

    def validate_path(self, name: str, value: str, check_exists: bool = None) -> str:
        """
        Ensure value is a valid path-like string and normalize it.
        
        Args:
            name: Field name for error messages
            value: Path string to validate
            check_exists: If True, verify path exists. If None, uses self.strict_validation
            
        Returns:
            Normalized path string
            
        Raises:
            ValueError: If validation fails
        """
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{name} must be a non-empty string.")

        # Normalize path
        try:
            path = Path(value)
            normalized = path.as_posix().strip().rstrip("/")
        except Exception as e:
            raise ValueError(f"{name}: invalid path format - {e}")
        
        # Basic sanity check
        if not normalized or normalized in ('/', '.'):
            raise ValueError(f"{name}: path '{value}' is not a valid directory/file path")
        
        # Check existence if requested
        check_exists = check_exists if check_exists is not None else self.strict_validation
        if check_exists:
            if not path.exists():
                if self.auto_create_dirs and name.endswith('_dir'):
                    try:
                        path.mkdir(parents=True, exist_ok=True)
                    except Exception as e:
                        raise ValueError(f"{name}: failed to create directory '{value}' - {e}")
                else:
                    raise ValueError(f"{name}: path '{value}' does not exist")

        return normalized

    def validate_requirements(self, 
                              required_fields: Dict[str, Type]
                              ) -> Tuple[bool, Optional[List[str]]]:
        """
        Validate whether the configuration satisfies the required constraints.
        
        Args:
            required_fields: Dict mapping field name -> expected type
                Example: {'db_dir': str, 'default_dir': str}
            
        Returns:
            Tuple of (is_valid, errors_list_or_none)
        """
        errors = []
        
        for field, expected_type in required_fields.items():
            # Check existence
            if not hasattr(self, field):
                errors.append(f"{field}: does not exist in config")
                continue
            
            # Check value
            value = getattr(self, field)
            if value is None or value == "":
                errors.append(f"{field}: is empty")
                continue

            # Check type (handle List types specially)
            if hasattr(expected_type, '__origin__'):  # Generic type like List[str]
                origin = expected_type.__origin__
                if not isinstance(value, origin):
                    errors.append(
                        f"{field}: expected {expected_type}, got {type(value).__name__}"
                    )
            else:
                if not isinstance(value, expected_type):
                    errors.append(
                        f"{field}: expected {expected_type.__name__}, got {type(value).__name__}"
                    )
        
        is_valid = len(errors) == 0
        return is_valid, errors if not is_valid else None
    
    def get_available_fields(self) -> List[str]:
        """Get all available field names"""
        return list(self.__dataclass_fields__.keys())
    
    def to_dict(self) -> Dict[str, any]:
        """Convert config to dictionary"""
        return {
            field: getattr(self, field) 
            for field in self.get_available_fields()
        }
    
    def create_directories(self, dir_fields: Optional[List[str]] = None) -> List[str]:
        """
        Create directories for specified fields or all _dir fields.
        
        Args:
            dir_fields: List of field names to create dirs for. 
                       If None, creates all fields ending in '_dir'
        
        Returns:
            List of created directory paths
        """
        if dir_fields is None:
            dir_fields = [f for f in self.get_available_fields() if f.endswith('_dir')]
        
        created = []
        for field in dir_fields:
            if hasattr(self, field):
                dir_path = getattr(self, field)
                if dir_path:
                    path = Path(dir_path)
                    path.mkdir(parents=True, exist_ok=True)
                    created.append(dir_path)
        
        return created