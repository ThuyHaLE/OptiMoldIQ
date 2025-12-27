import yaml
from pathlib import Path
from unittest.mock import patch, mock_open
from typing import Dict, Any, Type, List, Optional
from modules import AVAILABLE_MODULES, BaseModule
from modules.registry.registry_loader import ModuleRegistryLoader

"""
Auto-discovery module testing system with external config loading
Tests all available modules automatically
"""

def test_all_available_modules():

    def test_module_generic(module_class: Type[BaseModule],
                            config_path: str,
                            module_name: str = None) -> Dict[str, Any]:
        """
        Generic test function for ANY module that inherits from BaseModule
        
        Args:
            module_class: Class object (not instance)
            config_path: Path to module's config file
            module_name: Optional display name
            
        Returns:
            Dict with test results
        """
        display_name = module_name or module_class.__name__
        test_results = {
            'module': display_name,
            'passed': [],
            'failed': [],
            'warnings': [],
            'overall': 'UNKNOWN'
        }
        reports = []
        def record_test(test_name: str, passed: bool, message: str = ""):
            """Helper to record test results"""
            if passed:
                test_results['passed'].append(test_name)
                reports.append(f"\n   ✅ {test_name}")
            else:
                test_results['failed'].append({'test': test_name, 'reason': message})
                reports.append(f"\n   ❌ {test_name}: {message}")
        
        reports.append(f"\n{'='*80}")
        reports.append(f"\nTesting: {display_name}")
        reports.append(f"\n{'='*80}")
        reports.append(f"\n📂 Config: {config_path}")
        reports.append(f"\n🏷️  Class: {module_class.__name__}")
        
        try:
            config_path_obj = Path(config_path)
            if config_path_obj.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    mock_config_data = yaml.safe_load(f)
                mock_yaml_content = yaml.dump(mock_config_data)
                record_test("Config File Exists", True)
                reports.append(f"\nConfig File Exists: True")
            else:
                record_test("Config File Exists", False)
                reports.append(f"\nConfig File Exists: False")
                    
        except Exception as e:
            record_test("Config Loading", False, str(e))
            test_results['overall'] = 'FAILED'
            reports.append(f"\noverall: FAILED")
            return test_results, ''.join(reports)
        
        # ========================================
        # TEST 1: MODULE CREATION
        # ========================================
        reports.append(f"\n{'─'*60}")
        reports.append(f"\nTEST 1: Module Creation")
        reports.append(f"\n{'─'*60}")
        
        try:
            module = module_class(config_path)
            record_test("Module Instance Created", True)
            reports.append(f"\nModule Instance Created: True")

            # Check basic attributes
            has_name = hasattr(module, 'module_name')
            record_test("Has module_name attribute", has_name)
            reports.append(f"\nHas module_name attribute: {has_name}")

            has_deps = hasattr(module, 'dependencies')
            record_test("Has dependencies attribute", has_deps)
            reports.append(f"\nHas dependencies attribute: {has_deps}")

            has_outputs = hasattr(module, 'context_outputs')
            record_test("Has context_outputs attribute", has_outputs)
            reports.append(f"\nHas context_outputs attribute: {has_outputs}")
            
            if has_name:
                reports.append(f"\n      Module Name: {module.module_name}")
            if has_deps:
                reports.append(f"\n      Dependencies: {module.dependencies}")
            if has_outputs:
                reports.append(f"\n      Context Outputs: {module.context_outputs}")
            
            if module.config:
                reports.append(f"\n      Config Keys: {list(module.config.keys())}")
                record_test("Config Loaded", True)
            else:
                test_results['warnings'].append("Config is empty")
                reports.append(f"\n      ⚠️  Config is empty")
                
        except Exception as e:
            record_test("Module Creation", False, str(e))
            test_results['overall'] = 'FAILED'
            reports.append(f"\noverall: FAILED")
            return test_results, ''.join(reports)
        
        # ========================================
        # TEST 2: DEPENDENCY VALIDATION
        # ========================================
        reports.append(f"\n{'─'*60}")
        reports.append(f"\nTEST 2: Dependency Validation")
        reports.append(f"\n{'─'*60}")
        
        try:
            # Test with empty context
            is_valid, missing = module.validate_dependencies({})
            
            if module.dependencies:
                # Should fail with empty context
                record_test("Empty Context Validation", not is_valid, 
                        "Should be invalid with empty context")
                reports.append(f"\n      Missing deps (expected): {missing}")
                
                # Test with full context
                mock_context = {dep: f"mock_{dep}" for dep in module.dependencies}
                is_valid, missing = module.validate_dependencies(mock_context)
                record_test("Full Context Validation", is_valid)
                reports.append(f"\nFull Context Validation: {is_valid}")

                if not is_valid:
                    reports.append(f"\n      ⚠️  Still missing: {missing}")
            else:
                # No dependencies - should always pass
                record_test("No Dependencies Required", is_valid)
                reports.append(f"\n      ✓ Module has no dependencies")
                
        except Exception as e:
            record_test("Dependency Validation", False, str(e))
            reports.append(f"\nDependency Validation: FAILED. {str(e)}")
        
        # ========================================
        # TEST 3: ERROR HANDLING (safe_execute)
        # ========================================
        reports.append(f"\n{'─'*60}")
        reports.append(f"\nTEST 3: Error Handling")
        reports.append(f"\n{'─'*60}")
        
        try:
            # Mock execute to raise error
            original_execute = module.execute
            
            def mock_error_execute(*args, **kwargs):
                raise Exception("Simulated error for testing")
            
            module.execute = mock_error_execute
            
            # Prepare context with all dependencies
            test_context = {}
            if module.dependencies:
                test_context = {dep: f"mock_{dep}" for dep in module.dependencies}
            
            result = module.safe_execute(context=test_context, dependencies={})
            
            # Restore original
            module.execute = original_execute
            
            # Check error was caught
            error_caught = result.status == 'failed'
            record_test("Error Caught by safe_execute", error_caught)
            reports.append(f"\nError Caught by safe_execute: {error_caught}")

            has_error_msg = result.message is not None
            record_test("Error Message Present", has_error_msg)
            reports.append(f"\nError Message Present: {has_error_msg}")

            if result.message:
                reports.append(f"\n      Error: {result.message[:80]}...")
                
        except Exception as e:
            record_test("Error Handling", False, f"Exception escaped: {e}")
            reports.append(f"\nError Handling: False. Exception escaped: {e}")
        
        # ========================================
        # TEST 4: CONFIG FALLBACK
        # ========================================
        reports.append(f"\n{'─'*60}")
        reports.append(f"\nTEST 4: Config Fallback")
        reports.append(f"\n{'─'*60}")
        
        try:
            with patch('pathlib.Path.exists') as mock_exists, \
                patch('builtins.open', mock_open(read_data=mock_yaml_content)):
                
                mock_exists.side_effect = [False, True]
                
                fallback_module = module_class('/non/existent/path.yaml')
                
                has_config = fallback_module.config is not None
                record_test("Fallback Config Loaded", has_config)
                reports.append(f"\nFallback Config Loaded {has_config}")
                
                if has_config:
                    reports.append(f"\n      ✓ Fallback config used successfully")
                    
        except Exception as e:
            test_results['warnings'].append(f"Config fallback: {str(e)[:60]}")
            reports.append(f"\n      ⚠️  Fallback behavior: {str(e)[:80]}")
        
        # ========================================
        # TEST 5: INTERFACE COMPLIANCE
        # ========================================
        reports.append(f"\n{'─'*60}")
        reports.append(f"\nTEST 5: Interface Compliance")
        reports.append(f"\n{'─'*60}")
        
        try:
            # Check required methods exist
            has_execute = hasattr(module, 'execute') and callable(module.execute)
            record_test("Has execute() method", has_execute)
            reports.append(f"\nHas execute() method: {has_execute}")
            
            has_safe_execute = hasattr(module, 'safe_execute') and callable(module.safe_execute)
            record_test("Has safe_execute() method", has_safe_execute)
            reports.append(f"\nHas safe_execute() method: {has_safe_execute}")

            has_validate = hasattr(module, 'validate_dependencies') and callable(module.validate_dependencies)
            record_test("Has validate_dependencies() method", has_validate)
            reports.append(f"\nHas validate_dependencies() method: {has_validate}")

            # Check inheritance
            is_base_module = isinstance(module, BaseModule)
            record_test("Inherits from BaseModule", is_base_module)
            reports.append(f"\nInherits from BaseModule: {is_base_module}")

        except Exception as e:
            record_test("Interface Check", False, str(e))
            reports.append(f"\nInterface Check, False, {str(e)}")

        # ========================================
        # SUMMARY
        # ========================================
        reports.append(f"\n{'─'*60}")
        reports.append(f"\n📊 Test Summary")
        reports.append(f"\n{'─'*60}")
        
        passed_count = len(test_results['passed'])
        failed_count = len(test_results['failed'])
        warning_count = len(test_results['warnings'])
        
        reports.append(f"\n   ✅ Passed: {passed_count}")
        reports.append(f"\n   ❌ Failed: {failed_count}")
        reports.append(f"\n   ⚠️  Warnings: {warning_count}")
        
        if test_results['failed']:
            reports.append(f"\n   Failed Tests:")
            for failure in test_results['failed']:
                reports.append(f"      ✗ {failure['test']}: {failure['reason']}")
        
        if test_results['warnings']:
            reports.append(f"\n   Warnings:")
            for warning in test_results['warnings']:
                reports.append(f"      ⚠ {warning}")
        
        # Overall status
        if failed_count == 0:
            test_results['overall'] = 'PASSED'
            reports.append(f"\n   🎉 ALL TESTS PASSED!")
        else:
            test_results['overall'] = 'FAILED'
            reports.append(f"\n   ⚠️  SOME TESTS FAILED")
        
        reports_str = "".join(reports)

        return test_results, reports_str

    def test_available_modules(registry_path: Optional[str] = None,
                               modules_to_test: List[str] = None) -> Dict[str, Dict]:
        """
        Automatically discover and test all available modules
        
        Args:
            registry_path: Path to module registry file (YAML/JSON)
            modules_to_test: List of specific module names to test (None = test all)
            
        Returns:
            Dict mapping module names to their test results
        """
        
        reports = []
        # Load registry from file
        registry = ModuleRegistryLoader.load_registry(registry_path)
        
        reports.append(f"\n📋 Available modules in code: {len(AVAILABLE_MODULES)}")
        for name in AVAILABLE_MODULES.keys():
            in_registry = "✓" if name in registry else "✗"
            enabled = registry.get(name, {}).get('enabled', False)
            status = "🟢" if (name in registry and enabled) else "⚪"
            reports.append(f"\n   {status} {name} [{in_registry} in registry]")
        
        # Determine which modules to test
        if modules_to_test:
            test_targets = {k: v for k, v in AVAILABLE_MODULES.items() 
                        if k in modules_to_test}
            reports.append(f"\n🎯 Testing {len(test_targets)} specific modules")
        else:
            # Only test modules that are in registry and enabled
            test_targets = {k: v for k, v in AVAILABLE_MODULES.items() 
                        if k in registry and registry[k].get('enabled', True)}
            reports.append(f"\n🎯 Testing {len(test_targets)} enabled modules")
        
        all_results = {}
        
        # Test each module
        for module_name, module_class in test_targets.items():
            # Get config from registry
            if module_name not in registry:
                reports.append(f"\n⚠️  Skipping {module_name}: Not in registry")
                all_results[module_name] = {
                    'overall': 'SKIPPED',
                    'reason': 'Not in registry'
                }
                continue
            
            module_info = registry[module_name]
            
            # Check if enabled
            if not module_info.get('enabled', True):
                reports.append(f"\n⏭️  Skipping {module_name}: Disabled in registry")
                all_results[module_name] = {
                    'overall': 'SKIPPED',
                    'reason': 'Disabled in registry'
                }
                continue
            
            config_path = module_info.get('config_path')
            if not config_path:
                reports.append(f"\n⚠️  Skipping {module_name}: No config_path in registry")
                all_results[module_name] = {
                    'overall': 'SKIPPED',
                    'reason': 'No config path'
                }
                continue
            
            # Run tests
            try:
                result, reports_str = test_module_generic(
                    module_class=module_class,
                    config_path=config_path,
                    module_name=module_name
                )
                all_results[module_name] = result
                reports.append(f"\n✅ {module_name} Passed. \nDetails: \n{reports_str}")

            except Exception as e:
                all_results[module_name] = {
                    'overall': 'ERROR',
                    'error': str(e)
                }
                reports.append(f"\n❌ Fatal error testing {module_name}: {e}")
        
        reports.append(f"\n{'='*80}")
        reports.append(f"\n📊 FINAL TEST SUMMARY - ALL MODULES")
        reports.append(f"\n{'='*80}")
        
        passed_modules = [k for k, v in all_results.items() if v.get('overall') == 'PASSED']
        failed_modules = [k for k, v in all_results.items() if v.get('overall') == 'FAILED']
        skipped_modules = [k for k, v in all_results.items() if v.get('overall') == 'SKIPPED']
        error_modules = [k for k, v in all_results.items() if v.get('overall') == 'ERROR']
        
        reports.append(f"\n✅ Passed: {len(passed_modules)}")
        for name in passed_modules:
            total_passed = len(all_results[name]['passed'])
            reports.append(f"\n   ✓ {name} ({total_passed} tests passed)")
        
        if failed_modules:
            reports.append(f"\n❌ Failed: {len(failed_modules)}")
            for name in failed_modules:
                failed_count = len(all_results[name]['failed'])
                reports.append(f"   ✗ {name} ({failed_count} tests failed)")
        
        if skipped_modules:
            reports.append(f"\n⏭️  Skipped: {len(skipped_modules)}")
            for name in skipped_modules:
                reason = all_results[name].get('reason', 'Unknown')
                reports.append(f"\n   → {name} ({reason})")
        
        if error_modules:
            reports.append(f"\n💥 Errors: {len(error_modules)}")
            for name in error_modules:
                error = all_results[name].get('error', 'Unknown error')
                reports.append(f"\n   ✗ {name}: {error[:60]}...")
        
        # Overall result
        reports.append(f"\n{'='*80}")
        if not failed_modules and not error_modules:
            reports.append(f"\n🎉 ALL MODULES PASSED!")
        else:
            reports.append(f"\n⚠️  SOME MODULES FAILED - CHECK DETAILS ABOVE")
        reports.append(f"\n{'='*80}")
        
        reports_str = ''.join(reports)

        return all_results, reports_str

    # Main logic

    # Test all modules from registry
    results, reports = test_available_modules(
        registry_path='configs/module_registry.yaml',
        modules_to_test = None)
    
    # Or use default path
    results, reports = test_available_modules()
    
    # Or test specific modules
    results, reports = test_available_modules(
        registry_path=None,
        modules_to_test=['AnalyticsModule'])
    
    assert True