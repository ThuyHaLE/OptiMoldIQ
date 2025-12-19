from pathlib import Path
import shutil
from datetime import datetime
import pandas as pd
from loguru import logger
import os
import json 
import re
from tabulate import tabulate
from typing import Dict, Any, Optional, List, Iterable
import inspect
from dataclasses import fields, is_dataclass

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

def extract_latest_saved_files(log_text: str) -> Optional[List[str]]:
    """
    Extract all saved file names from the most recent EXPORT LOG section.
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

    # Extract all "Saved new file" entries from this section
    saved_files = re.findall(r'Saved new file:\s*(.+)', export_section)

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

#---------------#
# validate_path #
#---------------#

def validate_path(name: str, value: str):
    """Ensure value is a non-empty path-like string and normalize it."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string.")

    # Check path-like
    if "/" not in value and "\\" not in value:
        raise ValueError(f"{name} must look like a path (contain '/' or '\\').")

    # Normalize path: convert to POSIX, remove trailing spaces and extra slashes
    path = Path(value).as_posix().strip().rstrip("/")

    # Return normalized folder path (with trailing '/')
    return path + "/"

#--------------------------------------#
# validate_multi_level_analyzer_result #
#--------------------------------------#

def validate_multi_level_analyzer_result(
    data: Dict[str, Any],
    required_keys: Iterable[str],
    ) -> None:
    if not isinstance(data, dict):
        raise TypeError("MultiLevelAnalyzer result must be a dict.")

    missing = [k for k in required_keys if k not in data]
    if missing:
        raise KeyError(f"MultiLevelAnalyzer result missing keys: {missing}")

#-------------------#
# ConfigReportMixin #
#-------------------#

