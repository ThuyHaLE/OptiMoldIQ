import pandas as pd
from loguru import logger
from typing import Dict, Any, Optional, NoReturn, Tuple, Set, List

import os
from pathlib import Path
from datetime import datetime

from agents.utils import (
    load_annotation_path, read_change_log, get_latest_change_row, 
    camel_to_snake, save_output_with_versioning)

from configs.shared.config_report_format import ConfigReportMixin
from agents.autoPlanner.phases.initialPlanner.configs.initial_planner_config import InitialPlannerConfig

# Import agent report format components
from configs.shared.agent_report_format import (
    Executable,
    ExecutionResult,
    AtomicPhase,
    CompositeAgent,
    PhaseSeverity,
    ExecutionStatus,
    generate_execution_tree_as_str,
    print_execution_tree,
    analyze_execution, 
    update_change_log)

# ============================================
# DATA LOADING PHASE
# ============================================
class DataLoadingPhase(AtomicPhase):
    """Phase for loading all required data files"""
    
    RECOVERABLE_ERRORS = (FileNotFoundError, pd.errors.EmptyDataError, KeyError)
    CRITICAL_ERRORS = (MemoryError, KeyboardInterrupt)
    FALLBACK_FAILURE_IS_CRITICAL = True  # ⭐ Data loading is critical!

    def __init__(self, 
                 config: InitialPlannerConfig,
                 data_container: Dict[str, Any]):
        super().__init__("DataLoading")
        self.config = config.shared_source_config
        self.data_container = data_container
    
    def _load_annotation(self, path: str, name: str) -> Dict:

        """Helper to load annotation with consistent error handling"""

        try:
            return load_annotation_path(Path(path).parent, Path(path).name)
        
        except Exception as e:
            raise FileNotFoundError(f"Failed to load {name}: {e}")
        
    def _load_constant_configs(self, 
                               constant_configs: Dict) -> Dict[str, Any]:
        
        # Define configs to load
        configs_to_load = [
            ('ItemMoldCapacityEstimator', 'capacity_constant_config'),
            ('PriorityMatrixCalculator', 'calculator_constant_config'),
            ('ProducingOrderPlanner', 'planner_constant_config'),
            ('ProductionScheduleGenerator', 'generator_constant_config'),
        ]
        
        loaded_configs = {}
        missing_configs = []
        
        for config_key, config_name in configs_to_load:
            config = constant_configs.get(config_key)
            
            if config is None:
                missing_configs.append(f"{config_key}: not found in constant_configs")
                continue
                
            if not isinstance(config, dict):
                missing_configs.append(f"{config_key}: must be a dict, got {type(config)}")
                continue
            
            loaded_configs[config_name] = config
            logger.debug("Loaded constant config '{}': {} keys", config_key, len(config))
        
        if missing_configs:
            raise KeyError("Missing or invalid constant configs:\n  - " + "\n  - ".join(missing_configs))
        
        return loaded_configs
    
    def _load_dataframes(self,
                         path_annotation: Dict) -> Dict[str, Any]:
        
        # Define dataframes to load
        dataframes_to_load = [
            ('moldSpecificationSummary', 'moldSpecificationSummary_df'),
            ('itemCompositionSummary', 'itemCompositionSummary_df'),
            ('productRecords', 'productRecords_df'),
            ('machineInfo', 'machineInfo_df'),
            ('moldInfo', 'moldInfo_df')
        ]
        
        loaded_dfs = {}
        missing_files = []
        failed_loads = []
        
        for path_key, attr_name in dataframes_to_load:
            path = path_annotation.get(path_key)
            
            if not path:
                missing_files.append(f"{path_key}: path not found in annotation")
                continue
            
            if not os.path.exists(path):
                missing_files.append(f"{path_key}: file not found at {path}")
                continue
            
            try:
                df = pd.read_parquet(path)
                loaded_dfs[attr_name] = df
                logger.debug("{}: {} - {}", path_key, df.shape, list(df.columns))
            except Exception as e:
                failed_loads.append(f"{path_key}: {str(e)}")
        
        # Check if we have critical failures
        if missing_files or failed_loads:
            error_msg = []
            if missing_files:
                error_msg.append("Missing files:\n  - " + "\n  - ".join(missing_files))
            if failed_loads:
                error_msg.append("Failed to load:\n  - " + "\n  - ".join(failed_loads))
            
            raise FileNotFoundError("\n".join(error_msg))
        
        return loaded_dfs

    def _execute_impl(self) -> Dict[str, Any]:
        """Load all required data"""
        logger.info("📂 Loading database schemas and path annotations...")
        
        # Load constant configurations
        constant_config = self._load_annotation(
            self.config.initial_planner_constant_config_path, 
            "constant config"
        )
        if not constant_config:
            logger.debug("Constant config not found in loaded YAML dict")
        
        # Load specific constant configs for each component
        logger.info("⚙️ Loading component constant configurations...")
        loaded_configs = self._load_constant_configs(constant_config)
        logger.info("✓ All constant configs loaded successfully ({} configs)", len(loaded_configs))

        # Load schemas
        databaseSchemas_data = self._load_annotation(
            self.config.databaseSchemas_path, "databaseSchemas"
        )
        sharedDatabaseSchemas_data = self._load_annotation(
            self.config.sharedDatabaseSchemas_path, "sharedDatabaseSchemas"
        )
        path_annotation = self._load_annotation(
            self.config.annotation_path, "path_annotation"
        )
        
        logger.info("📊 Loading DataFrames from parquet files...")
        loaded_dfs = self._load_dataframes(path_annotation)

        self.data_container.update({
            'constant_config': constant_config,
            'component_configs': loaded_configs,
            'databaseSchemas_data': databaseSchemas_data,
            'sharedDatabaseSchemas_data': sharedDatabaseSchemas_data,
            'path_annotation': path_annotation,
            'dataframes': loaded_dfs
        })


        logger.info("✓ All data loaded successfully ({} DataFrames)", len(loaded_dfs))
        
        return {
            'constant_config': constant_config,
            'component_configs': loaded_configs,
            'databaseSchemas_data': databaseSchemas_data,
            'sharedDatabaseSchemas_data': sharedDatabaseSchemas_data,
            'path_annotation': path_annotation,
            'dataframes': loaded_dfs
        }

    def _fallback(self) -> NoReturn:
        """
        No valid fallback for data loading.
        Raise to ensure CRITICAL severity is applied.
        """
        logger.error("DataLoading cannot fallback - missing data files")
        
        raise FileNotFoundError(
            "Cannot proceed without required data files. "
            "Please check paths in configuration."
        )

