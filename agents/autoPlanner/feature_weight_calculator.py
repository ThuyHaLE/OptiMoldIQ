import pandas as pd
import numpy as np
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

import os
from typing import Tuple, Literal, Dict, Union, Optional
from pathlib import Path
from loguru import logger

from agents.autoPlanner.report_text_formatter import generate_confidence_report
from agents.decorators import validate_init_dataframes
from agents.utils import save_text_report_with_versioning, load_annotation_path, read_change_log, log_dict_as_table
from agents.core_helpers import check_newest_machine_layout, summarize_mold_machine_history
from agents.autoPlanner.hist_based_item_mold_optimizer import HistBasedItemMoldOptimizer

# Decorator to validate DataFrames are initialized with the correct schema
@validate_init_dataframes(lambda self: {
    "productRecords_df": list(self.databaseSchemas_data['dynamicDB']['productRecords']['dtypes'].keys()),
    "machineInfo_df": list(self.databaseSchemas_data['staticDB']['machineInfo']['dtypes'].keys()),
    "moldSpecificationSummary_df": list(self.databaseSchemas_data['staticDB']['moldSpecificationSummary']['dtypes'].keys()),
    "moldInfo_df": list(self.databaseSchemas_data['staticDB']['moldInfo']['dtypes'].keys()),
    "itemCompositionSummary_df": list(self.databaseSchemas_data['staticDB']['itemCompositionSummary']['dtypes'].keys()),
})

@validate_init_dataframes({"proStatus_df": ['poReceivedDate', 'poNo', 'itemCode', 'itemName', 'poETA',
                                            'itemQuantity', 'itemRemain', 'startedDate', 'actualFinishedDate',
                                            'proStatus', 'etaStatus', 'machineHist', 'itemType', 'moldList',
                                            'moldHist', 'moldCavity', 'totalMoldShot', 'totalDay', 'totalShift',
                                            'plasticResinCode', 'colorMasterbatchCode', 'additiveMasterbatchCode',
                                            'moldShotMap', 'machineQuantityMap', 'dayQuantityMap',
                                            'shiftQuantityMap', 'materialComponentMap', 'lastestRecordTime',
                                            'machineNo', 'moldNo', 'warningNotes'
                                            ]})

