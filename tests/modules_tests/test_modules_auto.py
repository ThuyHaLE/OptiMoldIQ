# tests/modules_tests/test_modules_auto.py

"""
Auto-discovery module testing system
Tests all available modules automatically with pytest integration
REAL DEPENDENCY EXECUTION - Uses shared database (no mocking)
"""

import pytest
from pathlib import Path
from typing import Dict, Any, Type
from unittest.mock import patch

from modules import AVAILABLE_MODULES, BaseModule
from modules.base_module import ModuleResult


# ============================================================================
# PARAMETRIZED TEST CLASS
# ============================================================================

class TestModulesAutomatically:
    """
    Automatically test all enabled modules using pytest parametrization
    Each module becomes a separate test case
    
    Uses fixtures from conftest.py for dependency management
    """
    
    @pytest.fixture
    def module_fixture(self, request, module_registry):
        """
        Fixture that provides module class and config for each test
        
        Uses module_registry from conftest.py (session-scoped)
        
        Returns:
            tuple: (module_name, module_class, config_path, module_info)
        """
        module_name = request.param
        
        if module_name not in AVAILABLE_MODULES:
            pytest.skip(f"Module {module_name} not in AVAILABLE_MODULES")
        
        if module_name not in module_registry:
            pytest.skip(f"Module {module_name} not in registry")
        
        module_class = AVAILABLE_MODULES[module_name]
        module_info = module_registry[module_name]
        config_path = module_info.get('config_path')
        
        if not config_path:
            pytest.skip(f"Module {module_name} has no config_path")
        
        return module_name, module_class, config_path, module_info
    
    # ========================================================================
    # TEST 1: MODULE CREATION
    # ========================================================================
    
    @pytest.mark.parametrize('module_fixture', 
                            [name for name in AVAILABLE_MODULES.keys()],
                            indirect=True)
    @pytest.mark.smoke
    @pytest.mark.no_dependencies
    def test_module_creation(self, module_fixture):
        """Test that module can be instantiated"""
        module_name, module_class, config_path, _ = module_fixture
        
        module = module_class(config_path)
        
        assert module is not None
        assert hasattr(module, 'module_name')
        assert hasattr(module, 'dependencies')
        assert hasattr(module, 'context_outputs')
    
    # ========================================================================
    # TEST 2: CONFIG LOADING
    # ========================================================================
    
    @pytest.mark.parametrize('module_fixture',
                            [name for name in AVAILABLE_MODULES.keys()],
                            indirect=True)
    @pytest.mark.no_dependencies
    def test_module_config_loading(self, module_fixture):
        """Test that module loads config correctly"""
        module_name, module_class, config_path, _ = module_fixture
        
        config_path_obj = Path(config_path)
        
        # Test with existing config
        if config_path_obj.exists():
            module = module_class(config_path)
            assert module.config is not None
            assert isinstance(module.config, dict)
        else:
            pytest.skip(f"Config file not found: {config_path}")
    
    # ========================================================================
    # TEST 3: DEPENDENCY VALIDATION
    # ========================================================================
    
    @pytest.mark.parametrize('module_fixture',
                            [name for name in AVAILABLE_MODULES.keys()],
                            indirect=True)
    @pytest.mark.no_dependencies
    def test_module_dependencies_validation(self, module_fixture):
        """Test dependency validation logic"""
        module_name, module_class, config_path, _ = module_fixture
        
        module = module_class(config_path)
        
        # Test with empty context
        is_valid, missing = module.validate_dependencies({})
        
        if module.dependencies:
            # Should fail with empty context
            assert not is_valid
            assert len(missing) > 0
            
            # Test with successful mock context
            mock_context = {
                dep: ModuleResult(
                    status='success',
                    data={'mock': True},
                    message=f'Mock {dep}'
                )
                for dep in module.dependencies
            }
            is_valid, missing = module.validate_dependencies(mock_context)
            assert is_valid
            assert len(missing) == 0
            
            # Test with failed dependency
            failed_context = {
                dep: ModuleResult(
                    status='failed',
                    data=None,
                    message=f'Failed {dep}'
                )
                for dep in module.dependencies
            }
            is_valid, missing = module.validate_dependencies(failed_context)
            assert not is_valid
            assert len(missing) == len(module.dependencies)
        else:
            # No dependencies - should always pass
            assert is_valid
            assert len(missing) == 0
    
    # ========================================================================
    # TEST 4: INTERFACE COMPLIANCE
    # ========================================================================
    
    @pytest.mark.parametrize('module_fixture',
                            [name for name in AVAILABLE_MODULES.keys()],
                            indirect=True)
    @pytest.mark.smoke
    @pytest.mark.no_dependencies
    def test_module_interface_compliance(self, module_fixture):
        """Test that module implements required interface"""
        module_name, module_class, config_path, _ = module_fixture
        
        module = module_class(config_path)
        
        # Check required methods
        assert hasattr(module, 'execute') and callable(module.execute)
        assert hasattr(module, 'safe_execute') and callable(module.safe_execute)
        assert hasattr(module, 'validate_dependencies') and callable(module.validate_dependencies)
        
        # Check properties
        assert hasattr(module, 'module_name')
        assert hasattr(module, 'dependencies')
        assert hasattr(module, 'context_outputs')
        
        # Check inheritance
        assert isinstance(module, BaseModule)
        
        # Check property types
        assert isinstance(module.module_name, str)
        assert isinstance(module.dependencies, list)
        assert isinstance(module.context_outputs, list)


