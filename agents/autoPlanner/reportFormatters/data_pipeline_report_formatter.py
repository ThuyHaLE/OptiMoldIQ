from datetime import datetime
from typing import Dict, Any

def format_bytes(bytes_value):
    """Convert bytes to MB with 3 decimal places"""
    if bytes_value is None:
        return "N/A"
    return f"{bytes_value:.3f} MB"

def format_number(num):
    """Format number with thousands separator"""
    if num is None:
        return "N/A"
    return f"{num:,}"

def format_timestamp(timestamp_str):
    """Format timestamp string to readable format"""
    try:
        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return timestamp_str

def dataclass_to_dict(obj):
    """Convert dataclass or object to dictionary"""
    if hasattr(obj, '__dict__'):
        result = {}
        for key, value in obj.__dict__.items():
            if hasattr(value, '__dict__'):  # Nested dataclass
                result[key] = dataclass_to_dict(value)
            elif isinstance(value, list):
                result[key] = [dataclass_to_dict(item) if hasattr(item, '__dict__') else item for item in value]
            elif isinstance(value, dict):
                result[key] = {k: dataclass_to_dict(v) if hasattr(v, '__dict__') else v for k, v in value.items()}
            else:
                result[key] = value
        return result
    return obj

def convert_dataframe_info(df_data):
    """Extract basic info from dataframe representation"""
    if df_data is None:
        return "No dataframe information"
    
    # If it's a pandas DataFrame object, extract info directly
    if hasattr(df_data, 'columns') and hasattr(df_data, 'shape'):
        shape_info = f"{df_data.shape[0]} rows x {df_data.shape[1]} columns"
        all_columns = list(df_data.columns)
        
        result = f"Shape: {shape_info}\n"
        result += f"Columns ({len(all_columns)}): {', '.join(all_columns)}"
        return result
    
    # Try to extract info from string representation
    df_str = str(df_data)
    lines = df_str.split('\n')
    
    # Look for shape info
    shape_info = ""
    for line in lines:
        if "rows x" in line and "columns" in line:
            shape_info = line.strip()
            break
    
    # Look for column names - improved extraction
    columns = []
    
    # Method 1: Look for the header line (usually after index column)
    for i, line in enumerate(lines[:15]):
        line = line.strip()
        if line and not line.startswith('[') and not 'rows x' in line and not line.startswith('...'):
            # Check if this looks like a header line
            parts = line.split()
            if len(parts) > 1:
                # Skip lines that start with numbers (data rows)
                if not parts[0].replace('.', '').replace('-', '').isdigit():
                    # This might be the header line
                    potential_columns = []
                    for part in parts:
                        # Clean up the column names
                        cleaned = part.strip()
                        # Skip obvious non-column elements
                        if (len(cleaned) > 1 and 
                            not cleaned.replace('.', '').replace('-', '').isdigit() and
                            cleaned not in ['NaN', '<NA>', '...', 'dtype:', 'object']):
                            potential_columns.append(cleaned)
                    
                    if potential_columns:
                        columns.extend(potential_columns)
                        break
    
    # Method 2: If no clear header found, extract from data patterns
    if not columns:
        for line in lines[:10]:
            if line.strip() and not line.startswith('[') and not 'rows x' in line:
                parts = line.split()
                if len(parts) > 1 and not parts[0].isdigit():
                    for part in parts:
                        if (len(part) > 2 and 
                            not part.replace('.', '').replace('-', '').isdigit() and
                            part not in ['NaN', '<NA>', '...', 'dtype:', 'object']):
                            if part not in columns:  # Avoid duplicates
                                columns.append(part)
    
    # Remove duplicates while preserving order
    unique_columns = []
    for col in columns:
        if col not in unique_columns:
            unique_columns.append(col)
    
    result = f"Shape: {shape_info}\n" if shape_info else ""
    if unique_columns:
        result += f"Columns ({len(unique_columns)}): {', '.join(unique_columns)}"
    else:
        result += "Columns: Could not extract column information"
    
    return result


def safe_get(obj, key, default=None):
    """Safely get value from object (dict or dataclass)"""
    if isinstance(obj, dict):
        return obj.get(key, default)
    elif hasattr(obj, key):
        return getattr(obj, key, default)
    elif hasattr(obj, '__dict__') and key in obj.__dict__:
        return obj.__dict__[key]
    else:
        return default

