# tests/modules_tests/conftest.py

"""
Module testing conftest - provides module registry and dependency management
This conftest only tests modules inheriting from BaseModule
"""

import pytest
from pathlib import Path
from typing import Dict, List, Set, Optional
from loguru import logger
import yaml
import copy

from modules.base_module import ModuleResult, BaseModule
from modules import AVAILABLE_MODULES

# ============================================================================
# MODULE REGISTRY FIXTURES
# ============================================================================
@pytest.fixture(scope="session")
def module_registry():
    """
    Integration test fixture. Loads REAL module_registry.yaml
    """
    registry_file = Path('configs/module_registry.yaml')
    if not registry_file.exists():
        logger.warning(f"Registry not found. Using empty config. Modules will use defaults.")
        return {}
    with open(registry_file, 'r', encoding='utf-8') as f:
        registry = yaml.safe_load(f) or {}
    logger.info(f"✅ Loaded registry: {len(registry)} modules configured")
    return copy.deepcopy(registry)

@pytest.fixture(scope="session")
def available_modules():
    """
    Get all available module classes from modules/__init__.py
    These are PURE MODULES - no workflow logic
    """
    return AVAILABLE_MODULES


@pytest.fixture(scope="session")
def enabled_modules(module_registry, available_modules):
    """
    Get list of enabled modules from registry
    Only modules that are enabled and exist in code
    
    Returns:
        List of tuples: [(module_name, module_info), ...]
    """
    enabled = []
    for name, info in module_registry.items():
        if info.get('enabled', True) and name in available_modules:
            enabled.append((name, info))
    return enabled


# ============================================================================
# DEPENDENCY GRAPH FIXTURE
# ============================================================================
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
    
@pytest.fixture(scope="session")
def module_dependency_graph(module_registry, available_modules):
    """
    Provides dependency graph for analyzing module relationships
    Uses ModuleDependencyGraph from workflows/ package
    """
    return ModuleDependencyGraph(module_registry, available_modules)

# ============================================================================
# MODULE DEPENDENCY EXECUTOR (Simplified for Testing)
# ============================================================================

