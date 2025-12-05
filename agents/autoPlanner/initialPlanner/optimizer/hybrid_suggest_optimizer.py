import os
import pandas as pd
from pathlib import Path
from typing import Tuple, List
from dataclasses import dataclass
from agents.decorators import validate_init_dataframes, validate_dataframe
from agents.utils import load_annotation_path, read_change_log, get_latest_change_row
from loguru import logger
from agents.autoPlanner.initialPlanner.optimizer.item_mold_capacity_optimizer import ItemMoldCapacityOptimizer
from agents.autoPlanner.initialPlanner.optimizer.mold_machine_priority_matrix_calculator import MoldMachinePriorityMatrixCalculator

@dataclass
class OptimizationResult:
    """Container for optimization results."""
    estimated_capacity_invalid_molds: List[str]
    priority_matrix_invalid_molds: List[str]
    mold_estimated_capacity_df: pd.DataFrame
    mold_machine_priority_matrix: pd.DataFrame


class FeatureWeights:
    """Constants for feature weights used in optimization."""
    
    # Default weights for different performance metrics
    DEFAULTS = {
        'shiftNGRate_weight': 0.1,       # Defect rate (10%)
        'shiftCavityRate_weight': 0.25,  # Cavity utilization (25%)  
        'shiftCycleTimeRate_weight': 0.25, # Cycle time efficiency (25%)
        'shiftCapacityRate_weight': 0.4   # Overall capacity (40% - highest priority)
    }
    
    # Required columns for feature weight calculations
    REQUIRED_COLUMNS = [
        'shiftNGRate', 'shiftCavityRate', 'shiftCycleTimeRate', 'shiftCapacityRate'
    ]


class MoldCapacityColumns:
    """Required columns for mold capacity estimation output."""
    REQUIRED = [
        'moldNo', 'moldName', 'acquisitionDate', 'machineTonnage',
        'moldCavityStandard', 'moldSettingCycle', 'cavityStabilityIndex',
        'cycleStabilityIndex', 'theoreticalMoldHourCapacity', 
        'effectiveMoldHourCapacity', 'estimatedMoldHourCapacity',
        'balancedMoldHourCapacity', 'totalRecords', 'totalCavityMeasurements',
        'totalCycleMeasurements', 'firstRecordDate', 'lastRecordDate'
    ]


# Decorator to validate DataFrames are initialized with the correct schema
# This ensures that required DataFrames have all necessary columns before processing
@validate_init_dataframes(lambda self: {
    "moldSpecificationSummary_df": list(self.databaseSchemas_data['staticDB']['moldSpecificationSummary']['dtypes'].keys()),
    "moldInfo_df": list(self.databaseSchemas_data['staticDB']['moldInfo']['dtypes'].keys()),
})

@validate_init_dataframes(lambda self: {
    "mold_stability_index": list(self.sharedDatabaseSchemas_data["mold_stability_index"]['dtypes'].keys()),
})

