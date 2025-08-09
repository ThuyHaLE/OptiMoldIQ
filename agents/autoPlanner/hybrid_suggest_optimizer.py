import os
import pandas as pd
from pathlib import Path
from agents.decorators import validate_init_dataframes
from agents.utils import (load_annotation_path, save_output_with_versioning,
                          read_change_log, get_latest_change_row)
from loguru import logger
from agents.autoPlanner.hist_based_item_mold_optimizer import HistBasedItemMoldOptimizer
from agents.autoPlanner.initialPlanner.history_processor import HistoryProcessor

# Decorator to validate DataFrames are initialized with the correct schema
# This ensures that required DataFrames have all necessary columns before processing
@validate_init_dataframes(lambda self: {
    "moldSpecificationSummary_df": list(self.databaseSchemas_data['staticDB']['moldSpecificationSummary']['dtypes'].keys()),
    "moldInfo_df": list(self.databaseSchemas_data['staticDB']['moldInfo']['dtypes'].keys()),
})


class HybridSuggestOptimizer():
    """
    A hybrid optimization system that combines historical data analysis with mold-machine
    compatibility matching to suggest optimal production configurations.

    This class integrates multiple optimization strategies:
    1. Historical-based mold capacity estimation
    2. Mold stability index analysis
    3. Feature weight calculation for mold-machine priority matrix
    4. Production efficiency optimization

    The optimizer helps manufacturing systems make data-driven decisions about
    mold selection, machine allocation, and production planning.
    """

    # Default weights (in case not enough insights from historical databases can be extracted) for different performance metrics used in optimization
    # These weights determine the relative importance of each factor in decision making
    INITIAL_FEATURE_WEIGHTS = {
        'shiftNGRate_weight': 0.1,      # Weight for defect rate (10%)
        'shiftCavityRate_weight': 0.25,  # Weight for cavity utilization (25%)
        'shiftCycleTimeRate_weight': 0.25, # Weight for cycle time efficiency (25%)
        'shiftCapacityRate_weight': 0.4   # Weight for overall capacity (40% - highest priority)
    }

    # Required columns for mold capacity estimation output
    # These columns contain essential mold performance and capacity metrics
    ESTIMATED_MOLD_REQUIRED_COLUMNS = [
        'moldNo',
        'moldName',
        'acquisitionDate',
        'machineTonnage',
        'moldCavityStandard',
        'moldSettingCycle',
        'cavityStabilityIndex',
        'cycleStabilityIndex',
        'theoreticalMoldHourCapacity',
        'effectiveMoldHourCapacity',
        'estimatedMoldHourCapacity',
        'balancedMoldHourCapacity',
        'totalRecords',
        'totalCavityMeasurements',
        'totalCycleMeasurements',
        'firstRecordDate',
        'lastRecordDate'
    ]

    # Required columns for feature weight calculations
    # These represent key performance indicators for mold-machine combinations
    FEATURE_WEIGHTS_REQUIRED_COLUMNS = [
        'shiftNGRate',        # Rate of defective products per shift
        'shiftCavityRate',    # Cavity utilization rate per shift
        'shiftCycleTimeRate', # Cycle time performance rate per shift
        'shiftCapacityRate'   # Overall production capacity rate per shift
    ]

    def __init__(self,
                 source_path: str = 'agents/shared_db/DataLoaderAgent/newest',
                 annotation_name: str = "path_annotations.json",
                 databaseSchemas_path: str = 'database/databaseSchemas.json',
                 default_dir: str = "agents/shared_db",
                 folder_path = "agents/OrderProgressTracker",
                 target_name = "change_log.txt",
                 mold_stability_index_folder = "agents/HistoryProcessor/mold_stability_index",
                 mold_stability_index_target_name = "change_log.txt",
                 mold_machine_weights_hist_path = "agents/FeatureWeightCalculator/weights_hist.xlsx",
                 efficiency: float = 0.85,
                 loss: float = 0.03,
                 ):
        """
        Initialize the HybridSuggestOptimizer with configuration paths and parameters.

        Args:
            source_path (str): Base path for data source files
            annotation_name (str): JSON file containing path mappings
            databaseSchemas_path (str): Path to database schema definitions
            default_dir (str): Default directory for shared database files
            folder_path (str): Path for order progress tracking files
            target_name (str): Name of the change log file
            mold_stability_index_folder (str): Folder containing mold stability indices
            mold_stability_index_target_name (str): Target file name for stability index
            mold_machine_weights_hist_path (str): Path to historical feature weights
            efficiency (float): Expected production efficiency (default 0.85 = 85%)
            loss (float): Expected production loss rate (default 0.03 = 3%)
        """

        # Initialize logger with class context for better debugging and monitoring
        self.logger = logger.bind(class_="HybridSuggestOptimizer")

        # Load database schema configuration for column validation
        # This ensures all DataFrames have the expected structure and data types
        self.databaseSchemas_data = load_annotation_path(
            Path(databaseSchemas_path).parent,
            Path(databaseSchemas_path).name
        )

        # Store production parameters for capacity calculations
        self.efficiency = efficiency  # Overall equipment effectiveness (OEE)
        self.loss = loss             # Expected material/time loss factor

        # Load path annotations that map logical names to actual file paths
        # This allows flexible configuration of data source locations without hardcoding paths
        self.path_annotation = load_annotation_path(source_path, annotation_name)

        # Configure paths for mold stability index data
        # Stability indices help assess mold reliability and performance consistency
        self.mold_stability_index_folder = mold_stability_index_folder
        self.mold_stability_index_target_name = mold_stability_index_target_name

        # Configure path for historical feature weights
        # These weights are learned from past performance data to optimize future decisions
        self.mold_machine_weights_hist_path = Path(mold_machine_weights_hist_path)

        # Load all required DataFrames from parquet files
        # This includes mold specifications, machine info, and historical records
        self._load_dataframes()

        # Initialize HistoryProcessor for analyzing historical production data
        # This component processes past performance to inform future optimization decisions
        self.history_processor = HistoryProcessor(source_path, annotation_name,
                                                  databaseSchemas_path, folder_path, target_name,
                                                  default_dir, self.efficiency, self.loss)

    def _load_dataframes(self) -> None:
        """
        Load all required DataFrames from parquet files with comprehensive error handling.

        This method loads the core data structures needed for optimization:
        - moldSpecificationSummary_df: Mold specifications and compatible item mappings
        - moldInfo_df: Detailed mold information including tonnage requirements and capabilities

        The method uses parquet format for efficient data storage and fast loading.
        All loading operations include error handling and logging for debugging.

        Raises:
            FileNotFoundError: If any required data file is missing
            Exception: If there are issues reading the parquet files (corrupt data, permissions, etc.)
        """

        # Define the mapping between path annotation keys and DataFrame attribute names
        # This creates a clean separation between logical names in config and actual attributes
        dataframes_to_load = [
            ('moldSpecificationSummary', 'moldSpecificationSummary_df'),  # Mold-item compatibility data
            ('moldInfo', 'moldInfo_df'),                                  # Detailed mold specifications
        ]

        # Load each DataFrame with comprehensive error handling and validation
        for path_key, attr_name in dataframes_to_load:
            # Retrieve the actual file path from path annotations configuration
            path = self.path_annotation.get(path_key)

            # Validate that the path exists and is accessible before attempting to read
            if not path or not os.path.exists(path):
                self.logger.error("Path to '{}' not found or does not exist: {}", path_key, path)
                raise FileNotFoundError(f"Path to '{path_key}' not found or does not exist: {path}")

            try:
                # Load DataFrame from parquet file
                # Parquet format provides efficient columnar storage, compression, and fast queries
                df = pd.read_parquet(path)

                # Dynamically set the DataFrame as an instance attribute
                # This allows flexible addition of new data sources without code changes
                setattr(self, attr_name, df)

                # Log successful loading with shape and column information for debugging
                # This helps verify data integrity and track data changes over time
                self.logger.debug("{}: {} - {}", path_key, df.shape, list(df.columns))

            except Exception as e:
                # Log detailed error information and re-raise for proper error handling
                # This ensures errors are visible in logs while allowing upstream handling
                self.logger.error("Failed to load {}: {}", path_key, str(e))
                raise

    def _load_mold_stability_index(self):
        """
        Load mold stability index data from the most recent file or create initial structure.

        The mold stability index contains metrics about how consistently each mold performs,
        including cavity stability, cycle time consistency, and overall reliability measures.
        This data is crucial for making informed decisions about mold selection.

        Returns:
            pd.DataFrame: Mold stability index with performance consistency metrics
        """
        # Attempt to find the latest mold stability index file from change log
        mold_stability_index_path = read_change_log(self.mold_stability_index_folder,
                                                   self.mold_stability_index_target_name)

        # Handle case where no historical stability index exists
        if mold_stability_index_path is None:
            self.logger.warning("Cannot find file {}/{}",
                              self.mold_stability_index_folder,
                              self.mold_stability_index_target_name)
            self.logger.info("Start loading initial mold stability index...")

            def initial_mold_stability_index():
                """Create an empty DataFrame with the required column structure."""
                return pd.DataFrame(columns=self.ESTIMATED_MOLD_REQUIRED_COLUMNS)

            # Create empty structure for first-time initialization
            mold_stability_index = initial_mold_stability_index()
        else:
            # Load existing stability index from Excel file
            self.logger.info("Start loading mold stability index...")
            mold_stability_index = pd.read_excel(mold_stability_index_path)

        self.logger.info("Loaded mold stability index")
        return mold_stability_index

    def _load_feature_weights(self):
        """
        Load the latest feature weights for calculating mold-machine priority matrix.

        Feature weights determine the relative importance of different performance metrics
        when evaluating mold-machine combinations. These weights are typically learned
        from historical performance data and updated over time.

        Returns:
            pd.Series: Feature weights for different performance metrics
        """
        # Check if historical feature weights file exists
        if not self.mold_machine_weights_hist_path.exists():
            self.logger.warning("File not found: {}. Please calculate feature weight first!",
                              self.mold_machine_weights_hist_path)

            def initial_feature_weights():
                """
                Create initial feature weights using predefined default values.
                These weights represent a balanced starting point for optimization.
                """
                # Initialize series with zeros for all required columns
                feature_weights = pd.Series(0, index=self.FEATURE_WEIGHTS_REQUIRED_COLUMNS, dtype=object)

                # Set initial weights based on manufacturing best practices
                feature_weights['shiftNGRate'] = self.INITIAL_FEATURE_WEIGHTS['shiftNGRate_weight']
                feature_weights['shiftCavityRate'] = self.INITIAL_FEATURE_WEIGHTS['shiftCavityRate_weight']
                feature_weights['shiftCycleTimeRate'] = self.INITIAL_FEATURE_WEIGHTS['shiftCycleTimeRate_weight']
                feature_weights['shiftCapacityRate'] = self.INITIAL_FEATURE_WEIGHTS['shiftCapacityRate_weight']

                return feature_weights

            self.logger.info("Start loading initial feature weight...")
            mold_machine_feature_weights = initial_feature_weights()
        else:
            # Load the most recent feature weights from historical data
            self.logger.info("Start loading mold machine feature weight...")
            mold_machine_feature_weights = get_latest_change_row(self.mold_machine_weights_hist_path)

        # Log the loaded weights for debugging and verification
        self.logger.info("Loaded mold machine feature weight. {}", mold_machine_feature_weights.to_dict())
        return mold_machine_feature_weights

    def process(self):
        """
        Execute the complete hybrid optimization process.

        This method orchestrates the entire optimization workflow:
        1. Load mold stability index data
        2. Estimate mold capacities using historical data
        3. Load feature weights for priority calculations
        4. Calculate mold-machine priority matrix

        The process combines multiple data sources and algorithms to provide
        comprehensive optimization recommendations for production planning.

        Returns:
            tuple: A three-element tuple containing:
                - invalid_molds: List of molds that couldn't be processed
                - mold_estimated_capacity_df: DataFrame with estimated capacities for each mold
                - mold_machine_priority_matrix: Matrix showing optimal mold-machine combinations
        """
        # Step 1: Load mold stability index containing performance consistency metrics
        mold_stability_index = self._load_mold_stability_index()

        # Step 2: Estimate mold capacities using historical-based optimization
        self.logger.info("Start estimating mold capacity...")
        invalid_molds, mold_estimated_capacity_df = HistBasedItemMoldOptimizer().process_mold_info(
            mold_stability_index,             # Stability metrics for each mold
            self.moldSpecificationSummary_df, # Mold-item compatibility mappings
            self.moldInfo_df,                 # Detailed mold specifications
            self.efficiency,                  # Expected production efficiency
            self.loss                         # Expected production loss rate
        )
        self.logger.info("Mold estimated capacity are ready.")

        # Step 3: Load feature weights for priority matrix calculation
        mold_machine_feature_weights = self._load_feature_weights()

        # Step 4: Calculate mold-machine priority matrix using historical performance data
        self.logger.info("Start calculating mold-machine priority matrix...")
        mold_machine_priority_matrix = self.history_processor.calculate_mold_machine_priority_matrix(
            mold_machine_feature_weights,  # Weights for different performance metrics
            mold_estimated_capacity_df     # Estimated capacity data for each mold
        )
        self.logger.info("Mold-machine priority matrix are ready.")

        # Return all optimization results for downstream processing
        return invalid_molds, mold_estimated_capacity_df, mold_machine_priority_matrix