class TestModuleDependencyExecutor:
    """
    Simplified executor for testing modules
    Executes modules with their dependencies
    Uses shared database - NO MOCKING
    
    Note: This is a TEST-ONLY version. Production uses workflows.executor.WorkflowExecutor
    """
    
    def __init__(self, module_registry: Dict, available_modules: Dict):
        self.module_registry = module_registry
        self.available_modules = available_modules
        self.dependency_graph = ModuleDependencyGraph(module_registry, available_modules)
        self._execution_results: Dict[str, ModuleResult] = {}
        self._test_dirs = self._setup_test_dirs()
    
    def _setup_test_dirs(self) -> Dict[str, Path]:
        """Setup test directories"""
        dirs = {
            "db_dir": Path("tests/mock_database"),
            "shared_dir": Path("tests/shared_db"),
            "cache_dir": Path("tests/cache"),
            "reports_dir": Path("tests/reports")
        }
        for dir_path in dirs.values():
            dir_path.mkdir(parents=True, exist_ok=True)
        return dirs
    
    def execute_with_dependencies(self, module_name: str) -> Dict[str, ModuleResult]:
        """
        Execute a module and all its dependencies
        Returns dict with all dependency results
        
        Args:
            module_name: The module to execute
            
        Returns:
            Dict[str, ModuleResult] - results for all executed modules
            
        Raises:
            ValueError: If circular dependency detected
        """
        # Get execution order (this validates no circular deps)
        execution_order = self.dependency_graph.get_execution_order(module_name)
        
        logger.info(f"📋 Execution order for {module_name}: {execution_order}")
        
        results = {}
        
        # Execute in order
        for mod_name in execution_order:
            if mod_name in self._execution_results:
                # Already executed, reuse result
                logger.info(f"♻️  Reusing cached result for {mod_name}")
                results[mod_name] = self._execution_results[mod_name]
            else:
                # Execute module
                logger.info(f"🚀 Executing {mod_name}...")
                result = self._execute_single_module(mod_name)
                
                # Cache result
                self._execution_results[mod_name] = result
                results[mod_name] = result
                
                if not result.is_success():
                    logger.error(f"❌ {mod_name} failed: {result.message}")
                    # Continue execution even if dependency fails
                    # This allows tests to verify failure handling
                else:
                    logger.success(f"✅ {mod_name} completed successfully")
        
        return results
    
    def _execute_single_module(self, module_name: str) -> ModuleResult:
        """
        Execute a single module
        
        Args:
            module_name: Module to execute
            
        Returns:
            ModuleResult
        """
        try:
            # Get module class
            if module_name not in self.available_modules:
                raise ValueError(f"Module {module_name} not in AVAILABLE_MODULES")
            
            module_class = self.available_modules[module_name]
            
            # Get config
            if module_name not in self.module_registry:
                raise ValueError(f"Module {module_name} not in registry")
            
            config_path = self.module_registry[module_name].get('config_path')
            
            # Instantiate
            module = module_class(config_path)
            
            # Execute (NO parameters)
            result = module.safe_execute()
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to execute {module_name}: {e}")
            return ModuleResult(
                status='failed',
                data=None,
                message=f"Execution error: {str(e)}",
                errors=[str(e)]
            )
    
    def get_context_for_module(self, module_name: str) -> Dict[str, ModuleResult]:
        """
        Get context (all dependency results) for a module
        Only executes dependencies, NOT the module itself
        
        Args:
            module_name: Module needing context
            
        Returns:
            Dict[str, ModuleResult] with dependency results
        """
        # Get only dependencies (not the module itself)
        dependencies = self.dependency_graph.get_all_dependencies(module_name)
        
        if not dependencies:
            logger.info(f"Module {module_name} has no dependencies")
            return {}
        
        logger.info(f"Getting context for {module_name}, dependencies: {dependencies}")
        
        results = {}
        
        # Execute each dependency
        for dep_name in dependencies:
            if dep_name in self._execution_results:
                results[dep_name] = self._execution_results[dep_name]
            else:
                # Execute dependency chain
                dep_results = self.execute_with_dependencies(dep_name)
                # Take only the final result
                results[dep_name] = dep_results[dep_name]
        
        return results
    
    def clear_cache(self):
        """Clear execution cache - useful between test runs"""
        self._execution_results.clear()
        logger.info("Cleared execution cache")
    
    def cleanup(self):
        """Cleanup test artifacts"""
        import shutil
        for dir_path in self._test_dirs.values():
            if dir_path.exists():
                try:
                    shutil.rmtree(dir_path)
                    logger.info(f"Cleaned up {dir_path}")
                except Exception as e:
                    logger.warning(f"Failed to cleanup {dir_path}: {e}")


@pytest.fixture(scope="session")
def module_dependency_executor(module_registry, available_modules):
    """
    Session-scoped dependency executor for modules
    This is a TEST-ONLY executor (production uses workflows.executor.WorkflowExecutor)
    """
    executor = TestModuleDependencyExecutor(module_registry, available_modules)
    yield executor
    executor.cleanup()


# ============================================================================
# MODULE-SPECIFIC FIXTURES
# ============================================================================

@pytest.fixture
def module_context_factory(module_dependency_executor):
    """
    Factory to get context for any module
    Automatically executes dependencies
    
    Usage:
        def test_my_module(module_context_factory):
            context = module_context_factory('InitialPlanningModule')
            # context now contains all dependency results
    """
    def _get_context(module_name: str) -> Dict[str, ModuleResult]:
        return module_dependency_executor.get_context_for_module(module_name)
    
    return _get_context


@pytest.fixture
def module_fixture_factory(module_registry, available_modules):
    """
    Factory fixture to create module instances for testing
    
    Usage in test:
        def test_something(module_fixture_factory):
            module = module_fixture_factory('InitialPlanningModule')
            result = module.safe_execute()  # No parameters needed
    """
    def _create_module(module_name: str, config_path: Optional[str] = None):
        if module_name not in available_modules:
            pytest.skip(f"Module {module_name} not available")
        
        if module_name not in module_registry:
            pytest.skip(f"Module {module_name} not in registry")
        
        module_class = available_modules[module_name]
        
        # Validate it's a BaseModule
        if not issubclass(module_class, BaseModule):
            pytest.fail(f"{module_name} must inherit from BaseModule")
        
        if config_path is None:
            config_path = module_registry[module_name].get('config_path')
        
        if not config_path:
            pytest.skip(f"No config_path for module {module_name}")
        
        return module_class(config_path)
    
    return _create_module


