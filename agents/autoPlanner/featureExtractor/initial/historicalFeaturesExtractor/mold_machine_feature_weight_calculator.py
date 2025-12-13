import pandas as pd
import numpy as np
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

from typing import Tuple, Literal, Dict, Union, Optional, List, Any
from pathlib import Path
from loguru import logger
from datetime import datetime
import shutil
import os

from dataclasses import dataclass, field
from enum import Enum

from agents.autoPlanner.reportFormatters.report_text_formatter import generate_confidence_report
from agents.core_helpers import check_newest_machine_layout, summarize_mold_machine_history
from agents.decorators import validate_init_dataframes, validate_dataframe
from agents.utils import load_annotation_path, log_dict_as_table, ConfigReportMixin
from configs.shared.shared_source_config import SharedSourceConfig


from agents.autoPlanner.initialPlanner.optimizer.hybrid_optimizer.item_mold_capacity_optimizer import ItemMoldCapacityOptimizer
from agents.autoPlanner.featureExtractor.initial.historicalFeaturesExtractor.configs.feature_weight_config import FeatureWeightConfig

from configs.recovery import (
    Dependency,
    DependencyValidator,
    get_dependency_data,
    OrderProgressTrackerHealer,
)

class ExecutionStatus(Enum):
    """Enum for execution status"""
    SUCCESS = "success"
    FAILED = "failed"
    WARNING = "warning"
    PARTIAL = "partial"

@dataclass
class FeatureWeightCalculatorInfo:
    """Standardized return structure for all agents"""
    agent_id: str
    status: str
    summary: Dict[str, Any]
    details: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)

# Decorator to validate DataFrames are initialized with the correct schema
@validate_init_dataframes(lambda self: {
    "productRecords_df": list(self.databaseSchemas_data['dynamicDB']['productRecords']['dtypes'].keys()),
    "machineInfo_df": list(self.databaseSchemas_data['staticDB']['machineInfo']['dtypes'].keys()),
    "moldSpecificationSummary_df": list(self.databaseSchemas_data['staticDB']['moldSpecificationSummary']['dtypes'].keys()),
    "moldInfo_df": list(self.databaseSchemas_data['staticDB']['moldInfo']['dtypes'].keys()),
})

@validate_init_dataframes(lambda self: {
    "proStatus_df": list(self.sharedDatabaseSchemas_data["pro_status"]['dtypes'].keys()),
    "machine_info_df": list(self.sharedDatabaseSchemas_data["machine_info"]['dtypes'].keys()),
})

