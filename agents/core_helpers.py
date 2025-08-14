import pandas as pd
import numpy as np
from loguru import logger
from typing import Tuple

##################################################
#     """ Machine Information Propressing """    #
##################################################

def check_newest_machine_layout(df: pd.DataFrame) -> pd.DataFrame:

    """
    Filter active machine layouts where 'layoutEndDate' is null.
    
    Args:
        df: DataFrame containing machine layout history
        
    Returns:
        Filtered DataFrame with only current machine layouts
    """

    if df.empty:
        return df
        
    machine_info_fields = ['machineNo', 'machineCode', 'machineName', 
                            'manufacturerName', 'machineTonnage']
    
    # Filter available fields
    available_fields = [field for field in machine_info_fields if field in df.columns]
    
    if 'layoutEndDate' not in df.columns:
        return df[available_fields]
        
    result = df[df['layoutEndDate'].isna()][available_fields]
    return result

##################################################
#  """ Mold Estimated Capacity Propressing """   #
##################################################

def calculate_mold_lead_times(pending_records: pd.DataFrame,
                              mold_estimated_capacity_df: pd.DataFrame) -> pd.DataFrame:

    """Calculate lead times for items that can be produced."""

    if pending_records.empty:
        logger.error("Pending DataFrame is empty")
        raise ValueError("Pending DataFrame is empty")
    
    if mold_estimated_capacity_df.empty:
        logger.error("Mold info DataFrame is empty")
        raise ValueError("Mold info DataFrame is empty")

    if (pending_records['itemQuantity'] <= 0).any():
        logger.warning("Found non-positive quantities in pending items")

    # Merge with mold information
    pending_with_mold_info = pending_records.merge(
        mold_estimated_capacity_df[['itemCode', 'moldNo', 'moldName',
                                    'moldCavityStandard', 'moldSettingCycle' ,
                                    'balancedMoldHourCapacity']],
                                    how = 'left', 
                                    on=['itemCode'])

    # Calculate aggregated metrics by mold
    agg_dict = {
        'totalQuantity': ('itemQuantity', 'sum'),
        'balancedMoldHourCapacity': ('balancedMoldHourCapacity', 'mean'),
    }

    lead_time_df = pending_with_mold_info.groupby(['itemCode', 'moldNo']).agg(**agg_dict).reset_index()

    # Calculate lead time in days
    HOURS_PER_DAY = 24
    lead_time_df['moldLeadTime'] = (
    ((lead_time_df['totalQuantity'] / lead_time_df['balancedMoldHourCapacity']) / HOURS_PER_DAY)
    .round()
    .astype('int')
    .replace(0, 1)
)

    return lead_time_df

