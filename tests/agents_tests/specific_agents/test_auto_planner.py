# tests/agents_tests/specific_agents/test_auto_planner.py

import pytest
from tests.agents_tests.base_agent_tests import BaseAgentTests
from tests.agents_tests.conftest import DependencyProvider
from configs.shared.agent_report_format import ExecutionStatus, ExecutionResult

class TestAutoPlanner(BaseAgentTests):
    """
    Test AutoPlanner - Auto planner workflows
    Inherits all structural tests from BaseAgentTests
    
    Dependencies:
        - DataPipelineOrchestrator
        - ValidationOrchestrator
        - OrderProgressTracker
    
    Purpose:
        - HistoricalFeaturesExtractor - manages a three-phase historical features extraction
        - Initial Planner - a two-phase planning component within the hybrid optimization system
    
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
        Create AutoPlanner instance
        Triggers DataPipelineOrchestrator dependency
        """
        # Trigger DataPipelineOrchestrator dependency
        dependency_provider.clear_all_dependencies()
        dependency_provider.trigger_all_dependencies(["DataPipelineOrchestrator",
                                                      "ValidationOrchestrator",
                                                      "OrderProgressTracker"])

        from agents.autoPlanner.auto_planner import InitialPlannerParams, FeatureExtractorParams, AutoPlanner, AutoPlannerConfig

        return AutoPlanner(
            config = AutoPlannerConfig(
            shared_source_config = dependency_provider.get_shared_source_config(),
            efficiency = 0.85,
            loss = 0.03,
            feature_extractor = FeatureExtractorParams(
                enabled = True,
                save_result = True
            ),
            initial_planner = InitialPlannerParams(
                enabled = True,
                save_result = True
            ),
            save_planner_log = True
            )
        )
    
    @pytest.fixture
    def execution_result(self, agent_instance):
        """
        Execute AutoPlanner
        
        Note: No assertions here - validated_execution_result fixture handles validation
        """
        # ✅ Just return - let validated_execution_result handle validation
        return agent_instance.run_scheduled_components()
    
    # ============================================
    # BUSINESS LOGIC TESTS
    # ============================================
        
    def test_has_scheduled_components_workflows(self, validated_execution_result):
        """Should execute scheduled components workflows"""
        assert validated_execution_result.is_composite, \
            "AutoPlanner should be composite (have sub-workflows)"
        
        assert len(validated_execution_result.sub_results) > 0, \
            "Should execute at least one scheduled components workflow"
    
    def test_expected_scheduled_components_exist(self, validated_execution_result):
        """Expected scheduled components should exist"""
        scheduled_components_names = {r.name for r in validated_execution_result.sub_results}
        
        expected_scheduled_components = {
            "HistoricalFeaturesExtractor",
            "InitialPlanner"
        }
        
        assert expected_scheduled_components.issubset(scheduled_components_names), \
            f"Missing expected scheduled components. Found: {scheduled_components_names}, Expected: {expected_scheduled_components}"
    
    def test_all_components_completed_or_skipped_with_reason(self, validated_execution_result):
        """All components should complete or have skip reason"""
        for component in validated_execution_result.sub_results:
            if component.status == ExecutionStatus.SKIPPED.value:
                # Should have skip reason
                assert component.skipped_reason is not None, \
                    f"Component '{component.name}' skipped without reason"

    def test_scheduled_components_output_structure(self, validated_execution_result):
        """Scheduled components results should follow the expected output structure"""
        if validated_execution_result is None:
            pytest.skip("AutoPlanner was not executed")

        # Successful scheduled components output should be composite (contain sub scheduled components)
        if validated_execution_result.status in {"success", "degraded", "warning"}:
            assert validated_execution_result.is_composite, \
                "AutoPlanner is expected to produce a composite result with sub scheduled components"

            # Expected scheduled components and their corresponding sub scheduled components
            expected_scheduled_components = {
                "HistoricalFeaturesExtractor": [
                    "MoldStabilityIndexCalculator",
                    "MoldMachineFeatureWeightCalculator",
                ],
                "InitialPlanner": [
                    "ProducingOrderPlanner",
                    "PendingOrderPlanner"
                ],
            }

            for component_name, sub_components in expected_scheduled_components.items():
                component_result = validated_execution_result.get_path(component_name)

                assert isinstance(component_result, ExecutionResult), \
                    f"Analyzer '{component_name}' should return an ExecutionResult"

                if component_result.status in {"success", "degraded", "warning"}:
                    for sub_component_name in sub_components:
                        sub_component_result = component_result.get_path(sub_component_name)

                        assert isinstance(sub_component_result, ExecutionResult), \
                            f"Sub-component '{sub_component_name}' should return an ExecutionResult"

                        # Successful sub-components are expected to expose structured result data
                        if validated_execution_result.status in {"success", "degraded", "warning"}:
                            assert isinstance(sub_component_result.data, dict), \
                                f"Sub-component '{sub_component_result.name}' should expose data as a dict"

                            assert "result" in sub_component_result.data, \
                                "Sub-component data is missing the 'result' field"

                            sub_component_data = sub_component_result.data["result"]

                            assert "payload" in sub_component_data, \
                                "Sub-component result is missing the 'payload' field"
    
    def test_no_critical_failures(self, validated_execution_result):
        """Auto planner should not have critical failures"""
        assert not validated_execution_result.has_critical_errors(), \
            f"AutoPlanner has critical errors: {validated_execution_result.get_failed_paths()}"
    
    # ============================================
    # CONFIGURATION TESTS
    # ============================================
    
    def test_efficiency_and_loss_config_applied(self, agent_instance):
        """Should use configured efficiency and loss parameters"""
        assert agent_instance.config.efficiency == 0.85, \
            "Efficiency parameter should be 0.85"
        assert agent_instance.config.loss == 0.03, \
            "Loss parameter should be 0.03"
        
    def test_all_components_enabled(self, agent_instance):
        """All components should be enabled in test configuration"""
        config = agent_instance.config
        
        assert config.feature_extractor.enabled is True
        assert config.initial_planner.enabled is True
    
    def test_all_components_save_enabled(self, agent_instance):
        """All components should have save enabled"""
        config = agent_instance.config
        
        assert config.feature_extractor.save_result is True
        assert config.initial_planner.save_result is True
    
    def test_planner_log_save_enabled(self, agent_instance):
        """Planner log save should be enabled"""
        assert agent_instance.config.save_planner_log is True
    
    # ============================================
    # INTEGRATION TESTS
    # ============================================
    
    @pytest.mark.integration
    def test_planner_and_component_logs_created(
        self,
        validated_execution_result,
        dependency_provider,
    ):
        """Planner and component logs should be created when enabled"""
        from pathlib import Path

        planner_result = validated_execution_result

        if planner_result is None:
            pytest.skip("AutoPlanner was not executed")

        if planner_result.status not in {"success", "degraded", "warning"}:
            pytest.skip("AutoPlanner did not complete successfully")

        shared_config = dependency_provider.get_shared_source_config()

        # -------------------------------------------------
        # Planner-level log
        # -------------------------------------------------
        auto_planner_change_log_path = Path(shared_config.auto_planner_change_log_path)
        assert auto_planner_change_log_path.exists(), \
            f"Auto planner log not created: {auto_planner_change_log_path}"

        # -------------------------------------------------
        # Scheduled components-level logs
        # -------------------------------------------------
        scheduled_components_log_paths = {
            "HistoricalFeaturesExtractor": shared_config.features_extractor_change_log_path,
            "InitialPlanner": shared_config.initial_planner_change_log_path,
        }

        for scheduled_component_name, log_path_str in scheduled_components_log_paths.items():
            scheduled_component_result = planner_result.get_path(scheduled_component_name)

            assert isinstance(scheduled_component_result, ExecutionResult), \
                f"Scheduled component '{scheduled_component_name}' should return an ExecutionResult"

            if scheduled_component_result.status in {"success", "degraded", "warning"}:
                log_path = Path(log_path_str)

                assert log_path.exists(), \
                    f"Log not created for scheduled component '{scheduled_component_name}': {log_path}"

    @pytest.mark.integration
    def test_component_directories_created(self, validated_execution_result):
        """All savable component outputs should be written to disk"""
        from pathlib import Path

        planner_result = validated_execution_result

        if planner_result.status not in {"success", "degraded", "warning"}:
            pytest.skip("Auto planner did not complete successfully")

        # Expected scheduled components to validate
        expected_scheduled_components = [
            "HistoricalFeaturesExtractor",
            "InitialPlanner",
        ]

        for scheduled_component_name in expected_scheduled_components:
            scheduled_component_result = planner_result.get_path(scheduled_component_name)

            assert isinstance(scheduled_component_result, ExecutionResult), \
                f"Scheduled component '{scheduled_component_name}' should return an ExecutionResult"

            save_routing = scheduled_component_result.metadata.get("save_routing", {})

            # All enabled & savable phases should have their output paths created
            for phase_name, phase_cfg in save_routing.items():
                if phase_cfg.get("enabled") and phase_cfg.get("savable"):
                    save_paths = phase_cfg.get("save_paths", {}).values()

                    assert all(Path(path).exists() for path in save_paths), \
                        (
                            f"Missing saved outputs for analyzer '{scheduled_component_name}', "
                            f"phase '{phase_name}'"
                        )
    
    # ============================================
    # PERFORMANCE TESTS
    # ============================================
    
    @pytest.mark.performance
    def test_planner_performance(self, validated_execution_result):
        """Planner should complete in reasonable time"""
        MAX_DURATION = 180.0  # 3 minutes - planner coordinates multiple workflows
        
        assert validated_execution_result.duration < MAX_DURATION, (
            f"Planner took {validated_execution_result.duration:.2f}s "
            f"(max {MAX_DURATION}s)"
        )
    
    @pytest.mark.performance
    def test_individual_component_performance(self, validated_execution_result):
        """Individual components should complete in reasonable time"""
        MAX_COMPONENT_DURATION = 90.0  # 1.5 minutes per component
        
        for component in validated_execution_result.sub_results:
            if component.status in {"success", "degraded", "warning"}:
                assert component.duration < MAX_COMPONENT_DURATION, (
                    f"Component '{component.name}' took {component.duration:.2f}s "
                    f"(max {MAX_COMPONENT_DURATION}s)"
                )

