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
    
    def _setup_test_dirs(self) -> Dict[str, Path]:
        """Setup test directories once"""
        dirs = {"shared_dir": Path("tests/shared_db")}
        for dir_path in dirs.values():
            dir_path.mkdir(parents=True, exist_ok=True)
        return dirs
    
    def get_shared_source_config(self) -> SharedSourceConfig:
        """Get basic config without running any dependencies"""
        if "shared_config" not in self._cache:
            self._cache["shared_config"] = SharedSourceConfig(
                db_dir="tests/mock_database", # Mock databases for testing
                default_dir=str(self._test_dirs["shared_dir"])
            )
        return self._cache["shared_config"]
    
    # ========== Individual Triggers (unchanged) ==========
    
    def trigger_data_pipeline_orchestrator(self) -> ExecutionResult:
        """Lazy load: Only run DataPipelineOrchestrator if requested"""
        from agents.dataPipelineOrchestrator.data_pipeline_orchestrator import DataPipelineOrchestrator
        config = self.get_shared_source_config()
        pipeline_orchestrator = DataPipelineOrchestrator(
            config=config
        )
        result = pipeline_orchestrator.run_collecting_and_save_results()
        
        self._validate_result(result, "DataPipelineOrchestrator")
    
    def trigger_validation_orchestrator(self) -> ExecutionResult:
        """Lazy load: Only run ValidationOrchestrator if requested"""
        from agents.validationOrchestrator.validation_orchestrator import ValidationOrchestrator
        config = self.get_shared_source_config()
        validation_orchestrator = ValidationOrchestrator(
            shared_source_config=config,
            enable_parallel=False,
            max_workers=None
        )
        result = validation_orchestrator.run_validations_and_save_results()
        
        self._validate_result(result, "ValidationOrchestrator")
    
    def trigger_order_progress_tracker(self) -> ExecutionResult:
        """Lazy load: Only run OrderProgressTracker if requested"""
        from agents.orderProgressTracker.order_progress_tracker import OrderProgressTracker
        
        config = self.get_shared_source_config()
        tracker = OrderProgressTracker(config=config)
        result = tracker.run_tracking_and_save_results()
        
        self._validate_result(result, "OrderProgressTracker")
    
    def trigger_historical_features_extractor(self) -> ExecutionResult:
        """Lazy load: Only run HistoricalFeaturesExtractor if requested"""
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
        
        self._validate_result(result, "HistoricalFeaturesExtractor")
    
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
    
    def trigger_all_dependencies(self, dependency_names: list[str]):
        """Trigger multiple dependencies and return results"""
        for dep in dependency_names:
            self.trigger(dep)
    
    def clear_all_dependencies(self):
        """Remove and recreate all dependency folders"""
        for dir_path in self._test_dirs.values():
            if dir_path.exists():
                shutil.rmtree(dir_path)
            dir_path.mkdir(parents=True, exist_ok=True)

        logger.info("✓ self._test_dirs reset to empty")

    # ========== CLEANUP ==========
    
    def cleanup(self):
        """Cleanup all test artifacts"""
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