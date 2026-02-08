# tests/agents_tests/test_analytics_orchestrator.py

import pytest
from tests.agents_tests.base_agent_tests import BaseAgentTests
from tests.agents_tests.conftest import DependencyProvider
from configs.shared.agent_report_format import ExecutionStatus, ExecutionResult

class TestAnalyticsOrchestrator(BaseAgentTests):
    """
    Test AnalyticsOrchestrator - Orchestrates analytics workflows
    Inherits all structural tests from BaseAgentTests
    
    Dependencies:
        - DataPipelineOrchestrator
    
    Purpose:
        - Track hardware changes (machine layout, mold-machine pairs)
        - Process performance data at multiple levels (day, month, year)
        - Coordinate analytics workflows
    
    Test Strategy:
        1. Structure tests from BaseAgentTests (inherited)
        2. Business logic: workflow coordination
        3. Component execution validation
        4. Output structure checks
    """
    
    # ============================================
    # FIXTURES - Required by BaseAgentTests
    # ============================================
    
    @pytest.fixture
    def agent_instance(self, dependency_provider: DependencyProvider):
        """
        Create AnalyticsOrchestrator instance
        Triggers DataPipelineOrchestrator dependency
        """
        # Trigger DataPipelineOrchestrator dependency
        dependency_provider.clear_all_dependencies()
        dependency_provider.trigger_all_dependencies(["DataPipelineOrchestrator"])

        from agents.analyticsOrchestrator.analytics_orchestrator import (
            ComponentConfig,
            AnalyticsOrchestratorConfig,
            AnalyticsOrchestrator
        )
        
        return AnalyticsOrchestrator(
            config=AnalyticsOrchestratorConfig(
                shared_source_config=dependency_provider.get_shared_source_config(),
                
                # Workflow 1: Hardware trackers
                machine_layout_tracker=ComponentConfig(
                    enabled=True,
                    save_result=True
                ),
                mold_machine_pair_tracker=ComponentConfig(
                    enabled=True,
                    save_result=True
                ),
                
                # Workflow 2: Performance processors
                day_level_processor=ComponentConfig(
                    enabled=True,
                    save_result=True,
                    requested_timestamp='2018-11-06'
                ),
                month_level_processor=ComponentConfig(
                    enabled=True,
                    save_result=True,
                    requested_timestamp='2019-01',
                    analysis_date='2019-01-15'
                ),
                year_level_processor=ComponentConfig(
                    enabled=True,
                    save_result=True,
                    requested_timestamp='2019',
                    analysis_date='2019-12-31'
                ),
                
                # Top-level logging
                save_orchestrator_log=True
            )
        )
    
    @pytest.fixture
    def execution_result(self, agent_instance):
        """
        Execute AnalyticsOrchestrator
        
        Note: No assertions here - validated_execution_result fixture handles validation
        """
        # ✅ Just return - let validated_execution_result handle validation
        return agent_instance.run_analyzing()
    
    # ============================================
    # BUSINESS LOGIC TESTS
    # ============================================
        
    def test_has_analytics_workflows(self, validated_execution_result):
        """Should execute analytics workflows"""
        assert validated_execution_result.is_composite, \
            "AnalyticsOrchestrator should be composite (have sub-workflows)"
        
        assert len(validated_execution_result.sub_results) > 0, \
            "Should execute at least one analytics workflow"
    
    def test_expected_analyzers_exist(self, validated_execution_result):
        """Expected analytics analyzers should exist"""
        analyzer_names = {r.name for r in validated_execution_result.sub_results}
        
        expected_analyzers = {
            "HardwareChangeAnalyzer",
            "MultiLevelPerformanceAnalyzer"
        }
        
        assert expected_analyzers.issubset(analyzer_names), \
            f"Missing expected analyzers. Found: {analyzer_names}, Expected: {expected_analyzers}"
    
    def test_all_components_completed_or_skipped_with_reason(self, validated_execution_result):
        """All components should complete or have skip reason"""
        for component in validated_execution_result.sub_results:
            if component.status == ExecutionStatus.SKIPPED.value:
                # Should have skip reason
                assert component.skipped_reason is not None, \
                    f"Component '{component.name}' skipped without reason"

    def test_analytics_output_structure(self, validated_execution_result):
        """Analytics results should follow the expected output structure"""
        if validated_execution_result is None:
            pytest.skip("AnalyticsOrchestrator was not executed")

        # Successful analytics output should be composite (contain sub-trackers)
        if validated_execution_result.status in {"success", "degraded", "warning"}:
            assert validated_execution_result.is_composite, \
                "AnalyticsOrchestrator is expected to produce a composite result with sub-trackers"

            # Expected analyzers and their corresponding trackers
            expected_analyzers = {
                "HardwareChangeAnalyzer": [
                    "MachineLayoutTracker",
                    "MoldMachinePairTracker",
                ],
                "MultiLevelPerformanceAnalyzer": [
                    "DayLevelDataProcessor",
                    "MonthLevelDataProcessor",
                    "YearLevelDataProcessor",
                ],
            }

            for analyzer_name, expected_trackers in expected_analyzers.items():
                analyzer_result = validated_execution_result.get_path(analyzer_name)

                assert isinstance(analyzer_result, ExecutionResult), \
                    f"Analyzer '{analyzer_name}' should return an ExecutionResult"

                if analyzer_result.status in {"success", "degraded", "warning"}:
                    for tracker_name in expected_trackers:
                        tracker_result = analyzer_result.get_path(tracker_name)

                        assert isinstance(tracker_result, ExecutionResult), \
                            f"Tracker '{tracker_name}' should return an ExecutionResult"

                        # Successful trackers are expected to expose structured result data
                        if validated_execution_result.status in {"success", "degraded", "warning"}:
                            assert isinstance(tracker_result.data, dict), \
                                f"Tracker '{tracker_result.name}' should expose data as a dict"

                            assert "result" in tracker_result.data, \
                                "Tracker data is missing the 'result' field"

                            tracker_data = tracker_result.data["result"]

                            assert "payload" in tracker_data, \
                                "Tracker result is missing the 'payload' field"
    
    def test_no_critical_failures(self, validated_execution_result):
        """Analytics orchestration should not have critical failures"""
        assert not validated_execution_result.has_critical_errors(), \
            f"AnalyticsOrchestrator has critical errors: {validated_execution_result.get_failed_paths()}"
    
    # ============================================
    # CONFIGURATION TESTS
    # ============================================
    
    def test_all_components_enabled(self, agent_instance):
        """All components should be enabled in test configuration"""
        config = agent_instance.config
        
        # Hardware trackers
        assert config.machine_layout_tracker.enabled is True
        assert config.mold_machine_pair_tracker.enabled is True
        
        # Performance processors
        assert config.day_level_processor.enabled is True
        assert config.month_level_processor.enabled is True
        assert config.year_level_processor.enabled is True
    
    def test_all_components_save_enabled(self, agent_instance):
        """All components should have save enabled"""
        config = agent_instance.config
        
        # Hardware trackers
        assert config.machine_layout_tracker.save_result is True
        assert config.mold_machine_pair_tracker.save_result is True
        
        # Performance processors
        assert config.day_level_processor.save_result is True
        assert config.month_level_processor.save_result is True
        assert config.year_level_processor.save_result is True
    
    def test_orchestrator_log_save_enabled(self, agent_instance):
        """Orchestrator log save should be enabled"""
        assert agent_instance.config.save_orchestrator_log is True
    
    # ============================================
    # INTEGRATION TESTS
    # ============================================
    
    @pytest.mark.integration
    def test_orchestrator_and_analyzer_logs_created(
        self,
        validated_execution_result,
        dependency_provider,
    ):
        """Orchestrator and analyzer logs should be created when enabled"""
        from pathlib import Path

        orchestrator_result = validated_execution_result

        if orchestrator_result is None:
            pytest.skip("AnalyticsOrchestrator was not executed")

        if orchestrator_result.status not in {"success", "degraded", "warning"}:
            pytest.skip("AnalyticsOrchestrator did not complete successfully")

        shared_config = dependency_provider.get_shared_source_config()

        # -------------------------------------------------
        # Orchestrator-level log
        # -------------------------------------------------
        orchestrator_log_path = Path(shared_config.analytics_orchestrator_log_path)
        assert orchestrator_log_path.exists(), \
            f"Analytics orchestrator log not created: {orchestrator_log_path}"

        # -------------------------------------------------
        # Analyzer-level logs
        # -------------------------------------------------
        analyzer_log_paths = {
            "HardwareChangeAnalyzer": shared_config.hardware_change_analyzer_log_path,
            "MultiLevelPerformanceAnalyzer": shared_config.multi_level_performance_analyzer_log_path,
        }

        for analyzer_name, log_path_str in analyzer_log_paths.items():
            analyzer_result = orchestrator_result.get_path(analyzer_name)

            assert isinstance(analyzer_result, ExecutionResult), \
                f"Analyzer '{analyzer_name}' should return an ExecutionResult"

            if analyzer_result.status in {"success", "degraded", "warning"}:
                log_path = Path(log_path_str)

                assert log_path.exists(), \
                    f"Log not created for analyzer '{analyzer_name}': {log_path}"

    @pytest.mark.integration
    def test_analyzer_directories_created(self, validated_execution_result):
        """All savable analyzer outputs should be written to disk"""
        from pathlib import Path

        orchestrator_result = validated_execution_result

        if orchestrator_result.status not in {"success", "degraded", "warning"}:
            pytest.skip("Orchestrator did not complete successfully")

        # Expected analyzers to validate
        expected_analyzers = [
            "HardwareChangeAnalyzer",
            "MultiLevelPerformanceAnalyzer",
        ]

        for analyzer_name in expected_analyzers:
            analyzer_result = orchestrator_result.get_path(analyzer_name)

            assert isinstance(analyzer_result, ExecutionResult), \
                f"Analyzer '{analyzer_name}' should return an ExecutionResult"

            save_routing = analyzer_result.metadata.get("save_routing", {})

            # All enabled & savable phases should have their output paths created
            for phase_name, phase_cfg in save_routing.items():
                if phase_cfg.get("enabled") and phase_cfg.get("savable"):
                    save_paths = phase_cfg.get("save_paths", {}).values()

                    assert all(Path(path).exists() for path in save_paths), \
                        (
                            f"Missing saved outputs for analyzer '{analyzer_name}', "
                            f"phase '{phase_name}'"
                        )
    
    # ============================================
    # PERFORMANCE TESTS
    # ============================================
    
    @pytest.mark.performance
    def test_orchestrator_performance(self, validated_execution_result):
        """Orchestrator should complete in reasonable time"""
        MAX_DURATION = 180.0  # 3 minutes - orchestrator coordinates multiple workflows
        
        assert validated_execution_result.duration < MAX_DURATION, (
            f"Orchestrator took {validated_execution_result.duration:.2f}s "
            f"(max {MAX_DURATION}s)"
        )
    
    @pytest.mark.performance
    def test_individual_analyzer_performance(self, validated_execution_result):
        """Individual analyzers should complete in reasonable time"""
        MAX_ANALYZER_DURATION = 90.0  # 1.5 minutes per analyzer
        
        for analyzer in validated_execution_result.sub_results:
            if analyzer.status in {"success", "degraded", "warning"}:
                assert analyzer.duration < MAX_ANALYZER_DURATION, (
                    f"Analyzer '{analyzer.name}' took {analyzer.duration:.2f}s "
                    f"(max {MAX_ANALYZER_DURATION}s)"
                )