class HybridSuggestOptimizer:
    """
    A hybrid optimization system that combines historical data analysis with mold-machine
    compatibility matching to suggest optimal production configurations.

    This class integrates multiple optimization strategies:
    1. Historical-based mold capacity estimation
    2. Feature weight and production efficiency-based mold-machine priority matrix

    The optimizer helps manufacturing systems make data-driven decisions about
    mold selection, machine allocation, and production planning.
    """

    def __init__(self,
                 databaseSchemas_data,
                 sharedDatabaseSchemas_data,
                 source_path: str = 'agents/shared_db/DataLoaderAgent/newest',
                 annotation_name: str = "path_annotations.json",
                 default_dir: str = "agents/shared_db",
                 folder_path: str = "agents/OrderProgressTracker",
                 target_name: str = "change_log.txt",
                 mold_stability_index_folder: str = "agents/MoldStabilityIndexCalculator/mold_stability_index",
                 mold_stability_index_target_name: str = "change_log.txt",
                 mold_machine_weights_hist_path: str = "agents/MoldMachineFeatureWeightCalculator/weights_hist.xlsx",
                 efficiency: float = 0.85,
                 loss: float = 0.03,
                 ):
        """
        Initialize the HybridSuggestOptimizer with configuration paths and parameters.

        Args:
            source_path (str): Base path for data source files
            annotation_name (str): JSON file containing path mappings
            databaseSchemas_data (dict): database schema for validation.
            sharedDatabaseSchemas_data (dict): shared database schema for validation.
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

        # Store all configuration parameters
        self.source_path = source_path
        self.annotation_name = annotation_name
        self._load_dataframes()

        # Load database schema configuration for column validation
        # This ensures all DataFrames have the expected structure
        self.databaseSchemas_data = databaseSchemas_data

        # Load shared database schema configuration for column validation
        self.sharedDatabaseSchemas_data = sharedDatabaseSchemas_data

        self.default_dir = default_dir
        self.folder_path = folder_path
        self.target_name = target_name

        # Store production parameters for capacity calculations
        self.efficiency = efficiency  # Overall equipment effectiveness (OEE)
        self.loss = loss             # Expected material/time loss factor


        # Load mold stability index containing performance consistency metrics
        self.logger.info("Loading mold stability index...")
        self.mold_stability_index = self._load_mold_stability_index(
            mold_stability_index_folder,
            mold_stability_index_target_name
        )

        # Load feature weights for priority matrix calculation
        self.logger.info("Loading feature weights...")
        self.mold_machine_feature_weights = self._load_feature_weights(
            mold_machine_weights_hist_path
        )

    def _load_dataframes(self) -> None:
        """Load all required DataFrames from parquet files with comprehensive error handling."""
        # Load path annotations that map logical names to actual file paths
        try:
            self.path_annotation = load_annotation_path(self.source_path, self.annotation_name)
        except Exception as e:
            self.logger.error("Failed to load path annotations: {}", str(e))
            raise

        # Define the mapping between path annotation keys and DataFrame attribute names
        dataframes_config = [
            ('moldSpecificationSummary', 'moldSpecificationSummary_df'),  # Mold-item compatibility data
            ('moldInfo', 'moldInfo_df'),                                  # Detailed mold specifications
        ]

        # Load each DataFrame with comprehensive error handling and validation
        for path_key, attr_name in dataframes_config:
            self._load_single_dataframe(path_key, attr_name)

    def _load_single_dataframe(self, path_key: str, attr_name: str) -> None:
        """Load a single DataFrame with comprehensive error handling."""
        # Retrieve the actual file path from path annotations configuration
        path = self.path_annotation.get(path_key)

        # Validate that the path exists and is accessible before attempting to read
        if not path or not os.path.exists(path):
            error_msg = f"Path to '{path_key}' not found or does not exist: {path}"
            self.logger.error(error_msg)
            raise FileNotFoundError(error_msg)

        try:
            # Load DataFrame from parquet file
            df = pd.read_parquet(path)
            
            # Dynamically set the DataFrame as an instance attribute
            setattr(self, attr_name, df)

            # Log successful loading with shape and column information for debugging
            self.logger.debug("{}: {} - {}", path_key, df.shape, list(df.columns))

        except Exception as e:
            # Log detailed error information and re-raise for proper error handling
            self.logger.error("Failed to load {}: {}", path_key, str(e))
            raise

    # ------------------------------------------------------ #
    # HYBRID SUGGEST OPTIMIZER:                              #
    # - ESTIMATE MOLD CAPACITY USING HISTORICAL DATA USING : #
    #     + MOLD MOLD STABILITY INDEX DATA                   #
    # - CALCULATE MOLD MACHINE PRIORITY MATRIX USING :       #
    #     + MOLD ESTIMATED CAPACITY                          #
    #     + MOLD-MACHINE FEATURE WEIGHTS                     #
    # ------------------------------------------------------ #

    def process(self) -> OptimizationResult:
        """
        Execute the complete hybrid optimization process.

        This method orchestrates the entire optimization workflow:
        1. Load mold stability index data
        2. Estimate mold capacities using historical data
        3. Load feature weights for priority calculations
        4. Calculate mold-machine priority matrix

        Returns:
            OptimizationResult: Container with invalid_molds, estimated_capacity_df, 
                              and priority_matrix
        """
        try:
            # Estimate mold capacities using historical-based optimization
            self.logger.info("Starting mold capacity estimation...")
            estimated_capacity_invalid_molds, mold_estimated_capacity_df = self._estimate_mold_capacities(
                self.mold_stability_index
            )
            try:
                cols = list(self.sharedDatabaseSchemas_data["mold_estimated_capacity"]['dtypes'].keys())
                logger.info('Validation for mold_estimated_capacity...')
                validate_dataframe(mold_estimated_capacity_df, cols)
            except Exception as e:
                logger.error("Validation failed for mold_estimated_capacity (expected cols: %s): %s", cols, e)
                raise

            self.logger.info("Mold capacity estimation completed. Found {} invalid molds.", 
                           len(estimated_capacity_invalid_molds))

            # Calculate mold-machine priority matrix using historical performance data
            self.logger.info("Starting mold-machine priority matrix calculation...")
            mold_machine_priority_matrix, priority_matrix_invalid_molds = self._calculate_priority_matrix(
                self.mold_machine_feature_weights, 
                mold_estimated_capacity_df
            )
            self.logger.info("Priority matrix calculation completed. Found {} invalid molds.", 
                           len(priority_matrix_invalid_molds))

            # Return structured optimization results
            return OptimizationResult(
                estimated_capacity_invalid_molds = estimated_capacity_invalid_molds,
                priority_matrix_invalid_molds=priority_matrix_invalid_molds,
                mold_estimated_capacity_df=mold_estimated_capacity_df,
                mold_machine_priority_matrix=mold_machine_priority_matrix
            )

        except Exception as e:
            self.logger.error("Optimization process failed: {}", str(e))
            raise

    def _estimate_mold_capacities(self, mold_stability_index: pd.DataFrame) -> Tuple[List[str], pd.DataFrame]:
        """Estimate mold capacities using historical-based optimization."""
        return ItemMoldCapacityOptimizer(
                 mold_stability_index,
                 self.moldSpecificationSummary_df,
                 self.moldInfo_df,
                 self.efficiency,
                 self.loss,
                 self.databaseSchemas_data,
                 self.sharedDatabaseSchemas_data
                 ).process()

    def _calculate_priority_matrix(self, 
                                   feature_weights: pd.Series, 
                                   capacity_df: pd.DataFrame) -> pd.DataFrame:
        
        """Initialize MoldMachinePriorityMatrixCalculator for analyzing historical production data."""
        try:
            mold_machine_priority_matrix_calculator = MoldMachinePriorityMatrixCalculator(
                feature_weights,  # Weights for different performance metrics
                capacity_df,       # Estimated capacity data for each mold
                self.databaseSchemas_data, self.sharedDatabaseSchemas_data, 
                self.source_path, self.annotation_name, 
                self.folder_path, self.target_name, self.default_dir, 
                self.efficiency, self.loss
            )
            self.logger.debug("MoldMachinePriorityMatrixCalculator initialized successfully")
        except Exception as e:
            self.logger.error("Failed to initialize MoldMachinePriorityMatrixCalculator: {}", str(e))
            raise

        """Calculate mold-machine priority matrix using historical performance data."""
        return mold_machine_priority_matrix_calculator.process()
    
    # ------------------------- #
    # LOAD MOLD STABILITY INDEX #
    # ------------------------- #

    def _load_mold_stability_index(self,
                                   mold_stability_index_folder,
                                   mold_stability_index_target_name) -> pd.DataFrame:
        """
        Load mold stability index data from the nearest monthly report or create initial structure.

        The mold stability index contains metrics about how consistently each mold performs,
        including cavity stability, cycle time consistency, and overall reliability measures.

        Returns:
            pd.DataFrame: Mold stability index with performance consistency metrics
        """
        # Attempt to find the latest mold stability index file from change log
        stability_path = read_change_log(
            mold_stability_index_folder,
            mold_stability_index_target_name
        )

        # Handle case where no historical stability index exists
        if stability_path is None:
            self.logger.warning(
                "Cannot find stability index file {}/{}",
                mold_stability_index_folder,
                mold_stability_index_target_name
            )
            self.logger.info("Creating initial mold stability index structure...")
            return self._create_initial_stability_index()
        
        # Load existing stability index from Excel file
        try:
            self.logger.info("Loading existing mold stability index from: {}", stability_path)
            stability_index = pd.read_excel(stability_path)
            self.logger.debug("Loaded stability index with shape: {}", stability_index.shape)
            return stability_index
        except Exception as e:
            self.logger.error("Failed to load stability index from {}: {}", stability_path, str(e))
            self.logger.info("Falling back to initial stability index structure...")
            return self._create_initial_stability_index()

    def _create_initial_stability_index(self) -> pd.DataFrame:
        """Create an empty DataFrame with the required column structure."""
        return pd.DataFrame(columns=MoldCapacityColumns.REQUIRED)
    
    # -------------------- #
    # LOAD FEATURE WEIGHTS #
    # -------------------- #

    def _load_feature_weights(self, 
                              mold_machine_weights_hist_path) -> pd.Series:
        """
        Load the monthly feature weights for calculating mold-machine priority matrix.

        Feature weights determine the relative importance of different performance metrics
        when evaluating mold-machine combinations. These weights are typically learned
        from historical performance data and updated over time.

        Returns:
            pd.Series: Feature weights for different performance metrics
        """
        # Check if historical feature weights file exists
        if not Path(mold_machine_weights_hist_path).exists():
            self.logger.warning(
                "Feature weights file not found: {}. Using default weights.",
                mold_machine_weights_hist_path
            )
            return self._create_initial_feature_weights()

        try:
            # Load the most recent feature weights from historical data
            self.logger.info("Loading historical feature weights from: {}", 
                             mold_machine_weights_hist_path)
            weights = get_latest_change_row(Path(mold_machine_weights_hist_path))
            
            # Validate loaded weights
            if not self._validate_feature_weights(weights):
                self.logger.warning("Invalid feature weights loaded. Using defaults.")
                return self._create_initial_feature_weights()
                
            self.logger.debug("Loaded feature weights: {}", weights.to_dict())
            return weights
            
        except Exception as e:
            self.logger.error("Failed to load feature weights: {}. Using defaults.", str(e))
            return self._create_initial_feature_weights()

    def _create_initial_feature_weights(self) -> pd.Series:
        """
        Create initial feature weights using predefined default values.
        These weights represent a balanced starting point for optimization.
        """
        # Initialize series with zeros for all required columns
        weights = pd.Series(0.0, index=FeatureWeights.REQUIRED_COLUMNS, dtype=float)

        # Set initial weights based on manufacturing best practices
        weight_mapping = {
            'shiftNGRate': FeatureWeights.DEFAULTS['shiftNGRate_weight'],
            'shiftCavityRate': FeatureWeights.DEFAULTS['shiftCavityRate_weight'],
            'shiftCycleTimeRate': FeatureWeights.DEFAULTS['shiftCycleTimeRate_weight'],
            'shiftCapacityRate': FeatureWeights.DEFAULTS['shiftCapacityRate_weight']
        }

        for col, weight in weight_mapping.items():
            weights[col] = weight

        self.logger.info("Created initial feature weights: {}", weight_mapping)
        return weights

    def _validate_feature_weights(self, weights: pd.Series) -> bool:
        """
        Validate that feature weights are properly formatted and within acceptable ranges.
        
        Args:
            weights: Series containing feature weights to validate
            
        Returns:
            bool: True if weights are valid, False otherwise
        """
        try:
            # Check if all required columns are present
            missing_cols = set(FeatureWeights.REQUIRED_COLUMNS) - set(weights.index)
            if missing_cols:
                self.logger.warning("Missing required weight columns: {}", missing_cols)
                return False

            # Check if all weights are numeric and non-negative
            for col in FeatureWeights.REQUIRED_COLUMNS:
                if not pd.api.types.is_numeric_dtype(type(weights[col])):
                    self.logger.warning("Non-numeric weight for column {}: {}", col, weights[col])
                    return False
                    
                if weights[col] < 0:
                    self.logger.warning("Negative weight for column {}: {}", col, weights[col])
                    return False

            # Check if weights sum to a reasonable total (should be close to 1.0)
            total_weight = weights[FeatureWeights.REQUIRED_COLUMNS].sum()
            if not (0.5 <= total_weight <= 2.0):  # Allow some flexibility
                self.logger.warning("Unusual total weight sum: {}. Expected close to 1.0", total_weight)
                return False

            return True

        except Exception as e:
            self.logger.error("Error validating feature weights: {}", str(e))
            return False

    def validate_configuration(self) -> bool:
        """
        Validate that all required configurations are accessible.
        
        Returns:
            bool: True if configuration is valid, False otherwise
        """
        validation_results = []
        
        # Validate configuration parameters
        if not (0 < self.efficiency <= 1):
            self.logger.error("Efficiency must be between 0 and 1, got: {}", self.efficiency)
            validation_results.append(False)
        else:
            validation_results.append(True)
            
        if not (0 <= self.loss < 1):
            self.logger.error("Loss must be between 0 and 1, got: {}", self.loss)
            validation_results.append(False)
        else:
            validation_results.append(True)
        
        is_valid = all(validation_results)
        if is_valid:
            self.logger.info("Configuration validation passed")
        else:
            self.logger.error("Configuration validation failed")
            
        return is_valid