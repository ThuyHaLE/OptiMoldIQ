import pandas as pd
import numpy as np
import warnings
from loguru import logger
from typing import Tuple

##################################################
#           """ Validate DataFrames """          #
##################################################

def validate_pending_records(pending_records: pd.DataFrame) -> None:

    """Validate input DataFrames and their required columns."""

    if pending_records.empty:
        logger.error("Pending DataFrame is empty")
        raise ValueError("Pending DataFrame is empty")

    required_pending_cols = ['itemCode', 'itemQuantity']

    missing_pending_cols = [col for col in required_pending_cols if col not in pending_records.columns]

    if missing_pending_cols:
        logger.error("Missing columns in pending DataFrame: {}", missing_pending_cols)
        raise ValueError(f"Missing columns in pending DataFrame: {missing_pending_cols}")

    # Validate data types and values
    if not pd.api.types.is_numeric_dtype(pending_records['itemQuantity']):
        logger.error("itemQuantity must be numeric")
        raise ValueError("itemQuantity must be numeric")

    if (pending_records['itemQuantity'] <= 0).any():
        logger.warning("Found non-positive quantities in pending items")

def validate_mold_info_df(mold_info_df: pd.DataFrame) -> None:

    """Validate input DataFrames and their required columns."""

    if mold_info_df.empty:
        logger.error("Mold info DataFrame is empty")
        raise ValueError("Mold info DataFrame is empty")

    required_mold_cols = ['isPriority', 'itemCode', 'moldNo', 'moldEstimatedHourCapacity']

    missing_mold_cols = [col for col in required_mold_cols if col not in mold_info_df.columns]

    if missing_mold_cols:
        logger.error("Missing columns in mold_info_df: {}", missing_mold_cols)
        raise ValueError(f"Missing columns in mold_info_df: {missing_mold_cols}")

    # Validate data types and values
    if not pd.api.types.is_numeric_dtype(mold_info_df['moldEstimatedHourCapacity']):
        logger.error("moldEstimatedHourCapacity must be numeric")
        raise ValueError("moldEstimatedHourCapacity must be numeric")
    

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
#      """ Mold Information Propressing """      #
##################################################

def compute_hourly_capacity(df: pd.DataFrame, 
                            efficiency, loss) -> pd.DataFrame:

    """
    Calculate mold production capacity per hour.
    
    Args:
        df: Mold info dataframe with columns 'moldSettingCycle', 'moldCavityStandard'
        
    Returns:
        Updated dataframe with capacity calculations
    """

    if df.empty:
        return df
        
    # Validate required columns
    required_cols = ['moldSettingCycle', 'moldCavityStandard']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
        
    df = df.copy()
    
    # Handle zero or negative values
    df['moldSettingCycle'] = df['moldSettingCycle'].replace(0, np.nan)
    df['moldCavityStandard'] = df['moldCavityStandard'].replace(0, np.nan)
    
    # Calculate capacities with error handling
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        df['moldFullHourCapacity'] = (
            3600 / df['moldSettingCycle'] * df['moldCavityStandard']
        ).fillna(0).round().astype('Int64')
        
        df['moldEstimatedHourCapacity'] = (
            df['moldFullHourCapacity'] * (efficiency - loss)
        ).fillna(0).round().astype('Int64')
    
    return df

def assign_priority_mold(df: pd.DataFrame) -> pd.DataFrame:

    """
    Mark the mold with the highest capacity for each itemCode.
    
    Args:
        df: DataFrame with mold information
        
    Returns:
        DataFrame with 'isPriority' column added
    """

    if df.empty:
        return df
        
    required_cols = ['itemCode', 'moldEstimatedHourCapacity', 'acquisitionDate']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
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
            
        max_capacity = group['moldEstimatedHourCapacity'].max()
        group_max = group[group['moldEstimatedHourCapacity'] == max_capacity]
        
        if len(group_max) == 1:
            idx = group_max.index[0]
        else:
            # Handle NaT values in acquisitionDate
            valid_dates = group_max.dropna(subset=['acquisitionDate'])
            if not valid_dates.empty:
                idx = valid_dates['acquisitionDate'].idxmax()
            else:
                idx = group_max.index[0]  # Fallback to first if no valid dates
        
        df.loc[idx, 'isPriority'] = True
    
    return df

