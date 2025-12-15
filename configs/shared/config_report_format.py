import inspect
from dataclasses import fields, is_dataclass

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