import pandas as pd
from agents.decorators import validate_dataframe
from typing import Tuple, List
pd.set_option('future.no_silent_downcasting', True)

def generate_coords(n_rows: int, 
                    n_cols: int) -> List[Tuple[int, int]]:
    """
    Generate a list of (row, col) coordinate pairs.
    """
    return [(r, c) for r in range(n_rows) for c in range(n_cols)]

def find_best_ncols(num_metrics: int, 
                    min_cols: int = 2, 
                    max_cols: int = 4) -> int:
    """
    Find a suitable number of subplot columns for a given number of metrics.

    Tries to find the smallest number of columns that evenly divides num_metrics.
    Falls back to `max_cols` if none found.
    """
    # Add validation at the start
    if num_metrics <= 0:
        return max_cols
    
    for n in range(min_cols, max_cols + 1):
        if num_metrics % n == 0:
            return n
    return max_cols

def add_new_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add derived features and formatted identifiers to the dataset.

    Features added:
    - itemComponent: concatenation of resin, color, and additive
    - recordInfo: combination of record date and working shift
    - recordMonth: YYYY-MM format
    """

    # Valid data frame
    required_columns = ['recordDate', 'workingShift', 'machineNo', 'machineCode', 'itemCode',
                        'itemName', 'colorChanged', 'moldChanged', 'machineChanged', 'poNote',
                        'moldNo', 'moldShot', 'moldCavity', 'itemTotalQuantity',
                        'itemGoodQuantity', 'itemBlackSpot', 'itemOilDeposit', 'itemScratch',
                        'itemCrack', 'itemSinkMark', 'itemShort', 'itemBurst', 'itemBend',
                        'itemStain', 'otherNG', 'plasticResin', 'plasticResinCode',
                        'plasticResinLot', 'colorMasterbatch', 'colorMasterbatchCode',
                        'additiveMasterbatch', 'additiveMasterbatchCode', 'recordMonth']
    validate_dataframe(df, required_columns)

    # Process data
    df['plasticResin'] = df['plasticResin'].fillna('').astype(str)
    df['colorMasterbatch'] = df['colorMasterbatch'].fillna('').astype(str)
    df['additiveMasterbatch'] = df['additiveMasterbatch'].fillna('').astype(str)

    df['itemComponent'] = (
        df['plasticResin'] + '_' + df['colorMasterbatch'] + '_' + df['additiveMasterbatch']
    )

    df['recordInfo'] = (
        df['recordDate'].dt.strftime('%Y-%m-%d') + '_' + df['workingShift'].astype(str)
    )
    df['recordMonth'] = df['recordDate'].dt.strftime('%Y-%m')

    return df

def detect_not_progress(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Detect non-productive shifts and days based on production data.

    Criteria:
    - Missing PO
    - Missing or zero total quantity

    Returns
    -------
    (pd.DataFrame, pd.DataFrame)
        shift_level : DataFrame with flag `is_shift_not_progress`
        day_level : DataFrame with flag `is_day_not_progress` (≥3 inactive shifts)
    """

    # Valid data frame
    required_columns = ['recordDate', 'workingShift', 'machineNo', 'machineCode', 'itemCode',
                        'itemName', 'colorChanged', 'moldChanged', 'machineChanged', 'poNote',
                        'moldNo', 'moldShot', 'moldCavity', 'itemTotalQuantity',
                        'itemGoodQuantity', 'itemBlackSpot', 'itemOilDeposit', 'itemScratch',
                        'itemCrack', 'itemSinkMark', 'itemShort', 'itemBurst', 'itemBend',
                        'itemStain', 'otherNG', 'plasticResin', 'plasticResinCode',
                        'plasticResinLot', 'colorMasterbatch', 'colorMasterbatchCode',
                        'additiveMasterbatch', 'additiveMasterbatchCode', 'recordMonth',
                        'itemComponent', 'recordInfo']
    validate_dataframe(df, required_columns)

    # --- Shift-level detection ---
    shift_level = df.assign(
        is_shift_not_progress=(
            df['poNote'].isna() |
            df['itemTotalQuantity'].isna() |
            (df['itemTotalQuantity'] == 0)
        )
    )[['machineCode', 'recordDate', 'workingShift', 'recordInfo', 'is_shift_not_progress']]

    # --- Day-level detection ---
    day_level = (
        shift_level.groupby(['machineCode', 'recordDate'])
        .agg(
            recordInfo=('recordInfo', 'first'),
            workingShifts=('recordInfo', 'nunique'),
            offShifts=('is_shift_not_progress', 'sum')
        )
        .reset_index()
        .assign(is_day_not_progress=lambda x: x['offShifts'] >= 3)
    )

    return shift_level, day_level[day_level['is_day_not_progress']]

