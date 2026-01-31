# agents/dataPipelineOrchestrator/processors/processor_utils.py

from agents.dataPipelineOrchestrator.configs.output_formats import DataProcessingReport, ProcessingStatus, ErrorType

from typing import Dict, List,  Any
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import os

#-------#
# Utils #
#-------#
def safe_convert(x) -> str:
    """
    Safely convert values to string, handling numeric and null values.
    
    Args:
        x: Value to convert
        
    Returns:
        String representation of the value, or original value if null
    """

    if pd.isna(x):
        return x
    if isinstance(x, (int, float)) and not pd.isna(x):
        return str(int(x))
    return str(x)

def check_null_str(df: pd.DataFrame) -> List:
    """
    Check for string values that should be treated as null/NaN.
    
    Args:
        df: Input dataframe
        
    Returns:
        List of suspect values found in the dataframe
    """

    suspect_values = ['nan', "null", "none", "", "n/a", "na"]
    nan_values = []
    for col in df.columns:
        for uniq in df[col].unique():
            if str(uniq).lower() in suspect_values:
                nan_values.append(uniq)
    return list(set(nan_values))

#---------------------#
# StaticDataProcessor #
#---------------------#
def process_static_database(
        db_path: Path | str,
        db_name: str,
        spec_cases: list[str],
        dtypes: dict[str, Any]) -> DataProcessingReport:

    warning = ""

    def build_metadata(df: pd.DataFrame) -> Dict[str, Any]:
        return {
            "records_processed": len(df),
            "warning": warning,
            "db_path": db_path,
            "db_name": db_name
        }

    try:
        df = pd.read_excel(db_path)
        warning = f"Loaded DataFrame is empty for {db_name}" if df.empty else ""

        if df.empty:
            return DataProcessingReport(
                status=ProcessingStatus.SUCCESS,
                data=df,
                metadata=build_metadata(df)
            )

        if spec_cases:
            try:
                for c in spec_cases:
                    if c in df.columns:
                        df[c] = df[c].map(safe_convert)
            except Exception as e:
                return DataProcessingReport(
                    status=ProcessingStatus.PARTIAL_SUCCESS,
                    data=df,
                    error_type=ErrorType.DATA_PROCESSING_ERROR,
                    error_message=f"Failed to handle special cases: {e}",
                    metadata=build_metadata(df)
                )

        try:
            df = df.astype(dtypes)
        except Exception as e:
            return DataProcessingReport(
                status=ProcessingStatus.PARTIAL_SUCCESS,
                data=df,
                error_type=ErrorType.DATA_PROCESSING_ERROR,
                error_message=f"Failed to apply data type schema: {e}",
                metadata=build_metadata(df)
            )

        df.replace(check_null_str(df), pd.NA, inplace=True)

        df.fillna(pd.NA, inplace=True)

        return DataProcessingReport(
            status=ProcessingStatus.SUCCESS,
            data=df,
            metadata=build_metadata(df)
        )

    except Exception as e:
        return DataProcessingReport(
            status=ProcessingStatus.ERROR,
            data=pd.DataFrame(),
            error_type=ErrorType.FILE_READ_ERROR,
            error_message=f"Failed to read file at {db_path}: {e}",
            metadata=build_metadata(pd.DataFrame())
        )

