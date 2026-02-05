# agents/dataPipelineOrchestrator/utils.py

from agents.dataPipelineOrchestrator.configs.output_formats import ProcessingStatus, ErrorType, DataProcessingReport
import hashlib
from pathlib import Path
import pandas as pd

def load_existing_data(file_path: Path | str
                       ) -> DataProcessingReport:
    """
    Load existing parquet/excel file if it exists.
    """
    
    file_path = Path(file_path)
    
    # Check file exists
    if not file_path.exists():
        return DataProcessingReport(
            status=ProcessingStatus.ERROR,
            data=pd.DataFrame(),
            error_type=ErrorType.FILE_NOT_FOUND,
            error_message=f"File not found: {file_path}",
        )
    
    # Define supported formats and readers
    file_suffix = file_path.suffix.lower()
    readers = {
        '.xlsb': lambda: pd.read_excel(file_path, engine='pyxlsb'),
        '.xlsx': lambda: pd.read_excel(file_path),
        '.parquet': lambda: pd.read_parquet(file_path),
    }
    
    # Check if file extension is supported
    if file_suffix not in readers:
        return DataProcessingReport(
            status=ProcessingStatus.ERROR,
            data=pd.DataFrame(),
            error_type=ErrorType.UNSUPPORTED_DATA_TYPE,
            error_message=f"Unsupported file extension '{file_suffix}'. "
                         f"Expected: {', '.join(readers.keys())}",
            metadata={"file_path": str(file_path)}
        )
    
    # Load file
    try:
        df = readers[file_suffix]()
        return DataProcessingReport(
            status=ProcessingStatus.SUCCESS,
            data=df,
            metadata={"file_path": str(file_path)}
        )
    except Exception as e:
        return DataProcessingReport(
            status=ProcessingStatus.ERROR,
            data=pd.DataFrame(),
            error_type=ErrorType.FILE_READ_ERROR,
            error_message=f"Failed to read {file_suffix} file: {e}",
        )

def dataframes_equal_fast(df1: pd.DataFrame, 
                          df2: pd.DataFrame) -> bool:
    """
    Fast comparison of dataframes using hash-based comparison.
    
    Strategy:
    1. Quick shape check (fastest)
    2. Hash-based comparison (fast for large data)
    3. Fallback to .equals() if hash fails
    
    Args:
        df1, df2: DataFrames to compare
        
    Returns:
        True if dataframes are equal, False otherwise
    """
    
    # Quick shape comparison first
    if df1.shape != df2.shape:
        return False
    
    # If both empty, they're equal
    if df1.empty and df2.empty:
        return True
    
    # Check column names (after sorting)
    if sorted(df1.columns) != sorted(df2.columns):
        return False
    
    try:
        # Sort both dataframes consistently
        df1_sorted = df1.sort_index(axis=1).sort_values(
            by=list(df1.columns)
        ).reset_index(drop=True)
        
        df2_sorted = df2.sort_index(axis=1).sort_values(
            by=list(df2.columns)
        ).reset_index(drop=True)
        
        # Hash-based comparison
        hash1 = hashlib.md5(
            pd.util.hash_pandas_object(df1_sorted, index=False).values
        ).hexdigest()
        
        hash2 = hashlib.md5(
            pd.util.hash_pandas_object(df2_sorted, index=False).values
        ).hexdigest()
        
        return hash1 == hash2
        
    except Exception:
        # Fallback to standard equals method
        return df1.equals(df2)