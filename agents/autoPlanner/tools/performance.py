import pandas as pd
import numpy as np
from loguru import logger

#----------------------------------#
# Mold-Machine History Propressing #
#----------------------------------#

def summarize_mold_machine_history(
        historical_records: pd.DataFrame,
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