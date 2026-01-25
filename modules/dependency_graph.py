from typing import Dict, List, Set
from loguru import logger
from modules.base_module import ModuleResult

class ModuleDependencyGraph:
    """
    Builds and resolves module dependency graph
    Ensures modules are executed in correct order
    """
    
    def __init__(self, module_registry: Dict, available_modules: Dict):
        self.module_registry = module_registry
        self.available_modules = available_modules
        self._execution_cache: Dict[str, ModuleResult] = {}
    
    def get_execution_order(self, module_name: str) -> List[str]:
        """
        Get execution order for a module and all its dependencies
        Returns list in execution order (dependencies first)
        
        Example: If C depends on B, B depends on A
        Returns: ['A', 'B', 'C']
        """
        visited = set()
        order = []
        
        def dfs(name: str):
            if name in visited:
                return
            
            visited.add(name)
            
            # Get module class
            if name not in self.available_modules:
                logger.warning(f"Module {name} not found in AVAILABLE_MODULES")
                return
            
            module_class = self.available_modules[name]
            
            # Get module config
            if name not in self.module_registry:
                logger.warning(f"Module {name} not found in registry")
                return
            
            config_path = self.module_registry[name].get('config_path')
            
            # Instantiate to get dependencies
            try:
                module = module_class(config_path)
                deps = module.dependencies
                
                # Visit dependencies first
                for dep in deps:
                    dfs(dep)
                
                # Add this module after dependencies
                order.append(name)
                
            except Exception as e:
                logger.error(f"Failed to instantiate {name}: {e}")
        
        dfs(module_name)
        return order
    
    def get_all_dependencies(self, module_name: str) -> Set[str]:
        """
        Get all dependencies (direct and transitive) for a module
        
        Returns:
            Set of module names that are dependencies
        """
        execution_order = self.get_execution_order(module_name)
        # Remove the module itself, keep only dependencies
        return set(execution_order[:-1]) if execution_order else set()