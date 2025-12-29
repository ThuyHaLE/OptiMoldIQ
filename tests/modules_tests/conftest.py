# tests/modules_tests/conftest.py - Module-specific fixtures

"""
Module testing conftest - provides module registry and REAL dependency execution
FIXED: Uses real agents like agent tests do (no more mocking)
"""

import pytest
from pathlib import Path
from typing import Dict, Any

from modules.registry.registry_loader import ModuleRegistryLoader
from modules.base_module import ModuleResult
from configs.shared.shared_source_config import SharedSourceConfig
from configs.shared.agent_report_format import ExecutionStatus


# ============================================================================
# MODULE REGISTRY FIXTURES
# ============================================================================

@pytest.fixture(scope="session")
def module_registry():
    """Load module registry once for entire test session"""
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


# ============================================================================
# MODULE DEPENDENCY PROVIDER - FIXED: Uses REAL agents
# ============================================================================

class ModuleDependencyProvider:
    """
    Manages module test dependencies by running REAL agents
    Similar to agent's DependencyProvider but for module context
    
    Key difference from agents/conftest.py:
    - Agents return AgentResult
    - Modules need context dict with ModuleResult objects
    """
    
    def __init__(self):
        self._cache: Dict[str, Any] = {}
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
    
    def get_shared_source_config(self) -> SharedSourceConfig:
        """Get basic config for testing"""
        if "shared_config" not in self._cache:
            config = SharedSourceConfig(
                db_dir=str(self._test_dirs["db_dir"]),
                default_dir=str(self._test_dirs["shared_dir"])
            )
            self._cache["shared_config"] = config
        return self._cache["shared_config"]
    
    # ========================================================================
    # TRIGGER REAL DEPENDENCIES (like agents/conftest.py)
    # ========================================================================
    
    def trigger_order_progress_tracker(self):
        """
        Run OrderProgressTracker agent and cache result
        This creates real data in shared_db that modules can read
        """
        if "order_progress_tracker" not in self._cache:
            from agents.orderProgressTracker.order_progress_tracker import OrderProgressTracker
            
            config = self.get_shared_source_config()
            tracker = OrderProgressTracker(config=config)
            result = tracker.run_tracking_and_save_results()
            
            assert result.status == ExecutionStatus.SUCCESS.value, \
                "Dependency agent failed: OrderProgressTracker"
            
            # Cache the agent result AND config
            self._cache["order_progress_tracker"] = {
                "status": "triggered",
                "result": result,
                "config": config
            }
    
    def trigger_historical_features_extractor(self):
        """
        Run HistoricalFeaturesExtractor agent and cache result
        """
        if "historical_features_extractor" not in self._cache:
            from agents.autoPlanner.featureExtractor.initial.historicalFeaturesExtractor.historical_features_extractor import (
                HistoricalFeaturesExtractor, FeaturesExtractorConfig)
            
            config = self.get_shared_source_config()
            extractor = HistoricalFeaturesExtractor(
                config=FeaturesExtractorConfig(
                    efficiency=0.85,
                    loss=0.03,
                    shared_source_config=config
                )
            )
            result = extractor.run_extraction_and_save_results()
            
            assert result.status == ExecutionStatus.SUCCESS.value, \
                "Dependency agent failed: HistoricalFeaturesExtractor"
            
            self._cache["historical_features_extractor"] = {
                "status": "triggered",
                "result": result,
                "config": config
            }
    
    def trigger_validation_orchestrator(self):
        """
        Run ValidationOrchestrator agent and cache result
        """
        if "validation_orchestrator" not in self._cache:
            from agents.validationOrchestrator.validation_orchestrator import ValidationOrchestrator
            
            config = self.get_shared_source_config()
            orchestrator = ValidationOrchestrator(
                shared_source_config=config,
                enable_parallel=False,
                max_workers=None
            )
            result = orchestrator.run_validations_and_save_results()
            
            assert result.status == ExecutionStatus.SUCCESS.value, \
                "Dependency agent failed: ValidationOrchestrator"
            
            self._cache["validation_orchestrator"] = {
                "status": "triggered",
                "result": result,
                "config": config
            }
    
    def trigger(self, dependency_name: str):
        """
        Generic trigger method - delegates to specific trigger methods
        Same interface as agents/conftest.py
        """
        if dependency_name == "OrderProgressTracker":
            self.trigger_order_progress_tracker()
        elif dependency_name == "HistoricalFeaturesExtractor":
            self.trigger_historical_features_extractor()
        elif dependency_name == "ValidationOrchestrator":
            self.trigger_validation_orchestrator()
        else:
            raise ValueError(f"Unknown dependency: {dependency_name}")
    
    # ========================================================================
    # MODULE CONTEXT BUILDER - Converts agent results to module context
    # ========================================================================
    
    def get_module_context(self, dependencies: list = None) -> Dict[str, ModuleResult]:
        """
        Build module context from real agent results
        
        This is the KEY difference from agents/conftest.py:
        - Agents just need dependencies to run
        - Modules need a context dict with ModuleResult objects
        
        Args:
            dependencies: List of dependency names (e.g., ['OrderProgressTracker'])
            
        Returns:
            Dict mapping dependency name to ModuleResult
            
        Usage:
            context = provider.get_module_context(['OrderProgressTracker'])
            module.safe_execute(context)
        """
        context = {}
        
        if dependencies:
            for dep in dependencies:
                # Trigger the real agent if not already run
                self.trigger(dep)
                
                # Convert agent result to ModuleResult for context
                agent_cache = self._cache.get(dep.lower().replace(" ", "_"))
                if agent_cache:
                    agent_result = agent_cache["result"]
                    
                    # Convert AgentResult to ModuleResult
                    context[dep] = ModuleResult(
                        status='success',
                        data=agent_result.data if hasattr(agent_result, 'data') else {},
                        message=agent_result.message if hasattr(agent_result, 'message') else 'Success'
                    )
        
        return context
    
    def cleanup(self):
        """Cleanup test artifacts"""
        import shutil
        for dir_path in self._test_dirs.values():
            if dir_path.exists():
                shutil.rmtree(dir_path)


