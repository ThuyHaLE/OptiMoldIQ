from typing import Dict, List, Set
from loguru import logger

class ModuleDependencyGraph:
    """
    Builds and resolves module dependency graph
    Ensures modules are executed in correct order
    Detects circular dependencies
    """
    
    def __init__(self, module_registry: Dict, available_modules: Dict):
        self.module_registry = module_registry
        self.available_modules = available_modules
    
    def get_execution_order(self, module_name: str) -> List[str]:
        """
        Get execution order for a module and all its dependencies
        Returns list in execution order (dependencies first)
        
        Example: If C depends on B, B depends on A
        Returns: ['A', 'B', 'C']
        
        Raises:
            ValueError: If circular dependency is detected
        """
        visited = set()
        rec_stack = set()  # Track recursion stack for cycle detection
        order = []
        
        def dfs(name: str, path: List[str]):
            """
            DFS with cycle detection
            
            Args:
                name: Current module name
                path: Current path (for error reporting)
            """
            # Circular dependency check
            if name in rec_stack:
                cycle_path = ' → '.join(path + [name])
                raise ValueError(
                    f"Circular dependency detected: {cycle_path}"
                )
            
            # Already visited - skip
            if name in visited:
                return
            
            # Check if module exists
            if name not in self.available_modules:
                logger.warning(f"Module {name} not found in AVAILABLE_MODULES")
                return
            
            if name not in self.module_registry:
                logger.warning(f"Module {name} not found in registry")
                return
            
            # Mark as being processed
            visited.add(name)
            rec_stack.add(name)
            
            # Get module config and instantiate
            module_class = self.available_modules[name]
            config_path = self.module_registry[name].get('config_path')
            
            try:
                module = module_class(config_path)
                deps = module.dependencies
                
                # Visit dependencies first (with updated path)
                for dep in deps:
                    dfs(dep, path + [name])
                
                # Add this module after all dependencies
                order.append(name)
                
            except Exception as e:
                logger.error(f"Failed to instantiate {name}: {e}")
                raise
            finally:
                # Remove from recursion stack
                rec_stack.remove(name)
        
        # Start DFS
        dfs(module_name, [])
        return order
    
    def get_all_dependencies(self, module_name: str) -> Set[str]:
        """
        Get all dependencies (direct and transitive) for a module
        
        Args:
            module_name: Module to analyze
            
        Returns:
            Set of module names that are dependencies
        """
        try:
            execution_order = self.get_execution_order(module_name)
            # Remove the module itself, keep only dependencies
            return set(execution_order[:-1]) if execution_order else set()
        except ValueError as e:
            # Circular dependency or other error
            logger.error(f"Failed to get dependencies for {module_name}: {e}")
            raise
    
    def has_circular_dependencies(self) -> bool:
        """
        Check if any module has circular dependencies
        
        Returns:
            True if circular dependencies exist
        """
        for module_name in self.available_modules.keys():
            try:
                self.get_execution_order(module_name)
            except ValueError as e:
                if "circular" in str(e).lower():
                    return True
        return False
    
    def validate_all_dependencies(self) -> Dict[str, List[str]]:
        """
        Validate all module dependencies
        
        Returns:
            Dict mapping module names to list of issues (empty if valid)
        """
        issues = {}
        
        for module_name in self.available_modules.keys():
            module_issues = []
            
            try:
                # Try to get execution order
                self.get_execution_order(module_name)
            except ValueError as e:
                module_issues.append(str(e))
            except Exception as e:
                module_issues.append(f"Unexpected error: {e}")
            
            if module_issues:
                issues[module_name] = module_issues
        
        return issues