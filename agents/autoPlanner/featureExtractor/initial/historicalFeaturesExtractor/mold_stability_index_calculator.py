import pandas as pd
import numpy as np
import os
from pathlib import Path
from loguru import logger

from agents.decorators import validate_init_dataframes
from typing import Dict, Optional, List, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

from agents.utils import load_annotation_path, save_output_with_versioning, ConfigReportMixin
from configs.shared.shared_source_config import SharedSourceConfig
from datetime import datetime
from agents.autoPlanner.reportFormatters.dict_based_report_generator import DictBasedReportGenerator
from agents.autoPlanner.featureExtractor.initial.historicalFeaturesExtractor.configs.mold_stability_config import MoldStabilityConfig

class ExecutionStatus(Enum):
    """Enum for execution status"""
    SUCCESS = "success"
    FAILED = "failed"
    WARNING = "warning"
    PARTIAL = "partial"

@dataclass
class MoldStabilityCalculatorInfo:
    """Standardized return structure for all agents"""
    agent_id: str
    status: str
    summary: Dict[str, Any]
    details: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)

# Decorator to validate DataFrames are initialized with the correct schema
# This ensures that required DataFrames have all necessary columns before processing
@validate_init_dataframes(lambda self: {
    "productRecords_df": list(self.databaseSchemas_data['dynamicDB']['productRecords']['dtypes'].keys()),
    "moldInfo_df": list(self.databaseSchemas_data['staticDB']['moldInfo']['dtypes'].keys()),
})