class ConfigReportMixin:
    """
    Mixin to add auto-config reporting capability to any class.
    Supports nested config validation and reporting.
    
    Usage:
        class MyOrchestrator(ConfigReportMixin):
            REQUIRED_FIELDS = {
                'analytics_dir': str,
                'enable_feature': bool,
                'change_config': {
                    'source_dir': str,
                    'output_dir': str,
                },
                'performance_config': {
                    'database_path': str,
                }
            }
            
            def __init__(self, config: MyConfig):
                self._capture_init_args()
                # ... rest of init code ...
            
            def run(self):
                # Show all fields
                config_header = self._generate_config_report()
                
                # Show only required fields
                config_header = self._generate_config_report(required_only=True)
    """
    
    def _capture_init_args(self):
        """
        Capture all __init__ arguments automatically.
        Must be called as first line in __init__.
        """
        frame = inspect.currentframe().f_back
        args_info = inspect.getargvalues(frame)
        self.init_args = {k: v for k, v in args_info.locals.items() if k != 'self'}
    
    def _format_value(self, value, indent_level: int = 0) -> list:
        """
        Format a value for display, handling nested configs and dataclasses.
        
        Args:
            value: The value to format
            indent_level: Current indentation level
            
        Returns:
            List of formatted strings
        """
        indent = "  " * indent_level
        lines = []
        
        # Handle dataclass instances
        if is_dataclass(value) and not isinstance(value, type):
            for field in fields(value):
                field_value = getattr(value, field.name)
                display_name = field.name.replace('_', ' ').title()
                
                # Recursively format nested dataclasses
                if is_dataclass(field_value) and not isinstance(field_value, type):
                    lines.append(f"{indent}⤷ {display_name}:")
                    lines.extend(self._format_value(field_value, indent_level + 1))
                else:
                    lines.append(f"{indent}⤷ {display_name}: {field_value}")
        
        # Handle dataclass types (not instantiated)
        elif is_dataclass(value) and isinstance(value, type):
            lines.append(f"{indent}[Uninstantiated Config Class: {value.__name__}]")
            lines.append(f"{indent}⚠ Note: Pass an instance instead of class")
        
        # Handle regular values
        else:
            lines.append(f"{indent}{value}")
        
        return lines
    
    def _extract_nested_value(self, obj, field_path: str):
        """
        Extract value from nested object using dot notation or direct attribute access.
        
        Args:
            obj: Object to extract from
            field_path: Field name (can be nested like 'config.source_dir')
            
        Returns:
            Extracted value or None if not found
        """
        try:
            # Handle dot notation (future feature)
            if '.' in field_path:
                parts = field_path.split('.')
                current = obj
                for part in parts:
                    current = getattr(current, part)
                return current
            else:
                return getattr(obj, field_path)
        except AttributeError:
            return None
    
    def _extract_required_fields_recursive(
        self, 
        obj, 
        required_spec: dict,
        parent_key: str = ""
    ) -> dict:
        """
        Recursively extract required fields from nested config objects.
        
        Args:
            obj: Object to extract from (can be dataclass or regular object)
            required_spec: Dictionary specifying required fields structure
            parent_key: Parent key for nested objects (for display)
            
        Returns:
            Dictionary of extracted field_name -> value
        """
        extracted = {}
        
        for key, value_spec in required_spec.items():
            # Build full key path for nested fields
            full_key = f"{parent_key}.{key}" if parent_key else key
            
            # Check if this is a nested config requirement (dict)
            if isinstance(value_spec, dict):
                # This key should point to a nested config object
                nested_obj = self._extract_nested_value(obj, key)
                if nested_obj is not None:
                    # Recursively extract from nested object
                    nested_fields = self._extract_required_fields_recursive(
                        nested_obj, 
                        value_spec,
                        parent_key=key
                    )
                    # Store nested object with its required fields
                    extracted[key] = {
                        '_object': nested_obj,
                        '_fields': nested_fields
                    }
            else:
                # This is a simple field requirement (type)
                field_value = self._extract_nested_value(obj, key)
                if field_value is not None:
                    extracted[key] = field_value
        
        return extracted
    
    def _get_filtered_args(self, required_only: bool = False) -> dict:
        """
        Get filtered init arguments based on requirements.
        Supports nested config objects and hierarchical field extraction.
        
        Args:
            required_only: If True, only return fields listed in REQUIRED_FIELDS
            
        Returns:
            Dictionary of filtered arguments
        """
        if not hasattr(self, 'init_args'):
            return {}
        
        if not required_only:
            return self.init_args
        
        # Filter by REQUIRED_FIELDS if defined
        if not hasattr(self, 'REQUIRED_FIELDS'):
            return self.init_args
        
        required_spec = self.REQUIRED_FIELDS
        filtered = {}
        
        # First, check direct init_args
        for key, value_spec in required_spec.items():
            if key in self.init_args:
                if isinstance(value_spec, dict):
                    # Nested config - extract recursively
                    nested_fields = self._extract_required_fields_recursive(
                        self.init_args[key],
                        value_spec,
                        parent_key=key
                    )
                    filtered[key] = {
                        '_object': self.init_args[key],
                        '_fields': nested_fields
                    }
                else:
                    # Simple field
                    filtered[key] = self.init_args[key]
        
        # If no direct matches, check inside config objects
        if not filtered:
            for arg_name, arg_value in self.init_args.items():
                # Check if this is a config object
                if (is_dataclass(arg_value) and not isinstance(arg_value, type)) or \
                   hasattr(arg_value, '__dict__'):
                    # Extract all required fields from this config object
                    extracted = self._extract_required_fields_recursive(
                        arg_value,
                        required_spec
                    )
                    filtered.update(extracted)
        
        return filtered
    
    def _format_filtered_value(self, key: str, value, indent_level: int = 0) -> list:
        """
        Format a filtered value for display, handling nested required fields.
        
        Args:
            key: Field name
            value: Field value (can be dict with '_object' and '_fields')
            indent_level: Current indentation level
            
        Returns:
            List of formatted strings
        """
        indent = "  " * indent_level
        lines = []
        display_name = key.replace('_', ' ').title()
        
        # Check if this is a nested config result
        if isinstance(value, dict) and '_object' in value and '_fields' in value:
            lines.append(f"{indent}⤷ {display_name}:")
            # Format nested fields
            for nested_key, nested_value in value['_fields'].items():
                lines.extend(
                    self._format_filtered_value(nested_key, nested_value, indent_level + 1)
                )
        else:
            # Regular value
            lines.append(f"{indent}⤷ {display_name}: {value}")
        
        return lines
    
    def _generate_config_report(
        self, 
        timestamp_str: str = None,
        required_only: bool = False
    ) -> str:
        """
        Generate configuration report header from init arguments.
        
        Args:
            timestamp_str: Optional timestamp string. If None, uses current time.
            required_only: If True, only show fields listed in REQUIRED_FIELDS
            
        Returns:
            Formatted configuration report string
        """
        if timestamp_str is None:
            timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Add indicator if showing required fields only
        config_section = "--Configuration--"
        if required_only and hasattr(self, 'REQUIRED_FIELDS'):
            config_section = "--Configuration (Required Fields Only)--"
        
        log_lines = [
            f"[{timestamp_str}] {self.__class__.__name__} Run",
            "",
            config_section
        ]
        
        # Get filtered arguments
        filtered_args = self._get_filtered_args(required_only)
        
        if not filtered_args:
            log_lines.append("⤷ No configuration parameters to display")
        else:
            # Auto-generate config lines from filtered args
            for key, value in filtered_args.items():
                if required_only:
                    # Use special formatting for nested required fields
                    log_lines.extend(self._format_filtered_value(key, value))
                else:
                    # Use standard formatting
                    display_name = key.replace('_', ' ').title()
                    
                    # Check if value is a dataclass or config object
                    if is_dataclass(value) and not isinstance(value, type):
                        # Expanded config display
                        log_lines.append(f"⤷ {display_name}:")
                        log_lines.extend(self._format_value(value, indent_level=1))
                    elif is_dataclass(value) and isinstance(value, type):
                        # Warning for uninstantiated config
                        log_lines.append(f"⤷ {display_name}: {value.__name__} (Class)")
                        log_lines.append(f"  ⚠ Warning: Config class not instantiated")
                    else:
                        # Regular value
                        log_lines.append(f"⤷ {display_name}: {value}")
        
        log_lines.append("")
        
        return "\n".join(log_lines)