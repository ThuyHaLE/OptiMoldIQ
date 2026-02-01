# tests/agents_tests/test_analytics_orchestrator.py

from platform import processor
import pytest
from tests.agents_tests.base_agent_tests import BaseAgentTests
from tests.agents_tests.conftest import DependencyProvider
from configs.shared.agent_report_format import ExecutionStatus

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
        dependency_provider.trigger("DataPipelineOrchestrator")

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
    
    # Test dependency usage
    def test_uses_pipeline_data(self, dependency_provider, validated_execution_result):
        """Should use data from DataPipelineOrchestrator"""
        # Get cached pipeline result
        pipeline_result = dependency_provider.get_result("DataPipelineOrchestrator")
        
        assert pipeline_result is not None, \
            "DataPipelineOrchestrator should be cached"
        
        # Verify pipeline completed successfully
        successful_statuses = {ExecutionStatus.SUCCESS.value, 
                               ExecutionStatus.DEGRADED.value, 
                               ExecutionStatus.WARNING.value}
        assert pipeline_result.status in successful_statuses, \
            "Pipeline dependency should have completed successfully"
    
    # Test dependency chain
    def test_dependency_triggered_before_execution(self, dependency_provider):
        """DataPipelineOrchestrator should be triggered before validation"""
        assert dependency_provider.is_triggered("DataPipelineOrchestrator"), \
            "DataPipelineOrchestrator dependency should be triggered"
        
        # Should be cached
        cached_result = dependency_provider.get_result("DataPipelineOrchestrator")
        assert cached_result is not None, \
            "Pipeline result should be cached"
        
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
        """Analytics results should have expected structure"""
        if validated_execution_result is None:
            pytest.skip("AnalyticsOrchestrator not executed")

        # Should be composite (have trackers)
        if validated_execution_result.status in {"success", "degraded", "warning"}:
            assert validated_execution_result.is_composite, \
                "AnalyticsOrchestrator should have sub-trackers"
            
            # Expected analyzers
            analyzer_names = {r.name for r in validated_execution_result.sub_results}
            expected_analyzers = {'HardwareChangeAnalyzer', 'MultiLevelPerformanceAnalyzer'}
            
            # At least one tracker should exist if analyzer succeeded
            assert len(analyzer_names & expected_analyzers) > 0, \
                f"No expected analyzers found. Found: {analyzer_names}"

            for sub in analyzer_names:
                self_result = validated_execution_result.get_path(sub)
                result_data = self_result.data["result"] 
                assert "payload" in result_data, \
                    "Missing 'payload' in result data"
    
    def test_no_critical_failures(self, validated_execution_result):
        """Analytics orchestration should not have critical failures"""
        assert not validated_execution_result.has_critical_errors(), \
            f"AnalyticsOrchestrator has critical errors: {validated_execution_result.get_failed_paths()}"
    
    # ============================================
    # ANALYZER-SPECIFIC TESTS
    # ============================================

    def test_hardware_analyzers_configuration(self, validated_execution_result):
        """Hardware analyzers should use correct configuration"""
        hardware_analyzer = validated_execution_result.get_path("HardwareChangeAnalyzer")
        
        if hardware_analyzer is None:
            pytest.skip("HardwareChangeAnalyzer not executed")
        
        # Each analyzer should have data if successful
        if hardware_analyzer.status in {"success", "degraded", "warning"}:
            assert isinstance(hardware_analyzer.data, dict), \
                f"Analyzer '{hardware_analyzer.name}' should have data dict"

    def test_performance_analyzers_timestamps(self, validated_execution_result):
        """Performance analyzers should have requested timestamps"""
        perf_analyzer = validated_execution_result.get_path("MultiLevelPerformanceAnalyzer")
        
        if perf_analyzer is None:
            pytest.skip("MultiLevelPerformanceAnalyzer not executed")
        
        # Check that analyzers have timestamp configuration
        if perf_analyzer.status in {"success", "degraded", "warning"}:
            # Verify analyzer executed with timestamp
            assert isinstance(perf_analyzer.data, dict)
            # Add specific timestamp checks based on implementation

    def test_day_level_processor_executed(self, validated_execution_result):
        """DayLevelProcessor should be executed"""
        # Navigate nested path
        processor = validated_execution_result.get_path("MultiLevelPerformanceAnalyzer.DayLevelProcessor")
        
        if processor is None:
            pytest.skip("DayLevelProcessor not found in execution tree")
        
        # Should have completed
        assert processor.status in {"success", "degraded", "warning"}, \
            f"DayLevelProcessor failed: {processor.error}"
        
    def test_month_level_processor_executed(self, validated_execution_result):
        """MonthLevelProcessor should be executed"""
        # Navigate nested path
        processor = validated_execution_result.get_path("MultiLevelPerformanceAnalyzer.MonthLevelProcessor")
        
        if processor is None:
            pytest.skip("MonthLevelProcessor not found in execution tree")
        
        # Should have completed
        assert processor.status in {"success", "degraded", "warning"}, \
            f"MonthLevelProcessor failed: {processor.error}"
        
    def test_year_level_processor_executed(self, validated_execution_result):
        """YearLevelProcessor should be executed"""
        # Navigate nested path
        processor = validated_execution_result.get_path("MultiLevelPerformanceAnalyzer.YearLevelProcessor")

        if processor is None:
            pytest.skip("YearLevelProcessor not found in execution tree")
        
        # Should have completed
        assert processor.status in {"success", "degraded", "warning"}, \
            f"YearLevelProcessor failed: {processor.error}"
        
    def test_machine_layout_tracker_executed(self, validated_execution_result):
        """MachineLayoutTracker should be executed"""
        # Navigate nested path
        tracker = validated_execution_result.get_path("HardwareChangeAnalyzer.MachineLayoutTracker")
        
        if tracker is None:
            pytest.skip("MachineLayoutTracker not found in execution tree")
        
        # Should have completed
        assert tracker.status in {"success", "degraded", "warning"}, \
            f"MachineLayoutTracker failed: {tracker.error}"
    
    def test_mold_machine_pair_tracker_executed(self, validated_execution_result):
        """MoldMachinePairTracker should be executed"""
        tracker = validated_execution_result.get_path("HardwareChangeAnalyzer.MoldMachinePairTracker")
        
        if tracker is None:
            pytest.skip("MoldMachinePairTracker not found in execution tree")
        
        # Should have completed
        assert tracker.status in {"success", "degraded", "warning"}, \
            f"MoldMachinePairTracker failed: {tracker.error}"
    
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
    
    def test_performance_processors_have_timestamps(self, agent_instance):
        """Performance processors should have timestamp configuration"""
        config = agent_instance.config
        
        # Day level
        assert config.day_level_processor.requested_timestamp == '2018-11-06'
        
        # Month level
        assert config.month_level_processor.requested_timestamp == '2019-01'
        assert config.month_level_processor.analysis_date == '2019-01-15'
        
        # Year level
        assert config.year_level_processor.requested_timestamp == '2019'
        assert config.year_level_processor.analysis_date == '2019-12-31'
    
    # ============================================
    # INTEGRATION TESTS
    # ============================================
    
    @pytest.mark.integration
    def test_orchestrator_directory_created(self, agent_instance):
        """Orchestrator directory should be created"""
        from pathlib import Path
        
        config = agent_instance.config
        shared_config = config.shared_source_config

        if config.machine_layout_tracker.save_result or \
           config.mold_machine_pair_tracker.save_result or \
           config.day_level_processor.save_result or \
           config.month_level_processor.save_result or \
           config.year_level_processor.save_result:

            orchestrator_dir = Path(shared_config.analytics_orchestrator_dir)

            assert orchestrator_dir.exists(), \
                f"Analytics orchestrator directory not created: {orchestrator_dir}"

    @pytest.mark.integration
    def test_orchestrator_log_created(self, agent_instance):
        """Orchestrator change log should be created"""
        from pathlib import Path
        
        config = agent_instance.config
        shared_config = config.shared_source_config

        if config.save_orchestrator_log:
            log_path = Path(shared_config.analytics_orchestrator_log_path)
            assert log_path.exists()
    
    @pytest.mark.integration
    def test_analyzer_directories_created(self, validated_execution_result, dependency_provider):
        """Analyzer directories should be created for executed analyzers"""
        from pathlib import Path
        
        shared_config = dependency_provider.get_shared_source_config()
        
        # Check hardware analyzer directory
        if validated_execution_result.get_path("HardwareChangeAnalyzer"):
            hardware_dir = Path(shared_config.hardware_change_analyzer_dir)
            hardware_analyzer = validated_execution_result.get_path("HardwareChangeAnalyzer")
            hardware_save_routing = hardware_analyzer.data['result']['payload'].metadata['save_routing']

            for sub in hardware_save_routing:
                if hardware_save_routing[sub]['enabled'] and hardware_save_routing[sub]['savable']:
                    assert hardware_dir.exists()
        
        # Check performance analyzer directory
        if validated_execution_result.get_path("MultiLevelPerformanceAnalyzer"):
            perf_dir = Path(shared_config.multi_level_performance_analyzer_dir)
            perf_analyzer = validated_execution_result.get_path("MultiLevelPerformanceAnalyzer")
            perf_save_routing = perf_analyzer.data['result']['payload'].metadata['save_routing']

            for sub in perf_save_routing:
                if perf_save_routing[sub]['enabled'] and perf_save_routing[sub]['savable']:
                    assert perf_dir.exists()    
    
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
    # DATA FLOW TESTS
    # ============================================
    
    def test_hardware_analyzer_produces_tracking_data(self, validated_execution_result):
        """HardwareChangeAnalyzer should produce tracking data"""
        hardware_analyzer = validated_execution_result.get_path("HardwareChangeAnalyzer")
        
        if hardware_analyzer is None:
            pytest.skip("HardwareChangeAnalyzer not executed")
        
        # Should have result data
        if hardware_analyzer.status in {"success", "degraded", "warning"}:
            result_data = hardware_analyzer.data.get("result", {})
            assert "payload" in result_data, \
                "HardwareChangeAnalyzer should have payload"
    
    def test_performance_analyzer_produces_metrics(self, validated_execution_result):
        """MultiLevelPerformanceAnalyzer should produce performance metrics"""
        perf_analyzer = validated_execution_result.get_path("MultiLevelPerformanceAnalyzer")
        
        if perf_analyzer is None:
            pytest.skip("MultiLevelPerformanceAnalyzer not executed")
        
        # Should have result data
        if perf_analyzer.status in {"success", "degraded", "warning"}:
            result_data = perf_analyzer.data.get("result", {})
            assert "payload" in result_data, \
                "MultiLevelPerformanceAnalyzer should have payload"


