from pathlib import Path
from typing import Dict, Any, List, NoReturn
from loguru import logger
from datetime import datetime
import pandas as pd
import os

from agents.utils import load_annotation_path, read_change_log
from configs.shared.dict_based_report_generator import DictBasedReportGenerator
from configs.shared.config_report_format import ConfigReportMixin
from agents.autoPlanner.featureExtractor.initial.historicalFeaturesExtractor.features_extractor_config import (
    FeaturesExtractorConfig)
from agents.autoPlanner.featureExtractor.initial.historicalFeaturesExtractor.save_output_formatter import (
    save_mold_stability_index, save_mold_machine_weights)

# Import agent report format components
from configs.shared.agent_report_format import (
    Executable,
    ExecutionResult,
    AtomicPhase,
    CompositeAgent,
    print_execution_summary,
    format_execution_tree,
    update_change_log,
    save_result,
    format_export_logs)

# ============================================
# DATA LOADING PHASE
# ============================================
class DataLoadingPhase(AtomicPhase):
    """Phase for loading all required data files"""
    
    RECOVERABLE_ERRORS = (FileNotFoundError, pd.errors.EmptyDataError, KeyError)
    CRITICAL_ERRORS = (MemoryError, KeyboardInterrupt)
    FALLBACK_FAILURE_IS_CRITICAL = True  # ⭐ Data loading is critical!

    def __init__(self, 
                 config: FeaturesExtractorConfig,
                 data_container: Dict[str, Any]):
        super().__init__("DataLoading")
        self.config = config.shared_source_config
        self.data_container = data_container
    
    def _execute_impl(self) -> Dict[str, Any]:
        """Load all required data"""
        logger.info("📂 Loading database schemas and path annotations...")
        
        # Load database schema for productRecords_df
        try:
            # Load constant configurations
            constant_config = load_annotation_path(
                Path(self.config.features_extractor_constant_config_path).parent,
                Path(self.config.features_extractor_constant_config_path).name)
            if not constant_config:
                logger.debug("HistoricalFeaturesExtractor constant config not found in loaded YAML dict")
        except Exception as e:
            raise FileNotFoundError(f"Failed to load constant config for HistoricalFeaturesExtractor: {e}")
        
        # Load database schemas
        try:
            databaseSchemas_data = load_annotation_path(
                Path(self.config.databaseSchemas_path).parent,
                Path(self.config.databaseSchemas_path).name
            )
        except Exception as e:
            raise FileNotFoundError(f"Failed to load databaseSchemas: {e}")
        
        # Load shareddatabase schemas
        try:
            sharedDatabaseSchemas_data = load_annotation_path(
                Path(self.config.sharedDatabaseSchemas_path).parent,
                Path(self.config.sharedDatabaseSchemas_path).name
            )
        except Exception as e:
            raise FileNotFoundError(f"Failed to load sharedDatabaseSchemas_data: {e}")

        # Load path annotations
        try:
            path_annotation = load_annotation_path(
                Path(self.config.annotation_path).parent,
                Path(self.config.annotation_path).name
            )
        except Exception as e:
            raise FileNotFoundError(f"Failed to load path_annotation: {e}")
        
        logger.info("📊 Loading DataFrames from parquet files...")
        
        # Define dataframes to load
        dataframes_to_load = [
            ('productRecords', 'productRecords_df'),
            ('moldInfo', 'moldInfo_df'),
            ('moldSpecificationSummary', 'moldSpecificationSummary_df')
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
        
        self.data_container.update({
            'constant_config': constant_config,
            'databaseSchemas_data': databaseSchemas_data,
            'sharedDatabaseSchemas_data': sharedDatabaseSchemas_data,
            'path_annotation': path_annotation,
            'dataframes': loaded_dfs
        })

        logger.info("✓ All data loaded successfully ({} DataFrames)", len(loaded_dfs))
        
        return {
            'constant_config': constant_config,
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
# PHASE 1: MOLD STABILITY CALCULATING
# ============================================

class MoldStabilityCalculatingPhase(AtomicPhase):
    """Phase for running the actual mold stability calculator logic"""
    
    RECOVERABLE_ERRORS = (KeyError, ValueError, pd.errors.MergeError)
    CRITICAL_ERRORS = (MemoryError, KeyboardInterrupt)
    FALLBACK_FAILURE_IS_CRITICAL = True # Can return partial results
    
    def __init__(self, 
                 config: FeaturesExtractorConfig,
                 data_container: Dict[str, Any], 
                 index_data_container: Dict[str, Any]):
        super().__init__("MoldStabilityIndexCalculator")

        self.config = config
        self.loaded_data = data_container
        self.index_data_container = index_data_container

    def _execute_impl(self) -> Dict[str, Any]:
        """Run mold stability calculator logic"""
        logger.info("🔄 Running mold stability calculator...")
        
        # Import MoldStabilityIndexCalculator
        from agents.autoPlanner.calculators.mold_stability_index_calculator import MoldStabilityIndexCalculator
        
        mold_stability_config = self.config.mold_stability_config
        databaseSchemas_data = self.loaded_data['databaseSchemas_data']

        # Load required dataframes
        dataframes = self.loaded_data['dataframes']
        productRecords_df = dataframes["productRecords_df"]
        moldInfo_df = dataframes["moldInfo_df"]

        # Constant configurations for ItemMoldCapacityEstimator
        constant_config = self.loaded_data.get('constant_config', {})
        stability_constant_config = constant_config.get("MoldStabilityIndexCalculator", {})

        # Initialize and run calculator
        calculator = MoldStabilityIndexCalculator(
            databaseSchemas_data,
            productRecords_df,
            moldInfo_df,
            mold_stability_config,
            stability_constant_config)
        
        calculator_result = calculator.process()

        self.index_data_container.update(calculator_result.to_dict())
        
        logger.info("✓ MoldStabilityIndexCalculator completed")
        
        return {
            "payload": calculator_result.to_dict(),
            "savable": True
            }
            
    def _fallback(self) -> NoReturn:
        """
        No valid fallback for mold stability calculator.
        Raise to ensure CRITICAL severity is applied.
        """
        logger.error("MoldStabilityIndexCalculator cannot fallback - error mold stability calculator")
        
        raise RuntimeError(
            "Error mold stability calculator."
            "MoldStabilityIndexCalculator cannot fallback."
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
                 config: FeaturesExtractorConfig,
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
# PHASE 2: FEATURE WEIGHT CALCULATING
# ============================================

class FeatureWeightCalculatingPhase(AtomicPhase):
    """Phase for running the actual feature weight calulator logic"""
    
    RECOVERABLE_ERRORS = (KeyError, ValueError, pd.errors.MergeError)
    CRITICAL_ERRORS = (MemoryError, KeyboardInterrupt)
    FALLBACK_FAILURE_IS_CRITICAL = True # Can return partial results
    
    def __init__(self, 
                 config: FeaturesExtractorConfig,
                 data_container: Dict[str, Any], 
                 dependency_data_container: Dict[str, Any], 
                 index_data_container: Dict[str, Any]):
        super().__init__("MoldMachineFeatureWeightCalculator")

        self.config = config
        self.loaded_data = data_container
        self.dependency_data = dependency_data_container
        self.index_calculating_data = index_data_container

    def _execute_impl(self) -> Dict[str, Any]:
        """Run feature weight calulator logic"""
        logger.info("🔄 Running feature weight calulator...")
        
        try:
            # Running mold capacity estimator
            estimator_result = self._estimate_mold_capacity()
            logger.info("✓ ItemMoldCapacityEstimator completed")
        except Exception as e:
            raise FileNotFoundError(f"Failed to running mold capacity estimator: {e}")

        try: 
            # Running feature weight calulator
            calculator_result = self._calculate_feature_weight(estimator_result.mold_estimated_capacity)
            logger.info("✓ MoldMachineFeatureWeightCalculator completed")
        except Exception as e:
            raise FileNotFoundError(f"Failed to running feature weight calulator: {e}")

        return {
            "payload": calculator_result.to_dict(),
            "savable": True
            }

    def _estimate_mold_capacity(self):
        # Import ItemMoldCapacityEstimator
        from agents.autoPlanner.tools.item_mold_capacity_estimator import ItemMoldCapacityEstimator

        logger.info("🔄 Running mold stability calculator...")
        # Constant configurations for ItemMoldCapacityEstimator
        constant_config = self.loaded_data.get('constant_config', {})
        capacity_constant_config = constant_config.get("ItemMoldCapacityEstimator", {})

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
            self.index_calculating_data["mold_stability_index"],
            moldSpecificationSummary_df,
            moldInfo_df,
            capacity_constant_config,
            self.config.efficiency,
            self.config.loss,
            )
        
        return estimator.process_estimating()
    
    def _calculate_feature_weight(self, 
                                  mold_estimated_capacity: pd.DataFrame): 
        
        # Import MoldMachineFeatureWeightCalculator
        from agents.autoPlanner.calculators.mold_machine_feature_weight_calculator import (
            MoldMachineFeatureWeightCalculator)
        
        # Constant configurations for MoldMachineFeatureWeightCalculator
        constant_config = self.loaded_data.get('constant_config', {})
        weight_constant_config = constant_config.get("MoldMachineFeatureWeightCalculator", {})

        databaseSchemas_data = self.loaded_data['databaseSchemas_data']
        sharedDatabaseSchemas_data = self.loaded_data['sharedDatabaseSchemas_data']

        # Load required dataframes
        dataframes = self.loaded_data['dataframes']
        moldInfo_df = dataframes["moldInfo_df"]
        productRecords_df = dataframes["productRecords_df"]

        # Initialize and run calculator
        calculator = MoldMachineFeatureWeightCalculator(
            databaseSchemas_data,
            sharedDatabaseSchemas_data, 
            productRecords_df,
            moldInfo_df,
            self.dependency_data["proStatus_df"],
            mold_estimated_capacity,
            self.config.feature_weight_config,
            weight_constant_config)

        return calculator.process()
    
    def _fallback(self) -> NoReturn:
        """
        No valid fallback for feature weight calulator
        Raise to ensure CRITICAL severity is applied.
        """
        logger.error("MoldMachineFeatureWeightCalculator cannot fallback - error feature weight calulator")
        
        raise RuntimeError(
            "Error feature weight calulator."
            "MoldMachineFeatureWeightCalculator cannot fallback."
        )
    
# ============================================
# MAIN AGENT: HISTORICAL FEATURES EXTRACTOR
# ============================================

class HistoricalFeaturesExtractor(ConfigReportMixin):
    """
    Main orchestrator class that coordinates the historical features extraction pipeline.
    
    This class manages a three-phase extraction pipeline:
    1. Mold Stability Calculation: Calculate stability indices for molds
    2. Order Progress Tracking: Track progress of manufacturing orders
    3. Feature Weight Calculation: Calculate feature weights for mold-machine combinations
    
    The orchestrator includes error handling and comprehensive reporting.
    """

    REQUIRED_FIELDS = {
        'config': {
            'efficiency': float,
            'loss': float,
            'shared_source_config': {
                'databaseSchemas_path': str,
                'sharedDatabaseSchemas_path': str,
                'annotation_path': str,
                'progress_tracker_change_log_path': str,
                'mold_machine_weights_dir': str,
                'mold_machine_weights_hist_path': str,
                'mold_machine_weights_change_log_path': str,
                'mold_stability_index_dir': str,
                'mold_stability_index_change_log_path': str,
                'features_extractor_dir': str,
                'features_extractor_change_log_path': str,
                'features_extractor_constant_config_path': str
                },
            'feature_weight_config': {
                'efficiency': float,
                'loss': float,
                'scaling': str,
                'confidence_weight': float,
                'n_bootstrap': int,
                'confidence_level': float,
                'min_sample_size': int,
                'feature_weights': dict,
                'targets': dict
                },
            'mold_stability_config': {
                'efficiency': float,
                'loss': float,
                'cavity_stability_threshold': float,
                'cycle_stability_threshold': float,
                'total_records_threshold': int
                }
            }
    }
    
    def __init__(self, config: FeaturesExtractorConfig):
        """
        Initialize HistoricalFeaturesExtractor with configuration.
        
        Args:        
            config: FeaturesExtractorConfig containing processing parameters, including:

                Global processing parameters (propagated to sub-configs):
                    - efficiency (float): Global efficiency threshold to classify good/bad records.
                    - loss (float): Global allowable production loss threshold.

                - shared_source_config:
                    - annotation_path (str): Path to the JSON file containing path annotations.
                    - databaseSchemas_path (str): Path to database schema for validation.
                    - sharedDatabaseSchemas_path (str): Path to shared database schema for validation.
                    - progress_tracker_change_log_path (str): Path to the OrderProgressTracker change log.
                    - mold_stability_index_dir (str): Default directory for output and temporary files.
                    - mold_stability_index_change_log_path (str): Path to the MoldStabilityIndexCalculator change log.
                    - mold_machine_weights_dir (str): Base directory for storing reports.
                    - mold_machine_weights_hist_path (str): Path to the MoldMachineFeatureWeightCalculator weight hist.
                    - mold_machine_weights_change_log_path (str): Path to the MoldMachineFeatureWeightCalculator change log.
                    - features_extractor_dir (str): Base directory for storing reports.
                    - features_extractor_change_log_path (str): Path to the HistoricalFeaturesExtractor change log.
                    - features_extractor_constant_config_path (str): Path to the HistoricalFeaturesExtractor constant config.
                
                - feature_weight_config:
                    - efficiency (float): Inherited from FeaturesExtractorConfig.efficiency.
                    - loss (float): Inherited from FeaturesExtractorConfig.loss.
                    - scaling (str): Method to scale feature impacts ('absolute' or 'relative').
                    - confidence_weight (float): Weight assigned to confidence scores in final weight calculation.
                    - n_bootstrap (int): Number of bootstrap samples for confidence interval estimation.
                    - confidence_level (float): Desired confidence level for statistical tests.
                    - min_sample_size (int): Minimum sample size required for reliable estimation.
                    - feature_weights (dict): Optional preset weights for features.
                    - targets (dict): Target metrics and optimization directions or goals.

                - mold_stability_config:
                    - efficiency (float): Inherited from FeaturesExtractorConfig.efficiency.
                    - loss (float): Inherited from FeaturesExtractorConfig.loss.
                    - cavity_stability_threshold (float): Threshold for cavity stability.
                    - cycle_stability_threshold (float): Threshold for cycle stability.
                    - total_records_threshold (int): Minimum number of valid production records required
                    (at least 30 records per day).

        """
        self._capture_init_args()
        
        # Initialize logger with class-specific binding
        self.logger = logger.bind(class_="HistoricalFeaturesExtractor")

        # Store configuration
        self.config = config

        # Validate required configs
        is_valid, errors = self.config.shared_source_config.validate_requirements(
            self.REQUIRED_FIELDS['config']['shared_source_config'])
        if not is_valid:
            raise ValueError(
                f"{self.__class__.__name__} config validation failed:\n" +
                "\n".join(f"  - {e}" for e in errors)
            )
        self.logger.info("✓ Validation for shared_source_config requirements: PASSED!")

        self.save_routing = {
            "MoldStabilityIndexCalculator": {
                "enabled": True,
                "save_fn": save_mold_stability_index,
                "save_paths": {
                    "output_dir": self.config.shared_source_config.mold_stability_index_dir,
                    "change_log_path": self.config.shared_source_config.mold_stability_index_change_log_path
                }
            },
            "MoldMachineFeatureWeightCalculator": {
                "enabled": True,
                "save_fn": save_mold_machine_weights,
                "save_paths": {
                    "output_dir": self.config.shared_source_config.mold_machine_weights_dir,
                    "change_log_path": {
                        'mold_machine_weights_hist_path': self.config.shared_source_config.mold_machine_weights_hist_path,
                        'mold_machine_weights_change_log_path': self.config.shared_source_config.mold_machine_weights_change_log_path
                    }
                }
            },
        }

    def run_extraction(self) -> ExecutionResult:
        """
        Execute the complete historical features extraction pipeline.
        
        This is the main entry point that orchestrates the entire pipeline:
        1. Runs MoldStabilityIndexCalculator (Phase 1)
        2. Runs ItemMoldCapacityEstimator (Phase 2)
        3. Runs MoldMachineFeatureWeightCalculator (Phase 3)
        4. Returns comprehensive pipeline results
        
        Returns:
            ExecutionResult: Pipeline execution results and log string
        """

        self.logger.info("Starting HistoricalFeaturesExtractor ...")

        # ============================================
        # ✨ CREATE SHARED CONTAINER
        # ============================================
        shared_data = {}  # This will be populated by DataLoadingPhase
        index_calculating_data = {} # This will be populated by MoldStabilityCalculatingPhase
        dependency_data = {} # This will be populated by DependencyDataLoadingPhase
        
        # ============================================
        # BUILD PHASE LIST WITH SHARED CONTAINER
        # ============================================
        phases: List[Executable] = []
        
        # Phase 1: Data Loading (always required)
        phases.append(DataLoadingPhase(self.config, shared_data))
        
        # Phase 2: Mold Stability Index Calculation
        phases.append(MoldStabilityCalculatingPhase(self.config, shared_data, index_calculating_data))

        # Phase 3: Dependency data Loading (always required)
        phases.append(DependencyDataLoadingPhase(self.config, dependency_data))

        # Phase 4: Feature Weight Calculation
        phases.append(FeatureWeightCalculatingPhase(self.config, 
                                                    shared_data, 
                                                    dependency_data,
                                                    index_calculating_data))

        # ============================================
        # EXECUTE USING COMPOSITE AGENT
        # ============================================
        agent = CompositeAgent("HistoricalFeaturesExtractor", phases)
        result = agent.execute()
        
        # ============================================
        # PRINT EXECUTION TREE & ANALYSIS
        # ============================================
        self.logger.info("✅ HistoricalFeaturesExtractor completed in {:.2f}s!", result.duration)
        
        # Print execution tree for visibility
        print_execution_summary(result)
        
        return result
    
    def run_extraction_and_save_results(self, **kwargs) -> ExecutionResult:
        """
        Execute extraction and save results to Excel files.
        
        Returns:
            ExecutionResult: Hierarchical execution result with saved data
        """

        agent_id = self.__class__.__name__

        timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        config_header = self._generate_config_report(timestamp_str, required_only=True)

        try:
            # Execute extraction
            result = self.run_extraction(**kwargs)

            # Process save routing and collect metadata
            save_routing, export_metadata = save_result(self.save_routing, result)
            
            # Update result metadata
            result.metadata.update({
                'save_routing': save_routing,
                'export_metadata': export_metadata
            })

            # Generate summary report
            reporter = DictBasedReportGenerator(use_colors=False)
            summary = "\n".join(reporter.export_report(save_routing))
            
            # Save pipeline change log
            message = update_change_log(
                agent_id, 
                config_header, 
                format_execution_tree(result), 
                summary, 
                "\n".join(format_export_logs(export_metadata)), 
                Path(self.config.shared_source_config.features_extractor_change_log_path)
            )
            
            self.logger.info(f"Pipeline log saved: {message}")

            return result

        except Exception as e:
            self.logger.error("❌ Failed to save results: {}", str(e))
            raise