class MoldStabilityIndexCalculator(ConfigReportMixin): 

    """
    This class responsible for processing historical production data in order to process:
    1. Evaluate Mold Performance and Stability:
    - Analyze mold stability based on the number of active cavities and actual cycle time.
    - Apply criteria such as accuracy, consistency, compliance with standard limits, and data completeness.
    - Calculate key indicators: theoretical output, actual output, efficiency, and normalized productivity.
    """

    REQUIRED_FIELDS = {
        'shared_source_config': {
            'databaseSchemas_path': str,
            'annotation_path': str,
            'mold_stability_index_dir': str,
            },
        'mold_stability_config': {
            'efficiency': float,
            'loss': float,
            'cavity_stability_threshold': float,
            'cycle_stability_threshold': float,
            'total_records_threshold': int
            }
        }

    CONSTANT_CONFIG_PATH = (
        "agents/autoPlanner/featureExtractor/initial/historicalFeaturesExtractor/configs/constant_configurations.json")
    
    def __init__(self, 
                 shared_source_config: SharedSourceConfig, 
                 mold_stability_config: MoldStabilityConfig):
        
        """
        Initialize the MoldStabilityIndexCalculator.
        
        Args:
            shared_source_config: SharedSourceConfig containing processing parameters
                Including:
                    - annotation_path (str): Path to the JSON file containing path annotations
                    - databaseSchemas_path (str): Path to the database schema configuration file.
                    - mold_stability_index_dir (str): Default directory for output and temporary files.
            mold_stability_config: MoldStabilityConfig containing processing parameters
                Including:
                    - efficiency (float): Production efficiency score.
                    - loss (float): Production loss value.
                    - cavity_stability_threshold (float): Weight assigned to the cavity-stability feature.
                    - cycle_stability_threshold (float): Weight assigned to the cycle-stability feature.
                    - total_records_threshold (int): Minimum number of valid production records required
                    for processing (must be at least 30 records per day).

        """
        
        # Capture initialization arguments for reporting
        self._capture_init_args()

        # Initialize logger with class context for better debugging
        self.logger = logger.bind(class_="MoldStabilityIndexCalculator")

        # Validate required configs
        is_valid, errors = shared_source_config.validate_requirements(self.REQUIRED_FIELDS['shared_source_config'])
        if not is_valid:
            raise ValueError(
                f"{self.__class__.__name__} config validation failed:\n" +
                "\n".join(f"  - {e}" for e in errors)
            )
        self.logger.info("✓ Validation for shared_source_config requirements: PASSED!")

        # Load database schema configuration for column validation
        # This ensures all DataFrames have the expected structure
        self.databaseSchemas_data = load_annotation_path(
            Path(shared_source_config.databaseSchemas_path).parent,
            Path(shared_source_config.databaseSchemas_path).name
        )

        # Load path annotations that map logical names to actual file paths
        # This allows flexible configuration of data source locations
        self.path_annotation = load_annotation_path(
            Path(shared_source_config.annotation_path).parent, 
            Path(shared_source_config.annotation_path).name)
        
        # Load all required DataFrames from parquet files
        self._load_dataframes()

        # Load constant configurations
        self.constant_config = load_annotation_path(
            Path(self.CONSTANT_CONFIG_PATH).parent,
            Path(self.CONSTANT_CONFIG_PATH).name).get('MoldStabilityIndexCalculator', {})
        if not self.constant_config:
            self.logger.debug("MoldStabilityIndexCalculator constant config not found in loaded YAML dict")

        # Set up output configuration for saving results
        self.filename_prefix = "mold_stability_index"
        self.output_dir = Path(shared_source_config.mold_stability_index_dir) # Specific output directory
        
        # Store configurations
        self.config = mold_stability_config

        # Validate efficiency and loss parameters
        if not 0.0 <= self.config.efficiency <= 1.0:
            raise ValueError(f"Efficiency must be between 0.0 and 1.0, got {self.config.efficiency}")
        if not 0.0 <= self.config.loss <= 1.0:
            raise ValueError(f"Loss must be between 0.0 and 1.0, got {self.config.loss}")
        if self.config.efficiency <= self.config.loss:
            raise ValueError(
                f"Efficiency ({self.config.efficiency}) must be greater than loss ({self.config.loss})"
            )

    def _load_dataframes(self) -> None:

        """
        Load all required DataFrames from parquet files with consistent error handling.

        This method loads the following DataFrames:
        - productRecords_df: Historical production records with item, mold, machine data
        - moldInfo_df: Detailed mold information including tonnage requirements

        Raises:
            FileNotFoundError: If any required data file is missing
            Exception: If there are issues reading the parquet files
        """

        # Define the mapping between path annotation keys and DataFrame attribute names
        # This creates a clean separation between logical names and actual attributes
        dataframes_to_load = [
            ('productRecords', 'productRecords_df'),      # Historical production data
            ('moldInfo', 'moldInfo_df'),                  # Detailed mold information
        ]

        # Load each DataFrame with comprehensive error handling
        for path_key, attr_name in dataframes_to_load:
            # Retrieve the actual file path from annotations
            path = self.path_annotation.get(path_key)

            # Validate that the path exists and is accessible
            if not path or not os.path.exists(path):
                self.logger.error("Path to '{}' not found or does not exist: {}", path_key, path)
                raise FileNotFoundError(f"Path to '{path_key}' not found or does not exist: {path}")

            try:
                # Load DataFrame from parquet file
                # Parquet format provides efficient storage and fast loading
                df = pd.read_parquet(path)

                # Dynamically set the DataFrame as an instance attribute
                setattr(self, attr_name, df)

                # Log successful loading with shape and column information for debugging
                self.logger.debug("{}: {} - {}", path_key, df.shape, list(df.columns))

            except Exception as e:
                # Log detailed error information and re-raise for proper error handling
                self.logger.error("Failed to load {}: {}", path_key, str(e))
                raise

    def process(self,
                save_results: bool = False) -> MoldStabilityCalculatorInfo:
        """
        Calculates cavity and cycle stability indices for molds based on historical production data
        and will be used to estimate mold capacity in planning steps

        Args:
            df: A DataFrame containing production records with columns:
                - moldNo: Mold identifier
                - recordDate: Date of record
                - moldCavity: Actual cavity values (list of integers)
                - moldCavityStandard: Standard number of cavities
                - moldCycle: Actual cycle times (list of floats)
                - moldSettingCycle: Target (standard) cycle time

        Returns:
            A DataFrame with additional columns:
                - cavity_stability_index: Stability index of mold cavity (0-1)
                - cycle_stability_index: Stability index of mold cycle (0-1)
        """

        start_time = datetime.now()
        agent_id = f"{self.__class__.__name__}"
        warnings = []
        calculator_log_entries = []

        try:
            self.logger.info("Starting MoldStabilityIndexCalculator ...")

            # Generate config header using mixin
            timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            config_header = self._generate_config_report(timestamp_str, required_only=True)
            
            calculator_log_entries = [config_header]
            calculator_log_entries.append(f"--Processing Summary--\n")
            calculator_log_entries.append(f"⤷ {self.__class__.__name__} results:\n")

            # Extract historical data
            historical_data = self._stability_index_input_processing(self.productRecords_df, 
                                                                     self.moldInfo_df)

            # Calculate stability index
            stability_df = self._calculate_stability_index(historical_data)

            # Generate report
            reporter = DictBasedReportGenerator(use_colors=False)
            calculation_summary = "\n".join(reporter.export_report({"Mold Stability Index": stability_df}))
            calculator_log_entries.append(f"{calculation_summary}\n") 

            # Save results if required
            output_saved = False
            if save_results:
                try:
                    # Export results to Excel with versioning
                    self.logger.info("Exporting results to Excel...")
                    output_exporting_log =  save_output_with_versioning(
                        data = {"moldStabilityIndex": stability_df},  # Dictionary containing the data to save
                        output_dir = self.output_dir,                 # Directory where the file will be saved
                        filename_prefix = self.filename_prefix,       # Prefix for the output filename
                        report_text = calculation_summary
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

            return MoldStabilityCalculatorInfo(
                agent_id=agent_id,
                status=ExecutionStatus.SUCCESS.value if not warnings else ExecutionStatus.WARNING.value,
                
                summary={
                    "phases_completed": 1,
                    "all_phases_successful": True,
                    "molds_processed": len(stability_df),
                    "avg_cavity_stability": round(stability_df['cavityStabilityIndex'].mean(), 2),
                    "avg_cycle_stability": round(stability_df['cycleStabilityIndex'].mean(), 2),
                    "results_saved": output_saved,
                    "warnings_count": len(warnings)
                },
                
                # Include all molds' results
                details={
                    "stability_index": stability_df,
                    "summary_stats": {
                        "total_records": int(stability_df['totalRecords'].sum()),
                        "total_cavity_measurements": int(stability_df['totalCavityMeasurements'].sum()),
                        "total_cycle_measurements": int(stability_df['totalCycleMeasurements'].sum()),
                    }
                },
                
                metadata={
                    "processing_duration": processing_duration,
                    "processing_duration_formatted": f"{processing_duration:.2f}s",
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat(),
                    "log_entries": calculator_log_str,
                    "config": {
                        "efficiency": self.config.efficiency,
                        "loss": self.config.loss,
                        "cavity_stability_threshold": self.config.cavity_stability_threshold,
                        "cycle_stability_threshold": self.config.cycle_stability_threshold,
                        "total_records_threshold": self.config.total_records_threshold
                    },
                },
                
                warnings=warnings
            )

        except Exception as e:
            end_time = datetime.now()
            processing_duration = (end_time - start_time).total_seconds()
            
            self.logger.error("❌ {} failed: {}", agent_id, str(e))
            return MoldStabilityCalculatorInfo(
                agent_id=agent_id,
                status=ExecutionStatus.FAILED.value,
                
                summary={
                    "error_message": str(e),
                    "phases_completed": 0
                },
                
                details={
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
        
    def _stability_index_input_processing(self,
                                          productRecords_df: pd.DataFrame,
                                          moldInfo_df: pd.DataFrame) -> pd.DataFrame:
        """
        Extract historical data to calculate stability index calculation.
        
        Args:
            productRecords_df: Production records DataFrame
            moldInfo_df: Mold information DataFrame
            
        Returns:
            pd.DataFrame: Processed DataFrame with required fields
        """
        
        filter_df = productRecords_df[productRecords_df['moldShot'] > 0].copy()
        filter_df['moldCycle'] = (self.constant_config["PRODUCTION_WINDOW_SECONDS"] / filter_df['moldShot']).round(2)

        # Group and aggregate
        df = filter_df.groupby(['moldNo', 'recordDate'])[['moldCavity', 'moldCycle']].agg(list).reset_index()

        # Ensure correct data types
        df['moldCavity'] = df['moldCavity'].apply(lambda lst: [int(x) for x in lst])
        df['moldCycle'] = df['moldCycle'].apply(lambda lst: [float(x) for x in lst])
        
        merged_df = df.merge(moldInfo_df[['moldNo', 'moldName',
                                          'moldCavityStandard', 'moldSettingCycle',
                                          'acquisitionDate', 'machineTonnage']], 
                            how='left', 
                            on='moldNo')

        valid_df = merged_df[
            (merged_df['moldCavityStandard'] > 0) &
            (merged_df['moldSettingCycle'] > 0) &
            (merged_df['moldCavityStandard'].notna()) &
            (merged_df['moldSettingCycle'].notna())
        ]

        filtered_count = len(merged_df) - len(valid_df)
        if filtered_count > 0:
            invalid_molds = merged_df[~merged_df['moldNo'].isin(valid_df['moldNo'])]['moldNo'].unique()
            self.logger.warning("Filtered {} records from {} molds ", filtered_count, len(invalid_molds))
            self.logger.warning("with invalid cavity/cycle: {}", list(invalid_molds)[:5])

        return valid_df[self.constant_config["REQUIRED_DF_FIELDS"]]
    
    def _calculate_stability_index(self, 
                                   df: pd.DataFrame) -> pd.DataFrame:
        """Calculates cavity and cycle stability indices"""

        # Validate input DataFrame has required columns and data
        if df.empty:
            self.logger.error("Extracted historical data is empty. Cannot calculate cavity and cycle stability indices")
            raise ValueError("Extracted historical data is empty. Cannot calculate cavity and cycle stability indices")
        
        # Initialize list to collect ALL mold results
        stability_results_list = []

        # Iterate through each mold
        for mold_no in df['moldNo'].unique():

            mold_data = df[df['moldNo'] == mold_no].copy()

            if mold_data.empty:
                self.logger.warning(f"Mold {mold_no} has no data after filtering, skipping")
                continue

            # Extract mold info efficiently using iloc
            mold_info = mold_data.iloc[0]

            moldName = mold_info['moldName']
            acquisitionDate = mold_info['acquisitionDate']
            machineTonnage = mold_info['machineTonnage']
            standard_cavity = mold_info['moldCavityStandard']
            standard_cycle = mold_info['moldSettingCycle']

            # Calculate theoretical capacity
            theoretical_hour_capacity = self.constant_config["SECONDS_PER_HOUR"] / standard_cycle * standard_cavity

            # Gather all cavity and cycle values
            mold_data = mold_data.sort_values('recordDate')
            all_cavity_values = [val for sublist in mold_data['moldCavity'] for val in sublist]
            all_cycle_values = [val for sublist in mold_data['moldCycle'] for val in sublist]

            # Calculate stability scores
            total_records = len(mold_data)
            cavity_stability = self._calculate_cavity_stability(
                all_cavity_values, standard_cavity, total_records, self.config.total_records_threshold
                )
            cycle_stability = self._calculate_cycle_stability(
                all_cycle_values, standard_cycle, total_records, self.config.total_records_threshold
                )
            
            # Calculate weighted stability
            overall_stability = (
                cavity_stability * self.config.cavity_stability_threshold) + (
                    cycle_stability * self.config.cycle_stability_threshold)

            # Calculate effective capacity
            effective_hour_capacity = theoretical_hour_capacity * overall_stability

            # Calculate estimated capacity (considering efficiency and loss)
            estimated_hour_capacity = theoretical_hour_capacity * (self.config.efficiency - self.config.loss)
        
            # Calculate balanced capacity (balance effective and estimated capacity by using alpha
            # Alpha: trust coefficient from historical data (0.1 - 1.0)
            alpha = max(
                self.constant_config["MIN_HISTORICAL_TRUST"], 
                min(
                    self.constant_config["MAX_HISTORICAL_TRUST"], 
                    total_records / self.config.total_records_threshold)
                    )
            balanced_hour_capacity = alpha * effective_hour_capacity + (1 - alpha) * estimated_hour_capacity

            # Append single mold stability to result list
            stability_results = {
                'moldNo': mold_no,
                'moldName': moldName,
                'acquisitionDate': acquisitionDate,
                'machineTonnage': machineTonnage,
                'moldCavityStandard': standard_cavity,
                'moldSettingCycle': standard_cycle,

                'cavityStabilityIndex': round(cavity_stability, 2),
                'cycleStabilityIndex': round(cycle_stability, 2),

                'theoreticalMoldHourCapacity': round(theoretical_hour_capacity, 2),
                'effectiveMoldHourCapacity': round(effective_hour_capacity, 2),
                'estimatedMoldHourCapacity': round(estimated_hour_capacity, 2),
                'balancedMoldHourCapacity': round(balanced_hour_capacity, 2),

                'totalRecords': total_records,
                'totalCavityMeasurements': len(all_cavity_values),
                'totalCycleMeasurements': len(all_cycle_values),
                'firstRecordDate': mold_data['recordDate'].min(),
                'lastRecordDate': mold_data['recordDate'].max(),
            }

            # Append to list
            stability_results_list.append(stability_results)

        # Return result as DataFrame
        return pd.DataFrame(stability_results_list)
    
    def _calculate_cavity_stability(self,
                                    cavity_values: List[int],
                                    standard_cavity: float,
                                    total_records: int,
                                    total_records_threshold: int) -> float:
        """
        Calculate cavity stability index.
        
        Args:
            cavity_values: List of actual cavity values
            standard_cavity: Standard number of cavities
            total_records: Total number of production records
            total_records_threshold: Minimum threshold for records
            
        Returns:
            float: Stability score between 0.0 and 1.0
        """

        # 1. Accuracy rate (how many values match the standard)
        correct_count = sum(1 for val in cavity_values if val == standard_cavity)
        accuracy_rate = correct_count / len(cavity_values)

        # 2. Consistency: variation of cavity values
        if len(set(cavity_values)) == 1:
            consistency_score = 1.0  # Perfectly consistent
        else:
            mean_val = np.mean(cavity_values)
            if mean_val > 0:
                cv = np.std(cavity_values) / mean_val
                consistency_score = max(0, 1 - cv)
            else:
                consistency_score = 0

        # 3. Utilization rate: actual average cavity vs standard
        avg_active_cavity = np.mean(cavity_values)
        utilization_rate = min(1.0, avg_active_cavity / standard_cavity)

        # 4. Penalty for low data volume
        data_completeness = min(1.0, total_records / total_records_threshold)

        # Final weighted score
        stability_score = (
            accuracy_rate * self.constant_config['CAVITY_STABILITY_WEIGHTS']['accuracy_rate_weight'] +           # 40% - Accuracy
            consistency_score * self.constant_config['CAVITY_STABILITY_WEIGHTS']['consistency_score_weight'] +   # 30% - Consistency
            utilization_rate * self.constant_config['CAVITY_STABILITY_WEIGHTS']['utilization_rate_weight'] +     # 20% - Utilization
            data_completeness * self.constant_config['CAVITY_STABILITY_WEIGHTS']['data_completeness_weight']     # 10% - Data completeness
        )

        return min(1.0, max(0.0, stability_score))

    def _calculate_cycle_stability(self,
                                   cycle_values: List[float],
                                   standard_cycle: float,
                                   total_records: int,
                                   total_records_threshold: int) -> float:
        """
        Calculate cycle time stability index.
        
        Args:
            cycle_values: List of actual cycle times
            standard_cycle: Standard cycle time
            total_records: Total number of production records
            total_records_threshold: Minimum threshold for records
            
        Returns:
            float: Stability score between 0.0 and 1.0
        """

        # 1. Deviation from standard
        deviations = [abs(val - standard_cycle) / standard_cycle for val in cycle_values]
        avg_deviation = np.mean(deviations) if deviations else self.constant_config['EXTREME_DEVIATION_THRESHOLD']
        accuracy_score = max(0, 1 - avg_deviation)

        # 2. Consistency: variation of cycle time
        mean_val = np.mean(cycle_values)
        if mean_val > 0:
            cv = np.std(cycle_values) / mean_val
            consistency_score = max(0, 1 - cv)
        else:
            consistency_score = 0

        # 3. Compliance within ±20% range
        in_range_count = sum(1 for val in cycle_values
                            if abs(val - standard_cycle) / standard_cycle <= self.constant_config['CYCLE_TIME_TOLERANCE'])
        range_compliance = in_range_count / len(cycle_values) if cycle_values else 0

        # 4. Penalty for extreme outliers (deviation > 100%)
        extreme_outliers = sum(1 for val in cycle_values
                            if abs(val - standard_cycle) / standard_cycle > self.constant_config['EXTREME_DEVIATION_THRESHOLD'])
        outlier_penalty = max(0, 1 - (extreme_outliers / len(cycle_values))) if cycle_values else 0

        # 5. Data completeness penalty
        data_completeness = min(1.0, total_records / total_records_threshold)

        # Final weighted score
        stability_score = (
            accuracy_score * self.constant_config['CYCLE_STABILITY_WEIGHTS']['accuracy_score_weight'] +         # 30% - Accuracy
            consistency_score * self.constant_config['CYCLE_STABILITY_WEIGHTS']['consistency_score_weight'] +   # 25% - Consistency
            range_compliance * self.constant_config['CYCLE_STABILITY_WEIGHTS']['range_compliance_weight'] +     # 25% - Range compliance
            outlier_penalty * self.constant_config['CYCLE_STABILITY_WEIGHTS']['outlier_penalty_weight'] +       # 10% - Outlier penalty
            data_completeness * self.constant_config['CYCLE_STABILITY_WEIGHTS']['data_completeness_weight']     # 10% - Data completeness
        )

        return min(1.0, max(0.0, stability_score))