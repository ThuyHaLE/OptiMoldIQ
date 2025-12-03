# modules/__init__.py

from modules.base_module import BaseModule, ModuleResult
from modules.data_pipeline_module import DataPipelineModule
from modules.analytics_module import AnalyticsModule
from modules.dashboard_module import DashboardModule
from modules.validation_module import ValidationModule

# Registry of availble modules
AVAILABLE_MODULES = {
    'DataPipelineModule': DataPipelineModule,
    'AnalyticsModule': AnalyticsModule,
    'DashboardModule': DashboardModule,
    'ValidationModule': ValidationModule
}

def get_module(name: str, config: dict = None) -> BaseModule:
    """
    Factory function to create module instance
    
    Args:
        name: Module name
        config: Module optional config
        
    Returns:
        Module instance
    """
    if name not in AVAILABLE_MODULES:
        available = ', '.join(AVAILABLE_MODULES.keys())
        raise ValueError(f"Module '{name}' not found. Available modules: {available}")
    
    module_class = AVAILABLE_MODULES[name]
    return module_class(config)


def list_available_modules() -> list[str]:
    """List available modules"""
    return list(AVAILABLE_MODULES.keys())


__all__ = [
    'BaseModule',
    'ModuleResult',

    'DataPipelineModule',
    'AnalyticsModule',
    'DashboardModule',
    'ValidationModule'
    
    'get_module',
    'list_available_modules',
    'AVAILABLE_MODULES'
]