# ============================================
# OPTIONAL: Configuration Variation Tests
# ============================================

class TestAutoPlannerConfigurations:
    """
    Test AutoPlanner with different configurations
    Separate from BaseAgentTests to avoid interference
    """
    
    def test_with_feature_extractor_only(self, dependency_provider: DependencyProvider):
        """Test with only feature extractor enabled"""

        from agents.autoPlanner.auto_planner import FeatureExtractorParams, AutoPlanner, AutoPlannerConfig

        planner = AutoPlanner(
            config = AutoPlannerConfig(
            shared_source_config = dependency_provider.get_shared_source_config(),
            efficiency = 0.85,
            loss = 0.03,
            feature_extractor = FeatureExtractorParams(
                enabled = True,
                save_result = True
            ),
            save_planner_log = True
            )
        )

        result = planner.run_scheduled_components()
        
        # Should succeed with partial components
        assert result.status in {"success", "degraded", "warning"}
        
        # Feature extractor should exist
        assert result.get_path("HistoricalFeaturesExtractor") is not None
        
        # Initial planner might be skipped or absent
        perf_component = result.get_path("InitialPlanner")
        if perf_component:
            assert perf_component.status == ExecutionStatus.SKIPPED.value
    
    def test_with_initial_planner_only(self, dependency_provider: DependencyProvider):
        """Test with only initial planner enabled"""

        from agents.autoPlanner.auto_planner import InitialPlannerParams, AutoPlanner, AutoPlannerConfig

        planner = AutoPlanner(
            config = AutoPlannerConfig(
            shared_source_config = dependency_provider.get_shared_source_config(),
            efficiency = 0.85,
            loss = 0.03,
            initial_planner = InitialPlannerParams(
                enabled = True,
                save_result = True
            ),
            save_planner_log = True
            )
        )

        result = planner.run_scheduled_components()
        
        # Should succeed
        assert result.status in {"success", "degraded", "warning"}
        
        # Initial planner should exist
        assert result.get_path("InitialPlanner") is not None

        # Feature extractor might be skipped or absent
        perf_component = result.get_path("HistoricalFeaturesExtractor")
        if perf_component:
            assert perf_component.status == ExecutionStatus.SKIPPED.value
    
    def test_with_save_disabled(self, dependency_provider: DependencyProvider):
        """Test with save disabled for all components"""

        from agents.autoPlanner.auto_planner import InitialPlannerParams, FeatureExtractorParams, AutoPlanner, AutoPlannerConfig

        planner = AutoPlanner(
            config = AutoPlannerConfig(
            shared_source_config = dependency_provider.get_shared_source_config(),
            efficiency = 0.85,
            loss = 0.03,
            feature_extractor = FeatureExtractorParams(
                enabled = True,
                save_result = False
            ),
            initial_planner = InitialPlannerParams(
                enabled = True,
                save_result = False
            ),
            save_planner_log = False
            )
        )
        
        result = planner.run_scheduled_components()
        
        # Should still succeed
        assert result.status in {"success", "degraded", "warning"}

