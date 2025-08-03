import pandas as pd
import numpy as np
import warnings
from typing import List
from loguru import logger

class HistBasedItemMoldOptimizer:

    """
    A class for optimizing mold production capacity based on historical data.

    This optimizer calculates theoretical and estimated production capacities,
    identifies unused molds, and assigns priority molds for each item code.
    """

    def __init__(self):
        self.logger = logger.bind(class_="HistBasedItemMoldOptimizer")

    @staticmethod
    def compute_hourly_capacity(df: pd.DataFrame, efficiency: float, loss: float) -> pd.DataFrame:

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

            # Balanced capacity (currently same as estimated)
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
        capacity_df = HistBasedItemMoldOptimizer.compute_hourly_capacity(moldInfo_df, efficiency, loss)

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

    def process_mold_info(self,
                         used_molds_df: pd.DataFrame,
                         moldSpecificationSummary_df: pd.DataFrame,
                         moldInfo_df: pd.DataFrame,
                         efficiency: float,
                         loss: float) -> pd.DataFrame:

        """
        Process and combine mold information from specification and detail datasets.

        Args:
            used_molds_df: Historical mold usage data
            moldSpecificationSummary_df: Summary table mapping product codes to mold lists
            moldInfo_df: Detailed table with mold technical information
            efficiency: Production efficiency factor (0.0 to 1.0)
            loss: Production loss factor (0.0 to 1.0)

        Returns:
            Merged DataFrame with mold details and priority indicators
        """

        if moldSpecificationSummary_df.empty or moldInfo_df.empty:
            self.logger.error("Invalid dataframe with moldSpecificationSummary or moldInfo !!!")
            return pd.DataFrame()

        # Identify invalid molds (in historical records but not in moldInfo)
        invalid_molds = used_molds_df[~used_molds_df['moldNo'].isin(moldInfo_df['moldNo'])]['moldNo'].to_list()
        self.logger.info("Found {} mold(s) not in moldInfo (need double-check or update information): {}",
                         len(invalid_molds), invalid_molds)

        # Identify unused molds (in moldInfo but not in historical records)
        unused_molds = moldInfo_df[~moldInfo_df['moldNo'].isin(used_molds_df['moldNo'])]['moldNo'].tolist()
        self.logger.info("Found {} mold(s) not in historical data (never used): {}",
                         len(unused_molds), unused_molds)

        # Merge used and unused molds with capacity calculations
        self.logger.info("Start process with efficiency: {} - loss: {}", efficiency, loss)
        updated_capacity_moldInfo_df = HistBasedItemMoldOptimizer.merge_with_unused_molds(
            moldInfo_df, unused_molds, used_molds_df, efficiency, loss
        )

        # Process moldList column safely
        moldSpec_df = moldSpecificationSummary_df.copy()

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
        result_df = HistBasedItemMoldOptimizer.assign_priority_mold(merged_df)

        self.logger.info("Process finished!!!")

        return invalid_molds, result_df