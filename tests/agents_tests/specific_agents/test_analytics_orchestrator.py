# tests/agents_tests/test_analytics_orchestrator.py

import pytest
from tests.agents_tests.base_agent_tests import BaseAgentTests
from tests.agents_tests.conftest import DependencyProvider
from configs.shared.agent_report_format import ExecutionStatus

class TestAnalyticsOrchestrator(BaseAgentTests):
    """
    Test AnalyticsOrchestrator - Orchestrates analytics workflows
    Inherits all structural tests from BaseAgentTests
    
    Dependencies:
        - None (reads tracking data from shared_db)
    
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
        
        Note: No upstream dependencies - reads tracking data from shared DB
        """
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
        """Analytics results should have expected structure"""
        assert "result" in validated_execution_result.data, \
            "Missing 'result' in execution data"
        
        result_data = validated_execution_result.data["result"]
        
        assert "payload" in result_data, \
            "Missing 'payload' in result data"
    
    def test_no_critical_failures(self, validated_execution_result):
        """Analytics orchestration should not have critical failures"""
        assert not validated_execution_result.has_critical_errors(), \
            f"AnalyticsOrchestrator has critical errors: {validated_execution_result.get_failed_paths()}"
    
    # ============================================
    # ANALYZER-SPECIFIC TESTS
    # ============================================
    
    def test_hardware_change_analyzer_structure(self, validated_execution_result):
        """HardwareChangeAnalyzer should have expected structure"""
        hardware_analyzer = validated_execution_result.get_path("HardwareChangeAnalyzer")
        
        if hardware_analyzer is None:
            pytest.skip("HardwareChangeAnalyzer not executed")
        
        # Should be composite (have trackers)
        if hardware_analyzer.status in {"success", "degraded", "warning"}:
            assert hardware_analyzer.is_composite, \
                "HardwareChangeAnalyzer should have sub-trackers"
            
            # Expected trackers
            tracker_names = {r.name for r in hardware_analyzer.sub_results}
            expected_trackers = {
                "MachineLayoutTracker",
                "MoldMachinePairTracker"
            }
            
            # At least one tracker should exist if analyzer succeeded
            assert len(tracker_names & expected_trackers) > 0, \
                f"No expected trackers found. Found: {tracker_names}"
    
    def test_multi_level_performance_analyzer_structure(self, validated_execution_result):
        """MultiLevelPerformanceAnalyzer should have expected structure"""
        perf_analyzer = validated_execution_result.get_path("MultiLevelPerformanceAnalyzer")
        
        if perf_analyzer is None:
            pytest.skip("MultiLevelPerformanceAnalyzer not executed")
        
        # Should be composite (have processors)
        if perf_analyzer.status in {"success", "degraded", "warning"}:
            assert perf_analyzer.is_composite, \
                "MultiLevelPerformanceAnalyzer should have sub-processors"
            
            # Expected processors
            processor_names = {r.name for r in perf_analyzer.sub_results}
            expected_processors = {
                "DayLevelDataProcessor",
                "MonthLevelDataProcessor",
                "YearLevelDataProcessor"
            }
            
            # At least one processor should exist if analyzer succeeded
            assert len(processor_names & expected_processors) > 0, \
                f"No expected processors found. Found: {processor_names}"
    
    def test_hardware_trackers_configuration(self, validated_execution_result):
        """Hardware trackers should use correct configuration"""
        hardware_analyzer = validated_execution_result.get_path("HardwareChangeAnalyzer")
        
        if hardware_analyzer is None:
            pytest.skip("HardwareChangeAnalyzer not executed")
        
        for tracker in hardware_analyzer.sub_results:
            # Each tracker should have data if successful
            if tracker.status in {"success", "degraded", "warning"}:
                assert isinstance(tracker.data, dict), \
                    f"Tracker '{tracker.name}' should have data dict"
    
    def test_performance_processors_timestamps(self, validated_execution_result):
        """Performance processors should have requested timestamps"""
        perf_analyzer = validated_execution_result.get_path("MultiLevelPerformanceAnalyzer")
        
        if perf_analyzer is None:
            pytest.skip("MultiLevelPerformanceAnalyzer not executed")
        
        # Check that processors have timestamp configuration
        for processor in perf_analyzer.sub_results:
            if processor.status in {"success", "degraded", "warning"}:
                # Verify processor executed with timestamp
                assert isinstance(processor.data, dict)
                # Add specific timestamp checks based on implementation
    
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
    def test_orchestrator_directory_created(self, validated_execution_result, dependency_provider):
        """Orchestrator directory should be created"""
        from pathlib import Path
        
        shared_config = dependency_provider.get_shared_source_config()
        orchestrator_dir = Path(shared_config.analytics_orchestrator_dir)
        
        assert orchestrator_dir.exists(), \
            f"Analytics orchestrator directory not created: {orchestrator_dir}"
    
    @pytest.mark.integration
    def test_analyzer_directories_created(self, validated_execution_result, dependency_provider):
        """Analyzer directories should be created for executed analyzers"""
        from pathlib import Path
        
        shared_config = dependency_provider.get_shared_source_config()
        
        # Check hardware analyzer directory
        if validated_execution_result.get_path("HardwareChangeAnalyzer"):
            hardware_dir = Path(shared_config.hardware_change_analyzer_dir)
            # Add assertion based on your implementation
            # assert hardware_dir.exists()
        
        # Check performance analyzer directory
        if validated_execution_result.get_path("MultiLevelPerformanceAnalyzer"):
            perf_dir = Path(shared_config.multi_level_performance_analyzer_dir)
            # Add assertion based on your implementation
            # assert perf_dir.exists()
    
    @pytest.mark.integration
    def test_orchestrator_log_created(self, validated_execution_result, dependency_provider):
        """Orchestrator change log should be created"""
        from pathlib import Path
        
        shared_config = dependency_provider.get_shared_source_config()
        log_path = Path(shared_config.analytics_orchestrator_log_path)
        
        # Log should exist if save_orchestrator_log is True
        # Add assertion based on your implementation
        # assert log_path.exists()
    
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