class FeatureWeightCalculator:

    """
    This class calculates feature weights used to evaluate manufacturing process performance
    by analyzing production history and computing confidence-based metrics.

    Parameters:
        source_path (str): Path to the annotation data.
        annotation_name (str): File name of the path annotation.
        databaseSchemas_path (str): Path to database schema for validation.
        folder_path (str): Path to folder containing the production status log.
        target_name (str): Filename of the production status log.
        default_dir (str): Base directory for storing reports.
        efficiency (float): Efficiency threshold to classify good/bad records.
        loss (float): Allowable production loss threshold.
        scaling (str): Method to scale feature impacts ('absolute' or 'relative').
        confidence_weight (float): Weight assigned to confidence scores in final weight calculation.
        n_bootstrap (int): Number of bootstrap samples for confidence interval estimation.
        confidence_level (float): Desired confidence level for statistical tests.
        min_sample_size (int): Minimum sample size required for reliable estimation.
        feature_weights (dict): Optional preset weights for features.
        targets (dict): Target metrics and their optimization directions or goals.
    """

    def __init__(self,
                source_path: str = 'agents/shared_db/DataLoaderAgent/newest',
                annotation_name: str = "path_annotations.json",
                databaseSchemas_path: str = 'database/databaseSchemas.json',
                folder_path: str = 'agents/shared_db/OrderProgressTracker',
                target_name: str = "change_log.txt",
                default_dir: str = "agents/shared_db",
                efficiency: float = 0.85,
                loss: float = 0.03,
                scaling: Literal['absolute', 'relative'] = 'absolute',
                confidence_weight: float = 0.3,
                n_bootstrap: int = 500,
                confidence_level: float = 0.95,
                min_sample_size: int = 10,
                feature_weights: Optional[Dict[str, float]] = None,
                targets = {'shiftNGRate': 'minimize',
                           'shiftCavityRate': 1.0,
                           'shiftCycleTimeRate': 1.0,
                           'shiftCapacityRate': 1.0}
                           ):

        self.logger = logger.bind(class_="FeatureWeightCalculator")

        self.efficiency = efficiency
        self.loss = loss
        self.scaling = scaling
        self.confidence_weight = confidence_weight
        self.n_bootstrap = n_bootstrap
        self.confidence_level = confidence_level
        self.min_sample_size = min_sample_size
        self.feature_weights = feature_weights
        self.targets = targets

        # Load database schema configuration for column validation
        self.databaseSchemas_data = load_annotation_path(
            Path(databaseSchemas_path).parent,
            Path(databaseSchemas_path).name
        )
        # Load path annotations that map logical names to actual file paths
        self.path_annotation = load_annotation_path(source_path, annotation_name)

        # Set up output configuration
        self.filename_prefix = "confidence_report"
        self.default_dir = Path(default_dir)
        self.output_dir = self.default_dir / "FeatureWeightCalculator"

        # Load production report
        proStatus_path = read_change_log(folder_path, target_name)
        self.proStatus_df = pd.read_excel(proStatus_path)

        # Rename columns for consistency
        self.proStatus_df.rename(columns={'lastestMachineNo': 'machineNo',
                                          'lastestMoldNo': 'moldNo'
                                          }, inplace=True)

        # Load all required DataFrames from parquet files
        self._load_dataframes()

        self.machine_info_df = check_newest_machine_layout(self.machineInfo_df)

    def calculate(self,
                  mold_stability_index_folder = 'agents/shared_db/HistoryProcessor/mold_stability_index',
                  mold_stability_index_target_name = "change_log.txt"):

        """
        Main method to calculate feature confidence scores and enhanced weights.
        """

        # Load mold stability index
        mold_stability_index_path = read_change_log(mold_stability_index_folder,
                                                    mold_stability_index_target_name)
        
        if mold_stability_index_path is None:
            self.logger.error("Cannot find file {}/{}", mold_stability_index_folder, mold_stability_index_target_name)
            raise FileNotFoundError(f"Cannot find file {mold_stability_index_folder}/{mold_stability_index_target_name}")
            
        mold_stability_index = pd.read_excel(mold_stability_index_path)

        # Suggest the priority for the item-mold pair based on historical records
        _, capacity_mold_info_df = HistBasedItemMoldOptimizer().process_mold_info(mold_stability_index,
                                                                                  self.moldSpecificationSummary_df,
                                                                                  self.moldInfo_df,
                                                                                  self.efficiency,
                                                                                  self.loss)

        # Rename columns for compatibility
        self.productRecords_df.rename(columns={'poNote': 'poNo'}, inplace=True)

        # Separate good and bad production records based on efficiency/loss
        good_hist, bad_hist = FeatureWeightCalculator._group_hist_by_performance(self.proStatus_df,
                                                                                 self.productRecords_df,
                                                                                 self.moldInfo_df,
                                                                                 self.efficiency,
                                                                                 self.loss)

        good_sample, _ = summarize_mold_machine_history(good_hist,
                                                        capacity_mold_info_df)
        logger.debug('Historical information for good sample: {}-{}', good_sample.shape, good_sample.columns)

        bad_sample, _ = summarize_mold_machine_history(bad_hist,
                                                       capacity_mold_info_df)
        logger.debug('Historical information for bad sample: {}-{}', bad_sample.shape, bad_sample.columns)

        # Calculate confidence scores
        confidence_scores = FeatureWeightCalculator._calculate_confidence_scores(good_sample,
                                                                                 bad_sample,
                                                                                 self.targets,
                                                                                 self.n_bootstrap,
                                                                                 self.confidence_level,
                                                                                 self.min_sample_size)

        # Calculate overall confidence
        overall_confidence = FeatureWeightCalculator._calculate_overall_confidence(confidence_scores,
                                                                                   self.feature_weights)

        # Enhanced weights với confidence
        enhanced_weights = FeatureWeightCalculator._suggest_weights_with_confidence(good_sample,
                                                                                    bad_sample,
                                                                                    self.targets,
                                                                                    self.scaling,
                                                                                    self.confidence_weight,
                                                                                    self.n_bootstrap,
                                                                                    self.confidence_level,
                                                                                    self.min_sample_size)
        logger.debug('Enhanced Weights (with confidence): \n{}', log_dict_as_table(enhanced_weights, transpose = False))

        return confidence_scores, overall_confidence, enhanced_weights

    def calculate_and_save_report(self,
                                  mold_stability_index_folder = 'agents/shared_db/HistoryProcessor/mold_stability_index',
                                  mold_stability_index_target_name = "change_log.txt"):

        """
        Wrapper function to calculate weights and save the result as a report.
        """

        # Calculate feature weight
        confidence_scores, overall_confidence, enhanced_weights = self.calculate(mold_stability_index_folder,
                                                                                 mold_stability_index_target_name)

        #Generate confidence report
        report = generate_confidence_report(confidence_scores, overall_confidence)

        logger.info("\n=== ENHANCED MANUFACTURING ANALYSIS FUNCTIONS READY ===")
        logger.info("\n{}", report)

        save_text_report_with_versioning(text = report,
                                         output_dir = self.output_dir,
                                         filename_prefix = self.filename_prefix,
                                         weights = enhanced_weights)

    def _load_dataframes(self) -> None:

        """
        Load all required DataFrames from parquet files with consistent error handling.

        This method loads the following DataFrames:
        - productRecords_df: Production records with item, mold, machine data
        - machineInfo_df: Machine specifications and tonnage information
        - moldSpecificationSummary_df: Mold specifications and compatible items
        - moldInfo_df: Detailed mold information including tonnage requirements
        - itemCompositionSummary_df: Item composition details (resin, masterbatch, etc.)
        """

        # Define the mapping between path annotation keys and DataFrame attribute names
        dataframes_to_load = [
            ('moldSpecificationSummary', 'moldSpecificationSummary_df'),
            ('moldInfo', 'moldInfo_df'),
            ('machineInfo', 'machineInfo_df'),
            ('itemCompositionSummary', 'itemCompositionSummary_df'), #Quantity(KG) for 10000PCS
            ('productRecords', 'productRecords_df'),
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

    @staticmethod
    def _group_hist_by_performance(proStatus_df: pd.DataFrame,
                                   productRecords_df: pd.DataFrame,
                                   moldInfo_df: pd.DataFrame,
                                   efficiency: float = 0.85,
                                   loss: float = 0.03) -> Tuple[pd.DataFrame, pd.DataFrame]:

        """
        Group historical production data into good and bad performance categories.

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

        required_fields = ['poNo', 'recordDate', 'workingShift', 'machineNo', 'machineCode',
                        'itemCode', 'itemName', 'moldNo', 'moldShot', 'moldCavity',
                        'itemTotalQuantity', 'itemGoodQuantity']

        # Validate presence of required fields
        missing_fields = [field for field in required_fields if field not in productRecords_df.columns]
        if missing_fields:
            raise ValueError(f"Missing fields in productRecords_df: {missing_fields}")

        # Filter valid data and select only required fields
        hist = productRecords_df[productRecords_df['itemTotalQuantity'] > 0][required_fields].copy()

        # Group by PO, mold, and machine to aggregate shift and production stats
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

        # Filter out records with missing required mold info
        filtered_df = merged_results[
            merged_results[['moldCavityStandard', 'moldSettingCycle']].notna().all(axis=1)
        ].copy()

        # Calculate theoretical values
        with np.errstate(divide='ignore', invalid='ignore'):
            filtered_df['moldFullTotalShots'] = np.where(
                filtered_df['moldCavityStandard'] > 0,
                (filtered_df['itemQuantity'] / filtered_df['moldCavityStandard']).round().astype('Int64'),
                0
            )

            filtered_df['moldFullTotalSeconds'] = (
                filtered_df['moldFullTotalShots'] * filtered_df['moldSettingCycle']
            ).round().astype('Int64')

            filtered_df['moldFullShiftUsed'] = (
                filtered_df['moldFullTotalSeconds'] / (60 * 60 * 8)
            ).round().astype('Int64')

            # Estimate required shifts considering efficiency and loss
            net_efficiency = efficiency - loss
            filtered_df['moldEstimatedShiftUsed'] = (
                filtered_df['moldFullShiftUsed'] / net_efficiency
            ).apply(lambda x: max(1, int(x)) if x > 0 else 1)

        # Group again by PO for final performance comparison
        final_results = filtered_df.groupby('poNo').agg(
            shiftsUsed=('shiftsUsed', 'mean'),
            moldEstimatedShiftUsed=('moldEstimatedShiftUsed', 'mean'),
        ).reset_index()

        # Label as bad performance if actual shifts > estimated shifts
        final_results['isBad'] = final_results['shiftsUsed'] > final_results['moldEstimatedShiftUsed']

        # Separate good and bad performance histories
        bad_hist_list = final_results[final_results['isBad'] == True]['poNo'].tolist()
        good_hist_list = final_results[final_results['isBad'] == False]['poNo'].tolist()

        bad_hist = productRecords_df[required_fields][
            productRecords_df['poNo'].isin(bad_hist_list)
        ].copy()
        logger.debug('Bad groups information: {}-{}', bad_hist.shape, bad_hist.columns)

        good_hist = productRecords_df[required_fields][
            productRecords_df['poNo'].isin(good_hist_list)
        ].copy()
        logger.debug('Good groups information: {}-{}', good_hist.shape, good_hist.columns)

        return good_hist, bad_hist

    @staticmethod
    def _calculate_confidence_scores(good_hist_df: pd.DataFrame,
                                     bad_hist_df: pd.DataFrame,
                                     targets: Dict[str, Union[float, str]],
                                     n_bootstrap: int = 1000,
                                     confidence_level: float = 0.95,
                                     min_sample_size: int = 10) -> Dict[str, Dict[str, float]]:

        """
        Calculate confidence scores for good/bad groups using bootstrap sampling.

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
                good_sample = np.random.choice(good_data, size=min(len(good_data), 50), replace=True)
                bad_sample = np.random.choice(bad_data, size=min(len(bad_data), 50), replace=True)
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
        Calculate the overall confidence score for the entire classification model.

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

    @staticmethod
    def _suggest_weights_standard_based(good_hist_df: pd.DataFrame,
                                        bad_hist_df: pd.DataFrame,
                                        targets: Dict[str, Union[float, str]],
                                        scaling: Literal['absolute', 'relative'] = 'absolute') -> Dict[str, float]:

        """
        Suggest feature weights based on deviation from standards.

        Args:
            good_hist_df: Good performance data
            bad_hist_df: Bad performance data
            targets: Dict mapping feature names to target values or 'minimize'
            scaling: 'absolute' or 'relative' scaling method

        Returns:
            Dictionary of normalized weights (sum = 1)
        """

        features = list(targets.keys())

        if not features:
            raise ValueError("Features list cannot be empty")

        if scaling not in ['absolute', 'relative']:
            raise ValueError("Scaling must be 'absolute' or 'relative'")

        weights = {}

        for feature in features:
            if feature not in good_hist_df.columns or feature not in bad_hist_df.columns:
                logger.info(f"Warning: Feature '{feature}' not found in data. Setting weight to 0.")
                weights[feature] = 0
                continue

            # Calculate means with handling for empty data
            mean_good = good_hist_df[feature].mean() if len(good_hist_df) > 0 else 0
            mean_bad = bad_hist_df[feature].mean() if len(bad_hist_df) > 0 else 0

            if pd.isna(mean_good):
                mean_good = 0
            if pd.isna(mean_bad):
                mean_bad = 0

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

            weights[feature] = score

        # Normalize weights to sum to 1
        total = sum(weights.values())
        if total == 0:
            # If all scores are 0, assign equal weights
            return {k: 1 / len(weights) for k in weights}

        return {k: v / total for k, v in weights.items()}

    @staticmethod
    def _suggest_weights_with_confidence(good_hist_df: pd.DataFrame,
                                         bad_hist_df: pd.DataFrame,
                                         targets: Dict[str, Union[float, str]],
                                         scaling: Literal['absolute', 'relative'] = 'absolute',
                                         confidence_weight: float = 0.3,
                                         n_bootstrap: int = 1000,
                                         confidence_level: float = 0.95,
                                         min_sample_size: int = 10) -> Dict[str, float]:

        """
        Suggests weights by considering confidence scores.

        Args:
            good_hist_df: Good performance data
            bad_hist_df: Bad performance data
            targets: Target values for each feature
            scaling: 'absolute' or 'relative'
            confidence_weight: The weight of confidence in the final weight calculation

        Returns:
            Dict of weighted scores with confidence consideration
        """

        # Calculate traditional weights
        traditional_weights = FeatureWeightCalculator._suggest_weights_standard_based(good_hist_df,
                                                                                      bad_hist_df,
                                                                                      targets,
                                                                                      scaling)

        # Calculate confidence scores
        confidence_scores = FeatureWeightCalculator._calculate_confidence_scores(good_hist_df,
                                                                                 bad_hist_df,
                                                                                 targets,
                                                                                 n_bootstrap,
                                                                                 confidence_level,
                                                                                 min_sample_size)

        logger.debug('Confidence scores using bootstrap sampling: ', )
        logger.debug('\n{}', log_dict_as_table(confidence_scores, transpose = True))

        # Combine traditional weights with confidence
        enhanced_weights = {}

        for feature in list(targets.keys()):
            traditional_weight = traditional_weights.get(feature, 0)

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

        return {k: v / total for k, v in enhanced_weights.items()}