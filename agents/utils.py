from pathlib import Path
import shutil
from datetime import datetime
import pandas as pd
from loguru import logger
import os
import json 
import re
from tabulate import tabulate
from typing import Dict, Any, Optional, List

def load_json(json_path: str):
    """Load JSON file with error handling"""
    
    try:
        path = Path(json_path)

        if not path.exists():
            logger.warning(f"JSON file not found: {json_path}")
            return None
        
        if path.suffix.lower() != '.json':
            logger.error(f"Invalid file extension: {json_path}. Expected .json file")
            return None
        
        logger.info(f'Loading data from {json_path}')
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON format in {json_path}: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Error loading {json_path}: {str(e)}")
        return None
        
def camel_to_snake(name: str) -> str:
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

#-----------------------------#
# save_output_with_versioning #
#-----------------------------#

def save_output_with_versioning(
        data: dict[str, pd.DataFrame] | pd.DataFrame,
        output_dir: str | Path,
        filename_prefix: str,
        report_text: str | None = None
    ):  

    output_dir = Path(output_dir)
    timestamp_now = datetime.now()
    timestamp_str = timestamp_now.strftime("%Y-%m-%d %H:%M:%S")
    timestamp_file = timestamp_now.strftime("%Y%m%d_%H%M")

    log_entries = [f"[{timestamp_str}] Saving new version...\n"]

    newest_dir = output_dir / "newest"
    newest_dir.mkdir(parents=True, exist_ok=True)
    historical_dir = output_dir / "historical_db"
    historical_dir.mkdir(parents=True, exist_ok=True)

    # Move all files from newest/ to historical_db/
    archive_logs = archive_old_files(newest_dir, historical_dir)
    log_entries.append(archive_logs)
    
    # Save excel file
    excel_path = newest_dir / f"{timestamp_file}_{filename_prefix}_result.xlsx"
    write_excel_log = write_excel_data(excel_path, data)
    log_entries.append(write_excel_log)
    
    # Save report text if provided
    if report_text is not None:
        report_path = newest_dir / f"{timestamp_file}_{filename_prefix}_report.txt"
        write_report_log = write_text_report(report_path, report_text)
        log_entries.append(write_report_log)
    
    return "\n".join(log_entries)

def archive_old_files(newest_dir: str | Path, 
                      historical_dir: str | Path) -> str:
    
    """Move all files from newest_dir to historical_dir."""
    
    newest_dir = Path(newest_dir)
    newest_dir.mkdir(parents=True, exist_ok=True)

    historical_dir = Path(historical_dir)
    historical_dir.mkdir(parents=True, exist_ok=True)

    log_entries = []

    # Move old files to historical_db
    for f in newest_dir.iterdir():
        if f.is_file():
            try:
                dest = historical_dir / f.name
                shutil.move(str(f), dest)
                log_entries.append(f"  ⤷ Moved old file: {newest_dir}/{f.name} → {dest}")
                logger.info("Moved old file {}/{} → {}", 
                            newest_dir, f.name, dest)
            except Exception as e:
                logger.error("Failed to move file {}: {}", dest, e)
                raise OSError(f"Failed to move file {dest}: {e}")
    
    return "\n".join(log_entries)

def write_excel_data(excel_path: str | Path, 
                     excel_data: Dict | pd.DataFrame) -> str:
    
    """
    Write DataFrame(s) to Excel file.
    Supports single DataFrame or dict of DataFrames for multiple sheets.
    """
    excel_path = Path(excel_path)
    
    # Validate excel data, it must be a Dict or pd.DataFrame
    if not isinstance(excel_data, (dict, pd.DataFrame)):
        logger.error("❌ Expected dict or DataFrame but got: {}", type(excel_data))
        raise TypeError(f"Expected dict[str, pd.DataFrame] or pd.DataFrame but got: {type(excel_data)}")

    # Validate dict elements
    if isinstance(excel_data, dict) :
        for k, v in excel_data.items():
            if not isinstance(k, str) or not isinstance(v, pd.DataFrame):
                logger.error("❌ Invalid dict contents: key type {}, value type {}", type(k), type(v))
                raise TypeError(f"Expected dict keys to be str and values to be pd.DataFrame, but got key: {type(k)}, value: {type(v)}")
    
    # Support single/multiple sheet
    try:
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            if isinstance(excel_data, pd.DataFrame):
                excel_data.to_excel(writer, index=False)
            else:  # dict
                for sheet_name, df in excel_data.items():
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
        log_entries = f"  ⤷ Saved new file: {excel_path}"
        logger.info("✓ Saved new file: {}", excel_path)
        return log_entries
    
    except Exception as e:
        logger.error("Failed to save file as {}: {}", excel_path, e)
        raise OSError(f"Failed to save file as {excel_path}: {e}")
    