def detect_process_status(not_progress_df: pd.DataFrame,
                          all_progress_df: pd.DataFrame
                          ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Merge non-progress flags into the main dataset.

    Parameters
    ----------
    not_progress_df : pd.DataFrame
        Subset containing potential non-productive records.
    all_progress_df : pd.DataFrame
        The complete production dataset.
    """

    # Valid data frame
    required_columns = ['recordDate', 'workingShift', 'machineNo', 'machineCode', 'itemCode',
                        'itemName', 'colorChanged', 'moldChanged', 'machineChanged', 'poNote',
                        'moldNo', 'moldShot', 'moldCavity', 'itemTotalQuantity',
                        'itemGoodQuantity', 'itemBlackSpot', 'itemOilDeposit', 'itemScratch',
                        'itemCrack', 'itemSinkMark', 'itemShort', 'itemBurst', 'itemBend',
                        'itemStain', 'otherNG', 'plasticResin', 'plasticResinCode',
                        'plasticResinLot', 'colorMasterbatch', 'colorMasterbatchCode',
                        'additiveMasterbatch', 'additiveMasterbatchCode', 'recordMonth',
                        'itemComponent', 'recordInfo']
    validate_dataframe(not_progress_df, required_columns)
    validate_dataframe(all_progress_df, required_columns)

    # Process data
    shift_level, day_level = detect_not_progress(not_progress_df)

    merged_df = (
        all_progress_df
        .merge(
            day_level[['machineCode', 'recordDate', 'is_day_not_progress']],
            on=['machineCode', 'recordDate'],
            how='left'
        )
        .merge(
            shift_level[['machineCode', 'recordDate', 'workingShift', 'is_shift_not_progress']],
            on=['machineCode', 'recordDate', 'workingShift'],
            how='left'
        )
        .fillna({'is_day_not_progress': False, 'is_shift_not_progress': False})
    )

    return shift_level, day_level, merged_df

def process_not_progress_records(not_progress_df: pd.DataFrame,
                                 all_progress_df: pd.DataFrame,
                                 group_by_month: bool = False
                                 ) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Aggregate metrics for non-progress records (days/shifts).

    Parameters
    ----------
    not_progress_df : pd.DataFrame
        Data containing potential non-progress records.
    all_progress_df : pd.DataFrame
        Full dataset for merging.
    group_by_month : bool, default=False
        If True, group results by recordMonth.
    """

    # Valid data frame
    required_columns = ['recordDate', 'workingShift', 'machineNo', 'machineCode', 'itemCode',
                        'itemName', 'colorChanged', 'moldChanged', 'machineChanged', 'poNote',
                        'moldNo', 'moldShot', 'moldCavity', 'itemTotalQuantity',
                        'itemGoodQuantity', 'itemBlackSpot', 'itemOilDeposit', 'itemScratch',
                        'itemCrack', 'itemSinkMark', 'itemShort', 'itemBurst', 'itemBend',
                        'itemStain', 'otherNG', 'plasticResin', 'plasticResinCode',
                        'plasticResinLot', 'colorMasterbatch', 'colorMasterbatchCode',
                        'additiveMasterbatch', 'additiveMasterbatchCode', 'recordMonth',
                        'itemComponent', 'recordInfo']
    validate_dataframe(not_progress_df, required_columns)
    validate_dataframe(all_progress_df, required_columns)

    # Process data
    shift_level, day_level, merged_df = detect_process_status(not_progress_df, all_progress_df)

    # Aggregate non-progress counts
    grouped_df = (
        merged_df.groupby(['machineCode', 'recordDate', 'recordMonth'])
        .agg(
            notProgressDays=("is_day_not_progress", "mean"),
            notProgressShifts=("is_shift_not_progress", "sum")
        )
        .reset_index()
        .astype({'notProgressDays': int, 'notProgressShifts': int})
    )

    group_cols = ['recordMonth', 'machineCode'] if group_by_month else ['machineCode']
    not_progress_summary = (
        grouped_df.groupby(group_cols)
        .agg(
            notProgressDays=("notProgressDays", "sum"),
            notProgressShifts=("notProgressShifts", "sum")
        )
    )

    return not_progress_summary, merged_df

def calculate_aggregations(df: pd.DataFrame,
                           group_cols: List[str]) -> pd.DataFrame:
    """
    Compute aggregated production metrics, excluding non-productive periods.

    Includes:
    - Unique counts (POs, items, molds, components)
    - Quantities (total, good)
    - Working days/shifts
    - Average NG rate (%)
    """

    # Valid data frame
    required_columns = ['recordDate', 'workingShift', 'machineNo', 'machineCode', 'itemCode',
                        'itemName', 'colorChanged', 'moldChanged', 'machineChanged', 'poNote',
                        'moldNo', 'moldShot', 'moldCavity', 'itemTotalQuantity',
                        'itemGoodQuantity', 'itemBlackSpot', 'itemOilDeposit', 'itemScratch',
                        'itemCrack', 'itemSinkMark', 'itemShort', 'itemBurst', 'itemBend',
                        'itemStain', 'otherNG', 'plasticResin', 'plasticResinCode',
                        'plasticResinLot', 'colorMasterbatch', 'colorMasterbatchCode',
                        'additiveMasterbatch', 'additiveMasterbatchCode', 'recordMonth',
                        'itemComponent', 'recordInfo', 'is_day_not_progress',
                        'is_shift_not_progress']
    validate_dataframe(df, required_columns)

    # Process data
    productive_df = df[~df['is_shift_not_progress']].copy()

    summary = productive_df.groupby(group_cols).agg(
        poNums=("poNote", "nunique"),
        itemNums=("itemCode", "nunique"),
        moldNums=('moldNo', 'nunique'),
        itemComponentNums=('itemComponent', 'nunique'),
        totalMoldShot=('moldShot', 'sum'),
        totalQuantity=('itemTotalQuantity', 'sum'),
        goodQuantity=('itemGoodQuantity', 'sum')
    )

    # Count working days and shifts
    working_days = productive_df[
        ~productive_df['is_day_not_progress']
    ].groupby(group_cols)['recordDate'].nunique()

    working_shifts = productive_df.groupby(group_cols)['recordInfo'].nunique()

    summary['workingDays'] = working_days
    summary['workingShifts'] = working_shifts

    # Calculate NG rate
    summary['avgNGRate'] = (
        (summary['totalQuantity'] - summary['goodQuantity']) /
        summary['totalQuantity'] * 100
    ).fillna(0)

    return summary

def merge_by_fields(main_df: pd.DataFrame,
                    df_1: pd.DataFrame,
                    df_2: pd.DataFrame,
                    use_month: bool = False
                    ) -> Tuple[List[str], pd.DataFrame]:
    """
    Merge multiple aggregated tables by key fields (machineCode, optionally recordMonth).

    Parameters
    ----------
    main_df : pd.DataFrame
        Main dataframe for field reference.
    df_1 : pd.DataFrame
        First summary dataframe (e.g., in-progress).
    df_2 : pd.DataFrame
        Second summary dataframe (e.g., not-progress).
    use_month : bool, default=False
        If True, merge by (recordMonth, machineCode).

    """

    # Valid data frame
    main_required_columns = ['recordDate', 'workingShift', 'machineNo', 'machineCode', 'itemCode',
                             'itemName', 'colorChanged', 'moldChanged', 'machineChanged', 'poNote',
                             'moldNo', 'moldShot', 'moldCavity', 'itemTotalQuantity',
                             'itemGoodQuantity', 'itemBlackSpot', 'itemOilDeposit', 'itemScratch',
                             'itemCrack', 'itemSinkMark', 'itemShort', 'itemBurst', 'itemBend',
                             'itemStain', 'otherNG', 'plasticResin', 'plasticResinCode',
                             'plasticResinLot', 'colorMasterbatch', 'colorMasterbatchCode',
                             'additiveMasterbatch', 'additiveMasterbatchCode', 'recordMonth',
                             'itemComponent', 'recordInfo']
    df1_required_columns = ['poNums', 'itemNums', 'moldNums', 'itemComponentNums', 'totalMoldShot', 'totalQuantity', 
                            'goodQuantity', 'workingDays', 'workingShifts', 'avgNGRate']
    df2_required_columns = ['notProgressDays', 'notProgressShifts']

    validate_dataframe(main_df, main_required_columns)
    validate_dataframe(df_1, df1_required_columns)
    validate_dataframe(df_2, df2_required_columns)

    if 'machineCode' not in main_df.columns:
        raise ValueError(f"'machineCode' not found in main_df.")
    if use_month and 'recordMonth' not in main_df.columns:
        raise ValueError("recordMonth not found in main_df when use_month is True.")
    
    # Process data
    selected_fields = ['recordMonth', 'machineCode'] if use_month else ['machineCode']

    all_names = main_df[selected_fields].drop_duplicates().reset_index(drop=True)

    summary = (
        all_names
        .merge(df_1.reset_index(), on=selected_fields, how='left', suffixes=('', '_in_progress'))
        .merge(df_2.reset_index(), on=selected_fields, how='left', suffixes=('', '_not_progress'))
        .set_index(selected_fields)
        .fillna(0)
        .sort_values('machineCode', ascending=True)
    )

    return summary

def process_machine_based_data(df: pd.DataFrame,
                               group_by_month: bool = False
                               ) -> Tuple[List[str], pd.DataFrame]:
    """
    Full processing pipeline for machine-based production data.

    Steps:
    1. Add derived features.
    2. Identify and aggregate non-progress data.
    3. Filter productive records.
    4. Compute final summary statistics per machine.
    """

    # Valid data frame
    required_columns = ['recordDate', 'workingShift', 'machineNo', 'machineCode', 'itemCode',
                        'itemName', 'colorChanged', 'moldChanged', 'machineChanged', 'poNote',
                        'moldNo', 'moldShot', 'moldCavity', 'itemTotalQuantity',
                        'itemGoodQuantity', 'itemBlackSpot', 'itemOilDeposit', 'itemScratch',
                        'itemCrack', 'itemSinkMark', 'itemShort', 'itemBurst', 'itemBend',
                        'itemStain', 'otherNG', 'plasticResin', 'plasticResinCode',
                        'plasticResinLot', 'colorMasterbatch', 'colorMasterbatchCode',
                        'additiveMasterbatch', 'additiveMasterbatchCode', 'recordMonth']
    validate_dataframe(df, required_columns)

    # Process data
    filtered_df = add_new_features(df)

    # Identify non-productive records
    not_progress_df = filtered_df[
        filtered_df['poNote'].isna() |
        filtered_df['itemTotalQuantity'].isna() |
        (filtered_df['itemTotalQuantity'] == 0)
    ].copy()

    # Merge non-progress indicators
    not_progress_summary, merged_df = process_not_progress_records(
        not_progress_df, filtered_df, group_by_month
    )

    # Filter productive records
    in_progress_df = merged_df[
        ~(merged_df['poNote'].isna() |
          merged_df['itemTotalQuantity'].isna() |
          (merged_df['itemTotalQuantity'] == 0))
    ].copy()

    # Aggregate by machine or machine-month
    group_cols = ['recordMonth', 'machineCode'] if group_by_month else ['machineCode']
    in_progress_summary = calculate_aggregations(in_progress_df, group_cols)

    summary = merge_by_fields(filtered_df, in_progress_summary, not_progress_summary, group_by_month)

    return summary

def process_mold_based_data(main_df: pd.DataFrame,
                            group_by_month: bool = False
                            ) -> Tuple[List[str], pd.DataFrame]:
    """
    Process and summarize production data grouped by mold.

    Includes mold usage statistics such as:
    - Total shots
    - Average cavity count
    - Machine distribution
    - NG quantity and NG rate

    Parameters
    ----------
    main_df : pd.DataFrame
        Main production dataset.
    group_by_month : bool, default=False
        If True, group by (recordMonth, moldNo).
    """

    # Valid data frame
    required_columns = ['recordDate', 'workingShift', 'machineNo', 'machineCode', 'itemCode',
                        'itemName', 'colorChanged', 'moldChanged', 'machineChanged', 'poNote',
                        'moldNo', 'moldShot', 'moldCavity', 'itemTotalQuantity',
                        'itemGoodQuantity', 'itemBlackSpot', 'itemOilDeposit', 'itemScratch',
                        'itemCrack', 'itemSinkMark', 'itemShort', 'itemBurst', 'itemBend',
                        'itemStain', 'otherNG', 'plasticResin', 'plasticResinCode',
                        'plasticResinLot', 'colorMasterbatch', 'colorMasterbatchCode',
                        'additiveMasterbatch', 'additiveMasterbatchCode', 'recordMonth']
    validate_dataframe(main_df, required_columns)

    # Process data
    filtered_df = main_df[main_df['itemTotalQuantity'] > 0][
        ['machineCode', 'moldNo', 'moldShot', 'moldCavity',
         'itemTotalQuantity', 'itemGoodQuantity', 'recordMonth']
    ].copy()

    selected_fields = ['recordMonth', 'moldNo'] if group_by_month else ['moldNo']

    summary = (
        filtered_df.groupby(selected_fields)
        .agg(
            totalShots=('moldShot', 'sum'),
            cavityNums=('moldCavity', 'nunique'),
            avgCavity=('moldCavity', 'mean'),
            cavityList=('moldCavity', 'unique'),
            machineNums=('machineCode', 'nunique'),
            machineList=('machineCode', 'unique'),
            totalQuantity=('itemTotalQuantity', 'sum'),
            goodQuantity=('itemGoodQuantity', 'sum')
        )
        .assign(
            totalNG=lambda x: x['totalQuantity'] - x['goodQuantity'],
            totalNGRate=lambda x: (x['totalQuantity'] - x['goodQuantity']) /
                                  x['totalQuantity'] * 100
        )
        .sort_values('totalShots', ascending=False)
        .reset_index()
    )

    return summary