# ============================================
# DEPENDENCY DATA/REPORT LOADING PHASE
# ============================================
class DependencyDataLoadingPhase(AtomicPhase):
    """Phase for loading progress tracking data from dependency (OrderProgressTracker)"""
    
    RECOVERABLE_ERRORS = (FileNotFoundError, pd.errors.EmptyDataError, KeyError)
    CRITICAL_ERRORS = (MemoryError, KeyboardInterrupt)
    FALLBACK_FAILURE_IS_CRITICAL = True  # ⭐ Critical - cannot continue without progress tracking data
    
    def __init__(self, 
                 config: InitialPlannerConfig,
                 dependency_data_container: Dict[str, Any]):
        super().__init__("DependencyDataLoading")
        self.config = config.shared_source_config
        self.dependency_data_container = dependency_data_container
    
    def _execute_impl(self) -> Dict[str, Any]:
        """Load progress tracking data from dependency"""
        logger.info("📂 Loading log file from dependency OrderProgressTracker...")
        
        # Process the log file
        excel_file_path = read_change_log(
            Path(self.config.progress_tracker_change_log_path).parent,
            Path(self.config.progress_tracker_change_log_path).name
        )
        
        if excel_file_path is None:
            logger.info("No change log file found")
            raise FileNotFoundError("No progress tracking change log found")
        
        progress_tracking_data = pd.read_excel(excel_file_path)

        self.dependency_data_container.update({"proStatus_df": progress_tracking_data})

        logger.info(f"✓ Loaded tracking data ({len(progress_tracking_data)} sheets)")
        
        return {"proStatus_df": progress_tracking_data}
    
    def _fallback(self) -> NoReturn:
        """
        No valid fallback for dependency data loading.
        Raise to ensure CRITICAL severity is applied.
        """
        logger.error("DependencyDataLoading cannot fallback - missing data files")
        
        raise FileNotFoundError(
            "Cannot proceed without required data files. "
            "Please check paths in configuration."
        )
    
