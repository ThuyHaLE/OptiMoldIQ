# tests/modules_tests/conftest.py - Module-specific fixtures

"""
Module testing conftest - provides module registry and dependency management
Automatically triggers real module dependencies (no mocking - uses shared DB)
"""

import pytest
from pathlib import Path
from typing import Dict, List, Set
from loguru import logger
from configs.shared.agent_report_format import ExecutionStatus
from modules.registry.registry_loader import ModuleRegistryLoader
from modules.base_module import ModuleResult


# ============================================================================
# MODULE REGISTRY FIXTURES
# ============================================================================

@pytest.fixture(scope="session")
def module_registry():
    """
    Load module registry once for entire test session
    Similar to dependency_provider for agents
    """
    return ModuleRegistryLoader.load_registry('configs/module_registry.yaml')


@pytest.fixture(scope="session")
def available_modules():
    """Get all available module classes"""
    from modules import AVAILABLE_MODULES
    return AVAILABLE_MODULES


@pytest.fixture(scope="session")
def enabled_modules(module_registry, available_modules):
    """
    Get list of enabled modules from registry
    Only modules that are enabled and exist in code
    """
    enabled = []
    for name, info in module_registry.items():
        if info.get('enabled', True) and name in available_modules:
            enabled.append((name, info))
    return enabled



# Fixture provide all available dependency policies
@pytest.fixture(scope="session")
def all_dependency_policies():
    from modules.dependency_policies import AVAILABLE_POLICIES
    return list(AVAILABLE_POLICIES.values())

# ============================================================================
# DEPENDENCY GRAPH BUILDER
# ============================================================================

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


# ============================================================================
# MODULE DEPENDENCY EXECUTOR
# ============================================================================

class ModuleDependencyExecutor:
    """
    Executes modules with their dependencies
    Uses shared database - NO MOCKING
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
        Returns context with all dependency results
        
        Args:
            module_name: The module to execute
            
        Returns:
            Dict[str, ModuleResult] - context with all results
        """
        # Get execution order
        execution_order = self.dependency_graph.get_execution_order(module_name)
        
        logger.info(f"📋 Execution order for {module_name}: {execution_order}")
        
        context = {}
        
        # Execute in order
        for mod_name in execution_order:
            if mod_name in self._execution_results:
                # Already executed, reuse result
                logger.info(f"♻️  Reusing cached result for {mod_name}")
                context[mod_name] = self._execution_results[mod_name]
            else:
                # Execute module
                logger.info(f"🚀 Executing {mod_name}...")
                result = self._execute_single_module(mod_name, context)
                
                # Cache result
                self._execution_results[mod_name] = result
                context[mod_name] = result
                
                if not result.is_success():
                    logger.error(f"❌ {mod_name} failed: {result.message}")
                    # Stop execution if dependency fails
                    break
                else:
                    logger.success(f"✅ {mod_name} completed successfully")
        
        return context
    
    def _execute_single_module(self, module_name: str, context: Dict[str, ModuleResult]) -> ModuleResult:
        """
        Execute a single module with given context
        
        Args:
            module_name: Module to execute
            context: Context with dependency results
            
        Returns:
            ModuleResult
        """
        try:
            # Get module class
            module_class = self.available_modules[module_name]
            
            # Get config
            config_path = self.module_registry[module_name].get('config_path')
            
            # Instantiate
            module = module_class(config_path)
            
            # Execute with context
            result = module.safe_execute(context)
            
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
        
        context = {}
        
        # Execute each dependency
        for dep_name in dependencies:
            if dep_name in self._execution_results:
                context[dep_name] = self._execution_results[dep_name]
            else:
                # Execute dependency chain
                dep_context = self.execute_with_dependencies(dep_name)
                # Take only the final result
                context[dep_name] = dep_context[dep_name]
        
        return context
    
    def cleanup(self):
        """Cleanup test artifacts"""
        import shutil
        for dir_path in self._test_dirs.values():
            if dir_path.exists():
                shutil.rmtree(dir_path)


@pytest.fixture(scope="session")
def module_dependency_executor(module_registry, available_modules):
    """
    Session-scoped dependency executor for modules
    Manages real module execution with shared database
    """
    executor = ModuleDependencyExecutor(module_registry, available_modules)
    yield executor
    executor.cleanup()


@pytest.fixture(scope="session")
def module_dependency_graph(module_registry, available_modules):
    """
    Provides dependency graph for analyzing module relationships
    """
    return ModuleDependencyGraph(module_registry, available_modules)


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
            # context now contains ProgressTrackingModule and FeaturesExtractingModule results
    """
    def _get_context(module_name: str) -> Dict[str, ModuleResult]:
        return module_dependency_executor.get_context_for_module(module_name)
    
    return _get_context


@pytest.fixture
def sample_module_config(tmp_path):
    """Create a sample module configuration file"""
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


@pytest.fixture
def module_fixture_factory(module_registry, available_modules):
    """
    Factory fixture to create module instances for testing
    
    Usage in test:
        def test_something(module_fixture_factory):
            module = module_fixture_factory('InitialPlanningModule')
            result = module.safe_execute(context)
    """
    def _create_module(module_name: str, config_path: str = None):
        if module_name not in available_modules:
            pytest.skip(f"Module {module_name} not available")
        
        if module_name not in module_registry:
            pytest.skip(f"Module {module_name} not in registry")
        
        module_class = available_modules[module_name]
        
        if config_path is None:
            config_path = module_registry[module_name].get('config_path')
        
        return module_class(config_path)
    
    return _create_module


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


def pytest_collection_modifyitems(config, items):
    """
    Modify test collection for module tests
    Add markers automatically
    """
    for item in items:
        # Auto-mark module tests
        if "module_tests" in str(item.fspath):
            item.add_marker(pytest.mark.module_test)
        
        # Mark tests with dependencies
        if "with_dependencies" in item.nodeid.lower():
            item.add_marker(pytest.mark.requires_dependencies)


# ============================================================================
# HELPER FIXTURES
# ============================================================================

@pytest.fixture
def assert_module_success():
    """Helper fixture for asserting module success"""
    def _assert(result):
        successful_statuses = {
            ExecutionStatus.SUCCESS.value,
            ExecutionStatus.DEGRADED.value,
            ExecutionStatus.WARNING.value
        }
        assert isinstance(result, ModuleResult)
        assert result.status in successful_statuses, f"Module failed: {result.message}"
        assert result.data is not None
    return _assert


@pytest.fixture
def create_empty_context():
    """
    Create an empty context (for modules with no dependencies)
    
    Usage:
        def test_module_without_deps(module_fixture_factory, create_empty_context):
            module = module_fixture_factory('DataPipelineModule')
            context = create_empty_context()
            result = module.safe_execute(context)
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
        order = module_dependency_graph.get_execution_order(module_name)
        deps = module_dependency_graph.get_all_dependencies(module_name)
        
        print(f"\n{'='*60}")
        print(f"Dependency Analysis for: {module_name}")
        print(f"{'='*60}")
        print(f"Execution Order: {' → '.join(order)}")
        print(f"Dependencies: {deps}")
        print(f"{'='*60}\n")
    
    return _print