#----------------------#
# DynamicDataProcessor #
#----------------------#
def get_source_files(
        folder_path: str|Path, 
        name_start: str, 
        file_extension: str) -> DataProcessingReport:

    """
    Get and validate source files from the specified folder.
    """

    try:
        # Find files matching the pattern
        folder_path = Path(folder_path)

        files = [folder_path / f for f in os.listdir(folder_path) 
                 if f.startswith(name_start) and f.endswith(file_extension)]
        
        if not files:
            return DataProcessingReport(
                status=ProcessingStatus.ERROR,
                data=[],
                error_type=ErrorType.FILE_NOT_FOUND,
                error_message=f"No files found matching pattern {name_start}*{file_extension}",
                metadata={
                    "folder_path": folder_path,
                    "name_start": name_start,
                    "file_extension": file_extension
                    }
                )
        
        # Sort files by date (extracted from filename)
        def extract_yyyymm(fname: str) -> int:
            try:
                return int(fname.split('_')[1][:6])
            except Exception:
                return 999999
            
        files_sorted = sorted(files, key=lambda p: extract_yyyymm(p.name))

        return DataProcessingReport(
            status=ProcessingStatus.SUCCESS,
            data=files_sorted,
            metadata={
                "folder_path": folder_path,
                "name_start": name_start,
                "file_extension": file_extension
            }
        )
    
    except Exception as e:
        return DataProcessingReport(
            status=ProcessingStatus.ERROR,
            data=[],
            error_type=ErrorType.FILE_NOT_FOUND,
            error_message=f"Error searching files: {str(e)}",
            metadata={
                "folder_path": folder_path,
                "name_start": name_start,
                "file_extension": file_extension
            }
        )

def process_single_file(
        file_path: Path | str, 
        sheet_name: str,
        file_extension: str, 
        required_fields: List[str]) -> DataProcessingReport:
    
    """
    Process a single Excel file and validate its structure.
    
    Args:
        file_path: Full path to the Excel file
        sheet_name: Name of the sheet to read from
        file_extension: File extension (.xlsb or .xlsx)
        required_fields: List of required column names
        
    Returns:
        Dict containing processing status, data (if successful), and log entries
    """
    
    try:
        # Read Excel file based on extension
        if file_extension == '.xlsb':
            df = pd.read_excel(file_path, sheet_name=sheet_name, engine='pyxlsb')
        elif file_extension == '.xlsx':
            df = pd.read_excel(file_path, sheet_name=sheet_name)
        else:
            return DataProcessingReport(
                status=ProcessingStatus.ERROR,
                data=pd.DataFrame(),
                error_type=ErrorType.UNSUPPORTED_DATA_TYPE,
                error_message=f"Unsupported file extension: {file_extension}",
                metadata={
                    "file_path": file_path,
                    "sheet_name": sheet_name,
                    "file_extension": file_extension, 
                    }
            )

        # Validate that all required fields are present
        missing_fields = [col for col in required_fields if col not in df.columns]
        if missing_fields:
            return DataProcessingReport(
                status=ProcessingStatus.ERROR,
                data=pd.DataFrame(),
                error_type=ErrorType.MISSING_FIELDS,
                error_message=f"Missing required fields: {missing_fields} in {file_path}",
                metadata={
                    "file_path": file_path,
                    "sheet_name": sheet_name,
                    "file_extension": file_extension, 
                    }
            )
        
        # Filter dataframe to only include required columns
        df_filtered = df[required_fields].copy()
        return DataProcessingReport(
            status=ProcessingStatus.SUCCESS,
            data=df_filtered,
            metadata={
                    "file_path": file_path,
                    "sheet_name": sheet_name,
                    "file_extension": file_extension, 
                    }
        )
            
    except Exception as e:
        return DataProcessingReport(
            status=ProcessingStatus.ERROR,
            data=pd.DataFrame(),
            error_type=ErrorType.FILE_READ_ERROR,
            error_message=f"Failed to read file {file_path}: {str(e)}",
            metadata={
                    "file_path": file_path,
                    "sheet_name": sheet_name,
                    "file_extension": file_extension, 
                    }
        )

