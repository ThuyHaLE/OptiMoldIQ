# tests/agents_tests/test_dashboard_builder.py

from platform import processor
import pytest
import copy
from pathlib import Path
from tests.agents_tests.base_agent_tests import BaseAgentTests
from tests.agents_tests.conftest import DependencyProvider
from configs.shared.agent_report_format import ExecutionStatus

class TestDashboardBuilder(BaseAgentTests):
    """
    Test DashboardBuilder - Builds visualization dashboards
    
    Dependencies:
        - None (reads analytics results from shared_db)
    
    Purpose:
        - Visualize hardware changes
        - Visualize performance metrics at multiple levels
        - Generate dashboard components
    
    Test Strategy:
        1. Structure tests from BaseAgentTests (inherited)
        2. Business logic: visualization generation
        3. Output format validation
        4. Service coordination checks
    """
    
    # ============================================
    # FIXTURES - Required by BaseAgentTests
    # ============================================
    
    @pytest.fixture
    def agent_instance(self, dependency_provider: DependencyProvider):
        """
        Create DashboardBuilder instance
        
        Note: No upstream dependencies - reads analytics from shared DB
        """
        from agents.dashboardBuilder.dashboard_builder import (
            ComponentConfig,
            DashboardBuilderConfig,
            DashboardBuilder
        )
        
        # ✅ Use deepcopy to avoid modifying shared config
        shared_config = copy.deepcopy(dependency_provider.get_shared_source_config())
        
        # Override analytics dir for testing
        shared_config.analytics_orchestrator_dir = 'tests/shared_db/DashboardBuilder'
        
        return DashboardBuilder(
            config=DashboardBuilderConfig(
                shared_source_config=shared_config,
                
                # Workflow 1: Hardware visualization services
                machine_layout_visualization_service=ComponentConfig(
                    enabled=True,
                    save_result=True
                ),
                mold_machine_pair_visualization_service=ComponentConfig(
                    enabled=True,
                    save_result=True
                ),
                
                # Workflow 2: Performance visualization services
                day_level_visualization_service=ComponentConfig(
                    enabled=True,
                    save_result=True,
                    requested_timestamp='2018-11-06'
                ),
                month_level_visualization_service=ComponentConfig(
                    enabled=True,
                    save_result=True,
                    requested_timestamp='2019-01',
                    analysis_date='2019-01-15'
                ),
                year_level_visualization_service=ComponentConfig(
                    enabled=True,
                    save_result=True,
                    requested_timestamp='2019',
                    analysis_date='2019-12-31'
                ),
                
                # Top-level logging
                save_builder_log=True
            )
        )
    
    @pytest.fixture
    def execution_result(self, agent_instance):
        """
        Execute DashboardBuilder
        
        Note: No assertions here - validated_execution_result fixture handles validation
        """
        # ✅ Just return - let validated_execution_result handle validation
        return agent_instance.build_dashboard()
    
    # ============================================
    # BUSINESS LOGIC TESTS
    # ============================================
    
    def test_has_visualization_services(self, validated_execution_result):
        """Should execute visualization services"""
        assert validated_execution_result.is_composite, \
            "DashboardBuilder should be composite (have sub-services)"
        
        assert len(validated_execution_result.sub_results) > 0, \
            "Should execute at least one visualization service"
    
    def test_expected_services_exist(self, validated_execution_result):
        """Expected visualization services should exist"""
        service_names = {r.name for r in validated_execution_result.sub_results}
        
        expected_services = {
            "HardwareChangeVisualizationService",
            "MultiLevelPerformanceVisualizationService"
        }
        
        assert expected_services.issubset(service_names), \
            f"Missing expected services. Found: {service_names}, Expected: {expected_services}"
    
    def test_all_services_completed_or_skipped_with_reason(self, validated_execution_result):
        """All services should complete or have skip reason"""
        for service in validated_execution_result.sub_results:
            if service.status == ExecutionStatus.SKIPPED.value:
                # Should have skip reason
                assert service.skipped_reason is not None, \
                    f"Service '{service.name}' skipped without reason"
        
    def test_dashboard_output_structure(self, validated_execution_result):
        """Dashboard results should have expected structure"""
        if validated_execution_result is None:
            pytest.skip("DashboardBuilder not executed")

        # Should be composite (have trackers)
        if validated_execution_result.status in {"success", "degraded", "warning"}:
            assert validated_execution_result.is_composite, \
                "DashboardBuilder should have sub-trackers"
            
            # Expected services
            service_names = {r.name for r in validated_execution_result.sub_results}
            expected_services = {'HardwareChangeVisualizationService', 'MultiLevelPerformanceVisualizationService'}

            # At least one tracker should exist if service succeeded
            assert len(service_names & expected_services) > 0, \
                f"No expected services found. Found: {service_names}"

            for sub in service_names:
                self_result = validated_execution_result.get_path(sub)
                result_data = self_result.data["result"] 
                assert "payload" in result_data, \
                    "Missing 'payload' in result data"
    
    def test_no_critical_failures(self, validated_execution_result):
        """Dashboard building should not have critical failures"""
        assert not validated_execution_result.has_critical_errors(), \
            f"DashboardBuilder has critical errors: {validated_execution_result.get_failed_paths()}"
    
    # ============================================
    # SERVICE-SPECIFIC TESTS
    # ============================================
    
    def test_hardware_visualization_service_structure(self, validated_execution_result):
        """HardwareChangeVisualizationService should have expected structure"""
        hardware_viz = validated_execution_result.get_path("HardwareChangeVisualizationService")
        
        if hardware_viz is None:
            pytest.skip("HardwareChangeVisualizationService not executed")
        
        # Each service should have data if successful
        if hardware_viz.status in {"success", "degraded", "warning"}:
            assert isinstance(hardware_viz.data, dict), \
                f"Tracker '{hardware_viz.name}' should have data dict"
    
    def test_performance_visualization_service_structure(self, validated_execution_result):
        """MultiLevelPerformanceVisualizationService should have expected structure"""
        perf_viz = validated_execution_result.get_path("MultiLevelPerformanceVisualizationService")
        
        if perf_viz is None:
            pytest.skip("MultiLevelPerformanceVisualizationService not executed")
        
        # Each service should have data if successful
        if perf_viz.status in {"success", "degraded", "warning"}:
            assert isinstance(perf_viz.data, dict), \
                f"Service '{perf_viz.name}' should have data dict"
    
    def test_day_level_visualization_pipeline_executed(self, validated_execution_result):
        """DayLevelVisualizationPipeline should be executed"""
        # Navigate nested path
        pipeline = validated_execution_result.get_path("MultiLevelPerformanceVisualizationService.DayLevelVisualizationPipeline")
        
        if pipeline is None:
            pytest.skip("DayLevelVisualizationPipeline not found in execution tree")
        
        # Should have completed
        assert pipeline.status in {"success", "degraded", "warning"}, \
            f"DayLevelVisualizationPipeline failed: {pipeline.error}"
        
    def test_month_level_visualization_pipeline_executed(self, validated_execution_result):
        """MonthLevelVisualizationPipeline should be executed"""
        # Navigate nested path
        pipeline = validated_execution_result.get_path("MultiLevelPerformanceVisualizationService.MonthLevelVisualizationPipeline")
        
        if pipeline is None:
            pytest.skip("MonthLevelVisualizationPipeline not found in execution tree")
        
        # Should have completed
        assert pipeline.status in {"success", "degraded", "warning"}, \
            f"MonthLevelVisualizationPipeline failed: {pipeline.error}"
        
    def test_year_level_visualization_pipeline_executed(self, validated_execution_result):
        """YearLevelVisualizationPipeline should be executed"""
        # Navigate nested path
        pipeline = validated_execution_result.get_path("MultiLevelPerformanceVisualizationService.YearLevelVisualizationPipeline")

        if pipeline is None:
            pytest.skip("YearLevelVisualizationPipeline not found in execution tree")
        
        # Should have completed
        assert pipeline.status in {"success", "degraded", "warning"}, \
            f"YearLevelVisualizationPipeline failed: {pipeline.error}"
        
    def test_machine_layout_visualization_pipeline_executed(self, validated_execution_result):
        """MachineLayoutVisualizationPipeline should be executed"""
        # Navigate nested path
        pipeline = validated_execution_result.get_path("HardwareChangeVisualizationService.MachineLayoutVisualizationPipeline")
        
        if pipeline is None:
            pytest.skip("MachineLayoutVisualizationPipeline not found in execution tree")
        
        # Should have completed
        assert pipeline.status in {"success", "degraded", "warning"}, \
            f"MachineLayoutVisualizationPipeline failed: {pipeline.error}"
    
    def test_mold_machine_pair_visualization_pipeline_executed(self, validated_execution_result):
        """MoldMachinePairVisualizationPipeline should be executed"""
        pipeline = validated_execution_result.get_path("HardwareChangeVisualizationService.MoldMachinePairVisualizationPipeline")
        
        if pipeline is None:
            pytest.skip("MoldMachinePairVisualizationPipeline not found in execution tree")
        
        # Should have completed
        assert pipeline.status in {"success", "degraded", "warning"}, \
            f"MoldMachinePairVisualizationPipeline failed: {pipeline.error}"
        
    # ============================================
    # CONFIGURATION TESTS
    # ============================================
    
    def test_all_services_enabled(self, agent_instance):
        """All services should be enabled in test configuration"""
        config = agent_instance.config
        
        assert config.machine_layout_visualization_service.enabled is True
        assert config.mold_machine_pair_visualization_service.enabled is True
        assert config.day_level_visualization_service.enabled is True
        assert config.month_level_visualization_service.enabled is True
        assert config.year_level_visualization_service.enabled is True
    
    def test_all_services_save_enabled(self, agent_instance):
        """All services should have save enabled"""
        config = agent_instance.config
        
        assert config.machine_layout_visualization_service.save_result is True
        assert config.mold_machine_pair_visualization_service.save_result is True
        assert config.day_level_visualization_service.save_result is True
        assert config.month_level_visualization_service.save_result is True
        assert config.year_level_visualization_service.save_result is True
    
    def test_builder_log_save_enabled(self, agent_instance):
        """Builder log save should be enabled"""
        assert agent_instance.config.save_builder_log is True
    
    # ============================================
    # INTEGRATION TESTS
    # ============================================
    
    @pytest.mark.integration
    def test_builder_directory_created(self, agent_instance):
        """Builder directory should be created"""
        from pathlib import Path
        
        config = agent_instance.config
        shared_config = config.shared_source_config

        if config.machine_layout_visualization_service.save_result or \
            config.mold_machine_pair_visualization_service.save_result or \
            config.day_level_visualization_service.save_result or \
            config.month_level_visualization_service.save_result or \
            config.year_level_visualization_service.save_result:
            
            builder_dir = Path(shared_config.dashboard_builder_dir)

            assert builder_dir.exists(), \
                f"Analytics builder directory not created: {builder_dir}"

    @pytest.mark.integration
    def test_builder_log_created(self, agent_instance):
        """Builder change log should be created"""
        from pathlib import Path
        
        config = agent_instance.config
        shared_config = config.shared_source_config

        if config.save_builder_log:
            log_path = Path(shared_config.dashboard_builder_log_path)
            assert log_path.exists()
    
    @pytest.mark.integration
    def test_service_directories_created(self, validated_execution_result, dependency_provider):
        """Service directories should be created for executed analyzers"""
        from pathlib import Path
        
        shared_config = dependency_provider.get_shared_source_config()
        
        # Check hardware service directory
        if validated_execution_result.get_path("HardwareChangeVisualizationService"):
            hardware_dir = Path(shared_config.hardware_change_visualization_service_dir)
            hardware_service = validated_execution_result.get_path("HardwareChangeVisualizationService")
            hardware_save_routing = hardware_service.data['result']['payload'].metadata['save_routing']

            for sub in hardware_save_routing:
                if hardware_save_routing[sub]['enabled'] and hardware_save_routing[sub]['savable']:
                    assert hardware_dir.exists()
        
        # Check performance service directory
        if validated_execution_result.get_path("MultiLevelPerformanceVisualizationService"):
            perf_dir = Path(shared_config.multi_level_performance_visualization_service_dir)
            perf_service = validated_execution_result.get_path("MultiLevelPerformanceVisualizationService")
            perf_save_routing = perf_service.data['result']['payload'].metadata['save_routing']

            for sub in perf_save_routing:
                if perf_save_routing[sub]['enabled'] and perf_save_routing[sub]['savable']:
                    assert perf_dir.exists()    
    
    # ============================================
    # PERFORMANCE TESTS
    # ============================================
    
    @pytest.mark.performance
    def test_builder_performance(self, validated_execution_result):
        """Builder should complete in reasonable time"""
        MAX_DURATION = 300.0  # 5 minutes - builder can be complex
        
        assert validated_execution_result.duration < MAX_DURATION, (
            f"Builder took {validated_execution_result.duration:.2f}s "
            f"(max {MAX_DURATION}s)"
        )
    
    @pytest.mark.performance
    def test_individual_service_performance(self, validated_execution_result):
        """Individual services should complete in reasonable time"""
        MAX_SERVICE_DURATION = 60.0  # 1 minute per service
        
        for service in validated_execution_result.sub_results:
            if service.status in {"success", "degraded", "warning"}:
                assert service.duration < MAX_SERVICE_DURATION, (
                    f"Service '{service.name}' took {service.duration:.2f}s "
                    f"(max {MAX_SERVICE_DURATION}s)"
                )

