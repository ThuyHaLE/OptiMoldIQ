import pandas as pd
import os
from pathlib import Path
from loguru import logger
from agents.decorators import validate_init_dataframes, validate_dataframe
from datetime import datetime
from agents.utils import load_annotation_path, rank_nonzero, get_latest_change_row, ConfigReportMixin
from agents.autoPlanner.tools.machine_processing import check_newest_machine_layout
from agents.autoPlanner.tools.performance import summarize_mold_machine_history
from configs.shared.shared_source_config import SharedSourceConfig
from agents.autoPlanner.optimizer.hybrid_optimizer.config.hybrid_suggest_config import FeatureWeights
from typing import Tuple, List

from configs.recovery import (
    Dependency,
    DependencyValidator,
    get_dependency_data,
    OrderProgressTrackerHealer,
)

# Decorator to validate DataFrames are initialized with the correct schema
# This ensures that required DataFrames have all necessary columns before processing
@validate_init_dataframes(lambda self: {
    "productRecords_df": list(self.databaseSchemas_data['dynamicDB']['productRecords']['dtypes'].keys()),
    "machineInfo_df": list(self.databaseSchemas_data['staticDB']['machineInfo']['dtypes'].keys()),
    "moldInfo_df": list(self.databaseSchemas_data['staticDB']['moldInfo']['dtypes'].keys()),
    "proStatus_df": list(self.sharedDatabaseSchemas_data["pro_status"]['dtypes'].keys())
})

