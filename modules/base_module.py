# modules/base_module.py

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from pathlib import Path
import yaml
from loguru import logger

@dataclass
class ModuleResult:
    """Standardized result format returned by all modules"""
    status: str  # 'success' | 'failed' | 'skipped'
    data: Any
    message: str
    context_updates: Optional[Dict[str, Any]] = None
    errors: Optional[List[str]] = None
    
    def is_success(self) -> bool:
        return self.status == 'success'
    
    def is_failed(self) -> bool:
        return self.status == 'failed'


class BaseModule(ABC):
    """
    Base class for all modules/agents.
    
    Each module wraps a sub-agent and provides a standardized interface.
    """
    
    DEFAULT_CONFIG_PATH: str = None
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = self.load_config(config_path)
        self.logger = logger.bind(module=self.module_name)

    @classmethod
    def load_config(cls, config_path: Optional[str] = None) -> Dict:
        """
        Load module configuration from YAML file.
        
        Args:
            config_path: Path to config file. If None, uses DEFAULT_CONFIG_PATH
            
        Returns:
            Configuration dictionary
        """
        # Use provided path or fall back to default
        if config_path is None:
            if cls.DEFAULT_CONFIG_PATH is None:
                logger.warning(f"{cls.__name__} has no DEFAULT_CONFIG_PATH defined. Returning empty config.")
                return {}
            config_path = cls.DEFAULT_CONFIG_PATH
        
        config_path = Path(config_path)
        
        # Fallback to default if not exists
        if not config_path.exists():
            if cls.DEFAULT_CONFIG_PATH:
                default_path = Path(cls.DEFAULT_CONFIG_PATH)
                logger.warning(f"❌ Config not found: {config_path}")
                logger.info(f"📂 Using default config: {default_path}")
                config_path = default_path
            else:
                logger.error(f"❌ Config not found: {config_path} and no DEFAULT_CONFIG_PATH defined")
                return {}
        
        # Load YAML
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            logger.info(f"✅ Config loaded from: {config_path}")
            return config
        except Exception as e:
            logger.error(f"❌ Failed to load config from {config_path}: {e}")
            return {}

    @abstractmethod
    def execute(self, context: Dict[str, Any], dependencies: Dict[str, Any]) -> ModuleResult:
        """
        Execute the module logic.
        
        Args:
            context: Shared context dict containing data from previous modules
            dependencies: Dict containing data from its dependencies
            
        Returns:
            ModuleResult with status and data
        """
        pass
    
    @property
    @abstractmethod
    def module_name(self) -> str:
        """Unique module name"""
        pass
    
    @property
    def dependencies(self) -> List[str]:
        """
        List of context keys required by this module.
        
        Example: ['data_pipeline_result', 'validation_result']
        """
        return []
    
    @property
    def context_outputs(self) -> List[str]:
        """
        List of keys that this module will write into the context.
        
        Example: ['validation_result', 'validation_report']
        """
        return []
    
    def validate_dependencies(self, context: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        Validate that all required dependencies exist in the context.
        
        Returns:
            (is_valid, list_of_missing_dependencies)
        """
        missing = []
        for dep in self.dependencies:
            if dep not in context:
                missing.append(dep)
        
        return len(missing) == 0, missing
    
    def safe_execute(self,
                     context: Dict[str, Any],
                     dependencies: Dict[str, Any] = None) -> ModuleResult:
        """
        Wrapper around execute() with error handling.
        """
        try:
            if dependencies is None:
                dependencies = {}
            
            # Validate dependencies first
            is_valid, missing = self.validate_dependencies(context)
            if not is_valid:
                return ModuleResult(
                    status='failed',
                    data=None,
                    message=f"Missing dependencies: {missing}",
                    errors=missing
                )
            
            # Execute module
            self.logger.info(f"Executing {self.module_name}")
            result = self.execute(context, dependencies)
            
            if result.is_success():
                self.logger.info(f"{self.module_name} completed successfully")
            else:
                self.logger.warning(f"{self.module_name} completed with status: {result.status}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"{self.module_name} failed with error: {e}")
            return ModuleResult(
                status='failed',
                data=None,
                message=f"Execution failed: {str(e)}",
                errors=[str(e)]
            )