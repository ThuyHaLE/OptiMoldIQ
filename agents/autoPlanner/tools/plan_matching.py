import pandas as pd
from loguru import logger
from typing import Tuple
from agents.autoPlanner.tools.mold_capacity import split_pending_by_mold_availability, calculate_mold_lead_times

#---------------------------------------#
# Mold-Item Plan A Matching Propressing #
#---------------------------------------#

def mold_item_plan_a_matching(
        pending_records: pd.DataFrame, 
        mold_estimated_capacity_df: pd.DataFrame
        ) -> Tuple[pd.DataFrame, pd.DataFrame]:

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