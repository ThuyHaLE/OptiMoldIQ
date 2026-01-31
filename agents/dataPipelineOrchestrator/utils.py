# agents/dataPipelineOrchestrator/utils.py

from agents.dataPipelineOrchestrator.configs.output_formats import ProcessingStatus, ErrorType, DataProcessingReport
import hashlib
from pathlib import Path
from typing import Dict, Any
import pandas as pd
import shutil
import os

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

def compare_dataframes(df1: pd.DataFrame,
                       df2: pd.DataFrame) -> DataProcessingReport:
    """Compare two dataframes to detect changes."""
    
    try:
        are_equal = dataframes_equal_fast(df1, df2)
        return DataProcessingReport(
            status=ProcessingStatus.SUCCESS,
            data=are_equal
        )
    except Exception as e:
        return DataProcessingReport(
            status=ProcessingStatus.ERROR,
            data=False,
            error_type=ErrorType.HASH_COMPARISON_ERROR,
            error_message=f"Failed to compare dataframes: {e}",
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
    
def get_disk_usage(folder_path: Path | str, 
                   file_extensions: list[str] | str = '.parquet'
                   ) -> Dict[str, Any]:
    """
    Get disk usage information for monitoring purposes.
    
    Args:
        folder_path: Path to the folder to check
        file_extensions: Single extension (str) or list of extensions (list[str])
                        e.g., '.parquet' or ['.parquet', '.csv', '.json']
    """
    try:
        folder_path = Path(folder_path)
        
        # Normalize file_extensions to list
        if isinstance(file_extensions, str):
            file_extensions = [file_extensions]
        
        # Ensure extensions start with dot
        file_extensions = [
            ext if ext.startswith('.') else f'.{ext}' 
            for ext in file_extensions
        ]

        # Get disk usage for the directory
        disk_stat = shutil.disk_usage(folder_path)
        total_gb = disk_stat.total / (1024 ** 3)
        used_gb = disk_stat.used / (1024 ** 3)
        free_gb = disk_stat.free / (1024 ** 3)
        used_percent = (disk_stat.used / disk_stat.total) * 100

        # Calculate total size of files matching extensions
        files_size_mb = 0
        try:
            files_size_mb = sum(
                os.path.getsize(os.path.join(folder_path, f))
                for f in os.listdir(folder_path)
                if any(f.endswith(ext) for ext in file_extensions)
            ) / (1024 ** 2)
        except:
            pass

        return {
            "total": f"{total_gb:.2f}GB",
            "used": f"{used_gb:.2f}GB",
            "free": f"{free_gb:.2f}GB",
            "used_percent": round(used_percent, 2),
            "files_size_mb": round(files_size_mb, 2)
        }
    except Exception as e:
        return {
            "total": "N/A",
            "used": "N/A",
            "free": "N/A",
            "used_percent": "N/A",
            "files_size_mb": 0
        }
    
def get_memory_usage() -> Dict[str, Any]:
    
    """
    Get current memory usage information.
    """

    try:
        import psutil
        process = psutil.Process()
        return {
            "memory_mb": process.memory_info().rss / 1024 / 1024,
            "memory_percent": process.memory_percent()
        }
    except:
        return {"memory_mb": None, "memory_percent": None}