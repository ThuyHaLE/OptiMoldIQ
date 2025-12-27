# tests/modules_tests/conftest.py - Module-specific fixtures

"""
Module testing conftest - provides module registry and dependency management
"""

import pytest
from pathlib import Path
from typing import Dict, Any

from modules.registry.registry_loader import ModuleRegistryLoader
from configs.shared.shared_source_config import SharedSourceConfig
from configs.shared.agent_report_format import ExecutionStatus


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


# ============================================================================
# MODULE DEPENDENCY PROVIDER (Like agent's DependencyProvider)
# ============================================================================

class ModuleDependencyProvider:
    """
    Manages module test dependencies
    Reuses agent results when needed (don't re-run agents for each module test)
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
        """Get basic config for module testing"""
        if "shared_config" not in self._cache:
            config = SharedSourceConfig(
                db_dir=str(self._test_dirs["db_dir"]),
                default_dir=str(self._test_dirs["shared_dir"])
            )
            self._cache["shared_config"] = config
        return self._cache["shared_config"]
    
    def get_mock_context(self, dependencies: list = None) -> Dict[str, Any]:
        """
        Get mock context with specified dependencies
        
        Args:
            dependencies: List of dependency names needed
            
        Returns:
            Mock context dict with dependency data
        """
        context = {}
        
        if dependencies:
            for dep in dependencies:
                if dep == "OrderProgressTracker":
                    context[dep] = self.get_order_progress_tracker_result()
                elif dep == "HistoricalFeaturesExtractor":
                    context[dep] = self.get_historical_features_result()
                elif dep == "ValidationOrchestrator":
                    context[dep] = self.get_validation_orchestrator_result()
                else:
                    # Generic mock for unknown dependencies
                    context[dep] = {
                        'status': 'success',
                        'data': f'mock_data_for_{dep}'
                    }
        
        return context
    
    def get_order_progress_tracker_result(self) -> Dict[str, Any]:
        """
        Get OrderProgressTracker result (real or mock)
        Only runs once and caches
        """
        if "order_progress_tracker" not in self._cache:
            # Option 1: Use real agent (slow but accurate)
            # from agents.orderProgressTracker.order_progress_tracker import OrderProgressTracker
            # tracker = OrderProgressTracker(config=self.get_shared_source_config())
            # result = tracker.run_tracking_and_save_results()
            
            # Option 2: Use mock (fast for unit tests)
            result = self._create_mock_agent_result("OrderProgressTracker")
            
            self._cache["order_progress_tracker"] = result
        
        return self._cache["order_progress_tracker"]
    
    def get_historical_features_result(self) -> Dict[str, Any]:
        """Get HistoricalFeaturesExtractor result (mock)"""
        if "historical_features_extractor" not in self._cache:
            result = self._create_mock_agent_result("HistoricalFeaturesExtractor")
            self._cache["historical_features_extractor"] = result
        
        return self._cache["historical_features_extractor"]
    
    def get_validation_orchestrator_result(self) -> Dict[str, Any]:
        """Get ValidationOrchestrator result (mock)"""
        if "validation_orchestrator" not in self._cache:
            result = self._create_mock_agent_result("ValidationOrchestrator")
            self._cache["validation_orchestrator"] = result
        
        return self._cache["validation_orchestrator"]
    
    def _create_mock_agent_result(self, agent_name: str) -> Dict[str, Any]:
        """Create a mock agent result for testing"""
        return {
            'status': ExecutionStatus.SUCCESS.value,
            'agent': agent_name,
            'data': {
                'processed_records': 100,
                'timestamp': '2024-01-01T00:00:00'
            },
            'message': f'Mock result for {agent_name}'
        }
    
    def trigger_real_agent(self, agent_name: str):
        """
        Trigger real agent execution (for integration tests)
        Similar to agent_tests/conftest.py
        """
        config = self.get_shared_source_config()
        
        if agent_name == "OrderProgressTracker":
            from agents.orderProgressTracker.order_progress_tracker import OrderProgressTracker
            agent = OrderProgressTracker(config=config)
            result = agent.run_tracking_and_save_results()
            assert result.status == ExecutionStatus.SUCCESS.value
            self._cache["order_progress_tracker"] = result
            
        elif agent_name == "HistoricalFeaturesExtractor":
            from agents.autoPlanner.featureExtractor.initial.historicalFeaturesExtractor.historical_features_extractor import (
                HistoricalFeaturesExtractor, FeaturesExtractorConfig)
            agent = HistoricalFeaturesExtractor(
                config=FeaturesExtractorConfig(
                    efficiency=0.85,
                    loss=0.03,
                    shared_source_config=config
                )
            )
            result = agent.run_extraction_and_save_results()
            assert result.status == ExecutionStatus.SUCCESS.value
            self._cache["historical_features_extractor"] = result
            
        else:
            raise ValueError(f"Unknown agent: {agent_name}")
    
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
    Similar to agent's dependency_provider
    """
    provider = ModuleDependencyProvider()
    yield provider
    provider.cleanup()


# ============================================================================
# MODULE-SPECIFIC FIXTURES
# ============================================================================

@pytest.fixture
def mock_module_context(module_dependency_provider):
    """
    Provides a basic mock context for module testing
    Can be customized per test
    """
    return module_dependency_provider.get_mock_context()


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
        "markers", "requires_agent: mark test as requiring real agent execution"
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
        
        # Mark tests that require real agents
        if "integration" in item.nodeid.lower():
            item.add_marker(pytest.mark.requires_agent)


# ============================================================================
# HELPER FIXTURES
# ============================================================================

@pytest.fixture
def assert_module_success():
    """Helper fixture for asserting module success"""
    def _assert(result):
        from modules.base_module import ModuleResult
        assert isinstance(result, ModuleResult)
        assert result.status == 'success', f"Module failed: {result.message}"
        assert result.data is not None
    return _assert


@pytest.fixture
def create_mock_dependencies():
    """
    Helper to create mock dependencies on-the-fly
    
    Usage:
        def test_something(create_mock_dependencies):
            deps = create_mock_dependencies(['OrderProgressTracker'])
            module.safe_execute(deps)
    """
    def _create(dep_names: list) -> Dict[str, Any]:
        return {
            dep: {
                'status': 'success',
                'data': f'mock_{dep}',
                'timestamp': '2024-01-01'
            }
            for dep in dep_names
        }
    return _create