def generate_data_pipeline_report(report_data: Dict[str, Any]) -> str:
    """Convert report data to readable text format"""
    
    # Convert dataclass to dict if needed
    if hasattr(report_data, '__dict__'):
        report_data = dataclass_to_dict(report_data)
    
    output = []
    
    # Header
    output.append("=" * 80)
    output.append("DATA PROCESSING REPORT")
    output.append("=" * 80)
    
    # General info
    timestamp = safe_get(report_data, 'timestamp', 'N/A')
    overall_status = safe_get(report_data, 'overall_status', 'Unknown')
    
    output.append(f"Creation Time: {format_timestamp(timestamp)}")
    output.append(f"Overall Status: {overall_status.upper()}")
    output.append("")
    
    # Data Collector Results
    collector_result = safe_get(report_data, 'collector_result', {})
    if collector_result:
        # Convert to dict if it's a dataclass
        if hasattr(collector_result, '__dict__'):
            collector_result = dataclass_to_dict(collector_result)
            
        output.append("-" * 60)
        output.append("1. DATA COLLECTOR AGENT RESULTS")
        output.append("-" * 60)
        
        # Basic info
        summary = safe_get(collector_result, 'summary', {})
        output.append(f"Agent ID: {safe_get(collector_result, 'agent_id', 'N/A')}")
        output.append(f"Time: {format_timestamp(safe_get(collector_result, 'timestamp', 'N/A'))}")
        output.append(f"Status: {str(safe_get(collector_result, 'status', 'N/A')).replace('ProcessingStatus.', '').title()}")
        output.append(f"Total datasets: {safe_get(summary, 'total_datasets', 0)}")
        output.append(f"Successful: {safe_get(summary, 'successful', 0)}")
        output.append(f"Failed: {safe_get(summary, 'failed', 0)}")
        output.append(f"Warnings: {safe_get(summary, 'warnings', 0)}")
        output.append("")
        
        # Details for each dataset
        details = safe_get(collector_result, 'details', [])
        for i, detail in enumerate(details, 1):
            output.append(f"Dataset {i}: {safe_get(detail, 'data_type', 'Unknown')}")
            output.append(f"  - Status: {safe_get(detail, 'status', 'N/A').title()}")
            output.append(f"  - Files processed: {safe_get(detail, 'files_processed', 0)}")
            output.append(f"  - Files successful: {safe_get(detail, 'files_successful', 0)}")
            output.append(f"  - Records: {format_number(safe_get(detail, 'records_processed', 0))}")
            output.append(f"  - Output file: {safe_get(detail, 'output_file', 'N/A')}")
            output.append(f"  - Size: {format_bytes(safe_get(detail, 'file_size_mb', 0))}")
            output.append(f"  - Data updated: {'Yes' if safe_get(detail, 'data_updated') else 'No'}")
            
            failed_files = safe_get(detail, 'failed_files', [])
            if failed_files:
                output.append(f"  - Failed files: {', '.join(failed_files)}")
            output.append("")
    
    # Data Loader Results
    loader_result = safe_get(report_data, 'loader_result', {})
    if loader_result:
        # Convert to dict if it's a dataclass
        if hasattr(loader_result, '__dict__'):
            loader_result = dataclass_to_dict(loader_result)
            
        output.append("-" * 60)
        output.append("2. DATA LOADER AGENT RESULTS")
        output.append("-" * 60)
        
        # Basic info
        summary = safe_get(loader_result, 'summary', {})
        output.append(f"Agent ID: {safe_get(loader_result, 'agent_id', 'N/A')}")
        output.append(f"Time: {format_timestamp(safe_get(loader_result, 'timestamp', 'N/A'))}")
        output.append(f"Status: {str(safe_get(loader_result, 'status', 'N/A')).replace('ProcessingStatus.', '').title()}")
        output.append(f"Total databases: {safe_get(summary, 'total_databases', 0)}")
        output.append(f"Successful: {safe_get(summary, 'successful', 0)}")
        output.append(f"Failed: {safe_get(summary, 'failed', 0)}")
        output.append(f"Changed files: {safe_get(summary, 'changed_files', 0)}")
        output.append(f"Files saved: {safe_get(summary, 'files_saved', 0)}")
        output.append("")
        
        # Database details
        details = safe_get(loader_result, 'details', [])
        db_details = [d for d in details if safe_get(d, 'database_name')]
        
        if db_details:
            output.append("Details of processed databases:")
            output.append("")
            
            for i, detail in enumerate(db_details, 1):
                db_name = safe_get(detail, 'database_name', 'Unknown')
                db_type = safe_get(detail, 'database_type', 'Unknown')
                records = safe_get(detail, 'records_processed', 0)
                
                output.append(f"{i}. {db_name.upper()} ({db_type})")
                output.append(f"   - Database name: {db_name}")
                output.append(f"   - Type: {db_type}")
                output.append(f"   - Status: {safe_get(detail, 'status', 'N/A').title()}")
                output.append(f"   - Records: {format_number(records)}")
                output.append(f"   - Data updated: {'Yes' if safe_get(detail, 'data_updated') else 'No'}")
                
                # Dataframe info
                df_info = convert_dataframe_info(safe_get(detail, 'dataframe'))
                if df_info and df_info != "No dataframe information":
                    output.append(f"   - Data structure: {df_info}")
                
                warnings = safe_get(detail, 'warnings', [])
                if warnings:
                    output.append(f"   - Warnings: {'; '.join(warnings)}")
                
                output.append("")

    output.append("=" * 80)
    output.append("OPTIMOLDIQ WORKFLOW PROCESSING REPORT")
    output.append("=" * 80)

    output.append("-" * 60)
    output.append("1. RESULTS OF CHANGE DETECTION IN DATA")
    output.append("-" * 60)    
    
    return output