# ============================================
# OPTIONAL: Configuration Variation Tests
# ============================================

class TestAnalyticsOrchestratorConfigurations:
    """
    Test AnalyticsOrchestrator with different configurations
    Separate from BaseAgentTests to avoid interference
    """
    
    def test_with_hardware_only(self, dependency_provider):
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
    
    def test_with_performance_only(self, dependency_provider):
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
    
    def test_with_save_disabled(self, dependency_provider):
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
    
    def test_fails_without_pipeline(self, isolated_dependency_provider):
        """Should fail or degrade without DataPipelineOrchestrator"""
        from agents.analyticsOrchestrator.analytics_orchestrator import (
            ComponentConfig,
            AnalyticsOrchestratorConfig,
            AnalyticsOrchestrator
        )
        
        # Clear all dependencies
        isolated_dependency_provider.clear_all_dependencies()
        
        # Verify clean state
        assert not isolated_dependency_provider.is_triggered("DataPipelineOrchestrator"), \
            "DataPipelineOrchestrator should not be in cache"
        assert not isolated_dependency_provider.is_materialized("DataPipelineOrchestrator"), \
            "DataPipelineOrchestrator files should not exist on disk"
        
        # Create agent with full config
        agent = AnalyticsOrchestrator(
            config=AnalyticsOrchestratorConfig(
                shared_source_config=isolated_dependency_provider.get_shared_source_config(),
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
        
        if result.status == ExecutionStatus.FAILED.value:
            assert result.has_critical_errors(), \
                "Failed status should have critical errors"
    
    def test_recovery_after_dependency_added(self, isolated_dependency_provider):
        """Test that analytics works after DataPipelineOrchestrator is added"""
        from agents.analyticsOrchestrator.analytics_orchestrator import (
            ComponentConfig,
            AnalyticsOrchestratorConfig,
            AnalyticsOrchestrator
        )
        
        # Start with clean state
        isolated_dependency_provider.clear_all_dependencies()
        
        # Create agent
        agent = AnalyticsOrchestrator(
            config=AnalyticsOrchestratorConfig(
                shared_source_config=isolated_dependency_provider.get_shared_source_config(),
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
        
        # First execution - should fail
        result1 = agent.run_analyzing()
        assert result1.status in [ExecutionStatus.FAILED.value, 
                                  ExecutionStatus.DEGRADED.value]
        
        # Add dependency
        isolated_dependency_provider.trigger("DataPipelineOrchestrator")
        
        # Second execution - should succeed
        result2 = agent.run_analyzing()
        assert result2.status == ExecutionStatus.SUCCESS.value, \
            "Should succeed after DataPipelineOrchestrator is added"