# ============================================
# OPTIONAL: Configuration Variation Tests
# ============================================

class TestAnalyticsOrchestratorConfigurations:
    """
    Test AnalyticsOrchestrator with different configurations
    Separate from BaseAgentTests to avoid interference
    """
    
    def test_with_hardware_only(self, dependency_provider: DependencyProvider):
        """Test with only hardware trackers enabled"""
        from agents.analyticsOrchestrator.analytics_orchestrator import (
            ComponentConfig,
            AnalyticsOrchestratorConfig,
            AnalyticsOrchestrator
        )
        
        agent = AnalyticsOrchestrator(
            config=AnalyticsOrchestratorConfig(
                shared_source_config=dependency_provider.get_shared_source_config(),
                
                # Hardware trackers enabled
                machine_layout_tracker=ComponentConfig(
                    enabled=True,
                    save_result=True
                ),
                mold_machine_pair_tracker=ComponentConfig(
                    enabled=True,
                    save_result=True
                ),
                
                # Performance processors disabled
                day_level_processor=ComponentConfig(
                    enabled=False,
                    save_result=False
                ),
                month_level_processor=ComponentConfig(
                    enabled=False,
                    save_result=False
                ),
                year_level_processor=ComponentConfig(
                    enabled=False,
                    save_result=False
                ),
                
                save_orchestrator_log=True
            )
        )
        
        result = agent.run_analyzing()
        
        # Should succeed with partial components
        assert result.status in {"success", "degraded", "warning"}
        
        # Hardware analyzer should exist
        assert result.get_path("HardwareChangeAnalyzer") is not None
        
        # Performance analyzer might be skipped or absent
        perf_analyzer = result.get_path("MultiLevelPerformanceAnalyzer")
        if perf_analyzer:
            assert perf_analyzer.status == ExecutionStatus.SKIPPED.value
    
    def test_with_performance_only(self, dependency_provider: DependencyProvider):
        """Test with only performance processors enabled"""
        from agents.analyticsOrchestrator.analytics_orchestrator import (
            ComponentConfig,
            AnalyticsOrchestratorConfig,
            AnalyticsOrchestrator
        )
        
        agent = AnalyticsOrchestrator(
            config=AnalyticsOrchestratorConfig(
                shared_source_config=dependency_provider.get_shared_source_config(),
                
                # Hardware trackers disabled
                machine_layout_tracker=ComponentConfig(
                    enabled=False,
                    save_result=False
                ),
                mold_machine_pair_tracker=ComponentConfig(
                    enabled=False,
                    save_result=False
                ),
                
                # Performance processors enabled
                day_level_processor=ComponentConfig(
                    enabled=True,
                    save_result=True,
                    requested_timestamp='2018-11-06'
                ),
                month_level_processor=ComponentConfig(
                    enabled=True,
                    save_result=True,
                    requested_timestamp='2019-01',
                    analysis_date='2019-01-15'
                ),
                year_level_processor=ComponentConfig(
                    enabled=True,
                    save_result=True,
                    requested_timestamp='2019',
                    analysis_date='2019-12-31'
                ),
                
                save_orchestrator_log=True
            )
        )
        
        result = agent.run_analyzing()
        
        # Should succeed
        assert result.status in {"success", "degraded", "warning"}
        
        # Performance analyzer should exist
        assert result.get_path("MultiLevelPerformanceAnalyzer") is not None
    
    def test_with_save_disabled(self, dependency_provider: DependencyProvider):
        """Test with save disabled for all components"""
        from agents.analyticsOrchestrator.analytics_orchestrator import (
            ComponentConfig,
            AnalyticsOrchestratorConfig,
            AnalyticsOrchestrator
        )
        
        agent = AnalyticsOrchestrator(
            config=AnalyticsOrchestratorConfig(
                shared_source_config=dependency_provider.get_shared_source_config(),
                
                # All enabled but save disabled
                machine_layout_tracker=ComponentConfig(
                    enabled=True,
                    save_result=False
                ),
                mold_machine_pair_tracker=ComponentConfig(
                    enabled=True,
                    save_result=False
                ),
                day_level_processor=ComponentConfig(
                    enabled=True,
                    save_result=False,
                    requested_timestamp='2018-11-06'
                ),
                month_level_processor=ComponentConfig(
                    enabled=True,
                    save_result=False,
                    requested_timestamp='2019-01',
                    analysis_date='2019-01-15'
                ),
                year_level_processor=ComponentConfig(
                    enabled=True,
                    save_result=False,
                    requested_timestamp='2019',
                    analysis_date='2019-12-31'
                ),
                
                save_orchestrator_log=False
            )
        )
        
        result = agent.run_analyzing()
        
        # Should still succeed
        assert result.status in {"success", "degraded", "warning"}