# ============================================================================
# TESTS WITH REAL DEPENDENCIES
# ============================================================================

class TestModulesWithDependencies:
    """
    Test modules with REAL dependency execution
    Dependencies are executed first, data stored in shared DB
    """
    
    @pytest.mark.parametrize('module_name', 
                            [name for name in AVAILABLE_MODULES.keys()])
    @pytest.mark.requires_dependencies
    def test_module_with_real_dependencies(self, 
                                           module_name,
                                           module_fixture_factory,
                                           module_context_factory,
                                           print_dependency_graph):
        """
        Test module execution with REAL dependencies
        Dependencies are executed and results stored in shared DB
        """
        # Get module
        try:
            module = module_fixture_factory(module_name)
        except pytest.skip.Exception:
            pytest.skip(f"Module {module_name} not available")
        
        # Skip if no dependencies
        if not module.dependencies:
            pytest.skip(f"Module {module_name} has no dependencies to test")
        
        # Print dependency graph for debugging
        print_dependency_graph(module_name)
        
        # Get context (this will execute all dependencies)
        context = module_context_factory(module_name)
        
        # Validate all dependencies succeeded
        is_valid, missing = module.validate_dependencies(context)
        assert is_valid, f"Dependencies failed or missing: {missing}"
        
        # All dependencies should be successful
        for dep_name in module.dependencies:
            assert dep_name in context, f"Dependency {dep_name} not in context"
            assert context[dep_name].is_success(), \
                f"Dependency {dep_name} failed: {context[dep_name].message}"
    
    @pytest.mark.parametrize('module_name',
                            [name for name in AVAILABLE_MODULES.keys()])
    @pytest.mark.requires_dependencies
    def test_module_execution_with_dependencies(self,
                                                module_name,
                                                module_fixture_factory,
                                                module_context_factory,
                                                assert_module_success):
        """
        Test full module execution with dependencies
        This is the REAL end-to-end test
        """
        try:
            module = module_fixture_factory(module_name)
        except pytest.skip.Exception:
            pytest.skip(f"Module {module_name} not available")
        
        # Get context with all dependencies executed
        context = module_context_factory(module_name)
        
        # Execute module
        result = module.safe_execute(context)
        
        # Assert success
        assert_module_success(result)


# ============================================================================
# DEPENDENCY GRAPH TESTS
# ============================================================================

class TestModuleDependencyGraph:
    """
    Test dependency graph analysis and resolution
    """
    
    @pytest.mark.parametrize('module_name',
                            [name for name in AVAILABLE_MODULES.keys()])
    @pytest.mark.no_dependencies
    def test_dependency_graph_resolution(self,
                                         module_name,
                                         module_dependency_graph,
                                         available_modules):
        """
        Test that dependency graph can resolve execution order
        """
        if module_name not in available_modules:
            pytest.skip(f"Module {module_name} not available")
        
        # Get execution order
        execution_order = module_dependency_graph.get_execution_order(module_name)
        
        # Should include at least the module itself
        assert module_name in execution_order
        assert execution_order[-1] == module_name  # Module should be last
        
        # Get dependencies
        dependencies = module_dependency_graph.get_all_dependencies(module_name)
        
        # All dependencies should appear before the module in execution order
        module_index = execution_order.index(module_name)
        for dep in dependencies:
            assert dep in execution_order
            dep_index = execution_order.index(dep)
            assert dep_index < module_index, \
                f"Dependency {dep} should come before {module_name}"
    
    def test_circular_dependency_detection(self, module_dependency_graph):
        """
        Test that circular dependencies are handled gracefully
        (Should not happen, but good to check)
        """
        # This test would need modules with circular deps
        # For now, just check that all modules resolve
        from modules import AVAILABLE_MODULES
        
        for module_name in AVAILABLE_MODULES.keys():
            try:
                order = module_dependency_graph.get_execution_order(module_name)
                # Should not have duplicates (sign of circular dependency)
                assert len(order) == len(set(order)), \
                    f"Circular dependency detected in {module_name}: {order}"
            except Exception as e:
                pytest.fail(f"Failed to resolve {module_name}: {e}")