class MoldMachineFeatureWeightCalculator(ConfigReportMixin):

    """
    This class calculates feature weights used to evaluate manufacturing process performance
    by analyzing production history and computing confidence-based metrics. 
    It will be used as input of the next step (Mold-Machine Priority Matrix Generation - 
    generate a priority matrix to support optimal production planning)
    """

    REQUIRED_FIELDS = {
        'shared_source_config': {
            'databaseSchemas_path': str,
            'sharedDatabaseSchemas_path': str,
            'annotation_path': str,
            'progress_tracker_change_log_path': str,
            'mold_stability_index_change_log_path': str,
            'mold_machine_weights_dir': str
            },
        'feature_weight_config': {
            'efficiency': float,
            'loss': float,
            'scaling': str,
            'confidence_weight': float,
            'n_bootstrap': int,
            'confidence_level': float,
            'min_sample_size': int,
            'sample_size_threshold': int,
            'feature_weights': dict,
            'targets': dict
            }
        }
    
    def __init__(self,
                 shared_source_config: SharedSourceConfig, 
                 feature_weight_config: FeatureWeightConfig):

        """
        Initialize the MoldMachineFeatureWeightCalculator.
        
        Args:
            shared_source_config: SharedSourceConfig containing processing parameters
                Including:
                    - annotation_path (str): Path to the JSON file containing path annotations
                    - databaseSchemas_path (str): Path to database schema for validation.
                    - sharedDatabaseSchemas_path (str): Path to shared database schema for validation.
                    - progress_tracker_change_log_path (str): Path to the OrderProgressTracker change log.
                    - mold_stability_index_change_log_path (str): Path to the MoldStabilityIndexCalculator change log.
                    - mold_machine_weights_dir (str): Base directory for storing reports.
            feature_weight_config: FeatureWeightConfig containing processing parameters
                Including:
                    - efficiency (float): Efficiency threshold to classify good/bad records.
                    - loss (float): Allowable production loss threshold.
                    - scaling (str): Method to scale feature impacts ('absolute' or 'relative').
                    - confidence_weight (float): Weight assigned to confidence scores in final weight calculation.
                    - n_bootstrap (int): Number of bootstrap samples for confidence interval estimation.
                    - confidence_level (float): Desired confidence level for statistical tests.
                    - min_sample_size (int): Minimum sample size required for reliable estimation.
                    - feature_weights (dict): Optional preset weights for features.
                    - targets (dict): Target metrics and their optimization directions or goals.
        """

        # Capture initialization arguments for reporting
        self._capture_init_args()

        # Initialize logger with class context for better debugging
        self.logger = logger.bind(class_="MoldMachineFeatureWeightCalculator")

        # Validate required configs
        is_valid, errors = shared_source_config.validate_requirements(self.REQUIRED_FIELDS['shared_source_config'])
        if not is_valid:
            raise ValueError(
                f"{self.__class__.__name__} config validation failed:\n" +
                "\n".join(f"  - {e}" for e in errors)
            )
        self.logger.info("✓ Validation for shared_source_config requirements: PASSED!")
        
        # Store configurations
        self.shared_source_config = shared_source_config
        self.feature_weight_config = feature_weight_config

        # Load schemas and annotations
        self.load_schema_and_annotations()

        # Load all required DataFrames from parquet files
        self._load_dataframes()

        # Ensure using the newest machine layout
        self.machine_info_df = check_newest_machine_layout(self.machineInfo_df)

        # Define dependencies
        dependencies = [
            Dependency(
                name="progress_tracker",
                change_log_path=self.shared_source_config.progress_tracker_change_log_path,
                healing_agent=OrderProgressTrackerHealer(self.shared_source_config),
                required=True,
                file_type="excel",
                description="Production progress tracking"
            ),
        ]
        # DependencyValidator
        validator = DependencyValidator(shared_source_config)
        results = validator.validate_dependencies(
            dependencies=dependencies,
            auto_heal=True,
            load_data=True
        )
        # Load production report
        self.proStatus_df = get_dependency_data(results, "progress_tracker")

        # Set up output configuration
        self.filename_prefix = "confidence_report"
        self.output_dir = Path(self.shared_source_config.mold_machine_weights_dir)

    def _load_annotation_from_config(self, config_path):
        """Helper function to load annotation from a config path."""
        return load_annotation_path(
            Path(config_path).parent,
            Path(config_path).name
        )

    def load_schema_and_annotations(self):
        """Load database schemas and path annotations from configuration files."""
        self.databaseSchemas_data = self._load_annotation_from_config(
            self.shared_source_config.databaseSchemas_path
        )
        self.sharedDatabaseSchemas_data = self._load_annotation_from_config(
            self.shared_source_config.sharedDatabaseSchemas_path
        )
        self.path_annotation = self._load_annotation_from_config(
            self.shared_source_config.annotation_path
        )

    def _load_dataframes(self) -> None:

        """
        Load all required DataFrames from parquet files with consistent error handling.

        This method loads the following DataFrames:
        - productRecords_df: Production records with item, mold, machine data
        - machineInfo_df: Machine specifications and tonnage information
        - moldSpecificationSummary_df: Mold specifications and compatible items
        - moldInfo_df: Detailed mold information including tonnage requirements
        """

        # Define the mapping between path annotation keys and DataFrame attribute names
        dataframes_to_load = [
            ('productRecords', 'productRecords_df'),
            ('machineInfo', 'machineInfo_df'),
            ('moldSpecificationSummary', 'moldSpecificationSummary_df'),
            ('moldInfo', 'moldInfo_df'),
        ]

        # Load each DataFrame with error handling
        for path_key, attr_name in dataframes_to_load:
            path = self.path_annotation.get(path_key)

            # Validate path exists
            if not path or not os.path.exists(path):
                self.logger.error("Path to '{}' not found or does not exist: {}", path_key, path)
                raise FileNotFoundError(f"Path to '{path_key}' not found or does not exist: {path}")

            try:
                # Load DataFrame from parquet file
                df = pd.read_parquet(path)
                setattr(self, attr_name, df)
                self.logger.debug("{}: {} - {}", path_key, df.shape, list(df.columns))
            except Exception as e:
                self.logger.error("Failed to load {}: {}", path_key, str(e))
                raise

    def _validate_shared_database(self, df_name, df) -> None:
        """Validate shared database DataFrame against expected schema."""
        try:
            cols = list(self.sharedDatabaseSchemas_data[df_name]['dtypes'].keys())
            validate_dataframe(df, cols)
            self.logger.info("✓ Validation for {} requirements: PASSED!", df_name)
        except Exception as e:
            logger.error("Validation failed for {} (expected cols: %s): %s", df_name, cols, e)
            raise
    
    def process(self,
                save_results: bool = False) -> tuple[pd.DataFrame, str]:

        """
        Main method to calculate feature confidence scores and enhanced weights.
        """

        start_time = datetime.now()
        agent_id = f"{self.__class__.__name__}"
        warnings = []
        calculator_log_entries = []

        # Initial phase results
        phase_results = {}

        try:
            self.logger.info("Starting MoldMachineFeatureWeightCalculator ...")

            # Generate config header using mixin
            timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            config_header = self._generate_config_report(timestamp_str, required_only=True)
            
            calculator_log_entries.append(config_header)
            calculator_log_entries.append(f"--Processing Summary--\n")
            calculator_log_entries.append(f"⤷ {self.__class__.__name__} results:\n")

            # Rename columns for consistency
            self.productRecords_df.rename(columns={'poNote': 'poNo'}, inplace=True)
            self.proStatus_df.rename(columns={'lastestMachineNo': 'machineNo',
                                            'lastestMoldNo': 'moldNo'
                                            }, inplace=True)

            # Phase 1: Estimate mold capacity
            try:
                mold_estimated_capacity_df, optimization_log = self._estimate_mold_capacity()
                calculator_log_entries.append("ItemMoldCapacityOptimizer completed successfully!")
                calculator_log_entries.append(optimization_log)
                phase_results['phase1_optimization'] = {
                    'status': 'success',
                    'records_count': len(mold_estimated_capacity_df)
                }
            except Exception as e:
                phase_results['phase1_optimization'] = {
                    'status': 'failed',
                    'error': str(e)
                }
                raise

            # Phase 2: Group historical production records into good and bad performance categories
            try:
                good_sample, bad_sample = self._group_hist_by_performance(
                    self.proStatus_df,
                    self.productRecords_df,
                    self.moldInfo_df,
                    mold_estimated_capacity_df,
                    self.feature_weight_config.efficiency,
                    self.feature_weight_config.loss
                )
                
                good_count = good_sample.shape[0]
                bad_count = bad_sample.shape[0]
                
                calculator_log_entries.append("Grouping completed successfully!")
                calculator_log_entries.append(f"✓ Good performance records: {good_count} rows")
                calculator_log_entries.append(f"✓ Bad performance records: {bad_count} rows")
                
                # Check for sample size warnings
                if good_count < 10:
                    warnings.append(f"Low good sample size: {good_count} rows (minimum recommended: 10)")
                if bad_count < 10:
                    warnings.append(f"Low bad sample size: {bad_count} rows (minimum recommended: 10)")
                
                phase_results['phase2_grouping'] = {
                    'status': 'success',
                    'good_sample_count': good_count,
                    'bad_sample_count': bad_count
                }
            except Exception as e:
                phase_results['phase2_grouping'] = {
                    'status': 'failed',
                    'error': str(e)
                }
                raise

            # Phase 3: Calculate confidence scores
            try:
                confidence_scores, overall_confidence = self._calculate_confidence_scores(
                    good_sample, bad_sample
                )
                
                calculator_log_entries.append("Overall confidence calculated successfully!")
                calculator_log_entries.append(
                    f'Overall Confidence Scores: \n{log_dict_as_table(overall_confidence, transpose=False)}'
                )
                
                # Check confidence warnings
                model_reliability = overall_confidence.get('model_reliability', 0)
                if model_reliability < 0.5:
                    warnings.append(
                        f"Low model reliability: {model_reliability:.2%} (threshold: 50%)"
                    )
                
                phase_results['phase3_confidence'] = {
                    'status': 'success',
                    'model_reliability': model_reliability,
                    'valid_features': overall_confidence.get('valid_features', 0),
                    'total_features': overall_confidence.get('total_features', 0)
                }
            except Exception as e:
                phase_results['phase3_confidence'] = {
                    'status': 'failed',
                    'error': str(e)
                }
                raise

            # Phase 4: Suggests feature weights enhanced by confidence scores.
            try:
                enhanced_weights = self._suggest_weights_with_confidence(
                    good_sample,
                    bad_sample,
                    self.feature_weight_config.targets,
                    self.feature_weight_config.scaling,
                    self.feature_weight_config.confidence_weight,
                    self.feature_weight_config.n_bootstrap,
                    self.feature_weight_config.confidence_level,
                    self.feature_weight_config.min_sample_size,
                    self.feature_weight_config.sample_size_threshold
                )
                
                calculator_log_entries.append("Enhanced feature weights suggested successfully!")
                calculator_log_entries.append(
                    f'Enhanced Weights (with confidence): \n{log_dict_as_table(enhanced_weights, transpose=False)}'
                )
                
                phase_results['phase4_weights'] = {
                    'status': 'success',
                    'weights_calculated': list(enhanced_weights.keys())
                }
            except Exception as e:
                phase_results['phase4_weights'] = {
                    'status': 'failed',
                    'error': str(e)
                }
                raise
            
            # Generate confidence report
            confidence_report_text = generate_confidence_report(confidence_scores, overall_confidence)
            self.logger.info("Confidence report generated successfully!")
            calculator_log_entries.append("Confidence report generated successfully!")
            calculator_log_entries.append(f"{confidence_report_text}\n")

            # Save results if required
            output_saved = False
            if save_results:
                try:
                    self.logger.info("Start outputs exporting...")
                    output_exporting_log = self.save_output_with_versioning(
                        confidence_report_text,
                        enhanced_weights
                    )
                    self.logger.info("Results exported successfully!")
                    calculator_log_entries.append(f"{output_exporting_log}")
                    output_saved = True
                except Exception as e:
                    self.logger.error("Failed to save results: {}", str(e))
                    warnings.append(f"Failed to save results: {str(e)}")
            
            # Compile calculator log
            calculator_log_str = "\n".join(calculator_log_entries)

            # Save change log
            try:
                log_path = self.output_dir / "change_log.txt"
                with open(log_path, "a", encoding="utf-8") as log_file:
                    log_file.write(calculator_log_str)
                self.logger.info("✓ Updated and saved change log: {}", log_path)
            except Exception as e:
                self.logger.error("✗ Failed to save change log {}: {}", log_path, e)

            end_time = datetime.now()
            processing_duration = (end_time - start_time).total_seconds()
            self.logger.info("✅ Process finished!!!")

            #return (confidence_scores, overall_confidence, enhanced_weights), calculator_log_str
            return FeatureWeightCalculatorInfo(
                agent_id=agent_id,
                status=ExecutionStatus.SUCCESS.value if not warnings else ExecutionStatus.WARNING.value,
                
                summary={
                    "phases_completed": 4,
                    "all_phases_successful": all(
                        phase.get('status') == 'success' 
                        for phase in phase_results.values()
                    ),
                    "model_reliability": overall_confidence.get('model_reliability', 0),
                    "features_analyzed": overall_confidence.get('valid_features', 0),
                    "results_saved": output_saved,
                    "warnings_count": len(warnings)
                },
                
                details={
                    "confidence_scores": confidence_scores,
                    "overall_confidence": overall_confidence,
                    "enhanced_weights": enhanced_weights,
                    "phase_results": phase_results,
                    "good_sample_size": good_count,
                    "bad_sample_size": bad_count
                },
                
                metadata={
                    "processing_duration": processing_duration,
                    "processing_duration_formatted": f"{processing_duration:.2f}s",
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat(),
                    "log_entries": calculator_log_str,
                    "config": {
                        "efficiency": self.feature_weight_config.efficiency,
                        "loss": self.feature_weight_config.loss,
                        "confidence_level": self.feature_weight_config.confidence_level,
                        "n_bootstrap": self.feature_weight_config.n_bootstrap
                    },
                },
                
                warnings=warnings
            )

        except Exception as e:
            end_time = datetime.now()
            processing_duration = (end_time - start_time).total_seconds()
            
            self.logger.error("❌ {} failed: {}", agent_id, str(e))
            return FeatureWeightCalculatorInfo(
                agent_id=agent_id,
                status=ExecutionStatus.FAILED.value,
                
                summary={
                    "error_message": str(e),
                    "failure_point": self._identify_failure_point(e),
                    "phases_completed": len([
                        p for p in phase_results.values() 
                        if p.get('status') == 'success'
                    ])
                },
                
                details={
                    "phase_results": phase_results,
                    "error_type": type(e).__name__,
                    "error_traceback": str(e)
                },
                
                metadata={
                    "processing_duration": processing_duration,
                    "processing_duration_formatted": f"{processing_duration:.2f}s",
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat(),
                    "log_entries": "\n".join(calculator_log_entries)
                },
                
                warnings=warnings
            )

    def _identify_failure_point(self, error: Exception) -> str:
        """Identify which phase the failure occurred in"""
        
        error_str = str(error)
        
        if "estimate_mold_capacity" in error_str or "ItemMoldCapacityOptimizer" in error_str:
            return "phase1_mold_capacity_estimation"
        elif "group_hist_by_performance" in error_str:
            return "phase2_historical_grouping"
        elif "calculate_confidence" in error_str:
            return "phase3_confidence_calculation"
        elif "suggest_weights" in error_str:
            return "phase4_weight_suggestion"
        elif "save_output" in error_str:
            return "output_saving"
        else:
            return "initialization_or_preprocessing"
    
    #---------------------------------#
    # PHASE 1: ESTIMATE MOLD CAPACITY #
    #---------------------------------#
    def _estimate_mold_capacity(self):
        """Estimate mold capacity using ItemMoldCapacityOptimizer."""
        try:
            self.logger.info("Starting ItemMoldCapacityOptimizer ...")
            _, mold_estimated_capacity_df, optimization_log = ItemMoldCapacityOptimizer(
                shared_source_config=self.shared_source_config,
                efficiency=self.feature_weight_config.efficiency,
                loss=self.feature_weight_config.loss
                ).process()
            self._validate_shared_database(df_name="mold_estimated_capacity", 
                                           df=mold_estimated_capacity_df)
            
            # Log optimization results
            self.logger.info("ItemMoldCapacityOptimizer completed successfully!") 
            return mold_estimated_capacity_df, optimization_log
        except Exception as e:  
            self.logger.error("Failed to estimate mold capacity: {}", str(e))
            raise
    
    #---------------------------------#
    # PHASE 2: GROUP HISTORICAL DATA  #
    #---------------------------------#
    def _group_hist_by_performance(self,
                                   proStatus_df: pd.DataFrame,
                                   productRecords_df: pd.DataFrame,
                                   moldInfo_df: pd.DataFrame,
                                   mold_estimated_capacity_df: pd.DataFrame,
                                   efficiency: float = 0.85,
                                   loss: float = 0.03) -> Tuple[pd.DataFrame, pd.DataFrame]:

        """
        Group historical production records into good and bad performance categories

        Args:
            proStatus_df (pd.DataFrame): Production status dataframe.
            productRecords_df (pd.DataFrame): Production records dataframe.
            moldInfo_df (pd.DataFrame): Mold information dataframe.
            efficiency (float): Expected efficiency rate.
            loss (float): Expected loss rate.

        Returns:
            Tuple[pd.DataFrame, pd.DataFrame]: Two dataframes (good_hist, bad_hist)
            representing good and poor performance histories respectively.
        """

        # Define required fields
        required_fields = ['poNo', 'recordDate', 'workingShift', 'machineNo', 'machineCode',
                           'itemCode', 'itemName', 'moldNo', 'moldShot', 'moldCavity',
                           'itemTotalQuantity', 'itemGoodQuantity']

        # Validate required fields in productRecords_df
        missing_fields = [field for field in required_fields if field not in productRecords_df.columns]
        if missing_fields:
            raise ValueError(f"Missing fields in productRecords_df: {missing_fields}")
        self.logger.info("Validating required fields in productRecords_df successfully!")

        # Filter out records with zero total quantity
        hist = productRecords_df[productRecords_df['itemTotalQuantity'] > 0][required_fields].copy()

        self.logger.info("Starting grouping of historical data into good and bad performance categories ...")

        try:
            # Aggregate data by PO, mold, and machine
            results = hist.groupby(['poNo', 'moldNo', 'machineCode']).agg(
                shiftsUsed=('workingShift', 'count'),
                totalQuantity=('itemTotalQuantity', 'sum'),
                totalGoodQuantity=('itemGoodQuantity', 'sum'),
                totalShots=('moldShot', 'sum'),
                shiftShots=('moldShot', 'mean'),
                shiftCavities=('moldCavity', 'mean'),
            ).reset_index()

            # Merge with mold information and production status
            merged_results = results.merge(
                moldInfo_df[['moldNo', 'moldCavityStandard', 'moldSettingCycle']],
                how='left', on='moldNo'
                ).merge(
                    proStatus_df[['poNo', 'itemCode', 'itemQuantity']],
                    how='left', on='poNo'
                    )

            # Filter out records with missing mold specifications
            filtered_df = merged_results[
                merged_results[['moldCavityStandard', 'moldSettingCycle']].notna().all(axis=1)
                ].copy()

            # Calculate estimated mold usage metrics
            with np.errstate(divide='ignore', invalid='ignore'):

                # Calculate mold full total shots
                filtered_df['moldFullTotalShots'] = np.where(
                    filtered_df['moldCavityStandard'] > 0,
                    (filtered_df['itemQuantity'] / filtered_df['moldCavityStandard']).round().astype('Int64'),
                    0)

                # Calculate mold full total seconds
                filtered_df['moldFullTotalSeconds'] = (
                    filtered_df['moldFullTotalShots'] * filtered_df['moldSettingCycle']
                    ).round().astype('Int64')
                
                # Calculate mold full shifts used (8 hours per shift)
                filtered_df['moldFullShiftUsed'] = (
                    filtered_df['moldFullTotalSeconds'] / (60 * 60 * 8)
                    ).round().astype('Int64')

                # Calculate mold estimated shifts used adjusted for efficiency and loss
                net_efficiency = efficiency - loss
                filtered_df['moldEstimatedShiftUsed'] = (
                    filtered_df['moldFullShiftUsed'] / net_efficiency
                    ).apply(lambda x: max(1, int(x)) if x > 0 else 1)

            # Aggregate by PO number to get overall shifts used and estimated shifts
            final_results = filtered_df.groupby('poNo').agg(
                shiftsUsed=('shiftsUsed', 'mean'),
                moldEstimatedShiftUsed=('moldEstimatedShiftUsed', 'mean'),
                ).reset_index()

            # Classify performance based on shifts used vs estimated shifts
            final_results['isBad'] = final_results['shiftsUsed'] > final_results['moldEstimatedShiftUsed']

            # Separate bad and good history lists
            bad_hist_list = final_results[final_results['isBad'] == True]['poNo'].tolist()
            good_hist_list = final_results[final_results['isBad'] == False]['poNo'].tolist()

            # Extract bad and good historical records
            bad_hist = productRecords_df[required_fields][
                productRecords_df['poNo'].isin(bad_hist_list)
                ].copy()
            self.logger.debug('Bad groups information: {}-{}', bad_hist.shape, bad_hist.columns)

            good_hist = productRecords_df[required_fields][
                productRecords_df['poNo'].isin(good_hist_list)
                ].copy()
            self.logger.debug('Good groups information: {}-{}', good_hist.shape, good_hist.columns)

            # Summarize mold-machine history for both groups
            good_sample, _ = summarize_mold_machine_history(good_hist,
                                                            mold_estimated_capacity_df)
            bad_sample, _ = summarize_mold_machine_history(bad_hist,
                                                        mold_estimated_capacity_df)
            
            # Validate the resulting DataFrames
            self._validate_shared_database(df_name="mold_machine_history_summary", 
                                        df=good_sample)
            self._validate_shared_database(df_name="mold_machine_history_summary",
                                        df=bad_sample)

            self.logger.info("Grouping completed successfully!")
            return good_sample, bad_sample
        
        except Exception as e:  
            self.logger.error("Failed to group historical data: {}", str(e))
            raise

    #---------------------------------#
    # PHASE 3: CALCULATE CONFIDENCE   #
    #---------------------------------# 
    def _calculate_confidence_scores(self, 
                                     good_sample: pd.DataFrame, 
                                     bad_sample: pd.DataFrame) -> Dict[str, float]:
        
        """Calculate confidence scores based on good and bad samples."""

        # Step 1: Calculate confidence scores for each feature based on good and bad performance groups.
        try:
            self.logger.info("Calculating confidence scores for each feature ...")
            confidence_scores = MoldMachineFeatureWeightCalculator._calculate_feature_confidence_scores(
                good_sample,
                bad_sample,
                self.feature_weight_config.targets,
                self.feature_weight_config.n_bootstrap,
                self.feature_weight_config.confidence_level,
                self.feature_weight_config.min_sample_size,
                self.feature_weight_config.sample_size_threshold)
            self.logger.info("Confidence scores for each feature calculated successfully!")
        except Exception as e:
            self.logger.error("Failed to calculate confidence scores for each feature: {}", str(e))
            raise
        
        # Step 2: Calculate overall confidence scores by aggregating individual feature confidence scores
        try:
            self.logger.debug("Calculating overall confidence ...")
            overall_confidence = MoldMachineFeatureWeightCalculator._calculate_overall_confidence(
                confidence_scores,
                self.feature_weight_config.feature_weights)
            self.logger.info("Overall confidence calculated successfully!")
            return confidence_scores, overall_confidence
        except Exception as e:
            self.logger.error("Failed to calculate overall confidence: {}", str(e))
            raise
        
    @staticmethod
    def _calculate_feature_confidence_scores(good_hist_df: pd.DataFrame,
                                             bad_hist_df: pd.DataFrame,
                                             targets: Dict[str, Union[float, str]],
                                             n_bootstrap: int = 1000,
                                             confidence_level: float = 0.95,
                                             min_sample_size: int = 10,
                                             sample_size_threshold: int = 50) -> Dict[str, Dict[str, float]]:

        """
        Calculate confidence scores for each feature based on good and bad performance groups.

        Args:
            good_hist_df (pd.DataFrame): DataFrame of the good performance group.
            bad_hist_df (pd.DataFrame): DataFrame of the bad performance group.
            features (List[str]): List of features to analyze.
            targets (Dict[str, Union[float, str]]): Dictionary specifying target values for each feature.
            n_bootstrap (int): Number of bootstrap iterations (default: 1000).
            confidence_level (float): Desired confidence level (default: 0.95).
            min_sample_size (int): Minimum required sample size for valid confidence computation.

        Returns:
            Dict[str, Dict[str, float]]: A dictionary containing confidence scores and statistics per feature.
        """

        results = {}
        alpha = 1 - confidence_level

        features = list(targets.keys())
        for feature in features:
            if feature not in good_hist_df.columns or feature not in bad_hist_df.columns:
                results[feature] = {
                    'good_confidence': 0.0,
                    'bad_confidence': 0.0,
                    'separation_confidence': 0.0,
                    'sample_size_good': 0,
                    'sample_size_bad': 0,
                    'warning': f'Feature {feature} not found in data'
                }
                continue

            # Drop NaN values from both groups
            good_data = good_hist_df[feature].dropna()
            bad_data = bad_hist_df[feature].dropna()

            sample_size_good = len(good_data)
            sample_size_bad = len(bad_data)

            # Check for minimum sample size
            if sample_size_good < min_sample_size or sample_size_bad < min_sample_size:
                results[feature] = {
                    'good_confidence': 0.5,  # Neutral confidence
                    'bad_confidence': 0.5,
                    'separation_confidence': 0.0,
                    'sample_size_good': sample_size_good,
                    'sample_size_bad': sample_size_bad,
                    'warning': f'Sample size too small (good: {sample_size_good}, bad: {sample_size_bad})'
                }
                continue

            # Bootstrap sampling to estimate distributions
            good_bootstrap_means = []
            bad_bootstrap_means = []

            np.random.seed(42)  # For reproducibility

            for _ in range(n_bootstrap):
                good_sample = np.random.choice(good_data, size=min(len(good_data), 
                                                                   sample_size_threshold), replace=True)
                bad_sample = np.random.choice(bad_data, size=min(len(bad_data), 
                                                                 sample_size_threshold), replace=True)
                good_bootstrap_means.append(np.mean(good_sample))
                bad_bootstrap_means.append(np.mean(bad_sample))

            good_bootstrap_means = np.array(good_bootstrap_means)
            bad_bootstrap_means = np.array(bad_bootstrap_means)

            # Confidence intervals
            good_ci_lower = np.percentile(good_bootstrap_means, (alpha / 2) * 100)
            good_ci_upper = np.percentile(good_bootstrap_means, (1 - alpha / 2) * 100)
            bad_ci_lower = np.percentile(bad_bootstrap_means, (alpha / 2) * 100)
            bad_ci_upper = np.percentile(bad_bootstrap_means, (1 - alpha / 2) * 100)

            # Target-based confidence scoring
            target_value = targets[feature]

            if target_value == 'minimize':
                # Smaller is better
                good_target_achievement = np.mean(good_bootstrap_means < np.mean(bad_bootstrap_means))
                bad_target_achievement = np.mean(bad_bootstrap_means > np.mean(good_bootstrap_means))

                good_distance_from_ideal = np.mean(np.abs(good_bootstrap_means))
                bad_distance_from_ideal = np.mean(np.abs(bad_bootstrap_means))
            else:
                # Closer to the target is better
                good_distance_from_target = np.mean(np.abs(good_bootstrap_means - target_value))
                bad_distance_from_target = np.mean(np.abs(bad_bootstrap_means - target_value))

                good_target_achievement = np.mean(
                    np.abs(good_bootstrap_means - target_value) <
                    np.abs(bad_bootstrap_means - target_value)
                )
                bad_target_achievement = 1 - good_target_achievement

                good_distance_from_ideal = good_distance_from_target
                bad_distance_from_ideal = bad_distance_from_target

            # Separation confidence using CI overlap
            overlap = max(0, min(good_ci_upper, bad_ci_upper) - max(good_ci_lower, bad_ci_lower))
            total_range = max(good_ci_upper, bad_ci_upper) - min(good_ci_lower, bad_ci_lower)
            separation_confidence = 1 - (overlap / max(total_range, 0.001))

            # Statistical test (Mann-Whitney U) to detect significant difference
            try:
                stat, p_value = stats.mannwhitneyu(good_data, bad_data, alternative='two-sided')
                statistical_significance = 1 - p_value
            except:
                statistical_significance = 0.5

            # Final confidence score calculations
            good_confidence = (
                good_target_achievement * 0.4 +
                separation_confidence * 0.3 +
                statistical_significance * 0.2 +
                (1 / (1 + good_distance_from_ideal)) * 0.1
            )
            bad_confidence = (
                bad_target_achievement * 0.4 +
                separation_confidence * 0.3 +
                statistical_significance * 0.2 +
                (1 / (1 + bad_distance_from_ideal)) * 0.1
            )

            # Ensure within [0, 1]
            good_confidence = max(0, min(1, good_confidence))
            bad_confidence = max(0, min(1, bad_confidence))

            results[feature] = {
                'good_confidence': round(good_confidence, 3),
                'bad_confidence': round(bad_confidence, 3),
                'separation_confidence': round(separation_confidence, 3),
                'statistical_significance': round(statistical_significance, 3),
                'sample_size_good': sample_size_good,
                'sample_size_bad': sample_size_bad,
                'good_mean': round(np.mean(good_data), 4),
                'bad_mean': round(np.mean(bad_data), 4),
                'good_ci_lower': round(good_ci_lower, 4),
                'good_ci_upper': round(good_ci_upper, 4),
                'bad_ci_lower': round(bad_ci_lower, 4),
                'bad_ci_upper': round(bad_ci_upper, 4),
                'p_value': round(1 - statistical_significance, 4) if statistical_significance != 0.5 else 0.5
            }

        return results

    @staticmethod
    def _calculate_overall_confidence(confidence_scores: Dict[str, Dict[str, float]],
                                      feature_weights: Optional[Dict[str, float]] = None) -> Dict[str, float]:

        """
        Calculate overall confidence scores by aggregating individual feature confidence scores.

        Args:
            confidence_scores: Output from calculate_confidence_scores()
            feature_weights: Weights for each feature (optional)

        Returns:
            Dict with overall confidence scores
        """

        if not confidence_scores:
            return {'overall_good_confidence': 0.0, 'overall_bad_confidence': 0.0, 'model_reliability': 0.0}

        # Use equal weights if none are provided
        if feature_weights is None:
            feature_weights = {feature: 1.0 for feature in confidence_scores.keys()}

        # Normalize weights
        total_weight = sum(feature_weights.values())
        if total_weight > 0:
            feature_weights = {k: v / total_weight for k, v in feature_weights.items()}

        good_confidences = []
        bad_confidences = []
        separation_confidences = []
        valid_features = 0

        for feature, scores in confidence_scores.items():
            if 'warning' not in scores:
                weight = feature_weights.get(feature, 1.0)
                good_confidences.append(scores['good_confidence'] * weight)
                bad_confidences.append(scores['bad_confidence'] * weight)
                separation_confidences.append(scores['separation_confidence'] * weight)
                valid_features += 1

        if valid_features == 0:
            return {'overall_good_confidence': 0.0, 'overall_bad_confidence': 0.0, 'model_reliability': 0.0}

        overall_good_confidence = sum(good_confidences)
        overall_bad_confidence = sum(bad_confidences)
        overall_separation = sum(separation_confidences)

        # Model reliability based on separation and the number of valid features
        model_reliability = overall_separation * (valid_features / len(confidence_scores))

        logger.info("Model Reliability: {:.1%}", model_reliability)
        logger.info("Good Group Confidence: {:.1%}", overall_good_confidence)
        logger.info("Bad Group Confidence: {:.1%}", overall_bad_confidence)

        results = {
                'overall_good_confidence': round(overall_good_confidence, 3),
                'overall_bad_confidence': round(overall_bad_confidence, 3),
                'overall_separation_confidence': round(overall_separation, 3),
                'model_reliability': round(model_reliability, 3),
                'valid_features_ratio': round(valid_features / len(confidence_scores), 3),
                'total_features': len(confidence_scores),
                'valid_features': valid_features
                }

        # Diplay
        logger.debug('Overall confidence score: \n{}', log_dict_as_table(results, transpose = False))

        return results

    #----------------------------------#
    # PHASE 4: SUGGEST FEATURE WEIGHTS #
    #----------------------------------#
    def _suggest_weights_with_confidence(self, 
                                         good_hist_df: pd.DataFrame,
                                         bad_hist_df: pd.DataFrame,
                                         targets: Dict[str, Union[float, str]],
                                         scaling: Literal['absolute', 'relative'] = 'absolute',
                                         confidence_weight: float = 0.3,
                                         n_bootstrap: int = 1000,
                                         confidence_level: float = 0.95,
                                         min_sample_size: int = 10,
                                         sample_size_threshold: int = 50) -> Dict[str, float]:

        """
        Suggests feature weights enhanced by confidence scores.

        Args:
            good_hist_df: Good performance data
            bad_hist_df: Bad performance data
            targets: Target values for each feature
            scaling: 'absolute' or 'relative'
            confidence_weight: The weight of confidence in the final weight calculation

        Returns:
            Dict of weighted scores with confidence consideration
        """
        
        self.logger.info("Suggesting enhanced feature weights ...")

        # Suggests weights based on standard method without confidence consideration.
        try:
            self.logger.info("Calculating traditional weights ...")
            traditional_weights = MoldMachineFeatureWeightCalculator._suggest_weights_standard_based(
                good_hist_df,
                bad_hist_df,
                targets,
                scaling)
            self.logger.info("Traditional weights suggested successfully!")
        except Exception as e:
            self.logger.error("Failed to suggest traditional weights: {}", str(e))
            raise
            
        # Calculate confidence scores for each feature based on good and bad performance groups.
        try:
            self.logger.info("Calculating confidence scores for each feature ...")
            confidence_scores = MoldMachineFeatureWeightCalculator._calculate_feature_confidence_scores(
                good_hist_df,
                bad_hist_df,
                targets,
                n_bootstrap,
                confidence_level,
                min_sample_size,
                sample_size_threshold)
            self.logger.info("Confidence scores calculated successfully!")
        except Exception as e:
            self.logger.error("Failed to calculate confidence scores for each feature: {}", str(e))
            raise  

        # Display confidence scores for debugging
        logger.debug('Confidence scores using bootstrap sampling: ', )
        logger.debug('\n{}', log_dict_as_table(confidence_scores, transpose = True))

        # Enhance weights using traditional weights and confidence scores
        enhanced_weights = {}
        for feature in list(targets.keys()):
            traditional_weight = traditional_weights.get(feature, 0)
            # Adjust weight based on confidence
            if feature in confidence_scores and 'warning' not in confidence_scores[feature]:
                # Use separation confidence to adjust weight
                confidence_factor = confidence_scores[feature]['separation_confidence']
                # Enhanced weight = traditional_weight * (1 + confidence_factor * confidence_weight)
                enhanced_weight = traditional_weight * (1 + confidence_factor * confidence_weight)
            else:
                enhanced_weight = traditional_weight * 0.5  # Reduce weight if not reliable
            enhanced_weights[feature] = enhanced_weight

        # Normalize the weights
        total = sum(enhanced_weights.values())
        if total == 0:
            return {k: 1 / len(list(targets.keys())) for k in list(targets.keys())}

        self.logger.info("Enhanced feature weights suggested successfully!")
        
        return {k: v / total for k, v in enhanced_weights.items()}

    @staticmethod
    def _suggest_weights_standard_based(good_hist_df: pd.DataFrame,
                                        bad_hist_df: pd.DataFrame,
                                        targets: Dict[str, Union[float, str]],
                                        scaling: Literal['absolute', 'relative'] = 'absolute') -> Dict[str, float]:

        """
        Suggests weights based on standard method without confidence consideration.

        Args:
            good_hist_df: Good performance data
            bad_hist_df: Bad performance data
            targets: Dict mapping feature names to target values or 'minimize'
            scaling: 'absolute' or 'relative' scaling method

        Returns:
            Dictionary of normalized weights (sum = 1)
        """

        # Get list of features
        features = list(targets.keys())

        # Validate inputs
        if not features:
            raise ValueError("Features list cannot be empty")
        if scaling not in ['absolute', 'relative']:
            raise ValueError("Scaling must be 'absolute' or 'relative'")

        # Calculate raw weights
        weights = {}
        for feature in features:
            if feature not in good_hist_df.columns or feature not in bad_hist_df.columns:
                logger.info(f"Warning: Feature '{feature}' not found in data. Setting weight to 0.")
                weights[feature] = 0
                continue

            # Calculate means
            mean_good = good_hist_df[feature].mean() if len(good_hist_df) > 0 else 0
            mean_bad = bad_hist_df[feature].mean() if len(bad_hist_df) > 0 else 0
            if pd.isna(mean_good):
                mean_good = 0
            if pd.isna(mean_bad):
                mean_bad = 0

            # Calculate score based on target
            if targets[feature] == 'minimize':
                # For metrics like NG rate: lower is better
                deviation_good = abs(mean_good)  # deviation from 0
                deviation_bad = abs(mean_bad)
                score = abs(deviation_bad - deviation_good)
            else:
                # For metrics with target values: closer to target is better
                target = targets[feature]
                deviation_good = abs(mean_good - target)
                deviation_bad = abs(mean_bad - target)
                score = abs(deviation_bad - deviation_good)

            # Apply scaling
            if scaling == 'relative':
                if targets[feature] == 'minimize':
                    # Avoid division by zero
                    denominator = max(abs(mean_good), abs(mean_bad), 0.001)
                    score /= denominator
                else:
                    score /= max(abs(targets[feature]), 0.001)

            # Assign score to weights
            weights[feature] = score

        # Normalize weights to sum to 1
        total = sum(weights.values())
        if total == 0:
            # If all scores are 0, assign equal weights
            return {k: 1 / len(weights) for k in weights}

        return {k: v / total for k, v in weights.items()}

    def save_output_with_versioning(self, 
                                    confidence_report_text: str,
                                    enhanced_weights: Dict):

        timestamp_now = datetime.now()
        timestamp_str = timestamp_now.strftime("%Y-%m-%d %H:%M:%S")
        timestamp_file = timestamp_now.strftime("%Y%m%d_%H%M")
        log_entries = [f"[{timestamp_str}] Saving new version...\n"]

        newest_dir = self.output_dir / "newest"
        newest_dir.mkdir(parents=True, exist_ok=True)
        historical_dir = self.output_dir / "historical_db"
        historical_dir.mkdir(parents=True, exist_ok=True)

        # Move old reports to historical_db
        for f in newest_dir.iterdir():
            if f.is_file() and f.suffix == '.txt':
                try:
                    dest = historical_dir / f.name
                    shutil.move(str(f), dest)
                    log_entries.append(f"  ⤷ Moved old file: {f.name} → historical_db/{f.name}\n")
                    logger.info("Moved old file {} to historical_db as {}", f.name, dest.name)
                except Exception as e:
                    logger.error("Failed to move file {}: {}", f.name, e)
                    raise OSError(f"Failed to move file {f.name}: {e}")

        #Save confidence report    
        try:
            new_filename = f"{timestamp_file}_{self.filename_prefix}.txt"
            new_path = newest_dir / new_filename
            with open(new_path, "w", encoding="utf-8") as file:
                file.write(confidence_report_text)
            log_entries.append(f"  ⤷ Saved new file: {new_path}\n")
            logger.info("Saved new report: {}", new_path)
        except Exception as e:
            logger.error("Failed to save report {}: {}", new_path, e)
            raise OSError(f"Failed to save report {new_path}: {e}")
        
        # Append to weights_hist.xlsx if weights provided -> support feature_weight_calculator.py
        weights_path = self.output_dir / "weights_hist.xlsx"
        if enhanced_weights:
            try:
                weights_row = {
                    "shiftNGRate": enhanced_weights.get("shiftNGRate", None),
                    "shiftCavityRate": enhanced_weights.get("shiftCavityRate", None),
                    "shiftCycleTimeRate": enhanced_weights.get("shiftCycleTimeRate", None),
                    "shiftCapacityRate": enhanced_weights.get("shiftCapacityRate", None),
                    "change_timestamp": timestamp_str
                }
                weights_df = pd.DataFrame([weights_row])

                if weights_path.exists():
                    old_df = pd.read_excel(weights_path)
                    full_df = pd.concat([old_df, weights_df], ignore_index=True)
                else:
                    full_df = weights_df

                full_df.to_excel(weights_path, index=False)
                log_entries.append(f"  ⤷ Saved new weight change: {weights_path}\n")
                logger.info("Logged weight change to {}", weights_path)
            except Exception as e:
                logger.error("Failed to write weights_hist.xlsx: {}", e)
                raise OSError(f"Failed to write weights_hist.xlsx: {e}")

        return "".join(log_entries)