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

def save_output_with_versioning(
    data: dict[str, pd.DataFrame],
    output_dir: str | Path,
    filename_prefix: str,
    report_text: str | None = None,
):  
    if not isinstance(data, dict):
        logger.error("❌ Expected data to be a dict[str, pd.DataFrame] but got: {}", type(data))
        raise TypeError(f"Expected data to be a dict[str, pd.DataFrame] but got: {type(data)}")

    for k, v in data.items():
        if not isinstance(k, str) or not isinstance(v, pd.DataFrame):
            logger.error("❌ Invalid dict contents: key type {}, value type {}", type(k), type(v))
            raise TypeError(f"Expected dict keys to be str and values to be pd.DataFrame, but got key: {type(k)}, value: {type(v)}")

    output_dir = Path(output_dir)
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
    new_filename = f"{timestamp_file}_{filename_prefix}_result.xlsx"
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

    # Save report text if provided
    if report_text is not None:
        report_filename = f"{timestamp_file}_{filename_prefix}_report.txt"
        report_path = newest_dir / report_filename
        try:
            with open(report_path, "w", encoding="utf-8") as report_file:
                report_file.write(report_text)
            log_entries.append(f"  ⤷ Saved report: {newest_dir}/{report_filename}\n")
            logger.info("✓ Updated and saved dashboard log: {}", report_path)
        except Exception as e:
            logger.error("✗ Failed to save dashboard log {}: {}", report_path, e)
            raise OSError(f"Failed to save dashboard log {report_path}: {e}")
    
    return "".join(log_entries)

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

    # Match all log blocks (allow indentation before timestamp)
    pattern = r'\s*\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\](.*?)(?=\n\s*\[|$)'
    matches = re.findall(pattern, log_text, flags=re.DOTALL)

    if not matches:
        return None

    # Map timestamp → block content
    log_blocks = {
        ts: content.strip()
        for ts, content in matches
    }

    # Get the latest timestamp
    latest_ts = max(log_blocks, key=lambda t: datetime.strptime(t, "%Y-%m-%d %H:%M:%S"))
    latest_block = log_blocks[latest_ts]

    # Extract saved files
    saved_files = re.findall(r'Saved new file:\s*(.+)', latest_block)

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

def validate_multi_level_analyzer_result(
    data: Dict[str, Any],
    required_keys: Iterable[str],
    ) -> None:
    if not isinstance(data, dict):
        raise TypeError("MultiLevelAnalyzer result must be a dict.")

    missing = [k for k in required_keys if k not in data]
    if missing:
        raise KeyError(f"MultiLevelAnalyzer result missing keys: {missing}")

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