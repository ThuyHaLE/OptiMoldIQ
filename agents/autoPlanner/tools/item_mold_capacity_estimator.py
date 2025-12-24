import pandas as pd
import numpy as np
import warnings
from typing import List, Dict, Any
from loguru import logger
from agents.decorators import validate_init_dataframes
from datetime import datetime
from configs.shared.config_report_format import ConfigReportMixin
from dataclasses import dataclass, asdict

@dataclass
class CapacityEstimatorResult:
    mold_estimated_capacity: pd.DataFrame
    invalid_mold_list: List
    log_str: str
    def to_dict(self) -> Dict:
        """Convert dataclass to dictionary for serialization/logging."""
        return asdict(self)
    
# Decorator to validate DataFrames are initialized with the correct schema
# This ensures that required DataFrames have all necessary columns before processing
@validate_init_dataframes(lambda self: {
    "moldInfo_df": list(self.databaseSchemas_data['staticDB']['moldInfo']['dtypes'].keys()),
    "moldSpecificationSummary_df": list(self.databaseSchemas_data['staticDB']['moldSpecificationSummary']['dtypes'].keys()),
    "mold_stability_index": list(self.sharedDatabaseSchemas_data["mold_stability_index"]['dtypes'].keys()),
})
class ItemMoldCapacityEstimator(ConfigReportMixin):

    """
    Optimize mold production capacity using historical stability data.
    Workflow:
    1. Identify molds that have been used before (from the Mold Stability Index).
    2. Determine molds that have never been used by comparing against the full mold list.
    3. For unused molds:
        - Calculate theoretical capacity based on mold and machine specifications.
        - Estimate realistic capacity considering operational constraints.
    4. Merge used and unused mold data into one table.
    5. For each item code, assign priority to molds with the highest estimated capacity.

    This process helps select the most efficient mold for production,
    balancing proven historical performance with potential unused mold capacity.
    """

    SECONDS_PER_HOUR = 3600
    DECIMAL_PRECISION = 2

    # Define merge columns
    ESTIMATED_CAPACITY_DF_COLS = [
        'moldNo', 'moldName', 'acquisitionDate', 'machineTonnage',
        'moldCavityStandard', 'moldSettingCycle', 'theoreticalMoldHourCapacity',
        'estimatedMoldHourCapacity', 'balancedMoldHourCapacity'
    ]

    ASSIGNED_CAPACITY_DF_COLS = [
            'moldNo', 'moldName', 'acquisitionDate', 'moldCavityStandard',
            'moldSettingCycle', 'machineTonnage', 'theoreticalMoldHourCapacity',
            'balancedMoldHourCapacity']

    def __init__(self,
                 databaseSchemas_data: Dict,
                 sharedDatabaseSchemas_data: Dict,
                 mold_stability_index: pd.DataFrame,
                 moldSpecificationSummary_df: pd.DataFrame,
                 moldInfo_df: pd.DataFrame,
                 capacity_constant_config: Dict = {},
                 efficiency: float = 0.85,
                 loss: float = 0.03,
                 ):
        
        """
        Initialize the ItemMoldCapacityEstimator.
            
        Args:
            - databaseSchemas_data: Database schemas for validation
            - sharedDatabaseSchemas_data: Shared database schemas for validation
            - mold_stability_index: Cavity and cycle stability indices for molds based on historical production data
            (produced and shared by HistoricalFeaturesExtractor)
            - moldSpecificationSummary_df: Mold specifications and compatible items
            - moldInfo_df: Detailed mold information including tonnage requirements
            - capacity_constant_config: Constant config for capacity calculator
            - efficiency: Production efficiency factor (0.0 to 1.0)
            - loss: Production loss factor (0.0 to 1.0)
        """
        
        self._capture_init_args()

        # Initialize logger with class name for better tracking
        self.logger = logger.bind(class_="ItemMoldCapacityEstimator")

        self.efficiency = efficiency
        self.loss = loss
        self._validate_calculator_features()
    
        self.databaseSchemas_data = databaseSchemas_data
        self.sharedDatabaseSchemas_data = sharedDatabaseSchemas_data
        self.capacity_constant_config = capacity_constant_config
        
        self.moldSpecificationSummary_df = moldSpecificationSummary_df
        self.moldInfo_df = moldInfo_df
        
        self.mold_stability_index = self._validate_stability_index(mold_stability_index)

    def _validate_calculator_features(self): 
        # Validate efficiency and loss parameters
        if not 0.0 <= self.efficiency <= 1.0:
            raise ValueError(f"Efficiency must be between 0.0 and 1.0, got {self.efficiency}")
        if not 0.0 <= self.loss <= 1.0:
            raise ValueError(f"Loss must be between 0.0 and 1.0, got {self.loss}")
        if self.efficiency <= self.loss:
            raise ValueError(
                f"Efficiency ({self.efficiency}) must be greater than loss ({self.loss})"
            )
        
    def process_estimating(self) -> Dict[str, Any]:

        """
        Process and combine mold information from specification and detail datasets.
        """

        if self.moldSpecificationSummary_df.empty or self.moldInfo_df.empty:
            self.logger.error("Empty dataframe provided with moldSpecificationSummary or moldInfo !!!")
            raise ValueError("Empty dataframe provided with moldSpecificationSummary or moldInfo !!!")        
        
        try:
            self.logger.info("Starting ItemMoldCapacityEstimator ...")

            # Generate config header using mixin
            timestamp_start = datetime.now()
            timestamp_str = timestamp_start.strftime("%Y-%m-%d %H:%M:%S")
            config_header = self._generate_config_report(timestamp_str, required_only=True)

            optimization_log_lines = [config_header]
            optimization_log_lines.append(f"--Processing Summary--")
            optimization_log_lines.append(f"⤷ {self.__class__.__name__} results:")

            # Step 1: Identify molds that have been used before (load from the Mold Stability Index)
            self.logger.info("✓ Step 1: Mold stability index already loaded and validated in __init__")

            # Detect invalid mold list
            invalid_molds = self._detect_invalid_molds()
            optimization_log_lines.append(
                f"Found {len(invalid_molds)} mold(s) not in moldInfo (need double-check or update information): {invalid_molds}")
            
            # Step 2: Determine molds that have never been used by comparing against the full mold list.
            unused_molds = self._detect_unused_molds()
            optimization_log_lines.append(
                f"Found {len(unused_molds)} mold(s) not in historical data (never used): {unused_molds}")

            # Step 3: Consolidate used and unused mold capacity
            optimization_log_lines.append(f"Start process with efficiency: {self.efficiency} - loss: {self.loss}")
            updated_mold_stability_index = self._consolidate_all_molds_capacity(
                self.mold_stability_index, #used molds
                unused_molds)

            # Step 4: Assign molds priority for item code with the highest estimated capacity.
            item_mold_priority_df = self._assign_priority_mold(updated_mold_stability_index)

            # Calculate processing time
            timestamp_end = datetime.now()
            processing_time = (timestamp_end - timestamp_start).total_seconds()

            # Add summary statistics
            optimization_log_lines.append(f"--Assignment Results--")
            optimization_log_lines.append(f"⤷ Processing time: {processing_time:.2f} seconds")
            optimization_log_lines.append(f"⤷ End time: {timestamp_end.strftime('%Y-%m-%d %H:%M:%S')}")
            optimization_log_lines.append(f"--Priority Mold Assignment--")
            optimization_log_lines.append(f"⤷ Total: {len(item_mold_priority_df)} records, {item_mold_priority_df['itemCode'].nunique()} items")
            optimization_log_lines.append(f"⤷ Priority molds: {item_mold_priority_df['isPriority'].sum()}/{len(item_mold_priority_df)}")
            optimization_log_lines.append(f"⤷ Coverage: {(item_mold_priority_df.groupby('itemCode')['isPriority'].sum() > 0).sum()}/{item_mold_priority_df['itemCode'].nunique()} items")

            optimization_log_str = "\n".join(optimization_log_lines)
            self.logger.info("✅ Process finished!!!")

            return CapacityEstimatorResult(
                mold_estimated_capacity = item_mold_priority_df,
                invalid_mold_list = invalid_molds,
                log_str = optimization_log_str
                )
        
        except Exception as e:
            self.logger.error("Failed to process ItemMoldCapacityEstimator: {}", str(e))
            raise RuntimeError(f"ItemMoldCapacityEstimator processing failed: {str(e)}") from e
            
    #-------------------------------------------#
    # STEP 1: LOAD MOLD STABILITY INDEX         #
    #-------------------------------------------#
    def _validate_stability_index(self, mold_stability_index) -> None: 
        if mold_stability_index.empty:
            return self._create_initial_stability_index()
        return mold_stability_index
    
    def _create_initial_stability_index(self) -> pd.DataFrame:
        """Create an empty DataFrame with the required column structure."""
        return pd.DataFrame(columns=list(self.sharedDatabaseSchemas_data["mold_stability_index"]['dtypes'].keys()))
    
    def _detect_invalid_molds(self) -> List[str]:
        """Identify and report invalid molds."""
        invalid_molds = self.mold_stability_index[
            ~self.mold_stability_index['moldNo'].isin(self.moldInfo_df['moldNo'])
        ]['moldNo'].tolist()
        
        has_issues = len(invalid_molds) > 0
        if has_issues:
            self.logger.warning(
                f"Found {len(invalid_molds)} molds in historical data "
                f"but not in moldInfo: {invalid_molds[:5]}..."  # Show first 5
            )
        return invalid_molds

    #-------------------------------------------#
    # STEP 2: DETECT UNUSED MOLDS               #
    #-------------------------------------------#
    def _detect_unused_molds(self) -> None:
        """Identify unused molds (in moldInfo but not in historical records)"""
        return self.moldInfo_df[
            ~self.moldInfo_df['moldNo'].isin(self.mold_stability_index['moldNo'])]['moldNo'].tolist()

    #-------------------------------------------#
    # STEP 3: CONSOLIDATE ALL MOLD CAPACITY     #
    #-------------------------------------------#
    def _consolidate_all_molds_capacity(self,
                                        used_molds_df: pd.DataFrame,
                                        unused_molds: List[str]) -> pd.DataFrame:

        """
        Deal with unused molds:
            - Calculate theoretical capacity based on mold and machine specifications.
            - Estimate realistic capacity considering operational constraints.
        Then, merge unused molds with used molds data.

        Args:
            moldInfo_df: Complete mold information dataframe
            unused_molds: List of unused mold numbers
            used_molds_df: DataFrame of historically used molds
            efficiency: Production efficiency factor
            loss: Production loss factor

        Returns:
            Combined dataframe with all molds
        """        

        # Calculate capacity for all molds first
        capacity_df = self.compute_hourly_capacity(self.moldInfo_df, 
                                                   self.efficiency, 
                                                   self.loss,
                                                   self.capacity_constant_config.get("SECONDS_PER_HOUR", 
                                                                                     self.SECONDS_PER_HOUR),
                                                   self.capacity_constant_config.get("DECIMAL_PRECISION", 
                                                                                     self.DECIMAL_PRECISION)
                                                   )

        # Validate required columns
        merge_cols = self.capacity_constant_config.get(
            "ESTIMATED_CAPACITY_DF_COLS", self.ESTIMATED_CAPACITY_DF_COLS)
        
        missing_cols = [col for col in merge_cols if col not in capacity_df.columns]
        if missing_cols:
            logger.error("Missing required columns: {}", missing_cols)
            raise ValueError(f"Missing required columns: {missing_cols}")
        
        # Filter only unused molds and select required columns
        partial_df = capacity_df[capacity_df['moldNo'].isin(unused_molds)][merge_cols]

        # Create empty dataframe with same structure as used_molds_df
        empty_df = pd.DataFrame(columns=used_molds_df.columns)

        # Reindex unused molds to match used molds structure
        unused_molds_df = partial_df.reindex(columns=empty_df.columns, 
                                             fill_value=None)

        # Combine all molds
        if used_molds_df.empty:
            all_molds_df = unused_molds_df.copy()
        else:
            all_molds_df = pd.concat([used_molds_df, unused_molds_df], 
                                      ignore_index=True)

        return all_molds_df
    
    @staticmethod
    def compute_hourly_capacity(df: pd.DataFrame, 
                                efficiency: float, 
                                loss: float,
                                seconds_per_hour: int = 3600,
                                decimal_precision: int = 2) -> pd.DataFrame:

        """
        Calculate mold production capacity per hour.

        Args:
            df: Mold info dataframe with columns 'moldSettingCycle', 'moldCavityStandard'
            efficiency: Production efficiency factor (0.0 to 1.0)
            loss: Production loss factor (0.0 to 1.0)

        Returns:
            Updated dataframe with capacity calculations

        Raises:
            ValueError: If required columns are missing
        """

        if df.empty:
            return df

        # Validate required columns
        required_cols = ['moldSettingCycle', 'moldCavityStandard']

        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            logger.error("Missing required columns: {}", missing_cols)
            raise ValueError(f"Missing required columns: {missing_cols}")

        df = df.copy()

        # Handle zero or negative values - replace with NaN for proper calculation
        df['moldSettingCycle'] = df['moldSettingCycle'].replace([0, np.inf, -np.inf], np.nan)
        df['moldCavityStandard'] = df['moldCavityStandard'].replace([0, np.inf, -np.inf], np.nan)

        # Calculate capacities with error handling
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")

            # Theoretical capacity: items per hour = (3600 seconds/hour) / (cycle time) * cavities
            df['theoreticalMoldHourCapacity'] = (
                seconds_per_hour / df['moldSettingCycle'] * df['moldCavityStandard']
            ).fillna(0).round(decimal_precision)

            # Estimated capacity considering efficiency and loss
            df['estimatedMoldHourCapacity'] = (
                df['theoreticalMoldHourCapacity'] * (efficiency - loss)
            ).fillna(0).round(decimal_precision)

            # Ensure non-negative values
            df['estimatedMoldHourCapacity'] = df['estimatedMoldHourCapacity'].clip(lower=0)

            # Balanced capacity (currently same as estimated) if historical mold stability index not available
            df['balancedMoldHourCapacity'] = df['estimatedMoldHourCapacity']

        return df

    #--------------------------------------------#
    # STEP 4: ASSIGN MOLD PRIORITY FOR ITEM CODE # 
    #--------------------------------------------#
    def _assign_priority_mold(self,
                              updated_mold_stability_index: pd.DataFrame) -> pd.DataFrame:

        """
        Mark the mold with the highest capacity for each itemCode.
        In case of tie in capacity, selects the mold with the latest acquisition date.
        """

        # Process specification data
        moldSpec_df_exploded = self._expand_item_mold_specifications()

        # Validate required columns
        merge_cols = self.capacity_constant_config.get(
            "ASSIGNED_CAPACITY_DF_COLS", self.ASSIGNED_CAPACITY_DF_COLS)
        
        missing_cols = [col for col in merge_cols if col not in updated_mold_stability_index.columns]
        if missing_cols:
            logger.error("Missing required columns: {}", missing_cols)
            raise ValueError(f"Missing required columns: {missing_cols}")
        
        # Merge specification data with mold details
        merged_df = moldSpec_df_exploded.merge(
            updated_mold_stability_index[merge_cols],
            how='left',
            on=['moldNo']
        )

        if merged_df.empty:
            return merged_df

        item_mold_priority_df = merged_df.copy()

        # Convert acquisitionDate to datetime if not already
        item_mold_priority_df['acquisitionDate'] = pd.to_datetime(
            item_mold_priority_df['acquisitionDate'], errors='coerce'
        )

        # Group by itemCode and find priority molds
        item_mold_priority_df = item_mold_priority_df.sort_values(
            by=['itemCode', 'balancedMoldHourCapacity', 'acquisitionDate'],
            ascending=[True, False, False],
            na_position='last'
        )

        # Mark first record per itemCode as priority
        item_mold_priority_df['isPriority'] = False
        priority_mask = ~item_mold_priority_df.duplicated(subset=['itemCode'], keep='first')
        item_mold_priority_df.loc[priority_mask, 'isPriority'] = True

        return item_mold_priority_df
    
    def _expand_item_mold_specifications(self) -> pd.DataFrame:
        """
        Expand moldList into individual item-mold pairs.
        
        Processes the moldList column by splitting delimited mold numbers
        and creating separate rows for each item-mold combination.
        
        Args:
            moldSpec_df: DataFrame with moldList column (molds separated by '/')
            
        Returns:
            Expanded DataFrame with one row per item-mold pair
        """

        # Process moldList column safely
        moldSpec_df = self.moldSpecificationSummary_df.copy()

        # Handle missing or null moldList values
        moldSpec_df['moldList'] = moldSpec_df['moldList'].fillna('')
        moldSpec_df['moldList'] = moldSpec_df['moldList'].astype(str)

        # Split moldList by '/' delimiter and explode into separate rows
        moldSpec_df['moldList'] = moldSpec_df['moldList'].str.split('/')
        moldSpec_df_exploded = moldSpec_df.explode('moldList', ignore_index=True)

        # Clean up moldList values
        moldSpec_df_exploded['moldList'] = moldSpec_df_exploded['moldList'].str.strip()
        moldSpec_df_exploded = moldSpec_df_exploded[moldSpec_df_exploded['moldList'] != '']

        # Rename for merging
        moldSpec_df_exploded.rename(columns={'moldList': 'moldNo'}, inplace=True)

        return moldSpec_df_exploded