# ============================================
# DEPENDENCY INTERACTION TESTS
# ============================================

class TestAutoPlannerDependencyScenarios:
    """Test AutoPlanner behavior with different dependency states"""
    
    def test_with_all_dependencies(self, dependency_provider: DependencyProvider):
        """AutoPlanner should use historical features when available"""
        from agents.autoPlanner.auto_planner import (
            InitialPlannerParams, FeatureExtractorParams, 
            AutoPlanner, AutoPlannerConfig)
        
        # Trigger all dependencies and verify they succeeded
        dependency_provider.clear_all_dependencies()
        dependency_provider.trigger_all_dependencies(["DataPipelineOrchestrator",
                                                      "ValidationOrchestrator",
                                                      "OrderProgressTracker"])
        
        # Create agent
        planner = AutoPlanner(
            config = AutoPlannerConfig(
            shared_source_config = dependency_provider.get_shared_source_config(),
            efficiency = 0.85,
            loss = 0.03,
            feature_extractor = FeatureExtractorParams(
                enabled = True,
                save_result = True
            ),
            initial_planner = InitialPlannerParams(
                enabled = True,
                save_result = True
            ),
            save_planner_log = True
            )
        )
        
        # Execute
        result = planner.run_scheduled_components()
        
        # Should succeed with full features
        assert result.status == ExecutionStatus.SUCCESS.value, \
            f"Should succeed with all dependencies, got: {result.status}\n" \
            f"Error: {result.error}\n" \
            f"Failed paths: {result.get_failed_paths()}"
        
        # Should NOT use fallback (if your implementation tracks this)
        # Note: Only check if your implementation actually sets this field
        # assert result.data.get("fallback_used") is not True, \
        #     "Should not use fallback when features available"
    
    def test_without_historical_features(self, dependency_provider: DependencyProvider):
        """AutoPlanner should degrade gracefully without HistoricalFeaturesExtractor"""
        from agents.autoPlanner.auto_planner import (
            InitialPlannerParams, FeatureExtractorParams, 
            AutoPlanner, AutoPlannerConfig)
        
        # Trigger only OrderProgressTracker and verify it succeeded
        dependency_provider.clear_all_dependencies()
        dependency_provider.trigger_all_dependencies(["DataPipelineOrchestrator",
                                                      "ValidationOrchestrator",
                                                      "OrderProgressTracker"])
        
        # Create agent
        planner = AutoPlanner(
            config = AutoPlannerConfig(
            shared_source_config = dependency_provider.get_shared_source_config(),
            efficiency = 0.85,
            loss = 0.03,
            feature_extractor = FeatureExtractorParams(
                enabled = False,
                save_result = False
            ),
            initial_planner = InitialPlannerParams(
                enabled = True,
                save_result = True
            ),
            save_planner_log = True
            )
        )
        
        # Execute
        result = planner.run_scheduled_components()
        
        # Should degrade gracefully (use fallback)
        assert result.status in [ExecutionStatus.SUCCESS.value, 
                                 ExecutionStatus.DEGRADED.value], \
            f"Should succeed or degrade without features, got: {result.status}\n" \
            f"Error: {result.error}\n" \
            f"Failed paths: {result.get_failed_paths()}"
    
    def test_missing_required_dependency_fails(self, dependency_provider: DependencyProvider):
        """InitialPlanner should fail if OrderProgressTracker is missing"""
        from agents.autoPlanner.auto_planner import (
            InitialPlannerParams, FeatureExtractorParams, 
            AutoPlanner, AutoPlannerConfig)
        
        # Clear all dependencies
        dependency_provider.clear_all_dependencies()
        
        # Create agent
        planner = AutoPlanner(
            config = AutoPlannerConfig(
            shared_source_config = dependency_provider.get_shared_source_config(),
            efficiency = 0.85,
            loss = 0.03,
            feature_extractor = FeatureExtractorParams(
                enabled = True,
                save_result = True
            ),
            initial_planner = InitialPlannerParams(
                enabled = True,
                save_result = True
            ),
            save_planner_log = True
            )
        )
        
        # Execute
        result = planner.run_scheduled_components()
        
        # Should fail without required dependency
        assert result.status == ExecutionStatus.FAILED.value, \
            f"Should fail without required dependency, got: {result.status}"
        
        # Check for error information
        assert result.error is not None or len(result.get_failed_paths()) > 0, \
            "Failed status should have error information or failed paths"
    
    def test_recovery_after_dependency_added(self, dependency_provider: DependencyProvider):
        """Test that planner works after dependencies are added"""
        from agents.autoPlanner.auto_planner import (
            InitialPlannerParams, FeatureExtractorParams, 
            AutoPlanner, AutoPlannerConfig)
        
        # Start with clean state
        dependency_provider.clear_all_dependencies()
        
        # Create config (reusable)
        config = AutoPlannerConfig(
            shared_source_config = dependency_provider.get_shared_source_config(),
            efficiency = 0.85,
            loss = 0.03,
            feature_extractor = FeatureExtractorParams(
                enabled = True,
                save_result = True
            ),
            initial_planner = InitialPlannerParams(
                enabled = True,
                save_result = True
            ),
            save_planner_log = True
            )
        
        # First execution - should fail
        agent1 = AutoPlanner(config=config)
        result1 = agent1.run_scheduled_components()
        assert result1.status == ExecutionStatus.FAILED.value, \
            f"Should fail without DataPipelineOrchestrator first, got: {result1.status}"
        
        dependency_provider.clear_all_dependencies()
        dependency_provider.trigger_all_dependencies(["DataPipelineOrchestrator"])
        
        # Second execution with NEW instance - should fail
        agent2 = AutoPlanner(config=config)
        result2 = agent2.run_scheduled_components()
        assert result2.status == ExecutionStatus.FAILED.value, \
            f"Should fail without OrderProgressTracker, got: {result2.status}"
        
        dependency_provider.clear_all_dependencies()
        dependency_provider.trigger_all_dependencies(["DataPipelineOrchestrator",
                                                      "ValidationOrchestrator",
                                                      "OrderProgressTracker"])
        
        # Third execution with NEW instance - should fully succeed
        agent3 = AutoPlanner(config=config)
        result3 = agent3.run_scheduled_components()
        assert result3.status == ExecutionStatus.SUCCESS.value, \
            f"Should fully succeed with all dependencies, got: {result3.status}\n" \
            f"Error: {result3.error}\n" \
            f"Failed paths: {result3.get_failed_paths()}"