# ============================================
# DEPENDENCY INTERACTION TESTS
# ============================================

class TestAnalyticsOrchestratorDependencies:
    """Test AnalyticsOrchestrator's interaction with DataPipelineOrchestrator"""
    
    def test_fails_without_pipeline(self, dependency_provider: DependencyProvider):
        """Should fail or degrade without DataPipelineOrchestrator"""
        from agents.analyticsOrchestrator.analytics_orchestrator import (
            ComponentConfig,
            AnalyticsOrchestratorConfig,
            AnalyticsOrchestrator
        )
        
        # Clear all dependencies
        dependency_provider.clear_all_dependencies()
        
        # Create agent with full config
        agent = AnalyticsOrchestrator(
            config=AnalyticsOrchestratorConfig(
                shared_source_config=dependency_provider.get_shared_source_config(),
                machine_layout_tracker=ComponentConfig(enabled=True, save_result=True),
                mold_machine_pair_tracker=ComponentConfig(enabled=True, save_result=True),
                day_level_processor=ComponentConfig(
                    enabled=True,
                    save_result=True,
                    requested_timestamp='2018-11-06'
                ),
                month_level_processor=ComponentConfig(
                    enabled=True,
                    save_result=True,
                    requested_timestamp='2019-01',
                    analysis_date='2019-01-15'
                ),
                year_level_processor=ComponentConfig(
                    enabled=True,
                    save_result=True,
                    requested_timestamp='2019',
                    analysis_date='2019-12-31'
                ),
                save_orchestrator_log=True
            )
        )
        
        # Execute
        result = agent.run_analyzing()
        
        # Should fail or degrade
        assert result.status in [ExecutionStatus.FAILED.value, 
                                 ExecutionStatus.DEGRADED.value], \
            f"Should fail or degrade without DataPipelineOrchestrator, got: {result.status}"
        
        # Additional validation based on status
        if result.status == ExecutionStatus.FAILED.value:
            # Check for error information
            assert result.error is not None or len(result.get_failed_paths()) > 0, \
                "Failed status should have error information or failed paths"
    
    def test_recovery_after_dependency_added(self, dependency_provider: DependencyProvider):
        """Test that analytics works after DataPipelineOrchestrator is added"""
        from agents.analyticsOrchestrator.analytics_orchestrator import (
            ComponentConfig,
            AnalyticsOrchestratorConfig,
            AnalyticsOrchestrator
        )
        
        # Start with clean state
        dependency_provider.clear_all_dependencies()
        
        # Create agent config (reusable)
        config = AnalyticsOrchestratorConfig(
            shared_source_config=dependency_provider.get_shared_source_config(),
            machine_layout_tracker=ComponentConfig(enabled=True, save_result=True),
            mold_machine_pair_tracker=ComponentConfig(enabled=True, save_result=True),
            day_level_processor=ComponentConfig(
                enabled=True,
                save_result=True,
                requested_timestamp='2018-11-06'
            ),
            month_level_processor=ComponentConfig(
                enabled=True,
                save_result=True,
                requested_timestamp='2019-01',
                analysis_date='2019-01-15'
            ),
            year_level_processor=ComponentConfig(
                enabled=True,
                save_result=True,
                requested_timestamp='2019',
                analysis_date='2019-12-31'
            ),
            save_orchestrator_log=True
        )
        
        # First execution - should fail or degrade
        agent1 = AnalyticsOrchestrator(config=config)
        result1 = agent1.run_analyzing()
        
        assert result1.status in [ExecutionStatus.FAILED.value, 
                                  ExecutionStatus.DEGRADED.value], \
            f"Should fail or degrade without dependency, got: {result1.status}"
        
        # Add dependency
        dependency_provider.clear_all_dependencies()
        dependency_provider.trigger_all_dependencies(["DataPipelineOrchestrator"])
        
        # Second execution - should succeed (create new instance)
        agent2 = AnalyticsOrchestrator(config=config)
        result2 = agent2.run_analyzing()
        
        assert result2.status == ExecutionStatus.SUCCESS.value, \
            f"Should succeed after DataPipelineOrchestrator is added, got: {result2.status}\n" \
            f"Error: {result2.error}\n" \
            f"Failed paths: {result2.get_failed_paths()}"