class PriorityMatrixCalculator(ConfigReportMixin): # MoldMachinePriorityMatrixCalculator

    """
    This class responsible for processing historical production data in order to process:
    1. Generate Mold-Machine Priority Matrix:
    - Use historical production data to assess the performance of each mold-machine pair.
    - Score each pair based on historical weight and actual efficiency.
    - The results are presented in the form of a priority matrix to support optimal production planning.
    """

    REQUIRED_FIELDS = {
        'shared_source_config': {
            'annotation_path': str,
            'databaseSchemas_path': str,
            'sharedDatabaseSchemas_path': str,
            'progress_tracker_change_log_path': str,
            'mold_machine_weights_hist_path': str
            },
        'mold_estimated_capacity': pd.DataFrame,
        'efficiency': float,
        'loss': float
        }

    CONSTANT_CONFIG_PATH = (
        "agents/autoPlanner/initialPlanner/optimizer/hybrid_optimizer/config/constant_configurations.json")
    
    def __init__(self,
                 shared_source_config: SharedSourceConfig, 
                 mold_estimated_capacity: pd.DataFrame,
                 efficiency: float = 0.85,
                 loss: float = 0.03
                 ):

        """
        Initialize the MoldMachinePriorityMatrixCalculator.
        
        Args:
            shared_source_config: SharedSourceConfig containing processing parameters
            Including:
                - annotation_path: Path to the JSON file containing path annotations
                - databaseSchemas_path: Path to database schemas JSON file for validation
                - sharedDatabaseSchemas_path: Path to shared database schemas JSON file for validation
                - progress_tracker_change_log_path: Path to the OrderProgressTracker change log
                - mold_machine_weights_hist_path: Path to mold-machine feature weights (from MoldMachineFeatureWeightCalculator)
            mold_estimated_capacity: Estimated capacity data for each mold    
            efficiency: Production efficiency factor (0.0 to 1.0)
            loss: Production loss factor (0.0 to 1.0)
        """

        # Capture initialization arguments for reporting
        self._capture_init_args()

        # Initialize logger with class context for better debugging
        self.logger = logger.bind(class_="MoldMachinePriorityMatrixCalculator")

        # Validate required configs
        is_valid, errors = shared_source_config.validate_requirements(self.REQUIRED_FIELDS['shared_source_config'])
        if not is_valid:
            raise ValueError(
                f"{self.__class__.__name__} config validation failed:\n" +
                "\n".join(f"  - {e}" for e in errors)
            )
        self.logger.info("✓ Validation for shared_source_config requirements: PASSED!")

        # Store configurations
        self.config = shared_source_config
        
        self.mold_estimated_capacity_df = mold_estimated_capacity
        self.efficiency = efficiency
        self.loss = loss

        # Load database schema configuration for column validation
        self.load_schema_and_annotations()
        self._load_dataframes()

        # Define dependencies
        dependencies = [
            Dependency(
                name="progress_tracker",
                change_log_path=self.config.progress_tracker_change_log_path,
                healing_agent=OrderProgressTrackerHealer(self.config),
                required=True,
                file_type="excel",
                description="Production progress tracking"
            ),
        ]
        # DependencyValidator
        validator = DependencyValidator(self.config)
        results = validator.validate_dependencies(
            dependencies=dependencies,
            auto_heal=True,
            load_data=True
        )
        # Load production report
        self.proStatus_df = get_dependency_data(results, "progress_tracker")

        # Load constant configurations
        self.constant_config = load_annotation_path(
            Path(self.CONSTANT_CONFIG_PATH).parent,
            Path(self.CONSTANT_CONFIG_PATH).name).get('MoldMachinePriorityMatrixCalculator', {})
        if not self.constant_config:
            self.logger.debug("MoldMachinePriorityMatrixCalculator constant config not found in loaded YAML dict")

        # Loading feature weights
        self.logger.info("Loading feature weights...")
        self.mold_machine_feature_weights = self._load_feature_weights(self.config.mold_machine_weights_hist_path)
        self.logger.info("✓ Feature weights loaded successfully")

    def _load_annotation_from_config(self, config_path):
        """Helper function to load annotation from a config path."""
        return load_annotation_path(
            Path(config_path).parent,
            Path(config_path).name
        )

    def load_schema_and_annotations(self):
        """Load database schemas and path annotations from configuration files."""
        self.databaseSchemas_data = self._load_annotation_from_config(
            self.config.databaseSchemas_path
        )
        self.sharedDatabaseSchemas_data = self._load_annotation_from_config(
            self.config.sharedDatabaseSchemas_path
        )
        self.path_annotation = self._load_annotation_from_config(
            self.config.annotation_path
        )
        
    def _load_dataframes(self) -> None:

        """
        Load all required DataFrames from parquet files with consistent error handling.

        This method loads the following DataFrames:
        - productRecords_df: Production records with item, mold, machine data
        - machineInfo_df: Machine specifications and tonnage information
        - moldInfo_df: Detailed mold information including tonnage requirements
        """

        # Define the mapping between path annotation keys and DataFrame attribute names
        dataframes_to_load = [
            ('productRecords', 'productRecords_df'),
            ('machineInfo', 'machineInfo_df'),
            ('moldInfo', 'moldInfo_df')
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

    def _validate_process_inputs(self) -> None:
        """
        Validate all inputs before processing. 
        Both must be valid.
        """
        capacity_valid = self._validate_columns(
            self.mold_estimated_capacity_df,
            self.constant_config['ESTIMATED_MOLD_REQUIRED_COLUMNS'],
            "estimated_capacity"
        )
        weights_valid = self._validate_columns(
            self.mold_machine_feature_weights,
            self.constant_config['FEATURE_WEIGHTS_REQUIRED_COLUMNS'],
            "feature_weights"
        )
        if not capacity_valid or not weights_valid:
            raise ValueError("Input validation failed. Check logs for details.")
    
    def process(self) -> tuple[pd.DataFrame, 
                               pd.DataFrame, 
                               List[str], 
                               str]:

        """
        Calculate the priority matrix for mold-machine assignments based on historical data
        and will be used to suggest a list of machines (in priority order) for each mold in the subsequent planning steps

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

        try:
            self.logger.info("Starting MoldMachinePriorityMatrixCalculator ...")

            # Generate config header using mixin
            timestamp_start = datetime.now()
            timestamp_str = timestamp_start.strftime("%Y-%m-%d %H:%M:%S")
            config_header = self._generate_config_report(timestamp_str, required_only=True)

            optimization_log_lines = [config_header]
            optimization_log_lines.append(f"--Processing Summary--")
            optimization_log_lines.append(f"⤷ {self.__class__.__name__} results:")

            # Step 1: Validate inputs (feature weights already loaded in __init__)
            self._validate_process_inputs()
            self.logger.info("✓ Step 1: Inputs validated (feature weights pre-loaded)")

            # Step 2: Process historical production data for completed orders
            historical_data = self._process_historical_production_data()
            self.logger.info("✓ Step 2: Historical production data processed")
            
            # Step 3: Calculate performance metrics for each mold-machine combination
            mold_machine_history_summary, invalid_molds = self._calculate_performance_metrics(historical_data)
            self.logger.info("✓ Step 3: Performance metrics calculated")

            # Step 4: Apply weighted scoring based on multiple factors
            weighted_scores = self._apply_weighted_scoring(mold_machine_history_summary)
            self.logger.info("✓ Step 4: Weighted scoring applied")

            # Step 5: Rank combinations to create priority matrix
            priority_matrix = self._rank_and_create_priority_matrix(weighted_scores)
            self.logger.info("✓ Step 5: Priority matrix created")
            
            self.logger.info("✅ Process finished!!!")
            
            # Calculate processing time
            timestamp_end = datetime.now()
            processing_time = (timestamp_end - timestamp_start).total_seconds()

            # Add summary statistics
            optimization_log_lines.append(f"--Assignment Results--")
            optimization_log_lines.append(f"⤷ Processing time: {processing_time:.2f} seconds")
            optimization_log_lines.append(f"⤷ End time: {timestamp_end.strftime('%Y-%m-%d %H:%M:%S')}")

            if invalid_molds:
                optimization_log_lines.append(f"--Invalid molds detected!--")
                optimization_log_lines.append(f"⤷ Found {len(invalid_molds)} invalid molds with NaN values: {invalid_molds}")
            
            optimization_log_lines.append(f"--Priority Matrix Info--")
            optimization_log_lines.append(f"⤷ Matrix dimensions: {priority_matrix.shape[0]} molds × {priority_matrix.shape[1]} machines")
            optimization_log_lines.append(f"⤷ Total cells: {priority_matrix.size}")
            optimization_log_lines.append(f"⤷ Valid priorities (non-zero): {(priority_matrix > 0).sum().sum()}")
            optimization_log_lines.append(f"⤷ Coverage rate: {(priority_matrix > 0).sum().sum() / priority_matrix.size * 100:.1f}%")
            optimization_log_lines.append(f"⤷ Avg priorities per mold: {(priority_matrix > 0).sum(axis=1).mean():.1f}")
            optimization_log_lines.append(f"⤷ Max priority level: {int(priority_matrix.max().max())}")
            
            optimization_log_lines.append("Process finished!!!")

            optimization_log_str = "\n".join(optimization_log_lines)
            
            return self.proStatus_df, priority_matrix, invalid_molds, optimization_log_str

        except Exception as e:  
            self.logger.error("Failed to process MoldMachinePriorityMatrixCalculator: {}", str(e))
            raise RuntimeError(f"MoldMachinePriorityMatrixCalculator processing failed: {str(e)}") from e

    def _validate_columns(self, data, required_columns, data_type_name):
        """Generic validation for both DataFrames and Series"""
        if isinstance(data, pd.DataFrame):
            actual_columns = data.columns
        elif isinstance(data, pd.Series):
            actual_columns = data.index
        else:
            self.logger.error("Invalid input type: {}", type(data))
            return False
        
        missing = [col for col in required_columns if col not in actual_columns]
        if missing:
            self.logger.error("Missing {} columns: {}", data_type_name, missing)
            return False
        
        self.logger.info("✅ All {} columns present!", data_type_name)
        return True
    
    #--------------------------------------------#
    # STEP 1: LOAD FEATURE WEIGHTS               #
    #--------------------------------------------#
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
            if not (
                self.constant_config["WEIGHT_SUM_MIN"] <= total_weight <= self.constant_config["WEIGHT_SUM_MAX"]):
                self.logger.warning("Unusual total weight sum: {}. Expected close to 1.0", total_weight)
                return False

            return True

        except Exception as e:
            self.logger.error("Error validating feature weights: {}", str(e))
            return False
        
    #--------------------------------------------#
    # STEP 2: PROCESS HISTORICAL PRODUCTION DATA #
    #--------------------------------------------#
    def _process_historical_production_data(self) -> pd.DataFrame:
        """
        Step 2: Process historical production data for completed orders.
        
        This method:
        - Standardizes column names
        - Prepares mold-machine historical data
        - Validates the schema of prepared data
        
        Returns:
            pd.DataFrame: Processed historical data with completed orders
            
        Raises:
            Exception: If data validation fails
        """

        # Standardize column names to match expected schema
        self.proStatus_df.rename(columns={'lastestMachineNo': 'machineNo',
                                          'lastestMoldNo': 'moldNo'
                                          }, inplace=True)
        
        # Prepare historical data for analysis
        historical_data = self._prepare_mold_machine_historical_data(self.machineInfo_df, 
                                                                     self.proStatus_df, 
                                                                     self.productRecords_df)
        try:
            cols = list(self.sharedDatabaseSchemas_data["historical_records"]['dtypes'].keys())
            logger.info('Validation for historical_data...')
            validate_dataframe(historical_data, cols)
        except Exception as e:
            logger.error("Validation failed for historical_data (expected cols: %s): %s", cols, e)
            raise

        return historical_data
    
    @staticmethod
    def _prepare_mold_machine_historical_data(machineInfo_df: pd.DataFrame, 
                                              proStatus_df: pd.DataFrame, 
                                              productRecords_df: pd.DataFrame) -> pd.DataFrame:
        """
        Prepare and filter historical data for analysis.
        
        Args:
            machineInfo_df: Machine information DataFrame
            proStatus_df: Production status DataFrame
            productRecords_df: Product records DataFrame
            
        Returns:
            pd.DataFrame: Filtered historical data for completed orders
        """
        machine_info_df = check_newest_machine_layout(machineInfo_df)

        # Filter to completed orders and merge with machine info
        hist = proStatus_df.loc[proStatus_df['itemRemain'] == 0].merge(
            machine_info_df[['machineNo', 'machineCode', 'machineName', 'machineTonnage']],
            how='left', 
            on=['machineNo']
        )

        # Prepare product records (don't mutate input DataFrame)
        productRecords_working = productRecords_df.copy()
        productRecords_working.rename(columns={'poNote': 'poNo'}, inplace=True)

        df = productRecords_working[[
            'recordDate', 'workingShift',
            'machineNo', 'machineCode',
            'itemCode', 'itemName',
            'poNo', 'moldNo', 'moldShot', 'moldCavity',
            'itemTotalQuantity', 'itemGoodQuantity'
        ]]

        # Optimize filtering with set for O(1) lookups
        hist_po_set = set(hist['poNo'])
        filtered_df = df[
            df['poNo'].isin(hist_po_set) & (df['itemTotalQuantity'] > 0)
        ].copy()

        return filtered_df
    
    #--------------------------------------------#
    # STEP 3: CALCULATE MOLD-MACHINE PERFORMANCE #
    #--------------------------------------------#
    def _calculate_performance_metrics(self, historical_data: pd.DataFrame
                                       ) -> Tuple[pd.DataFrame, List[str]]:
        """
        Step 3: Calculate performance metrics for each mold-machine combination.
        
        This method analyzes historical data to compute key performance indicators
        such as:
        - Shift NG (defect) rate
        - Shift cavity utilization rate
        - Shift cycle time efficiency
        - Shift capacity utilization rate
        
        Args:
            historical_data: Processed historical production data
            
        Returns:
            Tuple containing:
                - mold_machine_history_summary: Performance metrics for each combination
                - invalid_molds: List of molds with validation issues (NaN values)
                
        Raises:
            Exception: If metrics validation fails
        """
        # Calculate performance metrics
        mold_machine_history_summary, invalid_molds = summarize_mold_machine_history(
            historical_data, 
            self.mold_estimated_capacity_df
        )
        
        # Validate schema
        try:
            cols = list(
                self.sharedDatabaseSchemas_data["mold_machine_history_summary"]['dtypes'].keys()
            )
            self.logger.info('Validating mold_machine_history_summary schema...')
            validate_dataframe(mold_machine_history_summary, cols)
        except Exception as e:
            self.logger.error(
                "Validation failed for mold_machine_history_summary (expected cols: %s): %s", 
                cols, e
            )
            raise
        
        return mold_machine_history_summary, invalid_molds
    
    #--------------------------------------------#
    # STEP 4: APPLY WEIGHTED SCORING             #
    #--------------------------------------------#

    def _apply_weighted_scoring(self, 
                                mold_machine_history_summary: pd.DataFrame) -> pd.DataFrame:
        """
        Step 4: Apply weighted scoring based on multiple performance factors.
        
        This method combines multiple performance metrics using learned feature weights
        to produce a composite score for each mold-machine combination. The weights
        reflect the relative importance of each performance factor.
        
        Args:
            mold_machine_history_summary: DataFrame with performance metrics
            
        Returns:
            pd.DataFrame: Summary with added 'total_score' column
        """
        # Apply weighted scoring
        mold_machine_history_summary["total_score"] = (
            mold_machine_history_summary[list(self.mold_machine_feature_weights.index)] * 
            self.mold_machine_feature_weights.values
        ).sum(axis=1)
        
        return mold_machine_history_summary

    #--------------------------------------------#
    # STEP 5: CREAT PRIORITY MATRIX              #
    #--------------------------------------------#
    def _rank_and_create_priority_matrix(self, 
                                         weighted_scores: pd.DataFrame) -> pd.DataFrame:
        """
        Step 5: Rank mold-machine combinations to create priority matrix.
        
        This method:
        - Pivots weighted scores into a matrix format
        - Ranks machines for each mold based on total scores
        - Produces priority rankings (1 = highest priority)
        
        Args:
            weighted_scores: DataFrame with total_score column
            
        Returns:
            pd.DataFrame: Priority matrix with molds as rows, machines as columns,
                        and priority rankings as values
        """
        # Create pivot table with weighted scores
        weighted_results = weighted_scores[['moldNo', 'machineCode', 'total_score']].pivot(
            index="moldNo", 
            columns="machineCode", 
            values="total_score"
        ).fillna(0)

        # Convert scores to priority rankings (1 = best, 2 = second best, etc.)
        priority_matrix = weighted_results.apply(rank_nonzero, axis=1)

        return priority_matrix