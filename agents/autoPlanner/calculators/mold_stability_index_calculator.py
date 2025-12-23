import pandas as pd
import numpy as np
from loguru import logger

from agents.decorators import validate_init_dataframes
from typing import List, Dict

from configs.shared.config_report_format import ConfigReportMixin
from datetime import datetime
from configs.shared.dict_based_report_generator import DictBasedReportGenerator
from agents.autoPlanner.calculators.configs.mold_stability_config import (
    MoldStabilityConfig, MoldStabilityCalculationResult)

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

    SECONDS_PER_HOUR = 3600
    CYCLE_TIME_TOLERANCE = 0.2
    EXTREME_DEVIATION_THRESHOLD = 1.0
    MIN_HISTORICAL_TRUST = 0.1
    MAX_HISTORICAL_TRUST = 1.0
    PRODUCTION_WINDOW_SECONDS = 28800

    CYCLE_STABILITY_WEIGHTS = {
        "accuracy_score_weight": 0.3,
        "consistency_score_weight": 0.25,
        "range_compliance_weight": 0.25,
        "outlier_penalty_weight": 0.1,
        "data_completeness_weight": 0.1}

    CAVITY_STABILITY_WEIGHTS = {
        "accuracy_rate_weight": 0.4,
        "consistency_score_weight": 0.3,
        "utilization_rate_weight": 0.2,
        "data_completeness_weight": 0.1}

    REQUIRED_DF_FIELDS = [
        "moldNo", "moldName", "recordDate",
        "moldCavity", "moldCavityStandard", "moldCycle", 
        "moldSettingCycle", "acquisitionDate", "machineTonnage"
        ]
    
    def __init__(self, 
                 databaseSchemas_data: Dict,
                 productRecords_df: pd.DataFrame,
                 moldInfo_df: pd.DataFrame,
                 mold_stability_config: MoldStabilityConfig,
                 stability_constant_config: Dict = {}):
        
        """
        Initialize the MoldStabilityIndexCalculator.
        
        Args:
            - databaseSchemas_data: Database schemas for validation
            - productRecords_df: Production records with item, mold, machine data
            - moldInfo_df: Detailed mold information including tonnage requirements
            - mold_stability_config: MoldStabilityConfig containing processing parameters
                Including:
                    - efficiency (float): Production efficiency score.
                    - loss (float): Production loss value.
                    - cavity_stability_threshold (float): Weight assigned to the cavity-stability feature.
                    - cycle_stability_threshold (float): Weight assigned to the cycle-stability feature.
                    - total_records_threshold (int): Minimum number of valid production records required
                    for processing (must be at least 30 records per day).
            - stability_constant_config: Constant config for mold stability index calculator
        """
        
        # Capture initialization arguments for reporting
        self._capture_init_args()

        # Initialize logger with class context for better debugging
        self.logger = logger.bind(class_="MoldStabilityIndexCalculator")

        self.databaseSchemas_data = databaseSchemas_data
        self.productRecords_df = productRecords_df
        self.moldInfo_df = moldInfo_df

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
        
        self.stability_constant_config = stability_constant_config
        if not self.stability_constant_config:
            self.logger.debug("MoldStabilityIndexCalculator constant config not found.")

    def process(self) -> MoldStabilityCalculationResult:
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

        try:
            self.logger.info("Starting MoldStabilityIndexCalculator ...")

            # Generate config header using mixin
            timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            config_header = self._generate_config_report(timestamp_str)
            
            calculator_log_entries = [config_header]
            calculator_log_entries.append(f"--Processing Summary--\n")
            calculator_log_entries.append(f"⤷ {self.__class__.__name__} results:\n")

            # Extract historical data
            historical_data = self._stability_index_input_processing()

            # Calculate stability index
            mold_stability_index = self._calculate_stability_index(historical_data)

            # Generate report
            reporter = DictBasedReportGenerator(use_colors=False)
            index_calculation_summary = "\n".join(reporter.export_report({"Mold Stability Index": mold_stability_index}))
            calculator_log_entries.append(f"{index_calculation_summary}\n") 

            # Compile calculator log
            calculator_log_str = "\n".join(calculator_log_entries)

            self.logger.info("✅ Process finished!!!")

            return MoldStabilityCalculationResult(
                mold_stability_index = mold_stability_index,
                index_calculation_summary = index_calculation_summary,
                log_str = calculator_log_str
                )

        except Exception as e:
            self.logger.error("Failed to process MoldStabilityIndexCalculator: {}", str(e))
            raise RuntimeError(f"MoldStabilityIndexCalculator processing failed: {str(e)}") from e

    #-------------------------#
    # Extract historical data #
    #-------------------------#
    def _stability_index_input_processing(self) -> pd.DataFrame:
        """
        Extract historical data to calculate stability index calculation.
        
        Args:
            productRecords_df: Production records DataFrame
            moldInfo_df: Mold information DataFrame
            
        Returns:
            pd.DataFrame: Processed DataFrame with required fields
        """
        required_fields = self.stability_constant_config.get(
            "REQUIRED_DF_FIELDS", self.REQUIRED_DF_FIELDS)
        
        filter_df = self.productRecords_df[self.productRecords_df['moldShot'] > 0].copy()
        filter_df['moldCycle'] = (self.stability_constant_config.get(
            "PRODUCTION_WINDOW_SECONDS", self.PRODUCTION_WINDOW_SECONDS) / filter_df['moldShot']).round(2)

        # Group and aggregate
        df = filter_df.groupby(['moldNo', 'recordDate'])[['moldCavity', 'moldCycle']].agg(list).reset_index()

        # Ensure correct data types
        df['moldCavity'] = df['moldCavity'].apply(lambda lst: [int(x) for x in lst])
        df['moldCycle'] = df['moldCycle'].apply(lambda lst: [float(x) for x in lst])
        
        merged_df = df.merge(self.moldInfo_df[['moldNo', 'moldName',
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

        return valid_df[required_fields]
    
    #---------------------------#
    # Calculate stability index #
    #---------------------------#
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
            theoretical_hour_capacity = self.stability_constant_config.get(
                "SECONDS_PER_HOUR", 
                self.SECONDS_PER_HOUR) / standard_cycle * standard_cavity

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
                self.stability_constant_config.get(
                    "MIN_HISTORICAL_TRUST", self.MIN_HISTORICAL_TRUST), 
                min(
                    self.stability_constant_config.get(
                        "MAX_HISTORICAL_TRUST", self.MAX_HISTORICAL_TRUST), 
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
        cavity_stability_weights = self.stability_constant_config.get(
            "CAVITY_STABILITY_WEIGHTS", self.CAVITY_STABILITY_WEIGHTS)
        stability_score = (
            accuracy_rate * cavity_stability_weights['accuracy_rate_weight'] +           # 40% - Accuracy
            consistency_score * cavity_stability_weights['consistency_score_weight'] +   # 30% - Consistency
            utilization_rate * cavity_stability_weights['utilization_rate_weight'] +     # 20% - Utilization
            data_completeness *cavity_stability_weights['data_completeness_weight']      # 10% - Data completeness
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
        avg_deviation = np.mean(deviations) if deviations else self.stability_constant_config.get(
            "EXTREME_DEVIATION_THRESHOLD", self.EXTREME_DEVIATION_THRESHOLD)
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
                            if abs(val - standard_cycle) / standard_cycle <= self.stability_constant_config.get(
                                "CYCLE_TIME_TOLERANCE", self.CYCLE_TIME_TOLERANCE))
        range_compliance = in_range_count / len(cycle_values) if cycle_values else 0

        # 4. Penalty for extreme outliers (deviation > 100%)
        extreme_outliers = sum(1 for val in cycle_values
                            if abs(val - standard_cycle) / standard_cycle > self.stability_constant_config.get(
                                "EXTREME_DEVIATION_THRESHOLD", self.EXTREME_DEVIATION_THRESHOLD))
        outlier_penalty = max(0, 1 - (extreme_outliers / len(cycle_values))) if cycle_values else 0

        # 5. Data completeness penalty
        data_completeness = min(1.0, total_records / total_records_threshold)

        # Final weighted score
        cycle_stability_weights = self.stability_constant_config.get(
            "CYCLE_STABILITY_WEIGHTS", self.CYCLE_STABILITY_WEIGHTS)
        stability_score = (
            accuracy_score * cycle_stability_weights['accuracy_score_weight'] +         # 30% - Accuracy
            consistency_score * cycle_stability_weights['consistency_score_weight'] +   # 25% - Consistency
            range_compliance * cycle_stability_weights['range_compliance_weight'] +     # 25% - Range compliance
            outlier_penalty * cycle_stability_weights['outlier_penalty_weight'] +       # 10% - Outlier penalty
            data_completeness * cycle_stability_weights['data_completeness_weight']     # 10% - Data completeness
        )

        return min(1.0, max(0.0, stability_score))