# ============================================
# OPTIONAL DEPENDENCY DATA/REPORT LOADING PHASE
# ============================================
class OptionalDependencyDataLoadingPhase(AtomicPhase):
    """Phase for loading progress tracking data from dependency (optional)"""
    
    RECOVERABLE_ERRORS = (FileNotFoundError, pd.errors.EmptyDataError, KeyError)
    CRITICAL_ERRORS = (MemoryError, KeyboardInterrupt)
    FALLBACK_FAILURE_IS_CRITICAL = False  # ⭐ Optional - can continue without this data
    
    def __init__(self, 
                 config: InitialPlannerConfig,
                 optional_data_container: Dict[str, Any]):
        super().__init__("OptionalDependencyDataLoading")
        self.config = config.shared_source_config
        self.optional_data_container = optional_data_container
    
    def _load_mold_stability_index(self) -> Optional[pd.DataFrame]:
        """Load mold stability index"""
        stability_path = read_change_log(
            Path(self.config.mold_stability_index_change_log_path).parent,
            Path(self.config.mold_stability_index_change_log_path).name
        )
        
        if stability_path is None:
            logger.warning("Stability index file not found")
            return None
        
        return pd.read_excel(stability_path)
    
    def _load_mold_machine_feature_weights(self) -> Optional[pd.Series]:
        """Load mold-machine feature weights"""
        weights_path = Path(self.config.mold_machine_weights_hist_path)
        
        if not weights_path.exists():
            logger.warning("Feature weights file not found: {}", weights_path)
            return None
        
        return get_latest_change_row(weights_path)
    
    def _execute_impl(self) -> Dict[str, Any]:
        """Load optional dependency data"""
        logger.info("📂 Loading optional dependency data...")
        
        moldStability_df = self._load_mold_stability_index()
        if moldStability_df is not None:
            logger.info("✓ Loaded mold stability index ({} records)", len(moldStability_df))
        else:
            logger.info("⚠ Mold stability index not available")
        
        featureWeights_series = self._load_mold_machine_feature_weights()
        if featureWeights_series is not None:
            logger.info("✓ Loaded feature weights ({} features)", len(featureWeights_series))
        else:
            logger.info("⚠ Feature weights not available")
        
        self.optional_data_container.update({
            "moldStability_df": moldStability_df,
            "featureWeights_series": featureWeights_series
            })

        return {
            "moldStability_df": moldStability_df,
            "featureWeights_series": featureWeights_series
        }
    
    def _fallback(self) -> Dict[str, Any]:
        """Fallback: return None for all optional data"""
        logger.warning("Using fallback - no optional dependency data available")
        
        self.optional_data_container.update({
            "moldStability_df": None,
            "featureWeights_series": None
            })
        
        return {
            "moldStability_df": None,
            "featureWeights_series": None
        }

