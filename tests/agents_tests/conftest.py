# tests/agents_tests/conftest.py - Centralized dependency providers

import pytest
from pathlib import Path
from typing import Dict, Any, Set
from configs.shared.shared_source_config import SharedSourceConfig
from configs.shared.agent_report_format import ExecutionStatus, ExecutionResult
from loguru import logger

# ============================================
# CONSTANTS
# ============================================

SUCCESSFUL_STATUSES = {
    ExecutionStatus.SUCCESS.value,
    ExecutionStatus.DEGRADED.value,
    ExecutionStatus.WARNING.value
}

# ============================================
# DEPENDENCY PROVIDER - Enhanced
# ============================================

class DependencyProvider:
    """
    Manages test dependencies - only loads what's needed
    Provides caching, validation, and health checks
    """
    
    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self._test_dirs = self._setup_test_dirs()
        self._dependency_graph = self._build_dependency_graph()
        self._validate_dependency_graph()
    
    def _setup_test_dirs(self) -> Dict[str, Path]:
        """Setup test directories once"""
        dirs = {
            "db_dir": Path("tests/mock_database"),
            "shared_dir": Path("tests/shared_db"),
            "cache_dir": Path("tests/cache")
        }
        for dir_path in dirs.values():
            dir_path.mkdir(parents=True, exist_ok=True)
        return dirs
    
    def _build_dependency_graph(self) -> Dict[str, Set[str]]:
        """Build dependency graph for validation"""
        return {
            "ValidationOrchestrator": set(),
            "OrderProgressTracker": {"ValidationOrchestrator"},
            "HistoricalFeaturesExtractor": {"OrderProgressTracker"},
            "InitialPlanner": {"OrderProgressTracker", "HistoricalFeaturesExtractor"}
        }
    
    def _validate_dependency_graph(self):
        """Ensure no circular dependencies"""
        def dfs(node: str, path: Set[str]):
            if node in path:
                cycle = list(path) + [node]
                raise ValueError(f"Circular dependency detected: {' -> '.join(cycle)}")
            
            if node not in self._dependency_graph:
                raise ValueError(f"Unknown dependency: {node}")
            
            for dep in self._dependency_graph[node]:
                dfs(dep, path | {node})
        
        for node in self._dependency_graph:
            dfs(node, set())
        
        logger.info("✓ Dependency graph validated - no circular dependencies")
    
    def get_shared_source_config(self) -> SharedSourceConfig:
        """Get basic config without running any dependencies"""
        if "shared_config" not in self._cache:
            self._cache["shared_config"] = SharedSourceConfig(
                db_dir=str(self._test_dirs["db_dir"]),
                default_dir=str(self._test_dirs["shared_dir"])
            )
        return self._cache["shared_config"]
    
    def is_triggered(self, dependency_name: str) -> bool:
        """Check if dependency has been triggered"""
        return dependency_name in self._cache
    
    def get_result(self, dependency_name: str) -> ExecutionResult:
        """Get cached result for dependency"""
        if dependency_name not in self._cache:
            raise ValueError(f"Dependency '{dependency_name}' not triggered yet")
        return self._cache[dependency_name]["result"]
    
    # ========== Individual Triggers ==========
    
    def trigger_validation_orchestrator(self) -> ExecutionResult:
        """Lazy load: Only run ValidationOrchestrator if requested"""
        if "ValidationOrchestrator" not in self._cache:
            from agents.validationOrchestrator.validation_orchestrator import ValidationOrchestrator
            
            config = self.get_shared_source_config()
            validation_orchestrator = ValidationOrchestrator(
                shared_source_config=config,
                enable_parallel=False,
                max_workers=None
            )
            result = validation_orchestrator.run_validations_and_save_results()
            
            self._validate_result(result, "ValidationOrchestrator")
            
            self._cache["ValidationOrchestrator"] = {
                "status": "triggered",
                "result": result,
                "config": config
            }
        
        return self._cache["ValidationOrchestrator"]["result"]
    
    def trigger_order_progress_tracker(self) -> ExecutionResult:
        """Lazy load: Only run OrderProgressTracker if requested"""
        if "OrderProgressTracker" not in self._cache:
            # Ensure dependencies
            self.trigger_validation_orchestrator()
            
            from agents.orderProgressTracker.order_progress_tracker import OrderProgressTracker
            
            config = self.get_shared_source_config()
            tracker = OrderProgressTracker(config=config)
            result = tracker.run_tracking_and_save_results()
            
            self._validate_result(result, "OrderProgressTracker")
            
            self._cache["OrderProgressTracker"] = {
                "status": "triggered",
                "result": result,
                "config": config
            }
        
        return self._cache["OrderProgressTracker"]["result"]
    
    def trigger_historical_features_extractor(self) -> ExecutionResult:
        """Lazy load: Only run HistoricalFeaturesExtractor if requested"""
        if "HistoricalFeaturesExtractor" not in self._cache:
            # Ensure dependencies
            self.trigger_order_progress_tracker()
            
            from agents.autoPlanner.featureExtractor.initial.historicalFeaturesExtractor.historical_features_extractor import (
                HistoricalFeaturesExtractor, FeaturesExtractorConfig
            )
            
            config = self.get_shared_source_config()
            extractor = HistoricalFeaturesExtractor(
                config=FeaturesExtractorConfig(
                    efficiency=0.85,
                    loss=0.03,
                    shared_source_config=config
                )
            )
            result = extractor.run_extraction_and_save_results()
            
            self._validate_result(result, "HistoricalFeaturesExtractor")
            
            self._cache["HistoricalFeaturesExtractor"] = {
                "status": "triggered",
                "result": result,
                "config": config
            }
        
        return self._cache["HistoricalFeaturesExtractor"]["result"]
    
    def _validate_result(self, result: ExecutionResult, name: str):
        """Validate execution result"""
        assert result.status in SUCCESSFUL_STATUSES, (
            f"Dependency '{name}' failed with status: {result.status}\n"
            f"Error: {result.error}\n"
            f"Traceback: {result.traceback}"
        )
    
    def trigger(self, dependency_name: str) -> ExecutionResult:
        """Generic trigger - delegates to specific methods"""
        trigger_map = {
            "ValidationOrchestrator": self.trigger_validation_orchestrator,
            "OrderProgressTracker": self.trigger_order_progress_tracker,
            "HistoricalFeaturesExtractor": self.trigger_historical_features_extractor
        }
        
        if dependency_name not in trigger_map:
            raise ValueError(
                f"Unknown dependency: {dependency_name}\n"
                f"Available: {list(trigger_map.keys())}"
            )
        
        return trigger_map[dependency_name]()
    
    def trigger_all_dependencies(self, dependency_names: list[str]) -> Dict[str, ExecutionResult]:
        """Trigger multiple dependencies and return results"""
        results = {}
        for dep in dependency_names:
            results[dep] = self.trigger(dep)
        return results
    
    def cleanup(self):
        """Cleanup test artifacts, but preserve prepared data"""

        import shutil
        from pathlib import Path

        shared_config = self.get_shared_source_config()
        protected_dir_name = Path(shared_config.data_pipeline_dir).name
        protected = {protected_dir_name}

        for dir_path in self._test_dirs.values():
            if not dir_path.exists():
                continue

            if dir_path.name == "shared_db":
                for child in dir_path.iterdir():
                    if child.name in protected:
                        continue
                    if child.is_dir():
                        shutil.rmtree(child)
            else:
                shutil.rmtree(dir_path)

# ============================================
# SESSION FIXTURES
# ============================================

@pytest.fixture(scope="session")
def dependency_provider():
    """
    Session-scoped provider - dependencies run once and cached
    """
    provider = DependencyProvider()
    yield provider
    provider.cleanup()

# ============================================
# VALIDATION FIXTURES
# ============================================

@pytest.fixture
def validated_execution_result(execution_result):
    """
    Validate execution result once, reuse in all tests
    This eliminates repetitive assertions in test methods
    """
    assert execution_result is not None, "ExecutionResult is None"
    
    assert execution_result.status in SUCCESSFUL_STATUSES, (
        f"Expected successful status, got '{execution_result.status}'\n"
        f"Error: {execution_result.error}\n"
        f"Failed paths: {execution_result.get_failed_paths()}"
    )
    
    return execution_result

# ============================================
# HELPER FIXTURES
# ============================================

@pytest.fixture
def execution_summary(validated_execution_result):
    """Get execution summary stats"""
    return validated_execution_result.summary_stats()

@pytest.fixture
def all_sub_results(validated_execution_result):
    """Get flattened list of all results"""
    return validated_execution_result.flatten()