import pandas as pd
from typing import Dict, List, Any

def generate_progress_report(data_dict: Dict[str, Any], 
                             max_rows_per_df: int = 10,
                             include_shape: bool = True,
                             include_columns: bool = True
                             ) -> List[str]:
    """
    Generate a report as a list of strings from a dictionary containing dataframes
    
    Args:
        data_dict: Dictionary containing dataframes
        max_rows_per_df: Maximum number of rows to display per dataframe
        include_shape: Whether to display the dataframe's shape
        include_columns: Whether to display column names
        
    Returns:
        List of strings for printing the report
    """
    report_lines = []
    
    for key, df in data_dict.items():
        # Section name
        report_lines.append(f"📊 {key.upper()}")
        report_lines.append("-" * 50)
        
        if df is None:
            report_lines.append("   ❌ No data available")
            report_lines.append("")
            continue
            
        if not isinstance(df, pd.DataFrame):
            report_lines.append(f"   ⚠️  Data type: {type(df)}")
            report_lines.append(f"   📄 Content: {str(df)}")
            report_lines.append("")
            continue
        
        # Basic dataframe info
        if include_shape:
            report_lines.append(f"   📏 Shape: {df.shape[0]} rows x {df.shape[1]} columns")
        
        if include_columns and len(df.columns) > 0:
            report_lines.append(f"   📋 Columns: {', '.join(df.columns.astype(str))}")
        
        # Check if dataframe is empty
        if df.empty:
            report_lines.append("   ❌ DataFrame is empty")
            report_lines.append("")
            continue
        
        # Display data preview
        report_lines.append("")
        report_lines.append("   📊 Data Preview:")
        
        # Limit number of rows displayed
        display_df = df.head(max_rows_per_df) if len(df) > max_rows_per_df else df
        
        # Convert dataframe to string and add indentation
        df_string = display_df.to_string(index=True, max_cols=None)
        for line in df_string.split('\n'):
            report_lines.append(f"   {line}")
        
        # Notify if more rows exist
        if len(df) > max_rows_per_df:
            report_lines.append(f"   ... and {len(df) - max_rows_per_df} more rows")
        
        report_lines.append("")
    
    return report_lines