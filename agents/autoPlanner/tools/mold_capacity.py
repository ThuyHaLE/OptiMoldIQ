import pandas as pd
from loguru import logger
from typing import Tuple

#-------------------------------------#
# Mold Estimated Capacity Propressing #
#-------------------------------------#

def calculate_mold_lead_times(
        pending_records: pd.DataFrame,
        mold_estimated_capacity_df: pd.DataFrame
        ) -> pd.DataFrame:

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

def split_pending_by_mold_availability(
        pending_records: pd.DataFrame, 
        mold_estimated_capacity_df: pd.DataFrame
        ) -> Tuple[pd.DataFrame, pd.DataFrame]:

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