@pytest.fixture
def sample_module_config(tmp_path):
    """Create a sample module configuration file for testing"""
    import yaml
    
    config = {
        'project_root': str(tmp_path),
        'module_settings': {
            'enabled': True,
            'timeout': 300
        }
    }
    
    config_file = tmp_path / "test_config.yaml"
    with open(config_file, 'w') as f:
        yaml.dump(config, f)
    
    return str(config_file)


# ============================================================================
# HELPER FIXTURES
# ============================================================================

@pytest.fixture
def assert_module_success():
    """
    Helper fixture for asserting module success
    
    Usage:
        def test_module(assert_module_success):
            result = module.safe_execute()
            assert_module_success(result)
    """
    def _assert(result: ModuleResult):
        assert isinstance(result, ModuleResult), \
            f"Result must be ModuleResult, got {type(result)}"
        
        assert result.status == "success", \
            f"Module failed with status '{result.status}': {result.message}"
        
        # Don't assert data is not None - it can be None for some modules
        # Just check that we have a proper result object
        
    return _assert


@pytest.fixture
def create_empty_context():
    """
    Create an empty context (for modules with no dependencies)
    
    Note: This fixture is now DEPRECATED since execute() takes no parameters
    Kept for backward compatibility
    
    Usage:
        def test_module_without_deps(module_fixture_factory):
            module = module_fixture_factory('DataPipelineModule')
            result = module.safe_execute()  # No context needed
    """
    def _create() -> Dict[str, ModuleResult]:
        return {}
    
    return _create


@pytest.fixture
def print_dependency_graph(module_dependency_graph):
    """
    Helper to print dependency graph for debugging
    
    Usage:
        def test_something(print_dependency_graph):
            print_dependency_graph('InitialPlanningModule')
    """
    def _print(module_name: str):
        try:
            order = module_dependency_graph.get_execution_order(module_name)
            deps = module_dependency_graph.get_all_dependencies(module_name)
            
            print(f"\n{'='*60}")
            print(f"Dependency Analysis for: {module_name}")
            print(f"{'='*60}")
            print(f"Execution Order: {' → '.join(order)}")
            print(f"Dependencies: {deps if deps else 'None'}")
            print(f"{'='*60}\n")
        except ValueError as e:
            print(f"\n{'='*60}")
            print(f"Dependency Analysis for: {module_name}")
            print(f"{'='*60}")
            print(f"ERROR: {e}")
            print(f"{'='*60}\n")
    
    return _print


# ============================================================================
# PYTEST HOOKS (Module-specific)
# ============================================================================

def pytest_configure(config):
    """Register custom markers for module tests"""
    config.addinivalue_line(
        "markers", "module_test: mark test as module test"
    )
    config.addinivalue_line(
        "markers", "requires_dependencies: mark test as requiring real dependency execution"
    )
    config.addinivalue_line(
        "markers", "no_dependencies: mark test as not requiring dependencies (unit test)"
    )
    config.addinivalue_line(
        "markers", "smoke: mark test as smoke test (quick validation)"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test (full pipeline)"
    )


def pytest_collection_modifyitems(config, items):
    """
    Modify test collection for module tests
    Add markers automatically based on test names and paths
    """
    for item in items:
        # Auto-mark module tests
        if "module_tests" in str(item.fspath):
            item.add_marker(pytest.mark.module_test)
        
        # Mark tests with dependencies
        if "with_dependencies" in item.nodeid.lower():
            item.add_marker(pytest.mark.requires_dependencies)
        
        # Mark smoke tests
        if "smoke" in item.nodeid.lower() or item.get_closest_marker("smoke"):
            item.add_marker(pytest.mark.smoke)


# ============================================================================
# SESSION CLEANUP
# ============================================================================

@pytest.fixture(scope="session", autouse=True)
def session_cleanup():
    """Auto cleanup after entire test session"""
    yield
    # Cleanup happens here after all tests
    logger.info("Test session completed - all module tests finished")