import pandas as pd

#---------------------------------#
# Machine Information Propressing #
#---------------------------------#

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