def write_text_report(report_path: str | Path, 
                      report_text: str) -> str :

    """Write text report to file."""
    report_path = Path(report_path)

    # Validate excel data, it must be string
    if not isinstance(report_text, str):
        logger.error("❌ Expected str but got: {}", type(report_text))
        raise TypeError(f"Expected str but got: {type(report_text)}")
    
    try:
        with open(report_path, "w", encoding="utf-8") as report_file:
            report_file.write(report_text)    
        log_entries = f"  ⤷ Saved report: {report_path}"
        logger.info("✓ Saved report: {}", report_path)
        return log_entries
    except Exception as e:
        logger.error("✗ Failed to save report as {}: {}", report_path, e)
        raise OSError(f"Failed to save report as {report_path}: {e}")

#------------------------------------------#
# update_weight_and_save_confidence_report #
#------------------------------------------#

def update_weight_and_save_confidence_report(
            report_text: str,
            output_dir: str | Path,
            filename_prefix: str,
            enhanced_weights: Dict[str, float]) -> str:  

        output_dir = Path(output_dir)
        
        timestamp_now = datetime.now()
        timestamp_str = timestamp_now.strftime("%Y-%m-%d %H:%M:%S")
        timestamp_file = timestamp_now.strftime("%Y%m%d_%H%M")

        log_entries = [f"[{timestamp_str}] Saving new version...\n"]

        newest_dir = output_dir / "newest"
        newest_dir.mkdir(parents=True, exist_ok=True)
        historical_dir = output_dir / "historical_db"
        historical_dir.mkdir(parents=True, exist_ok=True)

        # Move all files from newest/ to historical_db/
        archive_logs = archive_old_files(newest_dir, historical_dir)
        log_entries.append(archive_logs)
        
        # Write new confidence report
        report_path = newest_dir / f"{timestamp_file}_{filename_prefix}_report.txt"
        write_report_log = write_text_report(report_path, report_text)
        log_entries.append(write_report_log)

        # Update historical weights log with new enhanced weights
        weights_path = output_dir / "weights_hist.xlsx"
        if enhanced_weights:
            try:
                weights_row = {
                    "shiftNGRate": enhanced_weights.get("shiftNGRate", None),
                    "shiftCavityRate": enhanced_weights.get("shiftCavityRate", None),
                    "shiftCycleTimeRate": enhanced_weights.get("shiftCycleTimeRate", None),
                    "shiftCapacityRate": enhanced_weights.get("shiftCapacityRate", None),
                    "change_timestamp": timestamp_str
                }
                weights_df = pd.DataFrame([weights_row])

                if weights_path.exists():
                    old_df = pd.read_excel(weights_path)
                    full_df = pd.concat([old_df, weights_df], ignore_index=True)
                else:
                    full_df = weights_df

                full_df.to_excel(weights_path, index=False)
                log_entries.append(f"  ⤷ Saved new weight change: {weights_path}")
                logger.info("  ⤷ Saved new weight change: {}", weights_path)

            except Exception as e:
                logger.error("Failed to write weights_hist.xlsx: {}", e)
                raise OSError(f"Failed to write weights_hist.xlsx: {e}")
        
        return "\n".join(log_entries)

#-------------------#
# append_change_log #
#-------------------#

def append_change_log(log_path: str | Path, log_str: str) -> str:
    """
    Append a change log string to a file.

    Args:
        log_path: Path to the log file.
        log_str: Content to append (must be non-empty).

    Returns:
        Confirmation message.

    Raises:
        ValueError: If log_str is empty or whitespace.
        OSError: If writing to file fails.
    """
    if not log_str or not log_str.strip():
        logger.error("❌ Nothing to append. Log string is empty.")
        raise ValueError("Log string must not be empty.")

    log_path = Path(log_path)

    try:
        with log_path.open("a", encoding="utf-8") as f:
            if not log_str.endswith("\n"):
                log_str += "\n"
            f.write(log_str)

        logger.info(f"✓ Updated and saved change log: {log_path}")

    except OSError as e:
        logger.error("✗ Failed to save change log {}: {}", log_path, e)
        raise OSError(f"Failed to save change log {log_path}: {e}")

#----------------------#
# load_annotation_path #
#----------------------#

