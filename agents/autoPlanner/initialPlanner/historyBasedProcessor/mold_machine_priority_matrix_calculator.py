import pandas as pd
import os
from pathlib import Path
from loguru import logger
from agents.decorators import validate_init_dataframes

from agents.utils import (load_annotation_path, save_output_with_versioning,
                          read_change_log, rank_nonzero)
from agents.core_helpers import check_newest_machine_layout, summarize_mold_machine_history

# Decorator to validate DataFrames are initialized with the correct schema
# This ensures that required DataFrames have all necessary columns before processing
@validate_init_dataframes(lambda self: {
    "productRecords_df": list(self.databaseSchemas_data['dynamicDB']['productRecords']['dtypes'].keys()),
    "machineInfo_df": list(self.databaseSchemas_data['staticDB']['machineInfo']['dtypes'].keys()),
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

class MoldMachinePriorityMatrixCalculator:

    """
    This class responsible for processing historical production data in order to process:
    1. Generate Mold-Machine Priority Matrix:
    - Use historical production data to assess the performance of each mold-machine pair.
    - Score each pair based on historical weight and actual efficiency.
    - The results are presented in the form of a priority matrix to support optimal production planning.
    """

    # Configuration constants
    ESTIMATED_MOLD_REQUIRED_COLUMNS = ['moldNo', 'moldName', 'acquisitionDate', 'machineTonnage',
                                       'moldCavityStandard', 'moldSettingCycle', 'cavityStabilityIndex',
                                       'cycleStabilityIndex', 'theoreticalMoldHourCapacity',
                                       'effectiveMoldHourCapacity', 'estimatedMoldHourCapacity',
                                       'balancedMoldHourCapacity', 'totalRecords', 'totalCavityMeasurements',
                                       'totalCycleMeasurements', 'firstRecordDate', 'lastRecordDate',
                                       'itemCode', 'itemName', 'itemType', 'moldNum', 'isPriority']

    FEATURE_WEIGHTS_REQUIRED_COLUMNS = ['shiftNGRate', 'shiftCavityRate', 'shiftCycleTimeRate', 'shiftCapacityRate']

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
        Initialize the MoldMachinePriorityMatrixCalculator with configuration paths and parameters.

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
        self.logger = logger.bind(class_="MoldMachinePriorityMatrixCalculator")

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
        self.default_dir = Path(default_dir)  # Base directory for outputs
        self.output_dir = self.default_dir / "MoldMachinePriorityMatrixCalculator"  # Specific output directory
        self.prefix = "priority_matrix"
        
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

    # ----------------------------------------------#
    # MOLD MACHINE PRIORITY MATRIX CALCULATING PHASE
    # ----------------------------------------------#

    # Calculate the priority matrix for mold-machine assignments based on historical data
    # and will be used to suggest a list of machines (in priority order) for each mold in the subsequent planning steps
    def process(self,
                mold_machine_feature_weights,
                capacity_mold_info_df):

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

        # Valid inputs
        if not self._check_series_columns(mold_machine_feature_weights) and self._check_mold_dataframe_columns(capacity_mold_info_df):
            self.logger.error(f"Error: Invalid input!!!")

        # Prepare historical data for analysis
        historical_data = self._prepare_mold_machine_historical_data(self.machineInfo_df, 
                                                                     self.proStatus_df, 
                                                                     self.productRecords_df)

        # Calculate performance metrics
        performance_results = MoldMachinePriorityMatrixCalculator._calculate_mold_machine_performance_metrics(capacity_mold_info_df, 
                                                                                           historical_data)

        # Apply weighted scoring and create priority matrix
        priority_matrix = MoldMachinePriorityMatrixCalculator._create_mold_machine_priority_matrix(performance_results, 
                                                                                mold_machine_feature_weights)

        return priority_matrix

    # Calculate the priority matrix for mold-machine assignments based on historical data
    # optionally save the result as a report
    def process_and_save_result(self,
                                 mold_machine_feature_weights,
                                 capacity_mold_info_df):

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
        priority_matrix = self.calculate_mold_machine_priority_matrix(mold_machine_feature_weights,
                                                                      capacity_mold_info_df)

        # Prepare data for export by resetting index to include moldNo as a regular column
        # This makes the Excel output more readable and easier to work with
        self.data = {"priorityMatrix": priority_matrix.reset_index()}

        # Export to Excel file with automatic versioning
        # The versioning system prevents accidental overwrites of previous results
        logger.info("Start excel file exporting...")
        save_output_with_versioning(
            self.data,          # Dictionary containing the data to save
            self.output_dir/"priority_matrix",    # Directory where the file will be saved
            self.prefix, # Prefix for the output filename
        )
    
    def _check_mold_dataframe_columns(self, df: pd.DataFrame) -> bool:

        if not isinstance(df, pd.DataFrame):
            self.logger.error("Error: Input is not a DataFrame, got {}", type(df))
            return False

        missing_columns = [col for col in df.columns if col not in self.ESTIMATED_MOLD_REQUIRED_COLUMNS]

        if missing_columns:
            self.logger.error("Missing columns: {}", missing_columns)
            return False

        self.logger.info("✅ All required columns are present!")
        return True

    def _check_series_columns(self, series: pd.Series) -> bool:

        if not isinstance(series, pd.Series):
            self.logger.error("Error: Input is not a Series, got {}", type(series))
            return False

        missing_columns = [col for col in series.to_dict().keys() if col not in self.FEATURE_WEIGHTS_REQUIRED_COLUMNS]

        if missing_columns:
            self.logger.error("Missing columns: {}", missing_columns)
            return False

        self.logger.info("✅ All required columns are present!")
        return True
    
    # Static methods for mold machine priority matrix calculating phase

    @staticmethod
    def _prepare_mold_machine_historical_data(machineInfo_df, proStatus_df, productRecords_df):

        """Prepare and filter historical data for analysis."""

        machine_info_df = check_newest_machine_layout(machineInfo_df)

        # Filter to completed orders and merge with machine info
        hist = proStatus_df.loc[proStatus_df['itemRemain']==0].merge(
            machine_info_df[['machineNo', 'machineCode', 'machineName', 'machineTonnage']],
            how='left', on=['machineNo'])

        # Prepare product records
        productRecords_df.rename(columns={'poNote': 'poNo'}, inplace=True)

        df = productRecords_df[['recordDate', 'workingShift',
                                'machineNo', 'machineCode',
                                'itemCode','itemName',
                                'poNo', 'moldNo', 'moldShot', 'moldCavity',
                                'itemTotalQuantity', 'itemGoodQuantity']]

        # Filter to meaningful production data
        filtered_df = df[df['poNo'].isin(hist['poNo']) & (df['itemTotalQuantity'] > 0)]

        return filtered_df
    
    @staticmethod
    def _calculate_mold_machine_performance_metrics(capacity_mold_info_df,
                                                    historical_data):

        """Calculate performance metrics for mold-machine combinations."""

        performance_results, _ = summarize_mold_machine_history(historical_data, capacity_mold_info_df)

        return performance_results

    @staticmethod
    def _create_mold_machine_priority_matrix(results, weights):

        """Apply weights and create the final priority matrix."""

        # Apply weighted scoring
        results["total_score"] = (results[list(weights.index)] * weights.values).sum(axis=1)

        # Create pivot table
        weighted_results = results[['moldNo', 'machineCode', 'total_score']].pivot(
            index="moldNo", columns="machineCode", values="total_score").fillna(0)

        # Convert to priority rankings
        priority_matrix = weighted_results.apply(rank_nonzero, axis=1)

        return priority_matrix