# ============================================
# PHASE 1: PRODUCING ORDER PLANNING
# ============================================
class ProducingOrderPlanningPhase(AtomicPhase):
    """Phase for running the actual producing orders planner logic"""
    
    RECOVERABLE_ERRORS = (KeyError, ValueError, pd.errors.MergeError)
    CRITICAL_ERRORS = (MemoryError, KeyboardInterrupt)
    FALLBACK_FAILURE_IS_CRITICAL = True # Can return partial results
    
    def __init__(self, 
                 config: InitialPlannerConfig,
                 data_container: Dict[str, Any],
                 dependency_data_container: Dict[str, Any], 
                 optional_data_container: Dict[str, Any],
                 planning_data_container: Dict[str, Any]):
        super().__init__("ProducingOrderPlanner")

        self.config = config
        self.loaded_data = data_container
        self.dependency_data = dependency_data_container
        self.optional_dependency_data = optional_data_container
        self.planning_data_container = planning_data_container

    def _estimate_mold_capacity(self):
        # Import ItemMoldCapacityEstimator
        from agents.autoPlanner.tools.item_mold_capacity_estimator import ItemMoldCapacityEstimator

        logger.info("🔄 Running mold stability calculator...")

        constant_configs = self.loaded_data.get('component_configs', {})

        databaseSchemas_data = self.loaded_data['databaseSchemas_data']
        sharedDatabaseSchemas_data = self.loaded_data['sharedDatabaseSchemas_data']

        # Load required dataframes
        dataframes = self.loaded_data['dataframes']
        moldSpecificationSummary_df = dataframes["moldSpecificationSummary_df"]
        moldInfo_df = dataframes["moldInfo_df"]

        # Initialize and run estimator
        estimator = ItemMoldCapacityEstimator(
            databaseSchemas_data,
            sharedDatabaseSchemas_data,
            self.optional_dependency_data.get("moldStability_df", None),
            moldSpecificationSummary_df,
            moldInfo_df,
            constant_configs.get('capacity_constant_config', {}),
            self.config.efficiency,
            self.config.loss,
            )
        
        return estimator.process_estimating()
    
    def _producing_order_planning(self, 
                                  pro_status: pd.DataFrame,
                                  mold_estimated_capacity: pd.DataFrame):
        
        # Import ProducingOrderPlanner
        from agents.autoPlanner.phases.initialPlanner.producing_order_planner import ProducingOrderPlanner

        logger.info("🔄 Running producing orders planner...")

        constant_configs = self.loaded_data.get('component_configs', {})

        databaseSchemas_data = self.loaded_data['databaseSchemas_data']
        sharedDatabaseSchemas_data = self.loaded_data['sharedDatabaseSchemas_data']

        # Load required dataframes
        dataframes = self.loaded_data['dataframes']
        machineInfo_df = dataframes["machineInfo_df"]
        itemCompositionSummary_df = dataframes["itemCompositionSummary_df"]
        
        # Initialize and run planner
        planner = ProducingOrderPlanner(
            databaseSchemas_data,
            sharedDatabaseSchemas_data,
            machineInfo_df,
            itemCompositionSummary_df,
            pro_status,
            mold_estimated_capacity,
            constant_configs.get('planner_constant_config', {}))
        
        return planner.process_planning()
    
    def _execute_impl(self) -> Dict[str, Any]:
        """Run producing orders planner logic"""
        logger.info("🔄 Running producing orders planner...")
        
        pro_status = self.dependency_data["proStatus_df"].copy()
        pro_status.rename(columns={'lastestMachineNo': 'machineNo',
                                   'lastestMoldNo': 'moldNo'
                                   }, inplace=True)
        
        try:
            # Running mold capacity estimator
            estimator_result = self._estimate_mold_capacity()
            logger.info("✓ ItemMoldCapacityEstimator completed")
        except Exception as e:
            raise FileNotFoundError(f"Failed to running mold capacity estimator: {e}")
        
        try: 
            # Generate production, mold, and plastic plans for producing orders
            producing_planner_result = self._producing_order_planning(pro_status,
                                                                      estimator_result.mold_estimated_capacity)
            logger.info("✓ ProducingOrderPlanner completed")
        except Exception as e:
            raise FileNotFoundError(f"Failed to running producing orders planner: {e}")
        
        try: 
            # Extract information as final result
            final_result = {
                "mold_estimated_capacity": estimator_result.mold_estimated_capacity,
                "invalid_mold_list": pd.DataFrame([{
                    "invalid_molds": ",".join(map(str, estimator_result.invalid_mold_list))}]),
                "producing_status_data": producing_planner_result.producing_status_data,
                "pending_status_data": producing_planner_result.pending_status_data,
                "producing_pro_plan": producing_planner_result.producing_pro_plan,
                "producing_mold_plan": producing_planner_result.producing_mold_plan,
                "producing_plastic_plan": producing_planner_result.producing_plastic_plan,
            }
            log_str = "\n".join([estimator_result.log_str, producing_planner_result.log_str])
        except Exception as e:
            raise FileNotFoundError(f"Failed to extracting information as final result: {e}")
        
        self.planning_data_container.update({
            "result": final_result,
            "has_pending_status": len(producing_planner_result.pending_status_data) > 0,
            "planner_summary": producing_planner_result.planner_summary,
            "log_str": log_str
        })

        return {
            "result": final_result,
            "has_pending_status": len(producing_planner_result.pending_status_data) > 0,
            "planner_summary": producing_planner_result.planner_summary,
            "log_str": log_str
        }
    
    def _fallback(self) -> NoReturn:
        """
        No valid fallback for producing orders planner
        Raise to ensure CRITICAL severity is applied.
        """
        logger.error("ProducingOrderPlanner cannot fallback - error producing orders planner")
        
        raise RuntimeError(
            "Error producing orders planner."
            "ProducingOrderPlanner cannot fallback."
        )