def process_mold_info(moldSpecificationSummary_df: pd.DataFrame, 
                      moldInfo_df: pd.DataFrame,
                      efficiency,
                      loss) -> pd.DataFrame:

        """
        Process and combine mold information from specification and detail datasets.
        
        Args:
            moldSpecificationSummary_df: Summary table mapping product codes to mold lists
            moldInfo_df: Detailed table with mold technical information
            
        Returns:
            Merged DataFrame with mold details and priority indicators
        """

        if moldSpecificationSummary_df.empty or moldInfo_df.empty:
            return pd.DataFrame()
            
        # Calculate hourly capacity
        updated_capacity_moldInfo_df = compute_hourly_capacity(moldInfo_df, efficiency, loss)
                                     
        # Process moldList column safely
        moldSpec_df = moldSpecificationSummary_df.copy()
        
        # Handle missing or null moldList values
        moldSpec_df['moldList'] = moldSpec_df['moldList'].fillna('')
        moldSpec_df['moldList'] = moldSpec_df['moldList'].astype(str)
        
        # Split moldList and explode
        moldSpec_df['moldList'] = moldSpec_df['moldList'].str.split('/')
        moldSpec_df_exploded = moldSpec_df.explode('moldList', ignore_index=True)
        
        # Clean up moldList values
        moldSpec_df_exploded['moldList'] = moldSpec_df_exploded['moldList'].str.strip()
        moldSpec_df_exploded = moldSpec_df_exploded[moldSpec_df_exploded['moldList'] != '']
        
        moldSpec_df_exploded.rename(columns={'moldList': 'moldNo'}, inplace=True)
        
        # Merge with mold info
        merge_cols = ['moldNo', 'moldName', 'acquisitionDate', 'moldCavityStandard',
                     'moldSettingCycle', 'machineTonnage', 'moldFullHourCapacity',
                     'moldEstimatedHourCapacity']
        
        available_cols = [col for col in merge_cols if col in updated_capacity_moldInfo_df.columns]
        
        result_df = moldSpec_df_exploded.merge(
            updated_capacity_moldInfo_df[available_cols],
            how='left', on=['moldNo']
        )
        
        # Mark priority molds
        return assign_priority_mold(result_df)

def calculate_mold_lead_times(pending_records: pd.DataFrame, 
                              mold_info_df: pd.DataFrame) -> pd.DataFrame:

    """Calculate lead times for items that can be produced."""

    # Merge with mold information
    pending_with_mold_info = pending_records.merge(mold_info_df[['itemCode', 'moldNo', 'moldName',
                                                               'moldCavityStandard', 'moldSettingCycle' ,
                                                               'moldFullHourCapacity', 'moldEstimatedHourCapacity']],
                                                   how = 'left', on=['itemCode'])

    # Calculate aggregated metrics by mold
    agg_dict = {
        'totalQuantity': ('itemQuantity', 'sum'),
        'moldEstimatedHourCapacity': ('moldEstimatedHourCapacity', 'mean'),
    }

    lead_time_df = pending_with_mold_info.groupby(['moldNo']).agg(**agg_dict).reset_index()

    # Calculate lead time in days
    HOURS_PER_DAY = 24
    lead_time_df['moldLeadTime'] = ((lead_time_df['totalQuantity'] / lead_time_df['moldEstimatedHourCapacity']) / HOURS_PER_DAY).round().astype('int')

    return lead_time_df

