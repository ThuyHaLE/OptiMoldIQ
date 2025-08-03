import pandas as pd
import numpy as np
import os
from pathlib import Path
from loguru import logger
from agents.decorators import validate_init_dataframes

from agents.utils import (load_annotation_path, save_output_with_versioning,
                          read_change_log, rank_nonzero, get_latest_change_row)
from agents.core_helpers import check_newest_machine_layout, summarize_mold_machine_history
from agents.autoPlanner.hist_based_item_mold_optimizer import HistBasedItemMoldOptimizer

# Decorator to validate DataFrames are initialized with the correct schema
# This ensures that required DataFrames have all necessary columns before processing
@validate_init_dataframes(lambda self: {
    "productRecords_df": list(self.databaseSchemas_data['dynamicDB']['productRecords']['dtypes'].keys()),
    "machineInfo_df": list(self.databaseSchemas_data['staticDB']['machineInfo']['dtypes'].keys()),
    "moldSpecificationSummary_df": list(self.databaseSchemas_data['staticDB']['moldSpecificationSummary']['dtypes'].keys()),
    "moldInfo_df": list(self.databaseSchemas_data['staticDB']['moldInfo']['dtypes'].keys()),
})

# Additional validation decorator for production status DataFrame with explicit column list
@validate_init_dataframes({"proStatus_df": [
    'poReceivedDate', 'poNo', 'itemCode', 'itemName', 'poETA',
    'itemQuantity', 'itemRemain', 'startedDate', 'actualFinishedDate',
    'proStatus', 'etaStatus', 'machineHist', 'itemType', 'moldList',
    'moldHist', 'moldCavity', 'totalMoldShot', 'totalDay', 'totalShift',
    'plasticResinCode', 'colorMasterbatchCode', 'additiveMasterbatchCode',
    'moldShotMap', 'machineQuantityMap', 'dayQuantityMap',
    'shiftQuantityMap', 'materialComponentMap', 'lastestRecordTime',
    'machineNo', 'moldNo', 'warningNotes']})