# ============================================
# OPTIONAL: Configuration Variation Tests
# ============================================

class TestDashboardBuilderConfigurations:
    """
    Test DashboardBuilder with different configurations
    Separate from BaseAgentTests to avoid interference
    """
    
    def test_with_selective_services(self, dependency_provider):
        """Test with only some services enabled"""
        from agents.dashboardBuilder.dashboard_builder import (
            ComponentConfig,
            DashboardBuilderConfig,
            DashboardBuilder
        )
        
        shared_config = copy.deepcopy(dependency_provider.get_shared_source_config())
        shared_config.analytics_orchestrator_dir = 'tests/shared_db/DashboardBuilder'
        
        # Enable only hardware services
        agent = DashboardBuilder(
            config=DashboardBuilderConfig(
                shared_source_config=shared_config,
                
                # Hardware services enabled
                machine_layout_visualization_service=ComponentConfig(
                    enabled=True,
                    save_result=True
                ),
                mold_machine_pair_visualization_service=ComponentConfig(
                    enabled=True,
                    save_result=True
                ),
                
                # Performance services disabled
                day_level_visualization_service=ComponentConfig(
                    enabled=False,
                    save_result=False
                ),
                month_level_visualization_service=ComponentConfig(
                    enabled=False,
                    save_result=False
                ),
                year_level_visualization_service=ComponentConfig(
                    enabled=False,
                    save_result=False
                ),
                
                save_builder_log=True
            )
        )
        
        result = agent.build_dashboard()
        
        # Should succeed with partial services
        assert result.status in {"success", "degraded", "warning"}
        
        # Hardware service should exist
        assert result.get_path("HardwareChangeVisualizationService") is not None
        
        # Performance service might be skipped or absent
        perf_viz = result.get_path("MultiLevelPerformanceVisualizationService")
        if perf_viz:
            assert perf_viz.status == ExecutionStatus.SKIPPED.value
    
    def test_with_save_disabled(self, dependency_provider):
        """Test with save disabled"""
        from agents.dashboardBuilder.dashboard_builder import (
            ComponentConfig,
            DashboardBuilderConfig,
            DashboardBuilder
        )
        
        shared_config = copy.deepcopy(dependency_provider.get_shared_source_config())
        shared_config.analytics_orchestrator_dir = 'tests/shared_db/DashboardBuilder'
        
        # All enabled but save disabled
        agent = DashboardBuilder(
            config=DashboardBuilderConfig(
                shared_source_config=shared_config,
                
                machine_layout_visualization_service=ComponentConfig(
                    enabled=True,
                    save_result=False  # ⭐ Save disabled
                ),
                mold_machine_pair_visualization_service=ComponentConfig(
                    enabled=True,
                    save_result=False
                ),
                day_level_visualization_service=ComponentConfig(
                    enabled=True,
                    save_result=False,
                    requested_timestamp='2018-11-06'
                ),
                month_level_visualization_service=ComponentConfig(
                    enabled=True,
                    save_result=False,
                    requested_timestamp='2019-01',
                    analysis_date='2019-01-15'
                ),
                year_level_visualization_service=ComponentConfig(
                    enabled=True,
                    save_result=False,
                    requested_timestamp='2019',
                    analysis_date='2019-12-31'
                ),
                
                save_builder_log=False
            )
        )
        
        result = agent.build_dashboard()
        
        # Should still succeed
        assert result.status in {"success", "degraded", "warning"}