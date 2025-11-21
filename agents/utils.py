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

def save_output_with_versioning(
    data: dict[str, pd.DataFrame],
    output_dir: str | Path,
    filename_prefix: str = "output",
    file_format: str = 'xlsx',
):  
    if not isinstance(data, dict):
        logger.error("❌ Expected data to be a dict[str, pd.DataFrame] but got: {}", type(data))
        raise TypeError(f"Expected data to be a dict[str, pd.DataFrame] but got: {type(data)}")

    for k, v in data.items():
        if not isinstance(k, str) or not isinstance(v, pd.DataFrame):
            logger.error("❌ Invalid dict contents: key type {}, value type {}", type(k), type(v))
            raise TypeError(f"Expected dict keys to be str and values to be pd.DataFrame, but got key: {type(k)}, value: {type(v)}")

    output_dir = Path(output_dir)
    log_path = output_dir / "change_log.txt"
    timestamp_now = datetime.now()
    timestamp_str = timestamp_now.strftime("%Y-%m-%d %H:%M:%S")
    log_entries = [f"[{timestamp_str}] Saving new version...\n"]

    newest_dir = output_dir / "newest"
    newest_dir.mkdir(parents=True, exist_ok=True)
    historical_dir = output_dir / "historical_db"
    historical_dir.mkdir(parents=True, exist_ok=True)

    # Move old files to historical_db
    for f in newest_dir.iterdir():
        if f.is_file():
            try:
                dest = historical_dir / f.name
                shutil.move(str(f), dest)
                log_entries.append(f"  ⤷ Moved old file: {f.name} → historical_db/{f.name}\n")
                logger.info("Moved old file {} to historical_db as {}", f.name, dest.name)
            except Exception as e:
                logger.error("Failed to move file {}: {}", f.name, e)
                raise OSError(f"Failed to move file {f.name}: {e}")

    timestamp_file = timestamp_now.strftime("%Y%m%d_%H%M")
    new_filename = f"{timestamp_file}_{filename_prefix}.{file_format}"
    new_path = newest_dir / new_filename

    try:
        with pd.ExcelWriter(new_path, engine='openpyxl') as writer:
            for sheet_name, df in data.items():
                df.to_excel(writer, sheet_name=sheet_name, index=False)
        log_entries.append(f"  ⤷ Saved new file: {newest_dir}/{new_filename}\n")
        logger.info("Saved new file: {}/{}", newest_dir, new_filename)
    except Exception as e:
        logger.error("Failed to save file {}: {}", new_filename, e)
        raise OSError(f"Failed to save file {new_filename}: {e}")

    try:
        with open(log_path, "a", encoding="utf-8") as log_file:
            log_file.writelines(log_entries)
        logger.info("Updated change log {}", log_path)
    except Exception as e:
        logger.error("Failed to update change log {}: {}", log_path, e)
        raise OSError(f"Failed to update change log {log_path}: {e}")

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

def extract_latest_saved_files(log_text: str) -> Optional[List[str]]:
    """
    Extract all saved file names from the most recent log block.
    """
    if not log_text.strip():
        return None

    # Match all log blocks by timestamp
    pattern = r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\](.*?)(?=\n\[|$)'
    matches = re.findall(pattern, log_text, flags=re.DOTALL)

    if not matches:
        return None

    log_blocks = {}
    for ts_str, content in matches:
        log_blocks[ts_str] = content.strip()

    # Get the latest block based on timestamp
    latest_ts_str = max(log_blocks, key=lambda ts: datetime.strptime(ts, '%Y-%m-%d %H:%M:%S'))
    latest_block = log_blocks[latest_ts_str]

    # Extract ALL saved file names from the latest block
    saved_files = re.findall(r'⤷ Saved new file: (.+)', latest_block)

    return [f.strip() for f in saved_files] if saved_files else None

def read_change_log(folder_path, target_name):

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
            newest_files = extract_latest_saved_files(log_text)

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

def save_text_report_with_versioning(
    text: str,
    output_dir: str | Path,
    filename_prefix: str = "confidence_report",
    weights: dict = None ):

    """
    Save a formatted text report to a .txt file with versioning,
    and log any new weights to weights_hist.xlsx.
    """

    if not isinstance(text, str):
        logger.error("❌ Expected text to be a string but got: {}", type(text))
        raise TypeError(f"Expected text to be a string but got: {type(text)}")

    output_dir = Path(output_dir)
    log_path = output_dir / "change_log.txt"
    weights_path = output_dir / "weights_hist.xlsx"
    timestamp_now = datetime.now()
    timestamp_str = timestamp_now.strftime("%Y-%m-%d %H:%M:%S")
    log_entries = [f"[{timestamp_str}] Saving new version...\n"]

    newest_dir = output_dir / "newest"
    newest_dir.mkdir(parents=True, exist_ok=True)
    historical_dir = output_dir / "historical_db"
    historical_dir.mkdir(parents=True, exist_ok=True)

    # Move old reports to historical_db
    for f in newest_dir.iterdir():
        if f.is_file() and f.suffix == '.txt':
            try:
                dest = historical_dir / f.name
                shutil.move(str(f), dest)
                log_entries.append(f"  ⤷ Moved old file: {f.name} → historical_db/{f.name}\n")
                logger.info("Moved old file {} to historical_db as {}", f.name, dest.name)
            except Exception as e:
                logger.error("Failed to move file {}: {}", f.name, e)
                raise OSError(f"Failed to move file {f.name}: {e}")

    timestamp_file = timestamp_now.strftime("%Y%m%d_%H%M")
    new_filename = f"{timestamp_file}_{filename_prefix}.txt"
    new_path = newest_dir / new_filename

    try:
        with open(new_path, "w", encoding="utf-8") as file:
            file.write(text)
        log_entries.append(f"  ⤷ Saved new file: {newest_dir}/{new_filename}\n")
        logger.info("Saved new report: {}/{}", newest_dir, new_filename)
    except Exception as e:
        logger.error("Failed to save report {}: {}", new_filename, e)
        raise OSError(f"Failed to save report {new_filename}: {e}")

    try:
        with open(log_path, "a", encoding="utf-8") as log_file:
            log_file.writelines(log_entries)
        logger.info("Updated change log {}", log_path)
    except Exception as e:
        logger.error("Failed to update change log {}: {}", log_path, e)
        raise OSError(f"Failed to update change log {log_path}: {e}")

    # Append to weights_hist.xlsx if weights provided -> support feature_weight_calculator.py
    if weights:
        try:
            weights_row = {
                "shiftNGRate": weights.get("shiftNGRate", None),
                "shiftCavityRate": weights.get("shiftCavityRate", None),
                "shiftCycleTimeRate": weights.get("shiftCycleTimeRate", None),
                "shiftCapacityRate": weights.get("shiftCapacityRate", None),
                "change_timestamp": timestamp_str
            }
            weights_df = pd.DataFrame([weights_row])

            if weights_path.exists():
                old_df = pd.read_excel(weights_path)
                full_df = pd.concat([old_df, weights_df], ignore_index=True)
            else:
                full_df = weights_df

            full_df.to_excel(weights_path, index=False)
            logger.info("Logged weight change to {}", weights_path)
        except Exception as e:
            logger.error("Failed to write weights_hist.xlsx: {}", e)
            raise OSError(f"Failed to write weights_hist.xlsx: {e}")

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

# Support history_processor.py
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

# Support history_processor.py
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