def load_annotation_path(source_path: str = 'agents/shared_db/DataLoaderAgent/newest', 
                         annotation_name: str = "path_annotations.json"):
  annotation_path = Path(source_path) / annotation_name

  #Load existing path annotations
  if os.path.exists(annotation_path):
      with open(annotation_path, "r", encoding="utf-8") as f:
        path_annotation = json.load(f)
      logger.debug("Loaded existing annotation file: {}", path_annotation)
      return path_annotation
  else:
      logger.error("No existing annotation - please call dataLoader first...")
      raise FileNotFoundError(f"No existing annotation - please call dataLoader first: {annotation_path}")

#-----------------#
# read_change_log #
#-----------------#

def read_change_log(folder_path, 
                    target_name, 
                    pattern: str = r'Saved new file:\s*(.+)'):

    """
    Read a log file in the given folder and extract the path to the latest saved Excel file.
    """

    folder_path = Path(folder_path) 
    
    # Check if folder exists
    if not os.path.isdir(folder_path):
        logger.warning("Directory does not exist: {}", folder_path)
        return None
    
    file_path = os.path.join(folder_path, target_name)
    
    # Check if file exists
    if not os.path.isfile(file_path):
        logger.warning("Could not find '{}' in folder {}", target_name, folder_path)
        return None
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            log_text = f.read()
            newest_files = extract_latest_saved_files(log_text, pattern)

            if not newest_files:
                logger.warning(f"No file information found saved in '{target_name}'")
                return None 
            
            newest_paths = [
                (folder_path / f) if folder_path not in Path(f).parents else Path(f)
                for f in (newest_files if isinstance(newest_files, list) else [newest_files])
            ]
            
            if len(newest_paths) == 1:
                return newest_paths[0]
            
            return newest_paths
                
    except Exception as e:
        logger.error("Error reading file '{}': {}", target_name, str(e))
        raise

def extract_latest_saved_files(log_text: str,
                               pattern: str = r'Saved new file:\s*(.+)') -> Optional[List[str]]:
    """
    Extract all saved file paths from the most recent EXPORT LOG section.
    """
    if not log_text.strip():
        return None

    # Find all sections that contain "EXPORT LOG:"
    # Use lookahead to capture until next "====" or end of string
    sections = re.split(r'={60,}', log_text)
    
    # Find the last section containing "EXPORT LOG:"
    export_section = None
    for section in reversed(sections):
        if 'EXPORT LOG:' in section:
            export_section = section
            break
    
    if not export_section:
        return None

    # Extract all pattern entries from this section
    saved_files = re.findall(pattern, export_section)

    return [f.strip() for f in saved_files] if saved_files else None

#-------------------#
# log_dict_as_table #
#-------------------#

def log_dict_as_table(
        data_dict: Dict[str, Any],
        transpose: bool = False):

    """
    Log a dictionary as a Markdown table.

    Args:
        data_dict (Dict): The dictionary to log.
        transpose (bool): If True, show keys as columns (for matrix-like dicts).
    """

    # Format DataFrame
    if transpose:
        df = pd.DataFrame(data_dict).T.reset_index()
    else:
        df = pd.DataFrame(list(data_dict.items()), columns=["Metric", "Value"])

    # Compose output
    return tabulate(df, headers="keys", tablefmt="github", showindex=False)

#-----------------------#
# get_latest_change_row #
#-----------------------#

def get_latest_change_row(weights_hist_path: str) -> pd.Series:
    """
    Read the weights history Excel file and return the most recent row (excluding the timestamp).

    Args:
        weights_hist_path (str): Path to the Excel file containing weight change history.

    Returns:
        pd.Series: The latest row of weights (without the 'change_timestamp' column).
    """
    df = pd.read_excel(weights_hist_path)
    df['change_timestamp'] = pd.to_datetime(df['change_timestamp'])
    latest_row = df.loc[df['change_timestamp'].idxmax()]
    return latest_row.drop("change_timestamp")

#--------------#
# rank_nonzero #
#--------------#

def rank_nonzero(row):
    """
    Assign descending rank to non-zero values in a row.
    Zero values remain unchanged, and non-zero values are ranked in descending order.

    Args:
        row (pd.Series): A row of numerical values.

    Returns:
        pd.Series: The same row with non-zero values replaced by their descending ranks.
    """
    nonzero = row[row != 0]
    ranked = nonzero.sort_values(ascending=False).rank(method='first', ascending=False).astype('Int64')
    return row.where(row == 0, ranked).astype('Int64')