from pathlib import Path
from typing import Dict, Any, Set
from loguru import logger
from datetime import datetime
import pandas as pd
import os

from agents.utils import (
    load_annotation_path, read_change_log, 
    save_output_with_versioning, update_weight_and_save_confidence_report)

from configs.shared.config_report_format import ConfigReportMixin
from agents.autoPlanner.featureExtractor.initial.historicalFeaturesExtractor.features_extractor_config import (
    FeaturesExtractorConfig)

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
    
    CONSTANT_CONFIG_PATH = (
        "agents/autoPlanner/featureExtractor/initial/historicalFeaturesExtractor/constant_configurations.json")

    def __init__(self, config: FeaturesExtractorConfig):
        super().__init__("DataLoading")
        self.config = config.shared_source_config
    
    def _execute_impl(self) -> Dict[str, Any]:
        """Load all required data"""
        logger.info("📂 Loading database schemas and path annotations...")
        
        # Load database schema for productRecords_df
        try:
            # Load constant configurations
            constant_config = load_annotation_path(
                Path(self.CONSTANT_CONFIG_PATH).parent,
                Path(self.CONSTANT_CONFIG_PATH).name)
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
        
        logger.info("✓ All data loaded successfully ({} DataFrames)", len(loaded_dfs))
        
        return {
            'constant_config': constant_config,
            'databaseSchemas_data': databaseSchemas_data,
            'sharedDatabaseSchemas_data': sharedDatabaseSchemas_data,
            'path_annotation': path_annotation,
            'dataframes': loaded_dfs
        }

    def _fallback(self) -> Dict[str, Any]:
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
                 loaded_data: Dict[str, Any]):
        super().__init__("MoldStabilityIndexCalculator")

        self.config = config
        self.loaded_data = loaded_data

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
        logger.info("✓ MoldStabilityIndexCalculator completed")
        
        return calculator_result.to_dict()
    
    def _fallback(self) -> Dict[str, Any]:
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
    
    def __init__(self, config: FeaturesExtractorConfig):
        super().__init__("DependencyDataLoading")
        self.config = config.shared_source_config
    
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
        logger.info(f"✓ Loaded validation data ({len(progress_tracking_data)} sheets)")
        
        return {"proStatus_df": progress_tracking_data}
    
    def _fallback(self) -> Dict[str, Any]:
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
                 loaded_data: Dict[str, Any],
                 dependency_data: Dict[str, Any], 
                 index_calculating_data: Dict[str, Any]):
        super().__init__("MoldMachineFeatureWeightCalculator")

        self.config = config
        self.dependency_data = dependency_data
        self.index_calculating_data = index_calculating_data
        
        self.constant_config = loaded_data.get('constant_config', {})
        self.databaseSchemas_data = loaded_data['databaseSchemas_data']
        self.sharedDatabaseSchemas_data = loaded_data['sharedDatabaseSchemas_data']

        # Load required dataframes
        dataframes = loaded_data['dataframes']
        self.moldSpecificationSummary_df = dataframes["moldSpecificationSummary_df"]
        self.moldInfo_df = dataframes["moldInfo_df"]
        self.productRecords_df = dataframes["productRecords_df"]

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

        return calculator_result.to_dict()

    def _estimate_mold_capacity(self):
        # Import ItemMoldCapacityEstimator
        from agents.autoPlanner.tools.item_mold_capacity_estimator import ItemMoldCapacityEstimator

        logger.info("🔄 Running mold stability calculator...")
        # Constant configurations for ItemMoldCapacityEstimator
        capacity_constant_config = self.constant_config.get("ItemMoldCapacityEstimator", {})

        # Initialize and run estimator
        estimator = ItemMoldCapacityEstimator(
            self.databaseSchemas_data,
            self.sharedDatabaseSchemas_data,
            self.index_calculating_data["mold_stability_index"],
            self.moldSpecificationSummary_df,
            self.moldInfo_df,
            capacity_constant_config,
            self.config.efficiency,
            self.config.loss,
            )
        
        return estimator.process()
    
    def _calculate_feature_weight(self, 
                                  mold_estimated_capacity: pd.DataFrame): 
        
        # Import MoldMachineFeatureWeightCalculator
        from agents.autoPlanner.calculators.mold_machine_feature_weight_calculator import (
            MoldMachineFeatureWeightCalculator)
        
        # Constant configurations for MoldMachineFeatureWeightCalculator
        weight_constant_config = self.constant_config.get("MoldMachineFeatureWeightCalculator", {})

        # Initialize and run calculator
        calculator = MoldMachineFeatureWeightCalculator(
            self.databaseSchemas_data,
            self.sharedDatabaseSchemas_data, 
            self.productRecords_df,
            self.moldInfo_df,
            self.dependency_data["proStatus_df"],
            mold_estimated_capacity,
            self.config.feature_weight_config,
            weight_constant_config)

        return calculator.process()
    
    def _fallback(self) -> Dict[str, Any]:
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
                'mold_stability_index_change_log_path': str,
                'mold_machine_weights_dir': str,
                'mold_stability_index_dir': str,
                'features_extractor_dir': str
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
                    - features_extractor_dir (str): Base directory for storing reports.
                    - mold_stability_index_dir (str): Default directory for output and temporary files.
                    - annotation_path (str): Path to the JSON file containing path annotations.
                    - databaseSchemas_path (str): Path to database schema for validation.
                    - sharedDatabaseSchemas_path (str): Path to shared database schema for validation.
                    - progress_tracker_change_log_path (str): Path to the OrderProgressTracker change log.
                    - mold_stability_index_change_log_path (str): Path to the MoldStabilityIndexCalculator change log.
                    - mold_machine_weights_dir (str): Base directory for storing reports.

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

        self.loaded_data = {}
        self.dependency_data = {} 
        self.index_calculating_data = {}

    def run_extraction(self) -> tuple[Dict[str, Any], str]:
        """
        Execute the complete historical features extraction pipeline.
        
        This is the main entry point that orchestrates the entire pipeline:
        1. Runs MoldStabilityIndexCalculator (Phase 1)
        2. Runs ItemMoldCapacityEstimator (Phase 2)
        3. Runs MoldMachineFeatureWeightCalculator (Phase 3)
        4. Returns comprehensive pipeline results
        
        Returns:
            tuple[Dict[str, Any], str]: Pipeline execution results and log string
        """

        self.logger.info("Starting HistoricalFeaturesExtractor ...")

        # Create data loading phase
        data_phase = DataLoadingPhase(self.config)

        # Execute data loading first
        self.logger.info("📂 Step 1: Loading data...")
        data_result = data_phase.execute()

        # Check if data loading succeeded
        if data_result.status != "success":
            self.logger.error("❌ Data loading failed, cannot proceed with validations")
            
            # Return early with failed result
            return ExecutionResult(
                name="HistoricalFeaturesExtractor",
                type="agent",
                status="failed",
                duration=data_result.duration,
                severity=data_result.severity,
                sub_results=[data_result],
                total_sub_executions=1,
                error="Data loading failed"
            )
        
        self.loaded_data = data_result.data.get('result', {})
        self.logger.info("✓ Data loaded successfully")

        # Phase 1: Mold Stability Index Calculation
        self.logger.info("🔍 Step 2: Running mold stability index calculating ...")
        index_calculating_phase = MoldStabilityCalculatingPhase(self.config, self.loaded_data)
        index_calculating_result = index_calculating_phase.execute()

        # Check if stability index calculating succeeded
        if index_calculating_result.status != "success":
            self.logger.error("❌ Progress tracking failed")
            
            # Return early with failed result
            return ExecutionResult(
                name="HistoricalFeaturesExtractor",
                type="agent",
                status="failed",
                duration=index_calculating_result.duration,
                severity=index_calculating_result.severity,
                sub_results=[data_result, index_calculating_result],
                total_sub_executions=2,
                error="Error processing MoldStabilityCalculator"
            )

        self.index_calculating_data = index_calculating_result.data.get('result', {})
        self.logger.info("✓ Mold stability index calculated successfully")

        # Loading dependency data
        self.logger.info("📂 Step 3: Loading dependency data...")
        dependency_data_phase = DependencyDataLoadingPhase(self.config)
        dependency_data_result = dependency_data_phase.execute()

        # Check if dependency data loading succeeded
        if dependency_data_result.status != "success":
            self.logger.error("❌ Dependency data loading failed, cannot proceed with feature weight calculator")
            
            # Return early with failed result
            return ExecutionResult(
                name="HistoricalFeaturesExtractor",
                type="agent",
                status="failed",
                duration=dependency_data_result.duration,
                severity=dependency_data_result.severity,
                sub_results=[data_result, index_calculating_result, dependency_data_result],
                total_sub_executions=3,
                error="Dependency data loading failed"
            )

        self.dependency_data = dependency_data_result.data.get('result', {})
        self.logger.info("✓ Dependency data loaded successfully")

        # Phase 2: Feature Weight Calculation
        self.logger.info("🔍 Step 4: Running feature weight calculating ...")
        weight_calculating_phase = FeatureWeightCalculatingPhase(self.config, 
                                                                 self.loaded_data, 
                                                                 self.dependency_data,
                                                                 self.index_calculating_data)
        weight_calculating_result = weight_calculating_phase.execute()

        # Check if feature weight calculating succeeded
        if weight_calculating_result.status != "success":
            self.logger.error("❌ Progress tracking failed")
            
            # Return early with failed result
            return ExecutionResult(
                name="HistoricalFeaturesExtractor",
                type="agent",
                status="failed",
                duration=weight_calculating_result.duration,
                severity=weight_calculating_result.severity,
                sub_results=[data_result, index_calculating_result, dependency_data_result, weight_calculating_result],
                total_sub_executions=4,
                error="Error processing FeatureWeightCalculator"
            )

         # Combine data loading + validations into final result
        total_duration = (data_result.duration + 
                          index_calculating_result.duration + 
                          dependency_data_result.duration + 
                          weight_calculating_result.duration)
        
        final_result = ExecutionResult(
            name="HistoricalFeaturesExtractor",
            type="agent",
            status=weight_calculating_result.status,
            duration=total_duration,
            severity=weight_calculating_result.severity,
            sub_results=[data_result, index_calculating_result, dependency_data_result, weight_calculating_result],
            total_sub_executions= 4,
            warnings=weight_calculating_result.warnings
        )
        
        # Log completion
        self.logger.info("✅ HistoricalFeaturesExtractor completed in {:.2f}s!", final_result.duration)

        # Print execution tree for visibility
        print("\n" + "="*60)
        print("VALIDATION EXECUTION TREE")
        print("="*60)
        print_execution_tree(final_result)
        print("="*60 + "\n")
        
        # Print analysis
        analysis = analyze_execution(final_result)
        print("EXECUTION ANALYSIS:")
        print(f"  Status: {analysis['status']}")
        print(f"  Duration: {analysis['duration']:.2f}s")
        print(f"  Complete: {analysis['complete']}")
        print(f"  All Successful: {analysis['all_successful']}")
        print(f"  Statistics: {analysis['statistics']}")
        if analysis['failed_paths']:
            print(f"  Failed Paths: {analysis['failed_paths']}")
        print("="*60 + "\n")
        
        return final_result
    
    def _extract_historical_data(self, result: ExecutionResult) -> Dict[str, Any]:
        # Skip first sub_results (DataLoading and DependencyDataLoading phase) 
        extraction_results = [r for r in result.sub_results if r.name not in ["DataLoading", "DependencyDataLoading"]]

        # Find results by phase name
        mold_stability_result, mold_stability_data = self._extract_single_phase_data(
            "MoldStabilityIndexCalculator", 
            extraction_results,
            {'mold_stability_index', 'index_calculation_summary', 'log_str'})

        feature_weight_result, feature_weight_data = self._extract_single_phase_data(
            "MoldMachineFeatureWeightCalculator", 
            extraction_results,
            {'confidence_scores', 'overall_confidence', 'enhanced_weights', 
             'confidence_report_text', 'log_str'})
            
        return mold_stability_result, mold_stability_data, feature_weight_result, feature_weight_data
    
    def _extract_single_phase_data(self, 
                                   phase_name: str, 
                                   all_phase_results: list[ExecutionResult], 
                                   phase_keys: Set[str]) -> Dict[str, Any]:
        """Extract data from a single phase by name"""

        phase_result = next((r for r in all_phase_results 
                             if r.name == phase_name), None)
        phase_data = phase_result.data.get(
            'result', {}) if phase_result and phase_result.status == "success" else {}
        
        if not isinstance(phase_data, dict):
            return None, {}

        if not phase_keys.issubset(phase_data):
            return None, {}

        return phase_result, phase_data
    
    def run_extraction_and_save_results(self, **kwargs) -> ExecutionResult:
        """
        Execute extraction and save results to Excel files.
        
        Returns:
            ExecutionResult: Hierarchical execution result with saved data
        """

        agent_id = self.__class__.__name__

        try:
            # Execute extraction
            result = self.run_extraction(**kwargs)
            
            # Check if extraction succeeded
            if result.has_critical_errors():
                self.logger.error("❌ Validations failed with critical errors, skipping save")
                return result

            # Extract extraction data
            (mold_stability_result, mold_stability_data, 
             feature_weight_result, feature_weight_data) = self._extract_historical_data(result)
            
            if not mold_stability_data and not feature_weight_data:
                self.logger.error("❌ Validations failed: empty or invalid mold stability data and feature weight data, skipping save")
                return result
            
            # Generate config header using mixin
            start_time = datetime.now()
            timestamp_str = start_time.strftime("%Y-%m-%d %H:%M:%S")
            config_header = self._generate_config_report(timestamp_str, required_only=True)
            
            export_logs = []
            if mold_stability_data:

                phase_name = mold_stability_result.name
                phase_dir = Path(self.config.shared_source_config.mold_stability_index_dir)

                # Export Excel file with versioning
                logger.info("{}: Start excel file exporting...", phase_name)
                export_log = save_output_with_versioning(
                    data = {"moldStabilityIndex":  mold_stability_data['mold_stability_index']},
                    output_dir = phase_dir,
                    filename_prefix = phase_name.lower(),
                    report_text = mold_stability_data['index_calculation_summary']
                )
                export_logs.append(phase_name)
                export_logs.append("Export Log:")
                export_logs.append(export_log)
                self.logger.info("{}: Results exported successfully!", phase_name)

                # Add export info to result metadata
                mold_stability_result.metadata['export_log'] = export_log
                mold_stability_result.metadata['calculation_summary'] = mold_stability_data['index_calculation_summary']
                mold_stability_result.metadata['log_str'] = mold_stability_data['log_str']
                
                # Save change log
                log_path = phase_dir / "change_log.txt"
                message = update_change_log(mold_stability_result.name, 
                                            config_header, 
                                            mold_stability_result, 
                                            mold_stability_data['index_calculation_summary'], 
                                            export_log, 
                                            log_path)
                export_logs.append("Change Log:")
                export_logs.append(message)

            if feature_weight_data:
                
                phase_name = feature_weight_result.name
                phase_dir = Path(self.config.shared_source_config.mold_machine_weights_dir)
                
                # Export Excel file with versioning
                logger.info("{}: Start excel file exporting...", phase_name)
                export_log = update_weight_and_save_confidence_report(
                    report_text = feature_weight_data['confidence_report_text'],
                    output_dir = phase_dir,
                    filename_prefix = phase_name.lower(),
                    enhanced_weights = feature_weight_data['enhanced_weights'])
                export_logs.append(phase_name)
                export_logs.append("Export Log:")
                export_logs.append(export_log)
                self.logger.info("{}: Results exported successfully!", phase_name)

                # Add export info to result metadata
                feature_weight_result.metadata['export_log'] = export_log
                feature_weight_result.metadata['confidence_report_text'] = feature_weight_data['confidence_report_text']
                feature_weight_result.metadata['log_str'] = feature_weight_data['log_str']

                # Save change log
                log_path = phase_dir / "change_log.txt"
                message = update_change_log(phase_name, 
                                            config_header, 
                                            feature_weight_result, 
                                            feature_weight_data['confidence_report_text'], 
                                            export_log, 
                                            log_path)
                export_logs.append("Change Log:")
                export_logs.append(message)
                
            # Combine pipeline log lines
            pipeline_log_lines = [
                "⤷ Phase 1: Mold Stability Index Calculation",
                mold_stability_data['log_str'],
                "⤷ Phase 2: Feature Weight Calculation",
                feature_weight_data['log_str']
                ]
            
            # Save pipeline change log
            log_path = Path(self.config.shared_source_config.features_extractor_dir) / "change_log.txt"
            message = update_change_log(agent_id, 
                                        config_header, 
                                        result, 
                                        "\n".join(pipeline_log_lines), 
                                        "\n".join(export_logs), 
                                        log_path)
            
            self.logger.info("✓ All results saved successfully!")

            return result

        except Exception as e:
            self.logger.error("❌ Failed to save results: {}", str(e))
            raise