def merge_and_process_dfs(
        db_name: str, 
        merged_dfs: List[pd.DataFrame], 
        spec_cases: List[str], 
        dtypes: Dict[str,List]) -> DataProcessingReport:
    
    warnings = []
    
    def build_metadata(df: pd.DataFrame) -> Dict[str, Any]:
        return {
            'records_processed': len(df),
            'warning': "\n".join(warnings),
            'db_name': db_name
        }

    try:
        if not merged_dfs:
            return DataProcessingReport(
                status=ProcessingStatus.ERROR,
                data=pd.DataFrame(),
                error_type=ErrorType.FILE_NOT_FOUND,
                error_message=f"No input DataFrames provided for {db_name}",
                metadata=build_metadata(pd.DataFrame()))

        empty_indices = [i for i, df in enumerate(merged_dfs) if df.empty]
        empty_msg = (f"{len(empty_indices)} empty DataFrame(s) found at indices: {empty_indices}"
                     if empty_indices else "")

        if empty_msg:
            warnings.append(empty_msg)

        if len(empty_indices) == len(merged_dfs):
            return DataProcessingReport(
                status=ProcessingStatus.ERROR,
                data=pd.DataFrame(),
                error_type=ErrorType.FILE_NOT_FOUND,
                error_message=f"All merged DataFrames are empty for {db_name}",
                metadata=build_metadata(pd.DataFrame()))

        # Concatenate all dataframes into one
        non_empty_dfs = [df for df in merged_dfs if not df.empty]
        merged_df = pd.concat(non_empty_dfs, ignore_index=True)

        # Remove duplicate rows
        processed_df = merged_df.copy().drop_duplicates()
        duplicates_removed = len(merged_df) - len(processed_df)

        if duplicates_removed > 0:
            warnings.append(f"Removed {duplicates_removed} duplicate rows")

        # Apply data type specific transformations
        if db_name == "productRecords":
            # Standardize column names
            processed_df.rename(columns={"plasticResine": "plasticResin",
                                         "plasticResineCode": "plasticResinCode",
                                         "plasticResineLot": "plasticResinLot"
                                         }, inplace=True)
            
            # Convert Excel serial date to datetime
            # Trade-off:
            # - Assumes recordDate is Excel serial (int64) from .xlsb
            # - Faster & explicit, not universal by design
            if 'recordDate' in processed_df.columns:
                processed_df['recordDate'] = processed_df['recordDate'].apply(
                    lambda x: timedelta(days=x) + datetime(1899,12,30))
            
        if db_name == "purchaseOrders":
            # Convert date columns to datetime
            processed_df[['poReceivedDate', 'poETA']] = processed_df[['poReceivedDate','poETA']].apply(
                lambda col: pd.to_datetime(col, errors='coerce'))

        # Handle special cases for material code columns
        if spec_cases:
            try:
                for c in spec_cases:
                    if c in processed_df.columns:
                        processed_df[c] = processed_df[c].map(safe_convert)
            except Exception as e:
                return DataProcessingReport(
                    status=ProcessingStatus.PARTIAL_SUCCESS,
                    data=processed_df,
                    error_type=ErrorType.DATA_PROCESSING_ERROR,
                    error_message=f"Failed to handle special cases for material code columns: {str(e)}",
                    metadata=build_metadata(processed_df))

        # Apply data type schema
        try:
            processed_df = processed_df.astype(dtypes)
        except Exception as e:
            return DataProcessingReport(
                status=ProcessingStatus.PARTIAL_SUCCESS,
                data=processed_df,
                error_type=ErrorType.DATA_PROCESSING_ERROR,
                error_message=f"Failed to apply data type schema: {str(e)}",
                metadata=build_metadata(processed_df))

        # Standardize working shift values to uppercase
        if db_name == "productRecords":
            if 'workingShift' in processed_df.columns:
                processed_df['workingShift'] = processed_df['workingShift'].str.upper()

        # Replace various null-like string values with pandas NA
        processed_df.replace(check_null_str(processed_df), pd.NA, inplace=True)

        # Fill nan value
        processed_df.fillna(pd.NA, inplace=True)
         
        return DataProcessingReport(
            status=ProcessingStatus.SUCCESS,
            data=processed_df,
            metadata=build_metadata(processed_df))
    
    except Exception as e:
        return DataProcessingReport(
            status=ProcessingStatus.ERROR,
            data=pd.DataFrame(),
            error_type=ErrorType.DATA_PROCESSING_ERROR,
            error_message=f"Failed to merge and process data: {str(e)}",
            metadata=build_metadata(pd.DataFrame()))