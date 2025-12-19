import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

from typing import Tuple, Dict
from loguru import logger
from datetime import datetime

from agents.autoPlanner.tools.performance import summarize_mold_machine_history
from agents.autoPlanner.tools.mold_machine_feature_weight import suggest_weights_standard_based
from agents.autoPlanner.tools.bootstrap import (
    calculate_feature_confidence_scores, calculate_overall_confidence, generate_confidence_report)

from agents.decorators import validate_init_dataframes, validate_dataframe
from agents.utils import log_dict_as_table

from configs.shared.config_report_format import ConfigReportMixin
from agents.autoPlanner.calculators.configs.feature_weight_config import (
    FeatureWeightConfig, FeatureWeightCalculationResult)

# Decorator to validate DataFrames are initialized with the correct schema
@validate_init_dataframes(lambda self: {
    "productRecords_df": list(self.databaseSchemas_data['dynamicDB']['productRecords']['dtypes'].keys()),
    "moldInfo_df": list(self.databaseSchemas_data['staticDB']['moldInfo']['dtypes'].keys()),
    "proStatus_df": list(self.sharedDatabaseSchemas_data["pro_status"]['dtypes'].keys()),
    "mold_estimated_capacity_df": list(self.sharedDatabaseSchemas_data["mold_estimated_capacity"]['dtypes'].keys())
})
class MoldMachineFeatureWeightCalculator(ConfigReportMixin):

    """
    This class calculates feature weights used to evaluate manufacturing process performance
    by analyzing production history and computing confidence-based metrics. 
    It will be used as input of the next step (Mold-Machine Priority Matrix Generation - 
    generate a priority matrix to support optimal production planning)
    """

    # Define required fields
    PRO_RECORDS_REQUIRED_FIELDS = ['poNo', 'recordDate', 'workingShift', 'machineNo', 'machineCode',
                                   'itemCode', 'itemName', 'moldNo', 'moldShot', 'moldCavity',
                                   'itemTotalQuantity', 'itemGoodQuantity']

    def __init__(self,
                 databaseSchemas_data: Dict,
                 sharedDatabaseSchemas_data: Dict, 
                 productRecords_df: pd.DataFrame,
                 moldInfo_df: pd.DataFrame,
                 proStatus_df: pd.DataFrame,
                 mold_estimated_capacity_df: pd.DataFrame,
                 feature_weight_config: FeatureWeightConfig,
                 weight_constant_config: Dict = {}):

        """
        Initialize the MoldMachineFeatureWeightCalculator.
        
        Args:
            - databaseSchemas_data: Database schemas for validation
            - sharedDatabaseSchemas_data: Shared database schemas for validation
            - moldInfo_df: Detailed mold information including tonnage requirements
            - proStatus_df: Detailed order production progress.
            - mold_estimated_capacity_df: Detailed priority molds for each item code with the highest estimated capacity
            - feature_weight_config: FeatureWeightConfig containing processing parameters
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
            - weight_constant_config: Constant config for mold-machine feature weight calculator
        """

        # Capture initialization arguments for reporting
        self._capture_init_args()

        # Initialize logger with class context for better debugging
        self.logger = logger.bind(class_="MoldMachineFeatureWeightCalculator")

        self.databaseSchemas_data = databaseSchemas_data
        self.sharedDatabaseSchemas_data = sharedDatabaseSchemas_data

        self.productRecords_df = productRecords_df
        self.moldInfo_df = moldInfo_df
        self.proStatus_df = proStatus_df
        self.mold_estimated_capacity_df = mold_estimated_capacity_df
        
        # Store configurations
        self.config = feature_weight_config

        # Validate efficiency and loss parameters
        if not 0.0 <= self.config.efficiency <= 1.0:
            raise ValueError(f"Efficiency must be between 0.0 and 1.0, got {self.config.efficiency}")
        if not 0.0 <= self.config.loss <= 1.0:
            raise ValueError(f"Loss must be between 0.0 and 1.0, got {self.config.loss}")
        if self.config.efficiency <= self.config.loss:
            raise ValueError(
                f"Efficiency ({self.config.efficiency}) must be greater than loss ({self.config.loss})"
            )
        
        self.weight_constant_config = weight_constant_config
        if not self.weight_constant_config:
            self.logger.debug("MoldMachineFeatureWeightCalculator constant config not found.")
    
    def process(self) -> FeatureWeightCalculationResult:

        """
        Main method to calculate feature confidence scores and enhanced weights.
        """

        try:
            self.logger.info("Starting MoldMachineFeatureWeightCalculator ...")

            # Generate config header using mixin
            timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            config_header = self._generate_config_report(timestamp_str)

            calculator_log_entries = [config_header]
            calculator_log_entries.append(f"--Processing Summary--\n")
            calculator_log_entries.append(f"⤷ {self.__class__.__name__} results:\n")

            # Rename columns for consistency
            self.productRecords_df.rename(columns={'poNote': 'poNo'}, inplace=True)
            self.proStatus_df.rename(columns={'lastestMachineNo': 'machineNo',
                                              'lastestMoldNo': 'moldNo'}, inplace=True)

            # Step 1: Group historical production records into good and bad performance categories
            good_sample, bad_sample = self._group_hist_by_performance()
            
            good_count = good_sample.shape[0]
            bad_count = bad_sample.shape[0]
            
            calculator_log_entries.append("Grouping completed successfully!")
            calculator_log_entries.append(f"✓ Good performance records: {good_count} rows")
            calculator_log_entries.append(f"✓ Bad performance records: {bad_count} rows")
            
            # Check for sample size warnings
            if good_count < 10:
                self.logger.warning("Low good sample size: {} rows (minimum recommended: 10)", good_count)
                calculator_log_entries.append(f"Low good sample size: {good_count} rows (minimum recommended: 10)")
            if bad_count < 10:
                self.logger.warning("Low bad sample size: {} rows (minimum recommended: 10)", bad_count)
                calculator_log_entries.append(f"Low bad sample size: {bad_count} rows (minimum recommended: 10)")

            # Step 2: Calculate confidence scores
            confidence_scores, overall_confidence = self._calculate_confidence_scores(good_sample, 
                                                                                      bad_sample)
            
            calculator_log_entries.append("Overall confidence calculated successfully!")
            calculator_log_entries.append(
                f'Overall Confidence Scores: \n{log_dict_as_table(overall_confidence, transpose=False)}')
            
            # Check confidence warnings
            model_reliability = overall_confidence.get('model_reliability', 0)
            if model_reliability < 0.5:
                self.logger.warning("Low model reliability: {:.2%} (threshold: 50%)", model_reliability)
                calculator_log_entries.append(
                    f"Low model reliability: {model_reliability:.2%} (threshold: 50%)")
    
            # Step 3: Suggests feature weights enhanced by confidence scores.
            enhanced_weights = self._suggest_weights_with_confidence(good_sample,
                                                                     bad_sample)
            
            calculator_log_entries.append("Enhanced feature weights suggested successfully!")
            calculator_log_entries.append(
                f'Enhanced Weights (with confidence): \n{log_dict_as_table(enhanced_weights, transpose=False)}'
            )
            
            # Generate confidence report
            confidence_report_text = generate_confidence_report(confidence_scores, 
                                                                overall_confidence)
            
            self.logger.info("Confidence report generated successfully!")

            calculator_log_entries.append("Confidence report generated successfully!")
            calculator_log_entries.append(f"{confidence_report_text}\n")
            
            # Compile calculator log
            calculator_log_str = "\n".join(calculator_log_entries)

            self.logger.info("✅ Process finished!!!")

            return FeatureWeightCalculationResult(
                confidence_scores=confidence_scores,
                overall_confidence=overall_confidence,
                enhanced_weights=enhanced_weights,
                confidence_report_text=confidence_report_text,
                log_str=calculator_log_str
                )
        
        except Exception as e:
            self.logger.error("Failed to process MoldMachineFeatureWeightCalculator: {}", str(e))
            raise RuntimeError(f"MoldMachineFeatureWeightCalculator processing failed: {str(e)}") from e
        
    #---------------------------------#
    # PHASE 1: GROUP HISTORICAL DATA  #
    #---------------------------------#
    def _group_hist_by_performance(self) -> Tuple[pd.DataFrame, pd.DataFrame]:

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

        required_fields = self.weight_constant_config.get("PRO_RECORDS_REQUIRED_FIELDS", 
                                                          self.PRO_RECORDS_REQUIRED_FIELDS)
        
        # Validate required fields in productRecords_df
        missing_fields = [field for field in required_fields if field not in self.productRecords_df.columns]
        if missing_fields:
            raise ValueError(f"Missing fields in productRecords_df: {missing_fields}")
        self.logger.info("Validating required fields in productRecords_df successfully!")

        # Filter out records with zero total quantity
        hist = self.productRecords_df[
            self.productRecords_df['itemTotalQuantity'] > 0][required_fields].copy()

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
                self.moldInfo_df[['moldNo', 'moldCavityStandard', 'moldSettingCycle']],
                how='left', on='moldNo'
                ).merge(
                    self.proStatus_df[['poNo', 'itemCode', 'itemQuantity']],
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
                net_efficiency = self.config.efficiency - self.config.loss
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
            bad_hist = self.productRecords_df[required_fields][
                self.productRecords_df['poNo'].isin(bad_hist_list)
                ].copy()
            self.logger.debug('Bad groups information: {}-{}', bad_hist.shape, bad_hist.columns)

            good_hist = self.productRecords_df[required_fields][
                self.productRecords_df['poNo'].isin(good_hist_list)
                ].copy()
            self.logger.debug('Good groups information: {}-{}', good_hist.shape, good_hist.columns)

            # Summarize mold-machine history for both groups
            good_sample, _ = summarize_mold_machine_history(good_hist,
                                                            self.mold_estimated_capacity_df)
            bad_sample, _ = summarize_mold_machine_history(bad_hist,
                                                           self.mold_estimated_capacity_df)
            
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
    
    def _validate_shared_database(self, df_name, df) -> None:
        """Validate shared database DataFrame against expected schema."""
        try:
            cols = list(self.sharedDatabaseSchemas_data[df_name]['dtypes'].keys())
            validate_dataframe(df, cols)
            self.logger.info("✓ Validation for {} requirements: PASSED!", df_name)
        except Exception as e:
            logger.error("Validation failed for {} (expected cols: %s): %s", df_name, cols, e)
            raise
        
    #---------------------------------#
    # PHASE 2: CALCULATE CONFIDENCE   #
    #---------------------------------# 
    def _calculate_confidence_scores(self, 
                                     good_sample: pd.DataFrame, 
                                     bad_sample: pd.DataFrame) -> Dict[str, float]:
        
        """Calculate confidence scores based on good and bad samples."""

        # Step 1: Calculate confidence scores for each feature based on good and bad performance groups.
        try:
            self.logger.info("Calculating confidence scores for each feature ...")
            confidence_scores = calculate_feature_confidence_scores(
                good_sample,
                bad_sample,
                self.config.targets,
                self.config.n_bootstrap,
                self.config.confidence_level,
                self.config.min_sample_size,
                self.config.sample_size_threshold)
            self.logger.info("Confidence scores for each feature calculated successfully!")
        except Exception as e:
            self.logger.error("Failed to calculate confidence scores for each feature: {}", str(e))
            raise
        
        # Step 2: Calculate overall confidence scores by aggregating individual feature confidence scores
        try:
            self.logger.debug("Calculating overall confidence ...")
            overall_confidence = calculate_overall_confidence(
                confidence_scores,
                self.config.feature_weights)
            self.logger.info("Overall confidence calculated successfully!")
            return confidence_scores, overall_confidence
        except Exception as e:
            self.logger.error("Failed to calculate overall confidence: {}", str(e))
            raise

    #----------------------------------#
    # PHASE 3: SUGGEST FEATURE WEIGHTS #
    #----------------------------------#
    def _suggest_weights_with_confidence(self, 
                                         good_hist_df: pd.DataFrame,
                                         bad_hist_df: pd.DataFrame) -> Dict[str, float]:

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
            traditional_weights = suggest_weights_standard_based(
                good_hist_df,
                bad_hist_df,
                self.config.targets,
                self.config.scaling)
            self.logger.info("Traditional weights suggested successfully!")
        except Exception as e:
            self.logger.error("Failed to suggest traditional weights: {}", str(e))
            raise
            
        # Calculate confidence scores for each feature based on good and bad performance groups.
        try:
            self.logger.info("Calculating confidence scores for each feature ...")
            confidence_scores = calculate_feature_confidence_scores(
                good_hist_df,
                bad_hist_df,
                self.config.targets,
                self.config.n_bootstrap,
                self.config.confidence_level,
                self.config.min_sample_size,
                self.config.sample_size_threshold)
            self.logger.info("Confidence scores calculated successfully!")
        except Exception as e:
            self.logger.error("Failed to calculate confidence scores for each feature: {}", str(e))
            raise  

        # Display confidence scores for debugging
        logger.debug('Confidence scores using bootstrap sampling: ', )
        logger.debug('\n{}', log_dict_as_table(confidence_scores, transpose = True))

        # Enhance weights using traditional weights and confidence scores
        enhanced_weights = {}
        for feature in list(self.config.targets.keys()):
            traditional_weight = traditional_weights.get(feature, 0)
            # Adjust weight based on confidence
            if feature in confidence_scores and 'warning' not in confidence_scores[feature]:
                # Use separation confidence to adjust weight
                confidence_factor = confidence_scores[feature]['separation_confidence']
                # Enhanced weight = traditional_weight * (1 + confidence_factor * confidence_weight)
                enhanced_weight = traditional_weight * (1 + confidence_factor * self.config.confidence_weight)
            else:
                enhanced_weight = traditional_weight * 0.5  # Reduce weight if not reliable
            enhanced_weights[feature] = enhanced_weight

        # Normalize the weights
        total = sum(enhanced_weights.values())
        if total == 0:
            return {k: 1 / len(list(self.config.targets.keys())) for k in list(self.config.targets.keys())}

        self.logger.info("Enhanced feature weights suggested successfully!")
        
        return {k: v / total for k, v in enhanced_weights.items()}