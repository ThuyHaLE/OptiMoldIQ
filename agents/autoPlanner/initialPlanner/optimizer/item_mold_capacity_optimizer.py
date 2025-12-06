import pandas as pd
import numpy as np
import warnings
from typing import List, Dict
from loguru import logger
from agents.decorators import validate_init_dataframes
from datetime import datetime
from agents.utils import ConfigReportMixin

# Decorator to validate DataFrames are initialized with the correct schema
# This ensures that required DataFrames have all necessary columns before processing
@validate_init_dataframes(lambda self: {
    "moldInfo_df": list(self.databaseSchemas_data['staticDB']['moldInfo']['dtypes'].keys()),
    "moldSpecificationSummary_df": list(self.databaseSchemas_data['staticDB']['moldSpecificationSummary']['dtypes'].keys()),
})

@validate_init_dataframes(lambda self: {
    "mold_stability_index": list(self.sharedDatabaseSchemas_data["mold_stability_index"]['dtypes'].keys()),
})

class ItemMoldCapacityOptimizer(ConfigReportMixin):

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

    Parameters:
        mold_stability_index: Historical mold stability index
        moldSpecificationSummary_df: Summary table mapping product codes to mold lists
        moldInfo_df: Detailed table with mold technical information
        efficiency: Production efficiency factor (0.0 to 1.0)
        loss: Production loss factor (0.0 to 1.0)
        databaseSchemas_data: database schema for validation.
        sharedDatabaseSchemas_data: shared database schema for validation.
    """

    def __init__(self,
                 mold_stability_index: pd.DataFrame,
                 moldSpecificationSummary_df: pd.DataFrame,
                 moldInfo_df: pd.DataFrame,
                 efficiency: float,
                 loss: float,
                 databaseSchemas_data: Dict,
                 sharedDatabaseSchemas_data: Dict
                 ):
        
        """
        Process and combine mold information from specification and detail datasets.

        """
        
        self._capture_init_args()

        # Initialize logger with class name for better tracking
        self.logger = logger.bind(class_="ItemMoldCapacityOptimizer")

        # Load database schema configuration for column validation
        self.databaseSchemas_data = databaseSchemas_data

        # Load shared database schema configuration for column validation
        self.sharedDatabaseSchemas_data = sharedDatabaseSchemas_data

        self.mold_stability_index = mold_stability_index
        self.moldSpecificationSummary_df = moldSpecificationSummary_df
        self.moldInfo_df = moldInfo_df
        self.efficiency = efficiency
        self.loss = loss

    def process(self) -> pd.DataFrame:

        """
        Process and combine mold information from specification and detail datasets.
        """

        self.logger.info("Starting ItemMoldCapacityOptimizer ...")

        if self.moldSpecificationSummary_df.empty or self.moldInfo_df.empty:
            self.logger.error("Invalid dataframe with moldSpecificationSummary or moldInfo !!!")
            raise
        
        # Generate config header using mixin
        timestamp_start = datetime.now()
        timestamp_str = timestamp_start.strftime("%Y-%m-%d %H:%M:%S")
        config_header = self._generate_config_report(timestamp_str)

        optimization_log_lines = [config_header]
        optimization_log_lines.append(f"--Processing Summary--")
        optimization_log_lines.append(f"⤷ {self.__class__.__name__} results:")

        # Identify invalid molds (in historical records but not in moldInfo)
        invalid_molds = self.mold_stability_index[~self.mold_stability_index['moldNo'].isin(self.moldInfo_df['moldNo'])]['moldNo'].to_list()
        optimization_log_lines.append(f"Found {len(invalid_molds)} mold(s) not in moldInfo (need double-check or update information): {invalid_molds}")

        # Identify unused molds (in moldInfo but not in historical records)
        unused_molds = self.moldInfo_df[~self.moldInfo_df['moldNo'].isin(self.mold_stability_index['moldNo'])]['moldNo'].tolist()
        optimization_log_lines.append(f"Found {len(unused_molds)} mold(s) not in historical data (never used): {unused_molds}")

        # Merge used and unused molds with capacity calculations
        optimization_log_lines.append(f"Start process with efficiency: {self.efficiency} - loss: {self.loss}")
        updated_capacity_moldInfo_df = ItemMoldCapacityOptimizer.merge_with_unused_molds(
            self.moldInfo_df, unused_molds, self.mold_stability_index, self.efficiency, self.loss
        )

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

        # Define columns for merging
        merge_cols = [
            'moldNo', 'moldName', 'acquisitionDate', 'moldCavityStandard',
            'moldSettingCycle', 'machineTonnage', 'theoreticalMoldHourCapacity',
            'balancedMoldHourCapacity'
        ]

        # Filter available columns
        available_cols = [col for col in merge_cols if col in updated_capacity_moldInfo_df.columns]

        # Merge specification data with mold details
        merged_df = moldSpec_df_exploded.merge(
            updated_capacity_moldInfo_df[available_cols],
            how='left',
            on=['moldNo']
        )

        # Assign priority molds for each item code
        result_df = ItemMoldCapacityOptimizer.assign_priority_mold(merged_df)

        self.logger.info("✅ Process finished!!!")
        
        # Calculate processing time
        timestamp_end = datetime.now()
        processing_time = (timestamp_end - timestamp_start).total_seconds()

        # Add summary statistics
        optimization_log_lines.append(f"--Assignment Results--")
        optimization_log_lines.append(f"⤷ Processing time: {processing_time:.2f} seconds")
        optimization_log_lines.append(f"⤷ End time: {timestamp_end.strftime('%Y-%m-%d %H:%M:%S')}")

        optimization_log_lines.append(f"--Priority Mold Assignment--")
        optimization_log_lines.append(f"⤷ Total: {len(result_df)} records, {result_df['itemCode'].nunique()} items")
        optimization_log_lines.append(f"⤷ Priority molds: {result_df['isPriority'].sum()}/{len(result_df)}")
        optimization_log_lines.append(f"⤷ Coverage: {(result_df.groupby('itemCode')['isPriority'].sum() > 0).sum()}/{result_df['itemCode'].nunique()} items")
        
        optimization_log_lines.append("Process finished!!!")

        optimization_log_str = "\n".join(optimization_log_lines)

        return invalid_molds, result_df, optimization_log_str

    @staticmethod
    def compute_hourly_capacity(df: pd.DataFrame, 
                                efficiency: float, loss: float) -> pd.DataFrame:

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
                3600 / df['moldSettingCycle'] * df['moldCavityStandard']
            ).fillna(0).round(2)

            # Estimated capacity considering efficiency and loss
            df['estimatedMoldHourCapacity'] = (
                df['theoreticalMoldHourCapacity'] * (efficiency - loss)
            ).fillna(0).round(2)

            # Ensure non-negative values
            df['estimatedMoldHourCapacity'] = df['estimatedMoldHourCapacity'].clip(lower=0)

            # Balanced capacity (currently same as estimated) if historical mold stability index not available
            df['balancedMoldHourCapacity'] = df['estimatedMoldHourCapacity']

        return df

    @staticmethod
    def merge_with_unused_molds(moldInfo_df: pd.DataFrame,
                                unused_molds: List[str],
                                used_molds_df: pd.DataFrame,
                                efficiency: float,
                                loss: float) -> pd.DataFrame:

        """
        Merge unused molds with used molds data.

        Args:
            moldInfo_df: Complete mold information dataframe
            unused_molds: List of unused mold numbers
            used_molds_df: DataFrame of historically used molds
            efficiency: Production efficiency factor
            loss: Production loss factor

        Returns:
            Combined dataframe with all molds
        """

        # Define merge columns
        merge_cols = [
            'moldNo', 'moldName', 'acquisitionDate', 'machineTonnage',
            'moldCavityStandard', 'moldSettingCycle', 'theoreticalMoldHourCapacity',
            'estimatedMoldHourCapacity', 'balancedMoldHourCapacity'
        ]

        # Calculate capacity for all molds first
        capacity_df = ItemMoldCapacityOptimizer.compute_hourly_capacity(moldInfo_df, efficiency, loss)

        # Filter only unused molds and select required columns
        available_merge_cols = [col for col in merge_cols if col in capacity_df.columns]
        partial_df = capacity_df.loc[
            capacity_df['moldNo'].isin(unused_molds), available_merge_cols
        ]

        # Create empty dataframe with same structure as used_molds_df
        empty_df = pd.DataFrame(columns=used_molds_df.columns)

        # Reindex unused molds to match used molds structure
        unused_molds_df = partial_df.reindex(columns=empty_df.columns, fill_value=None)

        # Combine all molds
        if used_molds_df.empty:
            all_molds_df = unused_molds_df.copy()
        else:
            all_molds_df = pd.concat([used_molds_df, unused_molds_df], ignore_index=True)

        return all_molds_df

    @staticmethod
    def assign_priority_mold(df: pd.DataFrame) -> pd.DataFrame:

        """
        Mark the mold with the highest capacity for each itemCode.

        In case of tie in capacity, selects the mold with the latest acquisition date.

        Args:
            df: DataFrame with mold information

        Returns:
            DataFrame with 'isPriority' column added

        Raises:
            ValueError: If required columns are missing
        """

        if df.empty:
            return df

        required_cols = ['itemCode', 'balancedMoldHourCapacity', 'acquisitionDate']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            logger.error("Missing required columns: {}", missing_cols)
            raise ValueError(f"Missing required columns: {missing_cols}")

        df = df.copy()
        df['isPriority'] = False

        # Convert acquisitionDate to datetime if not already
        if not pd.api.types.is_datetime64_any_dtype(df['acquisitionDate']):
            df['acquisitionDate'] = pd.to_datetime(df['acquisitionDate'], errors='coerce')

        # Group by itemCode and find priority molds
        for itemCode, group in df.groupby('itemCode'):
            if group.empty:
                continue

            # Find maximum capacity
            max_capacity = group['balancedMoldHourCapacity'].max()

            # Handle case where max_capacity is NaN or 0
            if pd.isna(max_capacity) or max_capacity <= 0:
                # If no valid capacity, select first mold as fallback
                idx = group.index[0]
            else:
                # Get all molds with maximum capacity
                group_max = group[group['balancedMoldHourCapacity'] == max_capacity]

                if len(group_max) == 1:
                    idx = group_max.index[0]
                else:
                    # Handle ties: select mold with latest acquisition date
                    valid_dates = group_max.dropna(subset=['acquisitionDate'])
                    if not valid_dates.empty:
                        idx = valid_dates['acquisitionDate'].idxmax()
                    else:
                        # Fallback to first if no valid dates
                        idx = group_max.index[0]

            df.loc[idx, 'isPriority'] = True

        return df