def split_pending_by_mold_availability(pending_records: pd.DataFrame, 
                                       mold_estimated_capacity_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:

    """Split pending items into those with and without suitable molds."""

    if pending_records.empty:
        logger.error("Pending DataFrame is empty")
        raise ValueError("Pending DataFrame is empty")
    
    if mold_estimated_capacity_df.empty:
        logger.error("Mold info DataFrame is empty")
        raise ValueError("Mold info DataFrame is empty")

    if (pending_records['itemQuantity'] <= 0).any():
        logger.warning("Found non-positive quantities in pending items")

    available_items = set(mold_estimated_capacity_df['itemCode'].unique())
    pending_items = set(pending_records['itemCode'].unique())
    missing_items = pending_items - available_items

    if missing_items:
        logger.warning("No suitable molds found for items: {}. Consider checking mold priority or mapping data.", 
                       sorted(list(missing_items)))

    pending_without_molds = pending_records[pending_records['itemCode'].isin(missing_items)].copy()
    pending_with_molds = pending_records[~pending_records['itemCode'].isin(missing_items)].copy()

    return pending_with_molds, pending_without_molds

##################################################
# """ Mold-Item Plan A Matching Propressing """  #
##################################################

def mold_item_plan_a_matching(pending_records: pd.DataFrame, 
                              mold_estimated_capacity_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:

    """
    Match pending items with molds and calculate lead times.

    Args:
        pending_records: DataFrame with pending items (must have 'itemCode' and 'itemQuantity' columns)
        mold_estimated_capacity_df: DataFrame with mold information (must have 'isPriority', 'itemCode', etc.)

    Returns:
        Tuple of (lead_time_df, pending_without_molds):
            - lead_time_df: DataFrame with mold lead times
            - pending_without_molds: DataFrame with items that couldn't be matched

    Raises:
        ValueError: If input validation fails
    """

    if pending_records.empty:
        logger.error("Pending DataFrame is empty")
        raise ValueError("Pending DataFrame is empty")
    
    if mold_estimated_capacity_df.empty:
        logger.error("Mold info DataFrame is empty")
        raise ValueError("Mold info DataFrame is empty")

    if (pending_records['itemQuantity'] <= 0).any():
        logger.warning("Found non-positive quantities in pending items")

    # Filter priority molds
    mold_plan_a = mold_estimated_capacity_df[mold_estimated_capacity_df['isPriority'] == True].copy()

    if mold_plan_a.empty:
        logger.error("No priority molds found in mold_info_df")
        raise ValueError("No priority molds found in mold_info_df")

    # Identify items with and without suitable molds
    pending_with_molds, pending_without_molds = split_pending_by_mold_availability(pending_records, 
                                                                                   mold_plan_a)

    if pending_with_molds.empty:
        logger.warning("No pending items can be matched with available priority molds")
        return pd.DataFrame(), pending_without_molds

    # Merge with mold information and calculate lead times
    lead_time_df = calculate_mold_lead_times(pending_with_molds, mold_plan_a)

    return lead_time_df, pending_without_molds

##################################################
#    """ Mold-Machine History Propressing """    #
##################################################

def summarize_mold_machine_history(historical_records: pd.DataFrame,
                                   capacity_mold_info_df: pd.DataFrame) -> pd.DataFrame:

        """
        Calculate historical production performance by mold and machine.

        Args:
            historical_records (pd.DataFrame): Historical production data.
            capacity_mold_info_df (pd.DataFrame): Mold information dataframe.
            efficiency (float): Target efficiency rate.
            loss (float): Expected loss rate.

        Returns:
            pd.DataFrame: Performance statistics for each (moldNo, machineCode) pair.
        """

        # Step 1: Group by mold & machine to aggregate
        summary = historical_records.groupby(['moldNo', 'machineCode']).agg(
            shiftsUsed=('workingShift', 'count'),
            totalQuantity=('itemTotalQuantity', 'sum'),
            totalGoodQuantity=('itemGoodQuantity', 'sum'),
            latestDate=('recordDate', 'max'),
            oldestDate=('recordDate', 'min'),
            totalShots=('moldShot', 'sum'),
            shiftShots=('moldShot', 'mean'),
            shiftCavities=('moldCavity', 'mean'),
        ).reset_index()

        # Step 2: Merge with mold info
        result_df = summary.merge(
            capacity_mold_info_df[['moldNo', 'moldCavityStandard', 'moldSettingCycle', 
                                   'machineTonnage', 'balancedMoldHourCapacity']],
            on='moldNo',
            how='left'
        )

        # Step 2: Merge with mold info
        result_df = summary.merge(
            capacity_mold_info_df[['moldNo', 'moldCavityStandard', 'moldSettingCycle', 
                                   'machineTonnage', 'balancedMoldHourCapacity']],
            on='moldNo',
            how='left'
        )

        # Step 3: Calculate performance metrics
        result_df['shiftNGRate'] = np.where(
            result_df['totalQuantity'] > 0,
            ((result_df['totalQuantity'] - result_df['totalGoodQuantity']) / result_df['totalQuantity']) / result_df['shiftsUsed'],
            np.nan
        )

        # Handle NA values explicitly using pandas.notna()
        result_df['shiftCavityRate'] = np.where(
            (pd.notna(result_df['moldCavityStandard'])) & (result_df['moldCavityStandard'] > 0),
            result_df['shiftCavities'] / result_df['moldCavityStandard'],
            np.nan
        )

        result_df['shiftCycleTimeRate'] = np.where(
            (pd.notna(result_df['shiftShots'])) & (result_df['shiftShots'] > 0) & 
            (pd.notna(result_df['moldSettingCycle'])) & (result_df['moldSettingCycle'] > 0),
            ((8 * 3600) / result_df['shiftShots']) / result_df['moldSettingCycle'],
            np.nan
        )

        result_df['shiftCapacityRate'] = np.where(
            (pd.notna(result_df['balancedMoldHourCapacity'])) & (result_df['balancedMoldHourCapacity'] > 0) & 
            (result_df['shiftsUsed'] > 0),
            (result_df['totalGoodQuantity'] / result_df['shiftsUsed']) / (result_df['balancedMoldHourCapacity'] * 8),
            np.nan
        )

        # Remove duplicates
        summary_required_cols = ['moldNo', 'machineCode', 'shiftNGRate', 'shiftCavityRate',
                                'shiftCycleTimeRate', 'shiftCapacityRate']
        result_df = result_df[summary_required_cols].drop_duplicates().reset_index(drop=True)
        
        # Step 4: Check for invalid molds with NaN values
        summary_check_columns = ['shiftNGRate', 'shiftCavityRate', 'shiftCycleTimeRate', 'shiftCapacityRate']
        
        # Find molds with any NaN values in the check columns
        invalid_mask = result_df[summary_check_columns].isna().any(axis=1)
        invalid_molds = result_df.loc[invalid_mask, 'moldNo'].unique().tolist()
        
        # Log invalid molds (optional)
        if invalid_molds:
            logger.warning("Found {} invalid molds with NaN values: {}", len(invalid_molds), invalid_molds)
            # Remove invalid molds from the result
            clean_result = result_df[~result_df['moldNo'].isin(invalid_molds)]

            # Return both the dataframe and invalid molds list
            return clean_result, invalid_molds
        
        # Return both the dataframe and invalid molds list
        return result_df, invalid_molds

#############################################################
#    """ Mold-Machine compatibility matrix calculator"""    #
#############################################################

def create_mold_machine_compatibility_matrix(machineInfo_df: pd.DataFrame,
                                             moldInfo_df: pd.DataFrame,
                                             validate_data: bool = True) -> pd.DataFrame:
    """
    Create a binary compatibility matrix between molds and machines based on tonnage.

    Parameters
    ----------
    machineInfo_df : pd.DataFrame
        Machine data including 'machineTonnage' and 'machineCode'.
    moldInfo_df : pd.DataFrame
        Mold data including 'moldNo' and 'machineTonnage' (may contain multiple values separated by '/').
    validate_data : bool, default True
        Whether to validate input data and print summary statistics.

    Returns
    -------
    pd.DataFrame
        Binary compatibility matrix:
            - Index: moldNo
            - Columns: machineCode
            - Values: 1 if compatible, 0 if not
    """
    try:
        # 1. Process mold data (split tonnage list)
        mold_info_df = moldInfo_df.copy()
        mold_info_df["machineTonnage"] = mold_info_df["machineTonnage"].astype(str).str.split("/")

        # 2. Process machine data
        machine_info_df = check_newest_machine_layout(machineInfo_df)
        machine_info_df["machineTonnage"] = machine_info_df["machineTonnage"].astype(str)

        # 3. Check for missing data
        if validate_data:
          machine_missing = machine_info_df['machineTonnage'].isna().sum()
          mold_missing = moldInfo_df['machineTonnage'].isna().sum()

          if machine_missing > 0:
              print(f"Warning: {machine_missing} machines have no tonnage information")

          if mold_missing > 0:
              print(f"Warning: {mold_missing} molds have no tonnage information")

          # Check for empty data
          if machine_info_df.empty:
              raise ValueError("Machine data is empty")

          if moldInfo_df.empty:
              raise ValueError("Mold data is empty")

        # 4. Expand molds by tonnage
        tonnage_expanded_df = mold_info_df.explode("machineTonnage", ignore_index=True)

        # 5. Group machines by tonnage and merge
        machine_grouped = (
            machine_info_df.groupby("machineTonnage")["machineCode"]
            .unique()
            .reset_index()
        )
        merged_df = tonnage_expanded_df.merge(
            machine_grouped, on="machineTonnage", how="left"
        ).dropna(subset=["machineCode"])

        if merged_df.empty:
            print("⚠️ No mold-machine compatibility found based on tonnage.")
            return pd.DataFrame()

        # 6. Expand multiple compatible machines per mold-tonnage
        machine_expanded_df = merged_df.explode("machineCode", ignore_index=True)

        # 7. Build binary compatibility matrix
        compatibility_matrix = (
            machine_expanded_df.assign(value=1)
            .pivot_table(index="moldNo", columns="machineCode", values="value", fill_value=0).astype(int)
        )

        return compatibility_matrix

    except Exception as e:
        raise RuntimeError(f"Error creating mold-machine compatibility matrix: {e}")