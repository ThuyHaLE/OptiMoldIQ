# optiMoldMaster/workflows/registry/registry.py

from pathlib import Path
from typing import Dict, Optional
import yaml
from modules import get_module, AVAILABLE_MODULES
from loguru import logger

class ModuleRegistry:
    """
    Registry manages:
    - Module availability (AVAILABLE_MODULES)
    - Module configurations (from YAML)
    - Module metadata
    """
    
    def __init__(self, registry_path: str = "configs/module_registry.yaml"):
        self.registry_path = registry_path
        self.available_modules = AVAILABLE_MODULES  # From modules/__init__.py
        self.module_registry = self._load_registry()
        
    def _load_registry(self) -> Dict:
        """Load module registry from YAML"""
        registry_file = Path(self.registry_path)
        
        if not registry_file.exists():
            logger.warning(f"Registry not found: {self.registry_path}")
            logger.warning("Using empty config. Modules will use defaults.")
            return {}
        
        with open(registry_file, 'r', encoding='utf-8') as f:
            registry = yaml.safe_load(f) or {}
        
        logger.info(f"✅ Loaded registry: {len(registry)} modules configured")
        return registry
    
    def get_module_instance(self, 
                            module_name: str, 
                            override_config: Optional[dict] = None):
        """
        Get module instance with config from registry
        
        Args:
            module_name: Module class name (e.g., "DataPipelineModule")
            override_config: Optional config to override registry config
        
        Returns:
            Module instance
        """
        # Check module exists
        if module_name not in self.available_modules:
            available = ', '.join(self.available_modules.keys())
            raise ValueError(f"Module '{module_name}' not found. Available: {available}")
        
        # Get registry config
        registry_entry = self.module_registry.get(module_name, {})
        
        # Check if enabled
        if not registry_entry.get('enabled', True):
            raise ValueError(f"Module '{module_name}' is disabled in registry")
        
        # Load config from file if specified
        config = None
        config_path = registry_entry.get('config_path')
        
        if config_path:
            config = self._load_config(config_path)
        
        # Override with runtime config if provided
        if override_config:
            config = override_config
        
        # Use factory function from modules/__init__.py
        return get_module(module_name, config)
    
    def _load_config(self, config_path: str) -> dict:
        """Load module config from YAML file"""
        config_file = Path(config_path)
        
        if not config_file.exists():
            logger.warning(f"Config not found: {config_path}, using defaults")
            return {}
        
        with open(config_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    
    def list_modules(self, enabled_only: bool = False) -> list:
        """List available modules"""
        if not enabled_only:
            return list(self.available_modules.keys())
        
        # Filter enabled modules from registry
        enabled = [
            name for name, config in self.module_registry.items()
            if config.get('enabled', True)
        ]
        return enabled
    
    def get_module_info(self, module_name: str) -> dict:
        """Get module metadata from registry"""
        if module_name not in self.available_modules:
            raise ValueError(f"Module '{module_name}' not found")
        
        return self.module_registry.get(module_name, {})