# ============================================================================
# TESTS WITHOUT DEPENDENCIES (Unit Tests)
# ============================================================================

class TestModulesWithoutDependencies:
    """
    Test modules that have NO dependencies
    These are pure unit tests
    """
    
    def get_modules_without_dependencies(self, available_modules, module_registry):
        """Get list of modules with no dependencies"""
        no_dep_modules = []
        for name, module_class in available_modules.items():
            if name not in module_registry:
                continue
            config_path = module_registry[name].get('config_path')
            try:
                module = module_class(config_path)
                if not module.dependencies:
                    no_dep_modules.append(name)
            except:
                pass
        return no_dep_modules
    
    @pytest.mark.no_dependencies
    def test_modules_without_dependencies(self,
                                          available_modules,
                                          module_registry,
                                          module_fixture_factory,
                                          create_empty_context,
                                          assert_module_success):
        """
        Test all modules that have no dependencies
        These can run independently
        """
        no_dep_modules = self.get_modules_without_dependencies(
            available_modules, module_registry
        )
        
        if not no_dep_modules:
            pytest.skip("No modules without dependencies found")
        
        print(f"\n📋 Testing {len(no_dep_modules)} modules without dependencies:")
        print(f"   {', '.join(no_dep_modules)}\n")
        
        for module_name in no_dep_modules:
            print(f"Testing {module_name}...")
            
            module = module_fixture_factory(module_name)
            context = create_empty_context()
            
            result = module.safe_execute(context)
            assert_module_success(result)


# ============================================================================
# COMPREHENSIVE TEST SUITE
# ============================================================================

class TestModulesComprehensive:
    """
    Comprehensive test that validates entire module pipeline
    """
    
    @pytest.mark.integration
    def test_full_pipeline_execution(self,
                                     enabled_modules,
                                     module_dependency_executor,
                                     module_dependency_graph):
        """
        Test executing all enabled modules in dependency order
        This is the FULL END-TO-END test
        """
        if not enabled_modules:
            pytest.skip("No enabled modules")
        
        print("\n" + "="*80)
        print("FULL PIPELINE EXECUTION TEST")
        print("="*80)
        
        # Get all module names
        all_modules = [name for name, _ in enabled_modules]
        
        # Find modules with no dependencies (entry points)
        entry_points = []
        for module_name in all_modules:
            deps = module_dependency_graph.get_all_dependencies(module_name)
            if not deps:
                entry_points.append(module_name)
        
        print(f"\n📍 Entry points (no dependencies): {entry_points}")
        
        # Execute each module (with dependencies)
        results = {}
        for module_name in all_modules:
            print(f"\n{'='*60}")
            print(f"Testing: {module_name}")
            print(f"{'='*60}")
            
            context = module_dependency_executor.execute_with_dependencies(module_name)
            results[module_name] = context.get(module_name)
            
            if results[module_name]:
                if results[module_name].is_success():
                    print(f"✅ {module_name}: SUCCESS")
                else:
                    print(f"❌ {module_name}: FAILED - {results[module_name].message}")
        
        # Summary
        print("\n" + "="*80)
        print("SUMMARY")
        print("="*80)
        
        passed = sum(1 for r in results.values() if r and r.is_success())
        failed = sum(1 for r in results.values() if r and not r.is_success())
        
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print("="*80)
        
        # Assert all succeeded
        for module_name, result in results.items():
            assert result is not None, f"{module_name} returned None"
            assert result.is_success(), \
                f"{module_name} failed: {result.message}"


# ============================================================================
# SMOKE TESTS
# ============================================================================

@pytest.mark.smoke
def test_module_registry_exists(module_registry):
    """Quick test that registry file exists"""
    assert isinstance(module_registry, dict)
    assert len(module_registry) > 0


@pytest.mark.smoke
def test_available_modules_exist(available_modules):
    """Test that AVAILABLE_MODULES is populated"""
    assert isinstance(available_modules, dict)
    assert len(available_modules) > 0


@pytest.mark.smoke
def test_dependency_graph_available(module_dependency_graph):
    """Test that dependency graph is available"""
    assert module_dependency_graph is not None


@pytest.mark.smoke  
def test_dependency_executor_available(module_dependency_executor):
    """Test that dependency executor is available"""
    assert module_dependency_executor is not None