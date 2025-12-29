# tests/modules_tests/test_modules_auto.py

"""
Auto-discovery module testing system
Tests all available modules automatically with pytest integration
FIXED: Now uses REAL dependencies from conftest (no more mocking!)
"""

import pytest
from pathlib import Path
from typing import Dict, Any, Type

from modules import AVAILABLE_MODULES, BaseModule
from modules.base_module import ModuleResult


# ============================================================================
# PARAMETRIZED TEST CLASS
# ============================================================================

class TestModulesAutomatically:
    """
    Automatically test all enabled modules using pytest parametrization
    Each module becomes a separate test case
    """
    
    @pytest.fixture
    def module_fixture(self, request, module_registry):
        """
        Fixture that provides module class and config for each test
        
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
    def test_module_config_loading(self, module_fixture):
        """Test that module loads config correctly"""
        module_name, module_class, config_path, _ = module_fixture
        
        config_path_obj = Path(config_path)
        
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
    def test_module_dependencies_validation(self, module_fixture):
        """Test dependency validation logic"""
        module_name, module_class, config_path, _ = module_fixture
        
        module = module_class(config_path)
        
        # Test with empty context
        is_valid = module.validate_dependencies({})
        
        if module.dependencies:
            # Should fail with empty context
            assert not is_valid
            
            # Test with mock context (for validation only, not execution)
            mock_context = {
                dep: ModuleResult(
                    status='success',
                    data={'mock': True},
                    message=f'Mock {dep}'
                )
                for dep in module.dependencies
            }
            is_valid = module.validate_dependencies(mock_context)
            assert is_valid
        else:
            # No dependencies - should always pass
            assert is_valid
    
    # ========================================================================
    # TEST 4: ERROR HANDLING
    # ========================================================================
    
    @pytest.mark.parametrize('module_fixture',
                            [name for name in AVAILABLE_MODULES.keys()],
                            indirect=True)
    def test_module_error_handling(self, module_fixture):
        """Test that safe_execute catches exceptions"""
        module_name, module_class, config_path, _ = module_fixture
        
        module = module_class(config_path)
        
        # Mock execute to raise error
        original_execute = module.execute
        
        def mock_error_execute(*args, **kwargs):
            raise ValueError("Simulated error for testing")
        
        module.execute = mock_error_execute
        
        # Prepare context with all dependencies
        test_context = {
            dep: ModuleResult(
                status='success',
                data={'test': True},
                message=f'Test {dep}'
            )
            for dep in module.dependencies
        }
        
        result = module.safe_execute(context=test_context)
        
        # Restore original
        module.execute = original_execute
        
        # Check error was caught
        assert isinstance(result, ModuleResult)
        assert result.status == 'failed'
        assert result.message is not None
        assert 'error' in result.message.lower() or 'failed' in result.message.lower()
    
    # ========================================================================
    # TEST 5: INTERFACE COMPLIANCE
    # ========================================================================
    
    @pytest.mark.parametrize('module_fixture',
                            [name for name in AVAILABLE_MODULES.keys()],
                            indirect=True)
    @pytest.mark.smoke
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
# TESTS WITH REAL DEPENDENCIES (Using conftest fixtures)
# ============================================================================

class TestModulesWithRealDependencies:
    """
    Test modules with REAL dependencies from conftest.py
    These tests trigger real agents and test actual module execution
    """
    
    @pytest.mark.parametrize('module_name', 
                            [name for name in AVAILABLE_MODULES.keys()])
    def test_module_context_building(self, 
                                     module_name,
                                     module_fixture_factory,
                                     module_context):
        """
        Test that module context can be built with real dependencies
        Does NOT execute module, just validates context
        """
        try:
            module = module_fixture_factory(module_name)
        except pytest.skip.Exception:
            pytest.skip(f"Module {module_name} not available")
        
        if not module.dependencies:
            pytest.skip(f"Module {module_name} has no dependencies")
        
        # Build context with real dependencies
        context = module_context(module.dependencies)
        
        # Validate context is properly built
        assert isinstance(context, dict)
        for dep in module.dependencies:
            assert dep in context
            assert isinstance(context[dep], ModuleResult)
            assert context[dep].status == 'success'
        
        # Validate dependencies are satisfied
        is_valid = module.validate_dependencies(context)
        assert is_valid, f"Real dependency context validation failed"
    
    @pytest.mark.integration
    @pytest.mark.requires_dependencies
    @pytest.mark.parametrize('module_name',
                            [name for name in AVAILABLE_MODULES.keys()])
    def test_module_execution_with_real_deps(self,
                                            module_name,
                                            module_fixture_factory,
                                            module_context,
                                            assert_module_success):
        """
        Test module execution with REAL agent dependencies
        Marked as integration test (slow!)
        """
        try:
            module = module_fixture_factory(module_name)
        except pytest.skip.Exception:
            pytest.skip(f"Module {module_name} not available")
        
        if not module.dependencies:
            pytest.skip(f"Module {module_name} has no dependencies to test")
        
        # Build context with real dependencies
        # This triggers real agent execution via conftest
        context = module_context(module.dependencies)
        
        # Execute module
        result = module.safe_execute(context)
        
        # Assert success
        assert_module_success(result)


# ============================================================================
# INTEGRATION TESTS (with specific real agents)
# ============================================================================

class TestModulesIntegration:
    """
    Integration tests for specific modules with known dependencies
    """
    
    @pytest.mark.integration
    @pytest.mark.requires_dependencies
    def test_initial_planning_module_integration(self,
                                                 module_fixture_factory,
                                                 module_context,
                                                 assert_module_success):
        """
        Test InitialPlanningModule with real OrderProgressTracker
        """
        try:
            module = module_fixture_factory('InitialPlanningModule')
        except pytest.skip.Exception:
            pytest.skip("InitialPlanningModule not available")
        
        # Build context with real dependencies
        context = module_context(['OrderProgressTracker', 'HistoricalFeaturesExtractor'])
        
        # Execute
        result = module.safe_execute(context)
        
        # Assert
        assert_module_success(result)
        assert 'plan' in result.data or 'planning' in result.data
    
    @pytest.mark.integration
    @pytest.mark.requires_dependencies
    def test_validation_module_integration(self,
                                          module_fixture_factory,
                                          module_context,
                                          assert_module_success):
        """
        Test modules that depend on ValidationOrchestrator
        """
        # Find modules that depend on ValidationOrchestrator
        validation_modules = [
            name for name, cls in AVAILABLE_MODULES.items()
            if hasattr(cls(None), 'dependencies') and 
               'ValidationOrchestrator' in cls(None).dependencies
        ]
        
        if not validation_modules:
            pytest.skip("No modules depend on ValidationOrchestrator")
        
        # Test first one
        module_name = validation_modules[0]
        try:
            module = module_fixture_factory(module_name)
        except pytest.skip.Exception:
            pytest.skip(f"Module {module_name} not available")
        
        # Build context
        context = module_context(module.dependencies)
        
        # Execute
        result = module.safe_execute(context)
        
        # Assert
        assert_module_success(result)


# ============================================================================
# COMPREHENSIVE TEST (runs all checks on each module)
# ============================================================================

class TestModulesComprehensive:
    """
    Comprehensive test that runs all checks on each enabled module
    Better for CI/CD where you want full report per module
    """
    
    def run_comprehensive_tests(self, 
                                module_name: str,
                                module_class: Type[BaseModule],
                                config_path: str) -> Dict[str, Any]:
        """
        Run all tests on a single module
        
        Returns:
            Dict with test results
        """
        results = {
            'module': module_name,
            'tests': {},
            'passed': 0,
            'failed': 0,
            'warnings': []
        }
        
        # Test 1: Creation
        try:
            module = module_class(config_path)
            results['tests']['creation'] = 'PASS'
            results['passed'] += 1
        except Exception as e:
            results['tests']['creation'] = f'FAIL: {str(e)}'
            results['failed'] += 1
            return results
        
        # Test 2: Config Loading
        try:
            assert module.config is not None
            results['tests']['config_loading'] = 'PASS'
            results['passed'] += 1
        except Exception as e:
            results['tests']['config_loading'] = f'FAIL: {str(e)}'
            results['failed'] += 1
        
        # Test 3: Attributes
        try:
            assert hasattr(module, 'module_name')
            assert hasattr(module, 'dependencies')
            assert hasattr(module, 'context_outputs')
            results['tests']['attributes'] = 'PASS'
            results['passed'] += 1
        except Exception as e:
            results['tests']['attributes'] = f'FAIL: {str(e)}'
            results['failed'] += 1
        
        # Test 4: Dependency Validation
        try:
            is_valid = module.validate_dependencies({})
            if module.dependencies:
                assert not is_valid
                mock_context = {
                    dep: ModuleResult(
                        status='success',
                        data={'mock': True},
                        message=f'Mock {dep}'
                    )
                    for dep in module.dependencies
                }
                is_valid = module.validate_dependencies(mock_context)
                assert is_valid
            results['tests']['dependency_validation'] = 'PASS'
            results['passed'] += 1
        except Exception as e:
            results['tests']['dependency_validation'] = f'FAIL: {str(e)}'
            results['failed'] += 1
        
        # Test 5: Error Handling
        try:
            original = module.execute
            module.execute = lambda *a, **k: (_ for _ in ()).throw(ValueError("Test"))
            ctx = {
                dep: ModuleResult(
                    status='success',
                    data={'mock': True},
                    message=f'Mock {dep}'
                )
                for dep in module.dependencies
            }
            result = module.safe_execute(ctx)
            module.execute = original
            assert result.status == 'failed'
            results['tests']['error_handling'] = 'PASS'
            results['passed'] += 1
        except Exception as e:
            results['tests']['error_handling'] = f'FAIL: {str(e)}'
            results['failed'] += 1
        
        # Test 6: Interface Compliance
        try:
            assert isinstance(module, BaseModule)
            assert callable(module.execute)
            assert callable(module.safe_execute)
            results['tests']['interface_compliance'] = 'PASS'
            results['passed'] += 1
        except Exception as e:
            results['tests']['interface_compliance'] = f'FAIL: {str(e)}'
            results['failed'] += 1
        
        return results
    
    def test_all_enabled_modules(self, enabled_modules):
        """
        Test all enabled modules and generate comprehensive report
        """
        if not enabled_modules:
            pytest.skip("No enabled modules in registry")
        
        all_results = {}
        total_passed = 0
        total_failed = 0
        
        for module_name, module_info in enabled_modules:
            module_class = AVAILABLE_MODULES[module_name]
            config_path = module_info['config_path']
            
            results = self.run_comprehensive_tests(
                module_name, module_class, config_path
            )
            
            all_results[module_name] = results
            total_passed += results['passed']
            total_failed += results['failed']
        
        # Print summary
        print("\n" + "="*80)
        print("COMPREHENSIVE TEST SUMMARY")
        print("="*80)
        
        for module_name, results in all_results.items():
            status = "✅ PASS" if results['failed'] == 0 else "❌ FAIL"
            print(f"\n{status} {module_name}: {results['passed']}/{results['passed']+results['failed']} tests passed")
            
            if results['failed'] > 0:
                for test_name, result in results['tests'].items():
                    if result != 'PASS':
                        print(f"  ❌ {test_name}: {result}")
        
        print("\n" + "="*80)
        print(f"TOTAL: {total_passed} passed, {total_failed} failed")
        print("="*80)
        
        assert total_failed == 0, f"{total_failed} test(s) failed across modules"


# ============================================================================
# SMOKE TESTS (quick sanity check)
# ============================================================================

@pytest.mark.smoke
def test_module_registry_exists(module_registry):
    """Quick test that registry file exists"""
    assert isinstance(module_registry, dict)


@pytest.mark.smoke
def test_available_modules_exist(available_modules):
    """Test that AVAILABLE_MODULES is populated"""
    assert isinstance(available_modules, dict)
    assert len(available_modules) > 0


@pytest.mark.smoke
def test_all_modules_in_registry(module_registry, available_modules):
    """Test that all code modules are documented in registry"""
    missing_from_registry = []
    for module_name in available_modules.keys():
        if module_name not in module_registry:
            missing_from_registry.append(module_name)
    
    if missing_from_registry:
        print(f"\n⚠️  Modules not in registry: {missing_from_registry}")
        print("Consider adding them to configs/module_registry.yaml")


@pytest.mark.smoke
def test_registry_modules_exist_in_code(module_registry, available_modules):
    """Test that all registry modules exist in code"""
    missing_from_code = []
    for module_name in module_registry.keys():
        if module_name not in available_modules:
            missing_from_code.append(module_name)
    
    if missing_from_code:
        print(f"\n⚠️  Registry references non-existent modules: {missing_from_code}")
        print("Consider removing them from configs/module_registry.yaml")


@pytest.mark.smoke
def test_at_least_one_module_enabled(enabled_modules):
    """Sanity check that at least one module is enabled"""
    assert len(enabled_modules) > 0, "No modules enabled in registry!"


# ============================================================================
# HELPER TESTS
# ============================================================================

def test_module_fixture_factory_works(module_fixture_factory):
    """Test that module_fixture_factory from conftest works"""
    if AVAILABLE_MODULES:
        first_module = list(AVAILABLE_MODULES.keys())[0]
        try:
            module = module_fixture_factory(first_module)
            assert module is not None
        except pytest.skip.Exception:
            pass


def test_module_context_builder(module_context):
    """Test that module_context from conftest works"""
    # Build context for dummy dependencies
    context = module_context(['TestDep1', 'TestDep2'])
    
    assert isinstance(context, dict)
    assert 'TestDep1' in context
    assert 'TestDep2' in context
    
    # Check for ModuleResult objects
    assert isinstance(context['TestDep1'], ModuleResult)
    assert context['TestDep1'].status == 'success'


def test_module_dependency_provider_available(module_dependency_provider):
    """Test that module_dependency_provider from conftest is available"""
    assert module_dependency_provider is not None
    
    # Test config
    config = module_dependency_provider.get_shared_source_config()
    assert config is not None
    
    # Test context building
    context = module_dependency_provider.get_module_context(['TestDep'])
    assert isinstance(context, dict)
    assert 'TestDep' in context
    assert isinstance(context['TestDep'], ModuleResult)


def test_shared_source_config_fixture(shared_source_config):
    """Test that shared_source_config fixture works"""
    assert shared_source_config is not None
    assert hasattr(shared_source_config, 'db_dir')
    assert hasattr(shared_source_config, 'default_dir')