def split_pending_by_mold_availability(pending_records: pd.DataFrame, 
                                       mold_info_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:

    """Split pending items into those with and without suitable molds."""

    available_items = set(mold_info_df['itemCode'].unique())
    pending_items = set(pending_records['itemCode'].unique())
    missing_items = pending_items - available_items

    if missing_items:
        logger.warning("No suitable molds found for items: {}. Consider checking mold priority or mapping data.", 
                       sorted(list(missing_items)))

    pending_without_molds = pending_records[pending_records['itemCode'].isin(missing_items)].copy()
    pending_with_molds = pending_records[~pending_records['itemCode'].isin(missing_items)].copy()

    return pending_with_molds, pending_without_molds

##################################################
#    """ Mold-Machine History Propressing """    #
##################################################

def summarize_mold_machine_history(hist: pd.DataFrame,
                                   moldInfo_df: pd.DataFrame,
                                   efficiency: float = 0.85,
                                   loss: float = 0.03) -> pd.DataFrame:

        """ 
        Calculate historical production performance by mold and machine.

        Args:
            hist (pd.DataFrame): Historical production data.
            moldInfo_df (pd.DataFrame): Mold information dataframe.
            efficiency (float): Target efficiency rate.
            loss (float): Expected loss rate.

        Returns:
            pd.DataFrame: Performance statistics for each (moldNo, machineCode) pair.
        """

        required_cols = ['moldNo', 'machineCode', 
                         'shiftNGRate', 'shiftCavityRate', 
                         'shiftCycleTimeRate', 'shiftCapacityRate']

        # Step 1: Group by mold & machine to aggregate
        summary = hist.groupby(['moldNo', 'machineCode']).agg(
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
            moldInfo_df[['moldNo', 'moldCavityStandard', 'moldSettingCycle', 'machineTonnage']],
            on='moldNo',
            how='left'
        )

        # Step 3: Fill NA to avoid division/operation errors
        result_df['moldCavityStandard'] = result_df['moldCavityStandard'].fillna(0)
        result_df['moldSettingCycle'] = result_df['moldSettingCycle'].fillna(0)

        # Step 4: Calculate theoretical full capacity and estimated capacity (adjusted by efficiency/loss)
        result_df['moldFullHourCapacity'] = np.where(
            result_df['moldSettingCycle'] > 0,
            (3600 / result_df['moldSettingCycle']) * result_df['moldCavityStandard'],
            np.nan
        ).round().astype('int')

        result_df['moldEstimatedHourCapacity'] = (result_df['moldFullHourCapacity'] * (efficiency - loss)).round().astype('int')

        # Step 5: Calculate performance metrics
        result_df['shiftNGRate'] = np.where(
            result_df['totalQuantity'] > 0,
            ((result_df['totalQuantity'] - result_df['totalGoodQuantity']) / result_df['totalQuantity']) / result_df['shiftsUsed'],
            np.nan
        )

        result_df['shiftCavityRate'] = np.where(
            result_df['moldCavityStandard'] > 0,
            result_df['shiftCavities'] / result_df['moldCavityStandard'],
            np.nan
        )

        result_df['shiftCycleTimeRate'] = np.where(
            (result_df['shiftShots'] > 0) & (result_df['moldSettingCycle'] > 0),
            ((8 * 3600) / result_df['shiftShots']) / result_df['moldSettingCycle'],
            np.nan
        )

        result_df['shiftCapacityRate'] = np.where(
            (result_df['moldEstimatedHourCapacity'] > 0) & (result_df['shiftsUsed'] > 0),
            (result_df['totalGoodQuantity'] / result_df['shiftsUsed']) / (result_df['moldEstimatedHourCapacity'] * 8),
            np.nan
        )

        return result_df[required_cols]

##################################################
# """ Mold-Item Plan A Matching Propressing """  #
##################################################

def mold_item_plan_a_matching(pending_records: pd.DataFrame, 
                              mold_info_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:

    """
    Match pending items with molds and calculate lead times.

    Args:
        pending_records: DataFrame with pending items (must have 'itemCode' and 'itemQuantity' columns)
        mold_info_df: DataFrame with mold information (must have 'isPriority', 'itemCode', etc.)

    Returns:
        Tuple of (lead_time_df, pending_without_molds):
            - lead_time_df: DataFrame with mold lead times
            - pending_without_molds: DataFrame with items that couldn't be matched

    Raises:
        ValueError: If input validation fails
    """

    # Input validation
    validate_pending_records(pending_records)
    validate_mold_info_df(mold_info_df)

    # Filter priority molds
    mold_plan_a = mold_info_df[mold_info_df['isPriority'] == True].copy()

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