class HistoryProcessor:

    """
    A class for processing historical production data and calculating priority matrices.

    This processor analyzes production history to create priority matrices that help
    optimize mold-machine assignments based on historical performance and weights.

    The class loads production records, machine information, mold specifications,
    and generates prioritized recommendations for production planning.
    """

    # Configuration constants

    SECONDS_PER_HOUR = 3600
    CYCLE_TIME_TOLERANCE = 0.2
    EXTREME_DEVIATION_THRESHOLD = 1.0

    CYCLE_STABILITY_WEIGHTS = {'accuracy_score_weight': 0.3,
                               'consistency_score_weight': 0.25,
                               'range_compliance_weight': 0.25,
                               'outlier_penalty_weight': 0.1,
                               'data_completeness_weight': 0.1}

    CAVITY_STABILITY_WEIGHTS = {'accuracy_rate_weight': 0.4,
                                'consistency_score_weight': 0.3,
                                'utilization_rate_weight': 0.2,
                                'data_completeness_weight': 0.1}

    def __init__(self,
                 source_path: str = 'agents/shared_db/DataLoaderAgent/newest',
                 annotation_name: str = "path_annotations.json",
                 databaseSchemas_path: str = 'database/databaseSchemas.json',
                 folder_path: str = 'agents/shared_db/OrderProgressTracker',
                 target_name: str = "change_log.txt",
                 default_dir: str = "agents/shared_db",
                 efficiency: float = 0.85,
                 loss: float = 0.03,
                 ):

        """
        Initialize the HistoryProcessor with configuration paths and parameters.

        Args:
            source_path (str): Path to the data source directory containing parquet files
            annotation_name (str): Name of the JSON file containing path annotations
            databaseSchemas_path (str): Path to database schema configuration file
            folder_path (str): Path to folder containing change log for production status
            target_name (str): Name of the change log file to read production status from
            weights_hist_path (str): Path to Excel file containing feature weights history
            default_dir (str): Default directory for output files
        """

        # Initialize logger with class context for better debugging
        self.logger = logger.bind(class_="HistoryProcessor")

        # Load database schema configuration for column validation
        # This ensures all DataFrames have the expected structure
        self.databaseSchemas_data = load_annotation_path(
            Path(databaseSchemas_path).parent,
            Path(databaseSchemas_path).name
        )

        self.efficiency = efficiency
        self.loss = loss

        # Load path annotations that map logical names to actual file paths
        # This allows flexible configuration of data source locations
        self.path_annotation = load_annotation_path(source_path, annotation_name)

        # Set up output configuration for saving results
        self.filename_prefix = "priority_matrix"  # Prefix for output files
        self.default_dir = Path(default_dir)  # Base directory for outputs
        self.output_dir = self.default_dir / "HistoryProcessor"  # Specific output directory

        # Load production status report from the latest change log entry
        # This contains current production orders and their status
        proStatus_path = read_change_log(folder_path, target_name)
        self.proStatus_df = pd.read_excel(proStatus_path)

        # Rename columns for consistency across the system
        # Standardize column names to match expected schema
        self.proStatus_df.rename(columns={'lastestMachineNo': 'machineNo',
                                          'lastestMoldNo': 'moldNo'
                                          }, inplace=True)

        # Load all required DataFrames from parquet files
        self._load_dataframes()

    def _load_dataframes(self) -> None:

        """
        Load all required DataFrames from parquet files with consistent error handling.

        This method loads the following DataFrames:
        - productRecords_df: Historical production records with item, mold, machine data
        - machineInfo_df: Machine specifications including tonnage and capabilities
        - moldSpecificationSummary_df: Mold specifications and compatible item mappings
        - moldInfo_df: Detailed mold information including tonnage requirements

        Raises:
            FileNotFoundError: If any required data file is missing
            Exception: If there are issues reading the parquet files
        """

        # Define the mapping between path annotation keys and DataFrame attribute names
        # This creates a clean separation between logical names and actual attributes
        dataframes_to_load = [
            ('productRecords', 'productRecords_df'),      # Historical production data
            ('machineInfo', 'machineInfo_df'),            # Machine specifications
            ('moldSpecificationSummary', 'moldSpecificationSummary_df'),  # Mold-item compatibility
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

    def _load_mold_machine_feature_weights(self, weights_hist_path):

        """Load and validate feature weights from the latest calculation."""

        if not weights_hist_path.exists():
            logger.error("File not found: {}. Please calculate feature weight first!",
                        self.weights_hist_path)
            raise FileNotFoundError(f"File not found: {weights_hist_path}")

        return get_latest_change_row(weights_hist_path)

    def _prepare_mold_machine_historical_data(self):

        """Prepare and filter historical data for analysis."""

        machine_info_df = check_newest_machine_layout(self.machineInfo_df)

        # Filter to completed orders and merge with machine info
        hist = self.proStatus_df.loc[self.proStatus_df['itemRemain']==0].merge(
            machine_info_df[['machineNo', 'machineCode', 'machineName', 'machineTonnage']],
            how='left', on=['machineNo'])

        # Prepare product records
        self.productRecords_df.rename(columns={'poNote': 'poNo'}, inplace=True)

        df = self.productRecords_df[['recordDate', 'workingShift',
                                    'machineNo', 'machineCode',
                                    'itemCode','itemName',
                                    'poNo', 'moldNo', 'moldShot', 'moldCavity',
                                    'itemTotalQuantity', 'itemGoodQuantity']]

        # Filter to meaningful production data
        filtered_df = df[df['poNo'].isin(hist['poNo']) & (df['itemTotalQuantity'] > 0)]

        return filtered_df

    def _calculate_mold_machine_performance_metrics(self,
                                                    mold_stability_index_folder,
                                                    mold_stability_index_target_name,
                                                    historical_data):

        """Calculate performance metrics for mold-machine combinations."""

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

        performance_results, _ = summarize_mold_machine_history(historical_data, capacity_mold_info_df)

        return performance_results

    def _create_mold_machine_priority_matrix(self, results, weights):

        """Apply weights and create the final priority matrix."""

        # Apply weighted scoring
        results["total_score"] = (results[list(weights.index)] * weights.values).sum(axis=1)

        # Create pivot table
        weighted_results = results[['moldNo', 'machineCode', 'total_score']].pivot(
            index="moldNo", columns="machineCode", values="total_score").fillna(0)

        # Convert to priority rankings
        priority_matrix = weighted_results.apply(rank_nonzero, axis=1)

        return priority_matrix

    def calculate_mold_machine_priority_matrix(self,
                                               weights_hist_path: str = 'agents/shared_db/FeatureWeightCalculator/weights_hist.xlsx',
                                               mold_stability_index_folder = 'agents/shared_db/HistoryProcessor/mold_stability_index',
                                               mold_stability_index_target_name = "change_log.txt"):

        """
        Calculate the priority matrix for mold-machine assignments based on historical data.

        This method:
        1. Loads feature weights from the latest weight calculation
        2. Processes historical production data for completed orders
        3. Calculates performance metrics for each mold-machine combination
        4. Applies weighted scoring based on multiple factors
        5. Ranks combinations to create a priority matrix

        Returns:
            pandas.DataFrame: Priority matrix with molds as rows, machines as columns,
                            and priority rankings as values (1 = highest priority)

        Raises:
            FileNotFoundError: If weights history file is missing
        """

        # Load weights and validate prerequisites
        weights = self._load_mold_machine_feature_weights(Path(weights_hist_path))

        # Prepare historical data for analysis
        historical_data = self._prepare_mold_machine_historical_data()

        # Calculate performance metrics
        performance_results = self._calculate_mold_machine_performance_metrics(mold_stability_index_folder,
                                                                               mold_stability_index_target_name,
                                                                               historical_data)

        # Apply weighted scoring and create priority matrix
        priority_matrix = self._create_mold_machine_priority_matrix(performance_results, weights)

        return priority_matrix

    def calculate_and_save_mold_machine_priority_matrix(self,
                                                        weights_hist_path: str = 'agents/shared_db/FeatureWeightCalculator/weights_hist.xlsx',
                                                        mold_stability_index_folder = 'agents/shared_db/HistoryProcessor/mold_stability_index',
                                                        mold_stability_index_target_name = "change_log.txt"):

        """
        Calculate the priority matrix and save it to an Excel file with versioning.

        This method combines calculation and output functionality:
        1. Calculates the priority matrix using historical data and weights
        2. Formats the data for export
        3. Saves to Excel file with automatic versioning

        The output file will be saved in the configured output directory with
        a timestamp-based version number to prevent overwrites.
        """

        # Calculate the priority matrix using the main calculation method
        priority_matrix = self.calculate_mold_machine_priority_matrix(weights_hist_path,
                                                                      mold_stability_index_folder,
                                                                      mold_stability_index_target_name)

        # Prepare data for export by resetting index to include moldNo as a regular column
        # This makes the Excel output more readable and easier to work with
        self.data = {"priorityMatrix": priority_matrix.reset_index()}

        # Export to Excel file with automatic versioning
        # The versioning system prevents accidental overwrites of previous results
        logger.info("Start excel file exporting...")
        save_output_with_versioning(
            self.data,          # Dictionary containing the data to save
            self.output_dir/"priority_matrix",    # Directory where the file will be saved
            self.filename_prefix, # Prefix for the output filename
        )

    def calculate_mold_stability_index(self,
                                       cavity_stability_threshold = 0.6,
                                       cycle_stability_threshold = 0.4,
                                       total_records_threshold = 30) -> pd.DataFrame:

            """
            Calculates cavity and cycle stability indices for molds based on historical production data.

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

            def df_processing(productRecords_df, moldInfo_df):
                filter_df = productRecords_df[productRecords_df['moldShot'] > 0]
                filter_df['moldCycle'] = round((28800 / filter_df['moldShot']), 2)

                df = filter_df.groupby(['moldNo', 'recordDate'])[['moldCavity', 'moldCycle']].agg(list).reset_index()
                df['moldCavity'] = df['moldCavity'].apply(lambda lst: [int(x) for x in lst])
                df['moldCycle'] = df['moldCycle'].apply(lambda lst: [float(x) for x in lst])

                field_list = ['moldNo', 'moldName', 'recordDate',
                              'moldCavity', 'moldCavityStandard', 'moldCycle', 'moldSettingCycle',
                              'acquisitionDate', 'machineTonnage']

                merged_df = df.merge(moldInfo_df[['moldNo', 'moldName',
                                                  'moldCavityStandard', 'moldSettingCycle',
                                                  'acquisitionDate', 'machineTonnage']], how='left', on='moldNo')

                return merged_df[field_list]

            def calculate_cavity_stability(cavity_values, standard_cavity, total_records):
                """Calculate cavity stability index."""

                if standard_cavity == 0:
                    print("Invalid Mold Standard Cavity")
                    return 0.0

                # 1. Accuracy rate (how many values match the standard)
                correct_count = sum(1 for val in cavity_values if val == standard_cavity)
                accuracy_rate = correct_count / len(cavity_values) if cavity_values else 0

                # 2. Consistency: variation of cavity values
                if len(set(cavity_values)) == 1:
                    consistency_score = 1.0  # Perfectly consistent
                else:
                    cv = np.std(cavity_values) / np.mean(cavity_values) if np.mean(cavity_values) > 0 else 1
                    consistency_score = max(0, 1 - cv)

                # 3. Utilization rate: actual average cavity vs standard
                avg_active_cavity = np.mean(cavity_values) if cavity_values else 0
                utilization_rate = min(1.0, avg_active_cavity / standard_cavity) if standard_cavity > 0 else 0

                # 4. Penalty for low data volume
                data_completeness = min(1.0, total_records / total_records_threshold)

                # Final weighted score
                stability_score = (
                    accuracy_rate * HistoryProcessor.CAVITY_STABILITY_WEIGHTS['accuracy_rate_weight'] +           # 40% - Accuracy
                    consistency_score * HistoryProcessor.CAVITY_STABILITY_WEIGHTS['consistency_score_weight'] +   # 30% - Consistency
                    utilization_rate * HistoryProcessor.CAVITY_STABILITY_WEIGHTS['utilization_rate_weight'] +     # 20% - Utilization
                    data_completeness * HistoryProcessor.CAVITY_STABILITY_WEIGHTS['data_completeness_weight']     # 10% - Data completeness
                )

                return min(1.0, max(0.0, stability_score))

            def calculate_cycle_stability(cycle_values, standard_cycle, total_records):
                """Calculate cycle time stability index."""

                if standard_cycle == 0:
                    print("Invalid Mold Standard Cycle Time")
                    return 0.000001

                # 1. Deviation from standard
                deviations = [abs(val - standard_cycle) / standard_cycle for val in cycle_values]
                avg_deviation = np.mean(deviations) if deviations else HistoryProcessor.EXTREME_DEVIATION_THRESHOLD
                accuracy_score = max(0, 1 - avg_deviation)

                # 2. Consistency: variation of cycle time
                cv = np.std(cycle_values) / np.mean(cycle_values) if np.mean(cycle_values) > 0 else 1
                consistency_score = max(0, 1 - cv)

                # 3. Compliance within ±20% range
                in_range_count = sum(1 for val in cycle_values
                                    if abs(val - standard_cycle) / standard_cycle <= HistoryProcessor.CYCLE_TIME_TOLERANCE)
                range_compliance = in_range_count / len(cycle_values) if cycle_values else 0

                # 4. Penalty for extreme outliers (deviation > 100%)
                extreme_outliers = sum(1 for val in cycle_values
                                    if abs(val - standard_cycle) / standard_cycle > 1.0)
                outlier_penalty = max(0, 1 - (extreme_outliers / len(cycle_values))) if cycle_values else 0

                # 5. Data completeness penalty
                data_completeness = min(1.0, total_records / total_records_threshold)

                # Final weighted score
                stability_score = (
                    accuracy_score * HistoryProcessor.CYCLE_STABILITY_WEIGHTS['accuracy_score_weight'] +         # 30% - Accuracy
                    consistency_score * HistoryProcessor.CYCLE_STABILITY_WEIGHTS['consistency_score_weight'] +   # 25% - Consistency
                    range_compliance * HistoryProcessor.CYCLE_STABILITY_WEIGHTS['range_compliance_weight'] +     # 25% - Range compliance
                    outlier_penalty * HistoryProcessor.CYCLE_STABILITY_WEIGHTS['outlier_penalty_weight'] +       # 10% - Outlier penalty
                    data_completeness * HistoryProcessor.CYCLE_STABILITY_WEIGHTS['data_completeness_weight']     # 10% - Data completeness
                )

                return min(1.0, max(0.0, stability_score))

            # Stability calculation results
            stability_results = []

            # Iterate through each mold
            df = df_processing(self.productRecords_df, self.moldInfo_df)
            for mold_no in df['moldNo'].unique():

                mold_data = df[df['moldNo'] == mold_no].copy()

                moldName = mold_data['moldName'].unique()[0]
                acquisitionDate = mold_data['acquisitionDate'].unique()[0]
                machineTonnage = mold_data['machineTonnage'].unique()[0]

                mold_data = mold_data.sort_values('recordDate')

                total_records = len(mold_data)

                # Gather all cavity and cycle values
                all_cavity_values = []
                all_cycle_values = []
                standard_cavity = mold_data['moldCavityStandard'].fillna(0).iloc[0]
                standard_cycle = mold_data['moldSettingCycle'].fillna(0).iloc[0]

                for idx, row in mold_data.iterrows():
                    all_cavity_values.extend(row['moldCavity'])
                    all_cycle_values.extend(row['moldCycle'])

                # Calculate stability scores
                cavity_stability = calculate_cavity_stability(
                    all_cavity_values, standard_cavity, total_records
                )
                cycle_stability = calculate_cycle_stability(
                    all_cycle_values, standard_cycle, total_records
                )

                theoretical_hour_capacity = HistoryProcessor.SECONDS_PER_HOUR / standard_cycle * standard_cavity

                # Weighted stability
                overall_stability = (cavity_stability * cavity_stability_threshold) + (cycle_stability * cycle_stability_threshold)

                effective_hour_capacity = theoretical_hour_capacity * overall_stability
                estimated_hour_capacity = theoretical_hour_capacity * (self.efficiency - self.loss)

                # Trust coefficient from historical data
                alpha = max(0.1, min(1.0, total_records / total_records_threshold))

                balanced_hour_capacity = alpha * effective_hour_capacity + (1 - alpha) * estimated_hour_capacity

                # Append to result list
                stability_results.append({
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
                })

            # Return result as DataFrame
            result_df = pd.DataFrame(stability_results)

            return result_df

    def calculate_and_save_mold_stability_index(self,
                                                cavity_stability_threshold = 0.6,
                                                cycle_stability_threshold = 0.4,
                                                total_records_threshold = 30):

        """
        Calculate the mold stability index and save it to an Excel file with versioning.

        This method combines calculation and output functionality:
        1. Calculates the priority matrix using historical data and weights
        2. Formats the data for export
        3. Saves to Excel file with automatic versioning

        The output file will be saved in the configured output directory with
        a timestamp-based version number to prevent overwrites.
        """

        # Calculate the priority matrix using the main calculation method
        mold_stability_index = self.calculate_mold_stability_index(cavity_stability_threshold,
                                                                   cycle_stability_threshold,
                                                                   total_records_threshold)

        # Prepare data for export by resetting index to include moldNo as a regular column
        # This makes the Excel output more readable and easier to work with
        self.data = {"moldStabilityIndex": mold_stability_index}

        # Export to Excel file with automatic versioning
        # The versioning system prevents accidental overwrites of previous results
        logger.info("Start excel file exporting...")
        save_output_with_versioning(
            self.data,          # Dictionary containing the data to save
            self.output_dir/"mold_stability_index",    # Directory where the file will be saved
            self.filename_prefix, # Prefix for the output filename
        )