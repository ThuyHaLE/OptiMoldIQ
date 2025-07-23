import pandas as pd
import numpy as np
import warnings

def calculate_mold_hour_capacity(df: pd.DataFrame, 
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

def note_max_capacity(df: pd.DataFrame) -> pd.DataFrame:

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
        updated_capacity_moldInfo_df = calculate_mold_hour_capacity(moldInfo_df, efficiency, loss)
                                     
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
        
        merged_df = moldSpec_df_exploded.merge(
            updated_capacity_moldInfo_df[available_cols],
            how='left', on=['moldNo']
        )
        
        # Mark priority molds
        return note_max_capacity(merged_df)

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

def get_hist_info(hist: pd.DataFrame,
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

        required_cols = ['moldNo', 'machineCode', 'shiftNGRate', 'shiftCavityRate', 'shiftCycleTimeRate', 'shiftCapacityRate']

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
        merged = summary.merge(
            moldInfo_df[['moldNo', 'moldCavityStandard', 'moldSettingCycle', 'machineTonnage']],
            on='moldNo',
            how='left'
        )

        # Step 3: Fill NA to avoid division/operation errors
        merged['moldCavityStandard'] = merged['moldCavityStandard'].fillna(0)
        merged['moldSettingCycle'] = merged['moldSettingCycle'].fillna(0)

        # Step 4: Calculate theoretical full capacity and estimated capacity (adjusted by efficiency/loss)
        merged['moldFullHourCapacity'] = np.where(
            merged['moldSettingCycle'] > 0,
            (3600 / merged['moldSettingCycle']) * merged['moldCavityStandard'],
            np.nan
        ).round().astype('int')

        merged['moldEstimatedHourCapacity'] = (merged['moldFullHourCapacity'] * (efficiency - loss)).round().astype('int')

        # Step 5: Calculate performance metrics
        merged['shiftNGRate'] = np.where(
            merged['totalQuantity'] > 0,
            ((merged['totalQuantity'] - merged['totalGoodQuantity']) / merged['totalQuantity']) / merged['shiftsUsed'],
            np.nan
        )

        merged['shiftCavityRate'] = np.where(
            merged['moldCavityStandard'] > 0,
            merged['shiftCavities'] / merged['moldCavityStandard'],
            np.nan
        )

        merged['shiftCycleTimeRate'] = np.where(
            (merged['shiftShots'] > 0) & (merged['moldSettingCycle'] > 0),
            ((8 * 3600) / merged['shiftShots']) / merged['moldSettingCycle'],
            np.nan
        )

        merged['shiftCapacityRate'] = np.where(
            (merged['moldEstimatedHourCapacity'] > 0) & (merged['shiftsUsed'] > 0),
            (merged['totalGoodQuantity'] / merged['shiftsUsed']) / (merged['moldEstimatedHourCapacity'] * 8),
            np.nan
        )

        return merged[required_cols]