@pytest.fixture(scope="session")
def module_dependency_provider():
    """
    Session-scoped dependency provider for modules
    Runs real agents and caches results
    """
    provider = ModuleDependencyProvider()
    yield provider
    provider.cleanup()


# ============================================================================
# MODULE-SPECIFIC FIXTURES
# ============================================================================

@pytest.fixture
def module_context(module_dependency_provider):
    """
    Provides module context with real dependencies
    
    Usage in test:
        def test_module(module_context):
            # Trigger dependencies you need
            context = module_context(['OrderProgressTracker'])
            result = module.safe_execute(context)
    """
    def _get_context(dependencies: list = None):
        return module_dependency_provider.get_module_context(dependencies)
    
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
        def test_something(module_fixture_factory, module_context):
            module = module_fixture_factory('InitialPlanningModule')
            context = module_context(['OrderProgressTracker'])
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
# PYTEST HOOKS
# ============================================================================

def pytest_configure(config):
    """Register custom markers for module tests"""
    config.addinivalue_line(
        "markers", "module_test: mark test as module test"
    )
    config.addinivalue_line(
        "markers", "requires_dependencies: mark test as requiring real dependencies"
    )


def pytest_collection_modifyitems(config, items):
    """
    Modify test collection for module tests
    Auto-add markers
    """
    for item in items:
        # Auto-mark module tests
        if "module_tests" in str(item.fspath):
            item.add_marker(pytest.mark.module_test)


# ============================================================================
# HELPER FIXTURES
# ============================================================================

@pytest.fixture
def assert_module_success():
    """Helper fixture for asserting module success"""
    def _assert(result):
        assert isinstance(result, ModuleResult)
        assert result.status == 'success', f"Module failed: {result.message}"
        assert result.data is not None
    return _assert


@pytest.fixture
def shared_source_config(module_dependency_provider):
    """
    Quick access to shared config
    
    Usage:
        def test_something(shared_source_config):
            # Use config directly
            ...
    """
    return module_dependency_provider.get_shared_source_config()