# ============================================
# PHASE 2: PENDING ORDER PLANNING
# ============================================
class PendingOrderPlanningPhase(AtomicPhase):
    """Phase for running the actual pending orders planner logic"""
    
    RECOVERABLE_ERRORS = (KeyError, ValueError, pd.errors.MergeError)
    CRITICAL_ERRORS = (MemoryError, KeyboardInterrupt)
    FALLBACK_FAILURE_IS_CRITICAL = True # Can return partial results
    
    def __init__(self, 
                 config: InitialPlannerConfig,
                 data_container: Dict[str, Any],
                 dependency_data_container: Dict[str, Any], 
                 optional_data_container: Dict[str, Any],
                 planning_data_container: Dict[str, Any]):
        super().__init__("PendingOrderPlanner")

        self.config = config
        self.loaded_data = data_container
        self.dependency_data = dependency_data_container
        self.optional_dependency_data = optional_data_container
        self.planning_data_container = planning_data_container

    def _calculate_priority_matrix(self,
                                   pro_status: pd.DataFrame,
                                   mold_estimated_capacity: pd.DataFrame):
        
        # Import PriorityMatrixCalculator
        from agents.autoPlanner.calculators.priority_matrix_calculator import PriorityMatrixCalculator

        logger.info("🔄 Running mold-machine priority matrix calculator...")

        constant_configs = self.loaded_data.get('component_configs', {})

        databaseSchemas_data = self.loaded_data['databaseSchemas_data']
        sharedDatabaseSchemas_data = self.loaded_data['sharedDatabaseSchemas_data']

        # Load required dataframes
        dataframes = self.loaded_data['dataframes']
        productRecords_df = dataframes["productRecords_df"]
        machineInfo_df = dataframes["machineInfo_df"]
        moldInfo_df = dataframes["moldInfo_df"]

        calculator = PriorityMatrixCalculator(
            databaseSchemas_data,
            sharedDatabaseSchemas_data,
            productRecords_df,
            machineInfo_df,
            moldInfo_df,
            pro_status,
            mold_estimated_capacity,
            self.optional_dependency_data.get("featureWeights_series", None),
            constant_configs.get('calculator_constant_config', {}),
            self.config.efficiency,
            self.config.loss
        )

        return calculator.process_calculating()
    
    def _pending_order_planning(self,
                                producing_status_data: pd.DataFrame,
                                pending_status_data: pd.DataFrame,
                                mold_estimated_capacity: pd.DataFrame,
                                mold_machine_priority_matrix: pd.DataFrame):
        
        # Import PendingOrderPlanner
        from agents.autoPlanner.phases.initialPlanner.pending_order_planner import PendingOrderPlanner

        logger.info("🔄 Running mold-machine priority matrix calculator...")
        
        constant_configs = self.loaded_data.get('component_configs', {})
        databaseSchemas_data = self.loaded_data['databaseSchemas_data']
        sharedDatabaseSchemas_data = self.loaded_data['sharedDatabaseSchemas_data']

        # Load required dataframes
        dataframes = self.loaded_data['dataframes']
        machineInfo_df = dataframes["machineInfo_df"]
        moldInfo_df = dataframes["moldInfo_df"]

        planner = PendingOrderPlanner(
            databaseSchemas_data,
            sharedDatabaseSchemas_data,
            constant_configs.get("generator_constant_config", {}),
            moldInfo_df,
            machineInfo_df,
            producing_status_data,
            pending_status_data,
            mold_estimated_capacity,
            mold_machine_priority_matrix,
            self.config.priority_order,
            self.config.max_load_threshold,
            self.config.log_progress_interval
            )
        
        return planner.process_planning()
    
    def _execute_impl(self) -> Dict[str, Any]:
        """Run pending orders planner logic"""
        logger.info("🔄 Running pending orders planner...")

        producing_planning_data = self.planning_data_container["result"] 
        pro_status = self.dependency_data["proStatus_df"]

        try:
            # Running mold-machine priority matrix calculator
            matrix_calculator_result = self._calculate_priority_matrix(
                pro_status,
                producing_planning_data["mold_estimated_capacity"])
            logger.info("✓ PriorityMatrixCalculator completed")
        except Exception as e:
            raise FileNotFoundError(f"Failed to running mold-machine priority matrix calculator: {e}")
        
        try: 
            # Generate production assignments (machine-mold-item) for pending orders
             
            pending_planner_result = self._pending_order_planning(
                producing_planning_data["producing_status_data"],
                producing_planning_data["pending_status_data"],
                producing_planning_data["mold_estimated_capacity"],
                matrix_calculator_result.priority_matrix)
            logger.info("✓ PendingOrderPlanner completed")
        except Exception as e:
            raise FileNotFoundError(f"Failed to running pending orders planner: {e}")

        try:
            note = pd.DataFrame([
                {
                "invalid_molds": ",".join(map(str, matrix_calculator_result.invalid_mold_list)),
                "assigned_molds": ",".join(map(str, pending_planner_result.assigned_molds)),
                "unassigned_molds": ",".join(map(str, pending_planner_result.unassigned_molds)),
                "overloaded_machines": ",".join(map(str, pending_planner_result.overloaded_machines))
                }
            ])
                
            # Extract information as final result
            final_result = {
                "mold_machine_priority_matrix": matrix_calculator_result.priority_matrix,
                "initial_plan": pending_planner_result.initial_plan,
                "not_matched_pending": pending_planner_result.not_matched_pending,
                "note": note
            }

            log_str = "\n".join([matrix_calculator_result.log_str, 
                                 pending_planner_result.log_str])
        except Exception as e:
            raise FileNotFoundError(f"Failed to extracting information as final result: {e}")
        
        return {
            "result": final_result,
            "planner_summary": pending_planner_result.planner_summary,
            "log_str": log_str
        }
    
    def _fallback(self) -> NoReturn:
        """
        No valid fallback for producing orders planner
        Raise to ensure CRITICAL severity is applied.
        """
        logger.error("ProducingOrderPlanner cannot fallback - error producing orders planner")
        
        raise RuntimeError(
            "Error producing orders planner."
            "ProducingOrderPlanner cannot fallback."
        )

