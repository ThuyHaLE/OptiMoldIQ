# tests/agents_tests/test_dashboard_builder.py

import pytest
import copy
from tests.agents_tests.base_agent_tests import BaseAgentTests
from tests.agents_tests.conftest import DependencyProvider
from configs.shared.agent_report_format import ExecutionStatus, ExecutionResult

class TestDashboardBuilder(BaseAgentTests):
    """
    Test DashboardBuilder - Builds visualization dashboards
    
    Dependencies:
        - DataPipelineOrchestrator
    
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
        Triggers DataPipelineOrchestrator dependency
        """

        # Trigger DataPipelineOrchestrator dependency
        dependency_provider.clear_all_dependencies()
        dependency_provider.trigger_all_dependencies(["DataPipelineOrchestrator"])

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

        # Successful analytics output should be composite (contain sub-trackers)
        if validated_execution_result.status in {"success", "degraded", "warning"}:
            assert validated_execution_result.is_composite, \
                "DashboardBuilder is expected to produce a composite result with sub-trackers"

            # Expected analyzers and their corresponding trackers
            expected_analyzers = {
                "HardwareChangeVisualizationService": [
                    "MachineLayoutVisualizationPipeline",
                    "MachineLayoutVisualizationPipeline",
                ],
                "MultiLevelPerformanceVisualizationService": [
                    "DayLevelVisualizationPipeline",
                    "MonthLevelVisualizationPipeline",
                    "YearLevelVisualizationPipeline",
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
        """Dashboard building should not have critical failures"""
        assert not validated_execution_result.has_critical_errors(), \
            f"DashboardBuilder has critical errors: {validated_execution_result.get_failed_paths()}"
        
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
    def test_builder_and_service_logs_created(
        self,
        validated_execution_result,
        dependency_provider,
    ):
        """Builder and service logs should be created when enabled"""
        from pathlib import Path

        builder_result = validated_execution_result

        if builder_result is None:
            pytest.skip("DashboardBuilder was not executed")

        if builder_result.status not in {"success", "degraded", "warning"}:
            pytest.skip("DashboardBuilder did not complete successfully")

        shared_config = dependency_provider.get_shared_source_config()

        # -------------------------------------------------
        # Builder-level log
        # -------------------------------------------------
        builder_log_path = Path(shared_config.dashboard_builder_log_path)
        assert builder_log_path.exists(), \
            f"Dashboard buider log not created: {builder_log_path}"

        # -------------------------------------------------
        # Service-level logs
        # -------------------------------------------------
        service_log_paths = {
            "HardwareChangeVisualizationService": shared_config.hardware_change_visualization_service_log_path,
            "MultiLevelPerformanceVisualizationService": shared_config.multi_level_performance_visualization_service_log_path,
        }

        for service_name, log_path_str in service_log_paths.items():
            service_result = builder_result.get_path(service_name)

            assert isinstance(service_result, ExecutionResult), \
                f"Service '{service_name}' should return an ExecutionResult"

            if service_result.status in {"success", "degraded", "warning"}:
                log_path = Path(log_path_str)

                assert log_path.exists(), \
                    f"Log not created for service '{service_name}': {log_path}"

    @pytest.mark.integration
    def test_service_directories_created(self, validated_execution_result):
        """All savable service outputs should be written to disk"""
        from pathlib import Path

        builder_result = validated_execution_result

        if builder_result.status not in {"success", "degraded", "warning"}:
            pytest.skip("Builder did not complete successfully")

        # Expected analyzers to validate
        expected_services = [
            "HardwareChangeVisualizationService",
            "MultiLevelPerformanceVisualizationService",
        ]

        for service_name in expected_services:
            service_result = builder_result.get_path(service_name)

            assert isinstance(service_result, ExecutionResult), \
                f"Service '{service_name}' should return an ExecutionResult"

            save_routing = service_result.metadata.get("save_routing", {})

            # All enabled & savable phases should have their output paths created
            for phase_name, phase_cfg in save_routing.items():
                if phase_cfg.get("enabled") and phase_cfg.get("savable"):
                    save_paths = phase_cfg.get("save_paths", {}).values()

                    assert all(Path(path).exists() for path in save_paths), \
                        (
                            f"Missing saved outputs for analyzer '{service_name}', "
                            f"phase '{phase_name}'"
                        )
    
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
    
    def test_with_selective_services(self, dependency_provider: DependencyProvider):
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
    
    def test_with_save_disabled(self, dependency_provider: DependencyProvider):
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

# ============================================
# DEPENDENCY INTERACTION TESTS
# ============================================

class TestDashboardBuilderDependencies:
    """Test DashboardBuilder's interaction with DataPipelineOrchestrator"""
    
    def test_fails_without_pipeline(self, dependency_provider: DependencyProvider):
        """Should fail or degrade without DataPipelineOrchestrator"""
        from agents.dashboardBuilder.dashboard_builder import (
            ComponentConfig,
            DashboardBuilderConfig,
            DashboardBuilder
        )
        
        # Clear all dependencies
        dependency_provider.clear_all_dependencies()

        # Create agent with full config
        agent = DashboardBuilder(
            config=DashboardBuilderConfig(
                shared_source_config=dependency_provider.get_shared_source_config(),
                
                # Workflow 1: Hardware visualization services
                machine_layout_visualization_service=ComponentConfig(
                    enabled=True,
                    save_result=False
                ),
                mold_machine_pair_visualization_service=ComponentConfig(
                    enabled=False,
                    save_result=False
                ),
                
                # Workflow 2: Performance visualization services
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
                
                # Top-level logging
                save_builder_log=False
            )
        )
        
        # Execute
        result = agent.build_dashboard()
        
        # Should fail or degrade
        assert result.status in [ExecutionStatus.FAILED.value, 
                                 ExecutionStatus.DEGRADED.value], \
            f"Should fail or degrade without DataPipelineOrchestrator, got: {result.status}"
        
        if result.status == ExecutionStatus.FAILED.value:
            assert result.has_critical_errors(), \
                "Failed status should have critical errors"
    
    def test_recovery_after_dependency_added(self, dependency_provider: DependencyProvider):
        """Test that builders works after DataPipelineOrchestrator is added"""
        from agents.dashboardBuilder.dashboard_builder import (
            ComponentConfig,
            DashboardBuilderConfig,
            DashboardBuilder
        )
        
        # Start with clean state
        dependency_provider.clear_all_dependencies()
        
        # Create agent
        agent = DashboardBuilder(
            config=DashboardBuilderConfig(
                shared_source_config=dependency_provider.get_shared_source_config(),
                
                # Workflow 1: Hardware visualization services
                machine_layout_visualization_service=ComponentConfig(
                    enabled=True,
                    save_result=False
                ),
                mold_machine_pair_visualization_service=ComponentConfig(
                    enabled=False,
                    save_result=False
                ),
                
                # Workflow 2: Performance visualization services
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
                
                # Top-level logging
                save_builder_log=False
            )
        )
        
        # First execution - should fail
        result1 = agent.build_dashboard()
        assert result1.status in [ExecutionStatus.FAILED.value, 
                                  ExecutionStatus.DEGRADED.value]
        
        # Add dependency
        dependency_provider.clear_all_dependencies()
        dependency_provider.trigger_all_dependencies(["DataPipelineOrchestrator"])
        
        # Second execution - should succeed
        result2 = agent.build_dashboard()
        assert result2.status == ExecutionStatus.SUCCESS.value, \
            "Should succeed after DataPipelineOrchestrator is added"
