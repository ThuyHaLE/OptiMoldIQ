# tests/agents_tests/conftest.py - Centralized dependency providers

import pytest
from pathlib import Path
from typing import Dict, Any
from configs.shared.shared_source_config import SharedSourceConfig
from configs.shared.agent_report_format import ExecutionStatus

# ============================================
# DEPENDENCY PROVIDERS
# ============================================

class DependencyProvider:
    """
    Manages test dependencies - only loads what's needed
    """
    
    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self._test_dirs = self._setup_test_dirs()
    
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
    
    def get_shared_source_config(self) -> SharedSourceConfig:
        """Get basic config without running any dependencies"""
        from agents.orderProgressTracker.order_progress_tracker import SharedSourceConfig
        
        return SharedSourceConfig(
            db_dir=str(self._test_dirs["db_dir"]),
            default_dir=str(self._test_dirs["shared_dir"])
        )
    
    def trigger_order_progress_tracker(self, config: SharedSourceConfig) -> Dict[str, Any]:
        """
        Lazy load: Only run OrderProgressTracker if requested
        """
        if "order_progress_tracker" not in self._cache:
            from agents.orderProgressTracker.order_progress_tracker import OrderProgressTracker
            tracker = OrderProgressTracker(config=config)
            result = tracker.run_tracking_and_save_results()

            # Cache result
            assert result.status == ExecutionStatus.SUCCESS.value, "Dependency agent failed : OrderProgressTracker"
            self._cache["order_progress_tracker"] = {"status": "triggered", 
                                                     "result": result,
                                                     "config": config}
            
    def trigger_validation_orchestrator(self, config: SharedSourceConfig) -> Dict[str, Any]:
        """
        Lazy load: Only run ValidationOrchestrator if requested
        """
        if "validation_orchestrator" not in self._cache:
            from agents.validationOrchestrator.validation_orchestrator import ValidationOrchestrator
            validation_orchestrator = ValidationOrchestrator(
                shared_source_config=config,
                enable_parallel = False,
                max_workers = None)
            result = validation_orchestrator.run_validations_and_save_results()

            # Cache result
            assert result.status == ExecutionStatus.SUCCESS.value, "Dependency agent failed : ValidationOrchestrator"
            self._cache["validation_orchestrator"] = {"status": "triggered", 
                                                     "result": result,
                                                     "config": config}
    
    def trigger_historical_features_extractor(self, config: SharedSourceConfig) -> Dict[str, Any]:
        """
        Lazy load: Only run HistoricalFeaturesExtractor if requested
        """
        if "historical_features_extractor" not in self._cache:
            from agents.autoPlanner.featureExtractor.initial.historicalFeaturesExtractor.historical_features_extractor import (
                HistoricalFeaturesExtractor, FeaturesExtractorConfig)
            
            historical_features_extractor = HistoricalFeaturesExtractor(
                config = FeaturesExtractorConfig(
                    efficiency = 0.85,
                    loss = 0.03,
                    shared_source_config = config)
                    )
            result = historical_features_extractor.run_extraction_and_save_results()

            # Cache result
            assert result.status == ExecutionStatus.SUCCESS.value, "Dependency agent failed : HistoricalFeaturesExtractor"
            self._cache["historical_features_extractor"] = {"status": "triggered", 
                                                            "result": result,
                                                            "config": config}
        
    def trigger(self, dependency_name: str):
        if dependency_name == "ValidationOrchestrator":
            self.trigger_validation_orchestrator(self.get_shared_source_config())
        elif dependency_name == "OrderProgressTracker":
            self.trigger_order_progress_tracker(self.get_shared_source_config())
        elif dependency_name == "HistoricalFeaturesExtractor":
            self.trigger_historical_features_extractor(self.get_shared_source_config())
        else:
            raise ValueError(f"Unknown dependency: {dependency_name}")
        
    # Another dependency - only loads if needed
    # e.g., SharedSourceConfig provider
    
    def cleanup(self):
        """Cleanup test artifacts"""
        import shutil
        for dir_path in self._test_dirs.values():
            if dir_path.exists():
                shutil.rmtree(dir_path)


@pytest.fixture(scope="session")
def dependency_provider():
    """
    Session-scoped provider - dependencies run once and cached
    """
    provider = DependencyProvider()
    yield provider
    provider.cleanup()