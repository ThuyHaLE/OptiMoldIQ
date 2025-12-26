from typing import Any
import pandas as pd
from dataclasses import asdict, is_dataclass


class DictBasedReportGenerator:
    """
    A class for generating human-readable reports from nested dataclass/dict/list/enum structures
    with enhanced DataFrame display and color support.
    """
    
    def __init__(self, 
                 use_colors: bool = True, 
                 max_rows: int = 10, 
                 max_cols: int = 10):
        """
        Initialize the DictBasedReportGenerator.
        
        Args:
            use_colors: Whether to use ANSI color codes in output
            max_rows: Maximum number of rows to display for DataFrames
            max_cols: Maximum number of columns to display for DataFrames
        """
        self.max_rows = max_rows
        self.max_cols = max_cols
        
        # Color codes (ANSI)
        self.colors = {
            'key': '\033[94m',      # Blue
            'value': '\033[92m',    # Green
            'number': '\033[93m',   # Yellow
            'string': '\033[96m',   # Cyan
            'bool': '\033[95m',     # Magenta
            'null': '\033[90m',     # Gray
            'reset': '\033[0m',     # Reset
            'bold': '\033[1m',      # Bold
            'header': '\033[97m',   # White
            'border': '\033[37m',   # Light gray
            'info': '\033[36m',     # Cyan for info text
        } if use_colors else {k: '' for k in ['key', 'value', 'number', 'string', 'bool', 'null', 'reset', 'bold', 'header', 'border', 'info']}
    
    def _get_value_color(self, value: Any) -> str:
        """Get appropriate color for value based on its type."""
        if isinstance(value, bool):
            return self.colors['bool']
        elif isinstance(value, (int, float)):
            return self.colors['number']
        elif isinstance(value, str):
            return self.colors['string']
        elif value is None:
            return self.colors['null']
        else:
            return self.colors['value']
    
    def _normalize_content(self, obj: Any) -> Any:
        """
        Recursively convert dataclasses, enums, and other non-serializable objects 
        into JSON-friendly structures.
        """
        if is_dataclass(obj):
            return self._normalize_content(asdict(obj))  # dataclass -> dict
        elif hasattr(obj, "value"):  # Enum
            return obj.value
        elif isinstance(obj, dict):
            return {k: self._normalize_content(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple, set)):
            if all(not isinstance(v, (dict, list, tuple, set)) for v in obj):
                return ", ".join(str(self._normalize_content(v)) for v in obj)
            else:
                return [self._normalize_content(v) for v in obj]
        else:
            return obj
    
    def _format_dataframe(self, df: pd.DataFrame) -> str:
        """
        Format DataFrame for beautiful display in reports using box drawing characters.
        
        Args:
            df: The DataFrame to format
                
        Returns:
            str: Formatted string representation of the DataFrame with box drawing
        """
        if df.empty:
            return f"{self.colors['null']}Empty DataFrame{self.colors['reset']}"
        
        # Get basic info
        shape_info = f"{self.colors['info']}📊 Shape: {self.colors['number']}{df.shape[0]}{self.colors['reset']} rows × {self.colors['number']}{df.shape[1]}{self.colors['reset']} columns"
        
        # Truncate if necessary
        display_df = df.copy()
        truncated_rows = False
        truncated_cols = False
        
        if len(df) > self.max_rows:
            display_df = pd.concat([df.head(self.max_rows//2), df.tail(self.max_rows//2)])
            truncated_rows = True
            
        if len(df.columns) > self.max_cols:
            display_df = display_df.iloc[:, :self.max_cols]
            truncated_cols = True
        
        # Prepare data for box drawing with original indices
        headers = list(display_df.columns)
        rows = []
        original_indices = []
        
        for idx, (original_idx, row) in enumerate(display_df.iterrows()):
            rows.append([str(val) if pd.notna(val) else '' for val in row])
            original_indices.append(idx)  # Use sequential index for display_df
        
        # Calculate column widths (without color codes)
        col_widths = []
        for i, header in enumerate(headers):
            max_width = len(str(header))
            for row in rows:
                if i < len(row):
                    max_width = max(max_width, len(row[i]))
            col_widths.append(max(max_width + 2, 8))  # Minimum width of 8
        
        # Box drawing characters
        border_color = self.colors['border']
        reset = self.colors['reset']
        
        top_left = f"{border_color}┌{reset}"
        top_right = f"{border_color}┐{reset}"
        bottom_left = f"{border_color}└{reset}"
        bottom_right = f"{border_color}┘{reset}"
        horizontal = f"{border_color}─{reset}"
        vertical = f"{border_color}│{reset}"
        cross = f"{border_color}┼{reset}"
        top_cross = f"{border_color}┬{reset}"
        bottom_cross = f"{border_color}┴{reset}"
        left_cross = f"{border_color}├{reset}"
        right_cross = f"{border_color}┤{reset}"
        
        def create_border_line(left_char, 
                               cross_char, 
                               right_char):
            line = left_char
            for i, width in enumerate(col_widths):
                line += horizontal * width
                if i < len(col_widths) - 1:
                    line += cross_char
            line += right_char
            return line
        
        def create_data_line(data_list, 
                             is_header=False, 
                             row_idx=None):
            line = vertical
            for i, (data, width) in enumerate(zip(data_list, col_widths)):
                if is_header:
                    # Header formatting
                    color = self.colors['header'] + self.colors['bold']
                    formatted_data = f" {color}{data}{reset} ".center(width + len(color) + len(reset))
                else:
                    # Data formatting with type-based colors
                    try:
                        # Use the provided row_idx to get original data for coloring
                        if row_idx is not None and i < len(display_df.columns):
                            original_data = display_df.iloc[row_idx, i]
                        else:
                            # Fallback: try to parse the data to determine color
                            original_data = data
                            # Try to convert to appropriate type for coloring
                            if data == '':
                                original_data = None
                            elif data.lower() in ['true', 'false']:
                                original_data = data.lower() == 'true'
                            else:
                                try:
                                    if '.' in data:
                                        original_data = float(data)
                                    else:
                                        original_data = int(data)
                                except ValueError:
                                    original_data = data
                    except:
                        original_data = data
                    
                    color = self._get_value_color(original_data)
                    formatted_data = f" {color}{data}{reset} ".ljust(width + len(color) + len(reset))
                
                line += formatted_data
                line += vertical
            return line
        
        # Build the table
        formatted_lines = []
        formatted_lines.append(shape_info)
        
        if truncated_rows or truncated_cols:
            truncation_info = []
            if truncated_rows:
                truncation_info.append(f"showing first/last {self.colors['number']}{self.max_rows//2}{self.colors['reset']} rows")
            if truncated_cols:
                truncation_info.append(f"showing first {self.colors['number']}{self.max_cols}{self.colors['reset']} columns")
            formatted_lines.append(f"   {self.colors['info']}({', '.join(truncation_info)}){self.colors['reset']}")
        
        formatted_lines.append("")
        
        # Top border
        formatted_lines.append(create_border_line(top_left, top_cross, top_right))
        
        # Headers
        formatted_lines.append(create_data_line(headers, is_header=True))
        
        # Header separator
        formatted_lines.append(create_border_line(left_cross, cross, right_cross))
        
        # Data rows
        for row_idx, row in enumerate(rows):
            formatted_lines.append(create_data_line(row, is_header=False, row_idx=row_idx))
        
        # Bottom border
        formatted_lines.append(create_border_line(bottom_left, bottom_cross, bottom_right))
        
        # Add data types info for smaller DataFrames
        if len(df.columns) <= 6:
            formatted_lines.append("")
            formatted_lines.append(f"{self.colors['info']}📋 Data Types:{self.colors['reset']}")
            for col, dtype in display_df.dtypes.items():
                col_color = self.colors['key']
                type_color = self.colors['value']
                formatted_lines.append(f"   {self.colors['border']}•{self.colors['reset']} {col_color}{col}{self.colors['reset']}: {type_color}{dtype}{self.colors['reset']}")
        
        return '\n'.join(formatted_lines)
    
    def generate_report(self, 
                        content: Any, 
                        indent: int = 0) -> str:
        """
        Generate human-readable report from nested dataclass/dict/list/enum.
        Supports both success and error content with enhanced DataFrame display.
        
        Args:
            content: The content to generate a report for
            indent: Current indentation level
            
        Returns:
            str: Formatted report string
        """
        data = self._normalize_content(content)
        lines = []
        prefix = "  " * indent

        if isinstance(data, dict):
            for k, v in data.items():
                key_color = self.colors['key'] + self.colors['bold']
                reset = self.colors['reset']
                
                # Check for DataFrame first
                if isinstance(v, pd.DataFrame):
                    lines.append(f"{prefix}{self.colors['border']}•{reset} {key_color}{k.upper()}:{reset}")
                    df_formatted = self._format_dataframe(v)
                    # Add proper indentation to each line of the formatted DataFrame
                    for line in df_formatted.split('\n'):
                        lines.append(f"{prefix}  {line}")
                elif isinstance(v, (dict, list)):
                    lines.append(f"{prefix}{self.colors['border']}•{reset} {key_color}{k.upper()}:{reset}")
                    lines.append(self.generate_report(v, indent + 1))
                else:
                    value_color = self._get_value_color(v)
                    lines.append(f"{prefix}{self.colors['border']}•{reset} {key_color}{k.upper()}:{reset} {value_color}{v}{reset}")
                    
        elif isinstance(data, list):
            for idx, item in enumerate(data, start=1):
                if isinstance(item, pd.DataFrame):
                    lines.append(f"{prefix}{self.colors['info']}📊 DataFrame #{self.colors['number']}{idx}{self.colors['reset']}:")
                    df_formatted = self._format_dataframe(item)
                    for line in df_formatted.split('\n'):
                        lines.append(f"{prefix}  {line}")
                elif isinstance(item, dict):
                    lines.append(self.generate_report(item, indent + 1))
                else:
                    value_color = self._get_value_color(item)
                    lines.append(f"{prefix}{self.colors['border']}-{self.colors['reset']} {value_color}{item}{self.colors['reset']}")
        else:
            value_color = self._get_value_color(data)
            lines.append(f"{prefix}{value_color}{data}{self.colors['reset']}")
        
        return "\n".join(lines)
    
    def export_report(self, 
                     content: Any, 
                     title: str = None,
                     header: str = None,
                     footer: str = None):
        """
        Print a formatted report with an optional title.
        
        Args:
            content: The content to generate a report for
            title: Optional title for the report
        """
        lines = []

        if title:
            title_color = self.colors['bold'] + self.colors['header']
            lines.append(f"\n{title_color}{'='*60}{self.colors['reset']}")
            lines.append(f"{title_color}{title.center(60)}{self.colors['reset']}")
            lines.append(f"{title_color}{'='*60}{self.colors['reset']}\n")

        lines.append(self.generate_report(content))

        return lines