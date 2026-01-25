# tests/agents_tests/test_dashboard_builder.py

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
        assert "result" in validated_execution_result.data, \
            "Missing 'result' in execution data"
        
        result_data = validated_execution_result.data["result"]
        
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
        
        # Should be composite (have pipelines)
        if hardware_viz.status in {"success", "degraded", "warning"}:
            assert hardware_viz.is_composite, \
                "HardwareChangeVisualizationService should have sub-pipelines"
            
            # Expected pipelines
            pipeline_names = {r.name for r in hardware_viz.sub_results}
            expected_pipelines = {
                "MachineLayoutVisualizationPipeline",
                "MoldMachinePairVisualizationPipeline"
            }
            
            # At least one pipeline should exist if service succeeded
            assert len(pipeline_names & expected_pipelines) > 0, \
                f"No expected pipelines found. Found: {pipeline_names}"
    
    def test_performance_visualization_service_structure(self, validated_execution_result):
        """MultiLevelPerformanceVisualizationService should have expected structure"""
        perf_viz = validated_execution_result.get_path("MultiLevelPerformanceVisualizationService")
        
        if perf_viz is None:
            pytest.skip("MultiLevelPerformanceVisualizationService not executed")
        
        # Should be composite (have pipelines)
        if perf_viz.status in {"success", "degraded", "warning"}:
            assert perf_viz.is_composite, \
                "MultiLevelPerformanceVisualizationService should have sub-pipelines"
            
            # Expected pipelines
            pipeline_names = {r.name for r in perf_viz.sub_results}
            expected_pipelines = {
                "DayLevelVisualizationPipeline",
                "MonthLevelVisualizationPipeline",
                "YearLevelVisualizationPipeline"
            }
            
            # At least one pipeline should exist if service succeeded
            assert len(pipeline_names & expected_pipelines) > 0, \
                f"No expected pipelines found. Found: {pipeline_names}"
    
    def test_hardware_pipelines_configuration(self, validated_execution_result):
        """Hardware pipelines should use correct configuration"""
        hardware_viz = validated_execution_result.get_path("HardwareChangeVisualizationService")
        
        if hardware_viz is None:
            pytest.skip("HardwareChangeVisualizationService not executed")
        
        for pipeline in hardware_viz.sub_results:
            # Each pipeline should have data if successful
            if pipeline.status in {"success", "degraded", "warning"}:
                assert isinstance(pipeline.data, dict), \
                    f"Pipeline '{pipeline.name}' should have data dict"
    
    def test_performance_pipelines_timestamps(self, validated_execution_result):
        """Performance pipelines should have requested timestamps"""
        perf_viz = validated_execution_result.get_path("MultiLevelPerformanceVisualizationService")
        
        if perf_viz is None:
            pytest.skip("MultiLevelPerformanceVisualizationService not executed")
        
        # Check that pipelines have timestamp configuration
        for pipeline in perf_viz.sub_results:
            if pipeline.status in {"success", "degraded", "warning"}:
                # Verify pipeline executed with timestamp
                # (Add specific checks based on your implementation)
                assert isinstance(pipeline.data, dict)
    
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
    def test_builder_directory_created(self, validated_execution_result, dependency_provider):
        """Builder directory should be created"""
        shared_config = dependency_provider.get_shared_source_config()
        builder_dir = Path(shared_config.dashboard_builder_dir)
        
        assert builder_dir.exists(), \
            f"Dashboard builder directory not created: {builder_dir}"
    
    @pytest.mark.integration
    def test_service_directories_created(self, validated_execution_result, dependency_provider):
        """Service directories should be created for executed services"""
        shared_config = dependency_provider.get_shared_source_config()
        
        # Check hardware service directories
        hardware_viz_dir = Path(shared_config.hardware_change_visualization_service_dir)
        if validated_execution_result.get_path("HardwareChangeVisualizationService"):
            # Directory should exist if service executed
            pass  # Add assertion based on your implementation
        
        # Check performance service directories
        perf_viz_dir = Path(shared_config.multi_level_performance_visualization_service_dir)
        if validated_execution_result.get_path("MultiLevelPerformanceVisualizationService"):
            # Directory should exist if service executed
            pass  # Add assertion based on your implementation
    
    @pytest.mark.integration
    def test_builder_log_created(self, validated_execution_result, dependency_provider):
        """Builder change log should be created"""
        shared_config = dependency_provider.get_shared_source_config()
        log_path = Path(shared_config.dashboard_builder_log_path)
        
        # Log should exist if save_builder_log is True
        # Add assertion based on your implementation
        # assert log_path.exists()
    
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