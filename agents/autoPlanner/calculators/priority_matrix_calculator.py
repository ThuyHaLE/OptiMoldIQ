import pandas as pd
from loguru import logger

from datetime import datetime
from typing import Tuple, List, Dict

from configs.shared.config_report_format import ConfigReportMixin
from configs.shared.dict_based_report_generator import DictBasedReportGenerator
from agents.utils import rank_nonzero
from agents.decorators import validate_init_dataframes, validate_dataframe
from agents.autoPlanner.tools.performance import summarize_mold_machine_history
from agents.autoPlanner.tools.machine_processing import check_newest_machine_layout

from dataclasses import dataclass, asdict

@dataclass
class MatrixCalculatorResult:
    priority_matrix: pd.DataFrame
    invalid_mold_list: List
    log_str: str
    def to_dict(self) -> Dict:
        """Convert dataclass to dictionary for serialization/logging."""
        return asdict(self)

# Decorator to validate DataFrames are initialized with the correct schema
# This ensures that required DataFrames have all necessary columns before processing
@validate_init_dataframes(lambda self: {
    "productRecords_df": list(self.databaseSchemas_data['dynamicDB']['productRecords']['dtypes'].keys()),
    "machineInfo_df": list(self.databaseSchemas_data['staticDB']['machineInfo']['dtypes'].keys()),
    "moldInfo_df": list(self.databaseSchemas_data['staticDB']['moldInfo']['dtypes'].keys()),
    "proStatus_df": list(self.sharedDatabaseSchemas_data["pro_status"]['dtypes'].keys()),
    "machine_info_df": list(self.sharedDatabaseSchemas_data["machine_info"]['dtypes'].keys()),
    "mold_estimated_capacity_df": list(self.sharedDatabaseSchemas_data["mold_estimated_capacity"]['dtypes'].keys())
})
class PriorityMatrixCalculator(ConfigReportMixin): # MoldMachinePriorityMatrixCalculator

    """
    This class responsible for processing historical production data in order to generate Mold-Machine Priority Matrix:
    - Use historical production data to assess the performance of each mold-machine pair.
    - Score each pair based on historical weight and actual efficiency.
    - The results are presented in the form of a priority matrix to support optimal production planning.

    This method:
    1. Loads feature weights from the latest weight calculation
    2. Processes historical production data for completed orders
    3. Calculates performance metrics for each mold-machine combination
    4. Applies weighted scoring based on multiple factors
    5. Ranks combinations to create a priority matrix

    Returns:
        pandas.DataFrame: Priority matrix with molds as rows, machines as columns,
        and priority rankings as values (1 = highest priority)  
    """
    
    DEFAULT_FEATURE_WEIGHTS = {
        'shiftNGRate_weight': 0.1,         # Defect rate (10%)
        'shiftCavityRate_weight': 0.25,    # Cavity utilization (25%)  
        'shiftCycleTimeRate_weight': 0.25, # Cycle time efficiency (25%)
        'shiftCapacityRate_weight': 0.4    # Overall capacity (40% - highest priority)
    }
    
    FEATURE_WEIGHTS_REQUIRED_COLUMNS = [
        "shiftNGRate", "shiftCavityRate", "shiftCycleTimeRate", "shiftCapacityRate"]
    
    PRODUCT_RECORD_REQUIRED_COLS = [
        'recordDate', 'workingShift', 'machineNo', 'machineCode',
        'itemCode', 'itemName', 'poNo', 'moldNo', 'moldShot', 'moldCavity',
        'itemTotalQuantity', 'itemGoodQuantity'
        ]
    
    WEIGHT_SUM_MIN = 0.5
        
    WEIGHT_SUM_MAX = 2.0
    
    def __init__(self,
                 databaseSchemas_data: Dict,
                 sharedDatabaseSchemas_data: Dict,
                 productRecords_df: pd.DataFrame,
                 machineInfo_df: pd.DataFrame,
                 moldInfo_df: pd.DataFrame,
                 proStatus_df: pd.DataFrame,
                 mold_estimated_capacity: pd.DataFrame,
                 mold_machine_feature_weights: pd.Series | None,
                 calculator_constant_config: Dict = {},
                 efficiency: float = 0.85,
                 loss: float = 0.03
                 ):

        """
        Initialize the PriorityMatrixCalculator.
        
        Args:
            - databaseSchemas_data: Database schemas for validation
            - sharedDatabaseSchemas_data: Shared database schemas for validation
            - productRecords_df: Production records with item, mold, machine data
            - machineInfo_df: Machine specifications and tonnage information
            - moldInfo_df: Detailed mold information including tonnage requirements
            - proStatus_df: Detailed order production progress.
            - mold_estimated_capacity: Detailed priority molds for each item code with the highest estimated capacity
            - mold_machine_feature_weights: Learned mold-machine feature weights from historical data
            - calculator_constant_config: Constant config for priority matrix calculator
            - efficiency: Production efficiency factor (0.0 to 1.0)
            - loss: Production loss factor (0.0 to 1.0)
        """

        # Capture initialization arguments for reporting
        self._capture_init_args()

        # Initialize logger with class context for better debugging
        self.logger = logger.bind(class_="PriorityMatrixCalculator")
    
        self.databaseSchemas_data = databaseSchemas_data
        self.sharedDatabaseSchemas_data = sharedDatabaseSchemas_data
    
        self.productRecords_df = productRecords_df
        self.moldInfo_df = moldInfo_df

        self.machineInfo_df = machineInfo_df
        self.machine_info_df = check_newest_machine_layout(self.machineInfo_df)
        
        self.proStatus_df = proStatus_df
        
        self.mold_estimated_capacity_df = mold_estimated_capacity

        # Load constant configurations
        self.calculator_constant_config = calculator_constant_config
        if not self.calculator_constant_config:
            self.logger.debug("PriorityMatrixCalculator constant config not found.")

        self.mold_machine_feature_weights = self._load_feature_weights(mold_machine_feature_weights)

        self.efficiency = efficiency
        self.loss = loss

    def process_calculating(self) -> MatrixCalculatorResult:

        """
        Calculate the priority matrix for mold-machine assignments based on historical data
        and will be used to suggest a list of machines (in priority order) for each mold
        """

        self.logger.info("Starting PriorityMatrixCalculator ...")

        # Generate config header using mixin
        start_time = datetime.now()
        timestamp_str = start_time.strftime("%Y-%m-%d %H:%M:%S")
        config_header = self._generate_config_report(timestamp_str)
        
        # Initialize validation log entries for entire processing run
        calculator_log_lines = [config_header]
        calculator_log_lines.append(f"--Processing Summary--\n")
        calculator_log_lines.append(f"⤷ {self.__class__.__name__} results:\n")

        try:
            # Step 1: Load mold-machine feature weights (already loaded in __init__)
            self.logger.info("✓ Step 1: Mold-machine feature weights pre-loaded")

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

            # Log data summary
            calculator_log_lines.append("DATA EXPORT SUMMARY")
            calculator_log_lines.append(f"--Priority Matrix Info--")
            calculator_log_lines.append( f"⤷ Matrix dimensions: {priority_matrix.shape[0]} molds × {priority_matrix.shape[1]} machines")
            calculator_log_lines.append(f"⤷ Total cells: {priority_matrix.size}")
            calculator_log_lines.append(f"⤷ Valid priorities (non-zero): {(priority_matrix > 0).sum().sum()}")
            calculator_log_lines.append(f"⤷ Coverage rate: {(priority_matrix > 0).sum().sum() / priority_matrix.size * 100:.1f}%")
            calculator_log_lines.append(f"⤷ Avg priorities per mold: {(priority_matrix > 0).sum(axis=1).mean():.1f}")
            calculator_log_lines.append(f"⤷ Max priority level: {int(priority_matrix.max().max())}")
            if invalid_molds:
                calculator_log_lines.append(f"--Invalid molds detected!--")
                calculator_log_lines.append(f"⤷ Found {len(invalid_molds)} invalid molds with NaN values: {invalid_molds}")
            
            # Generate planner summary
            reporter = DictBasedReportGenerator(use_colors=False)
            calculator_summary = "\n".join(reporter.export_report({"production_status": self.proStatus_df,
                                                                   "priority_matrix": priority_matrix,
                                                                   "invalid_molds": invalid_molds}))
            calculator_log_lines.append(f"{calculator_summary}")

            calculator_log_lines.append("Process finished!!!")

            return MatrixCalculatorResult(
                priority_matrix = priority_matrix,
                invalid_mold_list = invalid_molds,
                log_str = "\n".join(calculator_log_lines)
                )
        
        except Exception as e:  
            self.logger.error("Failed to process PriorityMatrixCalculator: {}", str(e))
            raise RuntimeError(f"PriorityMatrixCalculator processing failed: {str(e)}") from e
         
    #--------------------------------------------#
    # STEP 1: LOAD FEATURE WEIGHTS               #
    #--------------------------------------------#
    def _load_feature_weights(self,
                              feature_weights: pd.Series | None
                              ) -> pd.Series:
        """
        Load and validate feature weights for mold-machine priority calculation.
        Fallback to default weights if input is missing or invalid.
        """

        if (feature_weights is None
            or not self._validate_feature_weights(feature_weights)
            ):
            self.logger.warning("Invalid or missing feature weights. Using default values.")
            return self._create_initial_feature_weights()

        self.logger.info("✓ Feature weights loaded successfully")

        return feature_weights
    
    def _create_initial_feature_weights(self) -> pd.Series:
        """
        Create initial feature weights using predefined default values.
        These weights represent a balanced starting point for optimization.
        """
        # Initialize series with zeros for all required columns
        required_cols = self.calculator_constant_config.get("FEATURE_WEIGHTS_REQUIRED_COLUMNS", 
                                                            self.FEATURE_WEIGHTS_REQUIRED_COLUMNS)
        weights = pd.Series(0.0, index=required_cols, dtype=float)

        # Set initial weights based on manufacturing best practices
        default_weights = self.calculator_constant_config.get("DEFAULT_FEATURE_WEIGHTS", 
                                                              self.DEFAULT_FEATURE_WEIGHTS)
        weight_mapping = {
            'shiftNGRate': default_weights['shiftNGRate_weight'],
            'shiftCavityRate': default_weights['shiftCavityRate_weight'],
            'shiftCycleTimeRate': default_weights['shiftCycleTimeRate_weight'],
            'shiftCapacityRate': default_weights['shiftCapacityRate_weight']
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
            required_cols = self.calculator_constant_config.get("FEATURE_WEIGHTS_REQUIRED_COLUMNS", 
                                                                self.FEATURE_WEIGHTS_REQUIRED_COLUMNS)
            
            # Check if all required columns are present
            missing_cols = set(required_cols) - set(weights.index)
            if missing_cols:
                self.logger.warning("Missing required weight columns: {}", missing_cols)
                return False

            # Check if all weights are numeric and non-negative
            for col in required_cols:
                if not pd.api.types.is_numeric_dtype(type(weights[col])):
                    self.logger.warning("Non-numeric weight for column {}: {}", col, weights[col])
                    return False
                    
                if weights[col] < 0:
                    self.logger.warning("Negative weight for column {}: {}", col, weights[col])
                    return False

            # Check if weights sum to a reasonable total (should be close to 1.0)
            total_weight = weights[required_cols].sum()
            if not (
                self.calculator_constant_config.get(
                    "WEIGHT_SUM_MIN", 
                    self.WEIGHT_SUM_MIN) <= total_weight <= self.calculator_constant_config.get("WEIGHT_SUM_MAX", 
                                                                                                self.WEIGHT_SUM_MAX)):
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
        Process historical production data for completed orders. This method:
            - Standardizes column names
            - Prepares mold-machine historical data
            - Validates the schema of prepared data
        """
        
        # Prepare historical data for analysis
        historical_data = self._prepare_mold_machine_historical_data()
        try:
            cols = list(self.sharedDatabaseSchemas_data["historical_records"]['dtypes'].keys())
            logger.info('Validation for historical_data...')
            validate_dataframe(historical_data, cols)
        except Exception as e:
            logger.error("Validation failed for historical_data (expected cols: %s): %s", cols, e)
            raise

        return historical_data

    def _prepare_mold_machine_historical_data(self) -> pd.DataFrame:
        """
        Prepare and filter historical data for analysis using:
            - machineInfo_df: Machine information DataFrame
            - proStatus_df: Production status DataFrame
            - productRecords_df: Product records DataFrame
        """

        # Standardize column names to match expected schema
        proStatus_df = self.proStatus_df.copy()
        proStatus_df.rename(columns={'lastestMachineNo': 'machineNo',
                                     'lastestMoldNo': 'moldNo'
                                     }, inplace=True)
        
        # Filter to completed orders and merge with machine info
        hist = proStatus_df.loc[proStatus_df['itemRemain'] == 0].merge(
            self.machine_info_df[['machineNo', 'machineCode', 'machineName', 'machineTonnage']],
            how='left', 
            on=['machineNo']
        )

        # Prepare product records (don't mutate input DataFrame)
        productRecords_working = self.productRecords_df.copy()
        productRecords_working.rename(columns={'poNote': 'poNo'}, inplace=True)

        df = productRecords_working[self.calculator_constant_config.get(
            "PRODUCT_RECORD_REQUIRED_COLS", self.PRODUCT_RECORD_REQUIRED_COLS)].copy()

        # Optimize filtering with set for O(1) lookups
        hist_po_set = set(hist['poNo'])
        filtered_df = df[df['poNo'].isin(hist_po_set) & (df['itemTotalQuantity'] > 0)].copy()

        return filtered_df
    
    #--------------------------------------------#
    # STEP 3: CALCULATE MOLD-MACHINE PERFORMANCE #
    #--------------------------------------------#
    def _calculate_performance_metrics(self, 
                                       historical_data: pd.DataFrame
                                       ) -> Tuple[pd.DataFrame, List[str]]:
        """
        Calculate performance metrics for each mold-machine combination.   
        This method analyzes historical production data to compute key performance indicators
        such as:
        - Shift NG (defect) rate
        - Shift cavity utilization rate
        - Shift cycle time efficiency
        - Shift capacity utilization rate
        """
        # Calculate performance metrics
        mold_machine_history_summary, invalid_molds = summarize_mold_machine_history(
            historical_data, 
            self.mold_estimated_capacity_df
        )
        
        # Validate schema
        try:
            cols = list(self.sharedDatabaseSchemas_data["mold_machine_history_summary"]['dtypes'].keys())
            self.logger.info('Validating mold_machine_history_summary schema...')
            validate_dataframe(mold_machine_history_summary, cols)
        except Exception as e:
            self.logger.error("Validation failed for mold_machine_history_summary (expected cols: {}): {}", cols, e)
            raise
        
        return mold_machine_history_summary, invalid_molds
    
    #--------------------------------------------#
    # STEP 4: APPLY WEIGHTED SCORING             #
    #--------------------------------------------#
    def _apply_weighted_scoring(self, 
                                mold_machine_history_summary: pd.DataFrame) -> pd.DataFrame:
        """
        Apply weighted scoring based on multiple performance factors.
        
        This method combines multiple performance metrics using learned feature weights
        to produce a composite score for each mold-machine combination. The weights
        reflect the relative importance of each performance factor.
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
        Rank mold-machine combinations to create priority matrix.
        This method:
        - Pivots weighted scores into a matrix format
        - Ranks machines for each mold based on total scores
        - Produces priority rankings (1 = highest priority)
        """
        # Create pivot table with weighted scores
        weighted_results = weighted_scores[
            ['moldNo', 'machineCode', 'total_score']].pivot(
                index="moldNo", 
                columns="machineCode", 
                values="total_score"
                ).fillna(0)

        # Convert scores to priority rankings (1 = best, 2 = second best, etc.)
        priority_matrix = weighted_results.apply(rank_nonzero, axis=1)

        return priority_matrix