class InitialPlanner(ConfigReportMixin): 
    
    """
    The Initial Planner is a two-phase planning component within the hybrid optimization system.
        - ProducingOrderPlanner: generate production, mold, and plastic plans for producing orders.
        - PendingOrderPlanner: generate production assignments (machine-mold-item) for pending orders

    It combines historical data analysis with mold-machine compatibility matching to:
    1. Estimate historical-based mold capacity.
    2. Calculate the mold-machine priority matrix using historical-based feature weights and mold capacity.
    3. Use estimated mold capacity (1) to generate production, mold, and plastic plans for producing orders.
    4. Use estimated mold capacity (1) and the mold-machine priority matrix (2) to generate
    production assignments (machine-mold-item) for pending orders.

    The planner supports data-driven decisions for mold selection, machine allocation,
    and production planning.
    """

    REQUIRED_FIELDS = {
        'config': {
            'shared_source_config': {
                'annotation_path': str,
                'databaseSchemas_path': str,
                'sharedDatabaseSchemas_path': str,
                'progress_tracker_change_log_path': str,
                'mold_machine_weights_hist_path': str,
                'mold_stability_index_change_log_path': str,
                'initial_planner_dir': str,
                'initial_planner_change_log_path': str,
                'initial_planner_constant_config_path': str,
                'pending_processor_dir': str,
                'pending_processor_change_log_path': str,
                'producing_processor_dir': str,
                'producing_processor_change_log_path': str
                },
            "priority_order": str,
            'max_load_threshold': int,
            'log_progress_interval': int,
            'efficiency': float,
            'loss': float
            }
        }

    def __init__(self,
                 config: InitialPlannerConfig):

        """
        Initialize InitialPlanner with configuration.
        
        Args:
            config: InitialPlannerConfig containing processing parameters
            including:
                - shared_source_config: 
                    - annotation_path (str): Path to the JSON file containing path annotations
                    - databaseSchemas_path (str): Path to database schemas JSON file for validation
                    - sharedDatabaseSchemas_path (str): Path to shared database schemas JSON file for validation
                    - progress_tracker_change_log_path (str): Path to the OrderProgressTracker change log
                    - mold_machine_weights_hist_path (str): Path to mold-machine feature weights (from MoldMachineFeatureWeightCalculator)
                    - mold_stability_index_change_log_path (str): Path to the MoldStabilityIndexCalculator change log
                    - initial_planner_dir (str): Base directory for storing reports
                    - initial_planner_change_log_path (str): Path to the InitialPlanner change log
                    - initial_planner_constant_config_path (str): Path to the InitialPlanner constant config.
                    - pending_processor_dir (str): Base directory for storing reports
                    - pending_processor_change_log_path (str): Path to the ProducingOrderPlanner change log
                    - producing_processor_dir (str): Base directory for storing reports
                    - producing_processor_change_log_path (str): Path to the PendingOrderPlanner change log
                - priority_order (str): Priority ordering strategy
                - max_load_threshold (int): Maximum allowed load threshold. If None, no load constraint is applied
                - log_progress_interval (int): Interval at which progress logs are emitted during processing.
                - efficiency (float): Production efficiency factor (0.0 to 1.0)
                - loss (float): Production loss factor (0.0 to 1.0)
        """

        self._capture_init_args()

        # Initialize logger with class context for better debugging and monitoring
        self.logger = logger.bind(class_="HybridSuggestOptimizer")

        # Store configuration
        self.config = config

        # Validate required configs
        is_valid, errors = self.config.shared_source_config.validate_requirements(self.REQUIRED_FIELDS['config']['shared_source_config'])
        if not is_valid:
            raise ValueError(
                f"{self.__class__.__name__} config validation failed:\n" +
                "\n".join(f"  - {e}" for e in errors)
            )
        self.logger.info("✓ Validation for shared_source_config requirements: PASSED!")
        
        #Validate production efficiency factor and loss factor 
        self.validate_configuration()
        self.logger.info("✓ Validation for production efficiency factor and loss factor: PASSED!")

    def validate_configuration(self) -> bool:
        """
        Validate that all required configurations are accessible.
        
        Returns:
            bool: True if configuration is valid, False otherwise
        """
        validation_results = []
        
        # Validate configuration parameters
        if not (0 < self.config.efficiency <= 1):
            self.logger.error("Efficiency must be between 0 and 1, got: {}", self.config.efficiency)
            validation_results.append(False)
        else:
            validation_results.append(True)
            
        if not (0 <= self.config.loss < 1):
            self.logger.error("Loss must be between 0 and 1, got: {}", self.config.loss)
            validation_results.append(False)
        else:
            validation_results.append(True)
        
        is_valid = all(validation_results)
        if is_valid:
            self.logger.info("Configuration validation passed")
        else:
            self.logger.error("Configuration validation failed")
            
        return is_valid
        
    def process_planning(self) -> ExecutionResult:
        """
        Execute the complete historical features extraction pipeline.
        
        This is the main entry point that orchestrates the entire pipeline:
        1. Runs ProducingOrderPlanner (Phase 1)
        2. Runs PendingOrderPlanner (Phase 2)
        3. Returns comprehensive pipeline results
        
        Returns:
            ExecutionResult: Pipeline execution results and log string
        """

        self.logger.info("Starting InitialPlanner ...")

         # ============================================
        # ✨ CREATE SHARED CONTAINER
        # ============================================
        shared_data = {}  # This will be populated by DataLoadingPhase
        dependency_data = {} # This will be populated by DependencyDataLoadingPhase
        optional_dependency_data = {} # This will be populated by OptionalDependencyDataLoadingPhase
        producing_planning_data = {} # This will be populated by ProducingOrderPlanningPhase
                
        # ============================================
        # BUILD PHASE LIST WITH SHARED CONTAINER
        # ============================================
        phases: List[Executable] = []
        
        # Phase 1: Data Loading (always required)
        phases.append(DataLoadingPhase(self.config, shared_data))
        
        # Phase 2: Dependency data Loading (always required)
        phases.append(DependencyDataLoadingPhase(self.config, dependency_data))

        # Phase 3: Optinal dependency data Loading
        phases.append(OptionalDependencyDataLoadingPhase(self.config, optional_dependency_data))
 
        # Phase 4: Producing Order Planner
        phases.append(ProducingOrderPlanningPhase(self.config, 
                                                  shared_data,
                                                  dependency_data, 
                                                  optional_dependency_data,
                                                  producing_planning_data))
        
        # Phase 5: Pending Order Planner
        phases.append(PendingOrderPlanningPhase(self.config, 
                                                shared_data,
                                                dependency_data, 
                                                optional_dependency_data,
                                                producing_planning_data))

        # ============================================
        # EXECUTE USING COMPOSITE AGENT
        # ============================================
        agent = CompositeAgent("HistoricalFeaturesExtractor", phases)
        result = agent.execute()
        
        # ============================================
        # PRINT EXECUTION TREE & ANALYSIS
        # ============================================
        self.logger.info("✅ HistoricalFeaturesExtractor completed in {:.2f}s!", result.duration)
        
        print("\n" + "="*60)
        print("EXECUTION TREE")
        print("="*60)
        print_execution_tree(result)
        print("="*60 + "\n")
        
        analysis = analyze_execution(result)
        print("EXECUTION ANALYSIS:")
        print(f"  Status: {analysis['status']}")
        print(f"  Duration: {analysis['duration']:.2f}s")
        print(f"  Complete: {analysis['complete']}")
        print(f"  All Successful: {analysis['all_successful']}")
        print(f"  Statistics: {analysis['statistics']}")
        if analysis['failed_paths']:
            print(f"  Failed Paths: {analysis['failed_paths']}")
        print("="*60 + "\n")
        
        return result
    
    def _extract_planning_data(self,
                                 result: ExecutionResult) -> Tuple[
                                     ExecutionResult, Dict, str, str,
                                     ExecutionResult, Dict, str, str]:
        
        # Skip first sub_results (DataLoading and DependencyDataLoading, OptionalDependencyDataLoading phase) 
        extraction_results = [
            r for r in result.sub_results if r.name not in [
                "DataLoading", "DependencyDataLoading", "OptionalDependencyDataLoading"
                ]
            ]

        # Find results by phase name
        (producing_planner_result, producing_planner_data, 
         producing_planner_summary, producing_planner_log) = self._extract_single_phase_data(
            "ProducingOrderPlanner", 
            extraction_results,
            {'mold_estimated_capacity', 'invalid_mold_list', 'producing_status_data', 
             'pending_status_data', 'producing_pro_plan', 'producing_mold_plan', 'producing_plastic_plan'})

        (pending_planner_result, pending_planner_data, 
         pending_planner_summary, pending_planner_log) = self._extract_single_phase_data(
            "PendingOrderPlanner", 
            extraction_results,
            {'mold_machine_priority_matrix', 'initial_plan', 'not_matched_pending', 'note'})
            
        return (producing_planner_result, producing_planner_data, producing_planner_summary, producing_planner_log, 
                pending_planner_result, pending_planner_data, pending_planner_summary, pending_planner_log)

    def _extract_single_phase_data(self,
                                   phase_name: str, 
                                   all_phase_results: list[ExecutionResult], 
                                   phase_keys: Set[str]
                                   ) -> Tuple[ExecutionResult, Dict, str, str]:
        """Extract data from a single phase by name"""

        phase_result = next((r for r in all_phase_results 
                            if r.name == phase_name), None)
        
        phase_data = phase_result.data.get(
            'result', {}).get(
                'result', {}) if phase_result and phase_result.status == "success" else {}

        phase_summary = phase_result.data.get(
                'result', {}).get(
                    'planner_summary', "") if phase_result and phase_result.status == "success" else ""
        
        phase_log = phase_result.data.get(
                'result', {}).get(
                    'log_str', "") if phase_result and phase_result.status == "success" else ""
        
        if not isinstance(phase_data, dict):
            return phase_result, {}, phase_summary, phase_log

        if not phase_keys.issubset(phase_data):
            return phase_result, {}, phase_summary, phase_log

        return phase_result, phase_data, phase_summary, phase_log
    
    def run_planning_and_save_results(self, **kwargs) -> ExecutionResult:
        """
        Execute planning and save results to Excel files.
        
        Returns:
            ExecutionResult: Hierarchical execution result with saved data
        """

        agent_id = self.__class__.__name__

        try:
            # Execute extraction
            result = self.process_planning(**kwargs)
            
            # Check if extraction succeeded
            if result.has_critical_errors():
                self.logger.error("❌ Validations failed with critical errors, skipping save")
                return result

            # Extract extraction data
            (producing_planner_result, producing_planner_data, 
             producing_planner_summary, producing_planner_log, 
             pending_planner_result, pending_planner_data, 
             pending_planner_summary, pending_planner_log) = self._extract_planning_data(result)
            
            if not producing_planner_data and not pending_planner_data:
                self.logger.error(
                    "❌ Validations failed: empty or invalid producing planner data and pending planner data, skipping save"
                    )
                return result
            
            # Generate config header using mixin
            start_time = datetime.now()
            timestamp_str = start_time.strftime("%Y-%m-%d %H:%M:%S")
            config_header = self._generate_config_report(timestamp_str, required_only=True)
            
            export_logs = []
            if producing_planner_data:

                phase_name = producing_planner_result.name

                # Export Excel file with versioning
                logger.info("{}: Start excel file exporting...", phase_name)
                export_log = save_output_with_versioning(
                    data = producing_planner_data,
                    output_dir = Path(self.config.shared_source_config.producing_processor_dir),
                    filename_prefix = camel_to_snake(phase_name),
                    report_text = producing_planner_summary
                )
                export_logs.append(phase_name)
                export_logs.append("Export Log:")
                export_logs.append(export_log)
                self.logger.info("{}: Results exported successfully!", phase_name)

                # Add export info to result metadata
                producing_planner_result.metadata['export_log'] = export_log
                producing_planner_result.metadata['planner_summary'] = producing_planner_summary
                producing_planner_result.metadata['log_str'] = producing_planner_log
                
                # Save change log
                message = update_change_log(producing_planner_result.name, 
                                            config_header, 
                                            producing_planner_result, 
                                            producing_planner_summary, 
                                            export_log, 
                                            Path(self.config.shared_source_config.producing_processor_change_log_path)
                                            )
                export_logs.append("Change Log:")
                export_logs.append(message)

            if pending_planner_data:
                
                phase_name = pending_planner_result.name
                
                # Export Excel file with versioning
                logger.info("{}: Start excel file exporting...", phase_name)
                export_log = save_output_with_versioning(
                    data = pending_planner_data,
                    output_dir = Path(self.config.shared_source_config.pending_processor_dir),
                    filename_prefix = camel_to_snake(phase_name),
                    report_text = pending_planner_summary
                )
                export_logs.append(phase_name)
                export_logs.append("Export Log:")
                export_logs.append(export_log)
                self.logger.info("{}: Results exported successfully!", phase_name)

                # Add export info to result metadata
                pending_planner_result.metadata['export_log'] = export_log
                pending_planner_result.metadata['planner_summary'] = pending_planner_summary
                pending_planner_result.metadata['log_str'] = pending_planner_log

                # Save change log
                message = update_change_log(phase_name, 
                                            config_header, 
                                            pending_planner_result, 
                                            pending_planner_summary, 
                                            export_log, 
                                            Path(self.config.shared_source_config.pending_processor_change_log_path))
                export_logs.append("Change Log:")
                export_logs.append(message)
                
            # Combine pipeline log lines
            pipeline_log_lines = [
                "⤷ Phase 1: ProducingOrderPlanner",
                producing_planner_log,
                "⤷ Phase 2: PendingOrderPlanner",
                pending_planner_log
                ]
            
            # Save pipeline change log
            message = update_change_log(agent_id, 
                                        config_header, 
                                        result, 
                                        "\n".join(pipeline_log_lines), 
                                        "\n".join(export_logs), 
                                        Path(self.config.shared_source_config.initial_planner_change_log_path)
                                        )
            
            self.logger.info("✓ All results saved successfully!")

            return result

        except Exception as e:
            self.logger.error("❌ Failed to save results: {}", str(e))
            raise