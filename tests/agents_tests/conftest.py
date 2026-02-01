# tests/agents_tests/conftest.py

import pytest
import shutil
from pathlib import Path
from typing import Dict, Any, Set, Optional
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
# DEPENDENCY PROVIDER - State Management
# ============================================

class DependencyProvider:
    """
    Manages test dependencies with proper state lifecycle
    
    Key insight:
    - Dependencies write to SHARED folders (via config)
    - We track what's been triggered
    - clear_dependency() removes both cache AND files
    - re-trigger regenerates everything
    """
    
    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self._test_dirs = self._setup_test_dirs()
        self._dependency_graph = self._build_dependency_graph()
        self._validate_dependency_graph()
        
        # Track what's been written to disk
        self._materialized_dependencies: Set[str] = set()
    
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
            "DataPipelineOrchestrator": set(),
            "AnalyticsOrchestrator": {"DataPipelineOrchestrator"},
            "DashboardBuilder": {"DataPipelineOrchestrator"},
            "ValidationOrchestrator": {"DataPipelineOrchestrator"},
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
    
    def is_materialized(self, dependency_name: str) -> bool:
        """Check if dependency files exist on disk"""
        return dependency_name in self._materialized_dependencies
    
    def get_result(self, dependency_name: str) -> ExecutionResult:
        """Get cached result for dependency"""
        if dependency_name not in self._cache:
            raise ValueError(f"Dependency '{dependency_name}' not triggered yet")
        return self._cache[dependency_name]["result"]
    
    # ========== DEPENDENCY OUTPUT PATHS ==========
    
    def _get_dependency_output_dir(self, dependency_name: str) -> Path:
        """Get output directory for a dependency"""
        base_dir = self._test_dirs["shared_dir"]
        
        # Map dependency names to their output folders
        dir_map = {
            "DataPipelineOrchestrator": base_dir / "DataPipelineOrchestrator",
            "AnalyticsOrchestrator": base_dir / "AnalyticsOrchestrator",
            "DashboardBuilder": base_dir / "DashboardBuilder",
            "ValidationOrchestrator": base_dir / "ValidationOrchestrator",
            "OrderProgressTracker": base_dir / "OrderProgressTracker",
            "HistoricalFeaturesExtractor": base_dir / "HistoricalFeaturesExtractor",
            "InitialPlanner": base_dir / "InitialPlanner"
        }
        
        return dir_map.get(dependency_name, base_dir / dependency_name)
    
    # ========== CLEAR DEPENDENCY ==========
    
    def clear_dependency(self, dependency_name: str, cascade: bool = True):
        """
        Clear a dependency and optionally its dependents
        
        Args:
            dependency_name: Name of dependency to clear
            cascade: If True, also clear all dependencies that depend on this one
        
        Example:
            clear_dependency("ValidationOrchestrator", cascade=True)
            # Also clears: OrderProgressTracker, HistoricalFeaturesExtractor, InitialPlanner
        """
        if dependency_name not in self._dependency_graph:
            raise ValueError(f"Unknown dependency: {dependency_name}")
        
        # Find all dependents if cascading
        to_clear = {dependency_name}
        if cascade:
            to_clear.update(self._get_all_dependents(dependency_name))
        
        # Clear in reverse dependency order
        sorted_clear = self._topological_sort(to_clear)
        
        for dep in sorted_clear:
            self._clear_single_dependency(dep)
        
        logger.info(f"✓ Cleared dependencies: {sorted_clear}")
    
    def _clear_single_dependency(self, dependency_name: str):
        """Clear a single dependency (cache + files)"""
        # 1. Remove from memory cache
        if dependency_name in self._cache:
            del self._cache[dependency_name]
        
        # 2. Remove files from disk
        output_dir = self._get_dependency_output_dir(dependency_name)
        if output_dir.exists():
            shutil.rmtree(output_dir)
            logger.debug(f"  Deleted: {output_dir}")
        
        # 3. Update materialized tracking
        self._materialized_dependencies.discard(dependency_name)
    
    def _get_all_dependents(self, dependency_name: str) -> Set[str]:
        """Get all dependencies that depend on this one (recursively)"""
        dependents = set()
        
        for node, deps in self._dependency_graph.items():
            if dependency_name in deps:
                dependents.add(node)
                # Recursive: also get dependents of dependents
                dependents.update(self._get_all_dependents(node))
        
        return dependents
    
    def _topological_sort(self, nodes: Set[str]) -> list[str]:
        """Sort nodes in reverse dependency order (leaves first)"""
        # Compute in-degree for nodes
        in_degree = {node: 0 for node in nodes}
        
        for node in nodes:
            for dep in self._dependency_graph[node]:
                if dep in nodes:
                    in_degree[node] += 1
        
        # Start with nodes that have no dependencies in the set
        queue = [n for n in nodes if in_degree[n] == 0]
        result = []
        
        while queue:
            node = queue.pop(0)
            result.append(node)
            
            # Find nodes that depend on current node
            for other in nodes:
                if node in self._dependency_graph[other] and other not in result:
                    in_degree[other] -= 1
                    if in_degree[other] == 0:
                        queue.append(other)
        
        # Reverse to get leaves first (for deletion order)
        return list(reversed(result))
    
    # ========== CLEAR ALL ==========
    
    def clear_all_dependencies(self):
        """Clear ALL dependencies - complete reset"""
        all_deps = set(self._dependency_graph.keys())
        sorted_deps = self._topological_sort(all_deps)
        
        for dep in sorted_deps:
            self._clear_single_dependency(dep)
        
        logger.info("✓ Cleared all dependencies")
    
    # ========== Individual Triggers (unchanged) ==========
    
    def trigger_data_pipeline_orchestrator(self) -> ExecutionResult:
        """Lazy load: Only run DataPipelineOrchestrator if requested"""
        if "DataPipelineOrchestrator" not in self._cache:
            from agents.dataPipelineOrchestrator.data_pipeline_orchestrator import DataPipelineOrchestrator
            
            config = self.get_shared_source_config()
            pipeline_orchestrator = DataPipelineOrchestrator(
                config=config
            )
            result = pipeline_orchestrator.run_collecting_and_save_results()
            
            self._validate_result(result, "DataPipelineOrchestrator")
            
            self._cache["DataPipelineOrchestrator"] = {
                "status": "triggered",
                "result": result,
                "config": config
            }
            
            # Mark as materialized (files written to disk)
            self._materialized_dependencies.add("ValidationOrchestrator")
        
        return self._cache["ValidationOrchestrator"]["result"]
    
    def trigger_validation_orchestrator(self) -> ExecutionResult:
        """Lazy load: Only run ValidationOrchestrator if requested"""
        if "ValidationOrchestrator" not in self._cache:
            # Ensure dependencies
            self.trigger_data_pipeline_orchestrator()

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
            
            # Mark as materialized (files written to disk)
            self._materialized_dependencies.add("ValidationOrchestrator")
        
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
            
            self._materialized_dependencies.add("OrderProgressTracker")
        
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
            
            self._materialized_dependencies.add("HistoricalFeaturesExtractor")
        
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
            "DataPipelineOrchestrator": self.trigger_data_pipeline_orchestrator,
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
    
    # ========== CLEANUP ==========
    
    def cleanup(self):
        """Cleanup all test artifacts"""
        self.clear_all_dependencies()
        
        # Also remove base directories
        for dir_path in self._test_dirs.values():
            if dir_path.exists():
                shutil.rmtree(dir_path)
        
        logger.info("✓ Complete cleanup done")

# ============================================
# FIXTURES
# ============================================

@pytest.fixture(scope="session")
def dependency_provider():
    """
    Session-scoped provider - dependencies run once and cached
    """
    provider = DependencyProvider()
    yield provider
    provider.cleanup()

@pytest.fixture(scope="function")
def isolated_dependency_provider():
    """
    Function-scoped provider - clears after each test
    Use when you need fresh state
    """
    provider = DependencyProvider()
    yield provider
    provider.clear_all_dependencies()

# ============================================
# VALIDATION FIXTURES
# ============================================

@pytest.fixture
def validated_execution_result(execution_result):
    """Validate execution result once, reuse in all tests"""
    assert execution_result is not None, "ExecutionResult is None"
    
    assert execution_result.status in SUCCESSFUL_STATUSES, (
        f"Expected successful status, got '{execution_result.status}'\n"
        f"Error: {execution_result.error}\n"
        f"Failed paths: {execution_result.get_failed_paths()}"
    )
    
    return execution_result

@pytest.fixture
def execution_summary(validated_execution_result):
    """Get execution summary stats"""
    return validated_execution_result.summary_stats()

@pytest.fixture
def all_sub_results(validated_execution_result):
    """Get flattened list of all results"""
    return validated_execution_result.flatten()