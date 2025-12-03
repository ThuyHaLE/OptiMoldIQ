import yaml
import json
from pathlib import Path
from typing import Dict, Optional
from modules import AVAILABLE_MODULES
from loguru import logger

class ModuleRegistryLoader:
    """Load module configuration from external files"""

    DEFAULT_REGISTRY_PATH = "configs/module_registry.yaml"
    SUPPORTED_FORMATS = ['.yaml', '.yml', '.json']
    
    @classmethod
    def load_registry(cls, 
                      registry_path: Optional[str] = None) -> Dict[str, Dict]:
        """
        Load module registry from file
        
        Args:
            registry_path: Path to registry file (YAML or JSON)
                          If None, uses DEFAULT_REGISTRY_PATH
        
        Returns:
            Dict mapping module names to their config info
        """
        if registry_path is None:
            registry_path = cls.DEFAULT_REGISTRY_PATH
        
        registry_file = Path(registry_path)
        
        # Check if file exists
        if not registry_file.exists():
            logger.warning("⚠️  Registry file not found: {}", registry_path)
            logger.warning("   Using empty registry. Create file to add modules.")
            return {}
        
        # Load based on file extension
        suffix = registry_file.suffix.lower()
        
        try:
            if suffix in ['.yaml', '.yml']:
                with open(registry_file, 'r', encoding='utf-8') as f:
                    registry = yaml.safe_load(f) or {}
                logger.info("✅ Loaded registry from YAML: {}", registry_path)
                
            elif suffix == '.json':
                with open(registry_file, 'r', encoding='utf-8') as f:
                    registry = json.load(f)
                logger.info("✅ Loaded registry from JSON: {}", registry_path)
                
            else:
                logger.warning("❌ Unsupported format: {}", suffix)
                logger.warning("   Supported: {}", cls.SUPPORTED_FORMATS)
                return {}
            
            # Validate structure
            if not isinstance(registry, dict):
                logger.warning("❌ Invalid registry format: expected dict, got {}", type(registry))
                return {}
            
            # Show loaded modules
            logger.info("📦 Found {} module(s) in registry", len(registry))
            
            return registry
            
        except Exception as e:
            logger.error("❌ Error loading registry: {}", e)
            return {}
    
    @classmethod
    def save_registry_template(cls, 
                               output_path: Optional[str] = None):
        """
        Generate a template registry file
        
        Args:
            output_path: Where to save template (default: configs/module_registry.yaml)
        """
        if output_path is None:
            output_path = cls.DEFAULT_REGISTRY_PATH
        
        # Create template based on AVAILABLE_MODULES
        template = {}
        
        for module_name in AVAILABLE_MODULES.keys():
            # Generate likely config path
            config_name = ''.join(['_' + c.lower() if c.isupper() else c 
                                  for c in module_name]).lstrip('_')
            
            template[module_name] = {
                'config_path': f'configs/modules/{config_name}.yaml',
                'enabled': True,
                'description': f'Configuration for {module_name}'
            }
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Save as YAML by default
        with open(output_file, 'w', encoding='utf-8') as f:
            yaml.dump(template, f, default_flow_style=False, sort_keys=False)
        
        logger.info("✅ Template saved to: {}", output_path)
        logger.info("   Edit this file to configure your modules")
        
        return template