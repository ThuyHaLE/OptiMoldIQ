# tests/agents_tests/test_all_agents_structure.py

import pytest
from typing import Callable, List, Optional
from tests.agents_tests.conftest import DependencyProvider, SUCCESSFUL_STATUSES

# ============================================
# AGENT FACTORY with dependency declaration
# ============================================

class AgentFactory:
    """
    Factory for creating agents with dependency metadata
    """
    def __init__(
        self,
        name: str,
        factory_fn: Callable,
        execute_method: str = "execute",
        required_dependencies: Optional[List[str]] = None
    ):
        self.name = name
        self.factory_fn = factory_fn
        self.execute_method = execute_method
        self.required_dependencies = required_dependencies or []

    def create(self, dependency_provider: DependencyProvider):
        """Create agent instance (without executing)"""
        return self.factory_fn(dependency_provider)
    
    def create_and_execute(self, dependency_provider: DependencyProvider):
        """
        Create agent and execute it with proper dependency chain
        
        ⚠️  CRITICAL: This method triggers dependencies which execute and cache results.
        The agent being created here will use those cached results.
        """
        # ✅ Trigger ALL dependencies - they execute and cache results
        for dep in self.required_dependencies:
            dependency_provider.trigger(dep)
        
        # ✅ Create agent - it will read from cached dependency results
        agent = self.create(dependency_provider)
        
        # ✅ Execute this specific agent
        execute_fn = getattr(agent, self.execute_method)
        return execute_fn()

# ============================================
# AGENT CREATION FUNCTIONS
# ============================================
def create_validation_orchestrator(provider):
    from agents.validationOrchestrator.validation_orchestrator import ValidationOrchestrator
    return ValidationOrchestrator(
        shared_source_config=provider.get_shared_source_config(),
        enable_parallel=False,
        max_workers=None
    )

def create_order_tracker(provider):
    from agents.orderProgressTracker.order_progress_tracker import OrderProgressTracker
    return OrderProgressTracker(
        config=provider.get_shared_source_config()
    )

def create_historical_extractor(provider):
    from agents.autoPlanner.featureExtractor.initial.historicalFeaturesExtractor.historical_features_extractor import (
        HistoricalFeaturesExtractor, FeaturesExtractorConfig
    )
    config = provider.get_shared_source_config()
    return HistoricalFeaturesExtractor(
        config=FeaturesExtractorConfig(
            efficiency=0.85,
            loss=0.03,
            shared_source_config=config
        )
    )

def create_initial_planner(provider):
    from agents.autoPlanner.phases.initialPlanner.initial_planner import (
        InitialPlannerConfig, InitialPlanner
    )
    config = provider.get_shared_source_config()
    return InitialPlanner(
        config=InitialPlannerConfig(
            shared_source_config=config
        )
    )

def create_analytics_orchestrator(provider):
    from agents.analyticsOrchestrator.analytics_orchestrator import (
        ComponentConfig,
        AnalyticsOrchestratorConfig,
        AnalyticsOrchestrator
    )
    return AnalyticsOrchestrator(
        config=AnalyticsOrchestratorConfig(
            shared_source_config=provider.get_shared_source_config(),
            
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

def create_dashboard_builder(provider):
    import copy
    from agents.dashboardBuilder.dashboard_builder import (
        ComponentConfig,
        DashboardBuilderConfig,
        DashboardBuilder
    )
    
    # Use deepcopy to avoid modifying shared config
    shared_config = copy.deepcopy(provider.get_shared_source_config())
    
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

# ============================================
# AGENT REGISTRY with metadata
# ============================================

AGENT_REGISTRY = {
    "ValidationOrchestrator": AgentFactory(
        name="ValidationOrchestrator",
        factory_fn=create_validation_orchestrator,
        execute_method="run_validations_and_save_results",
        required_dependencies=[]
    ),
    
    "OrderProgressTracker": AgentFactory(
        name="OrderProgressTracker",
        factory_fn=create_order_tracker,
        execute_method="run_tracking_and_save_results",
        required_dependencies=["ValidationOrchestrator"]
    ),
    
    "HistoricalFeaturesExtractor": AgentFactory(
        name="HistoricalFeaturesExtractor",
        factory_fn=create_historical_extractor,
        execute_method="run_extraction_and_save_results",
        required_dependencies=["OrderProgressTracker"]
    ),
    
    "InitialPlanner": AgentFactory(
        name="InitialPlanner",
        factory_fn=create_initial_planner,
        execute_method="run_planning_and_save_results",
        required_dependencies=["OrderProgressTracker", "HistoricalFeaturesExtractor"]
    ),
    
    "AnalyticsOrchestrator": AgentFactory(
        name="AnalyticsOrchestrator",
        factory_fn=create_analytics_orchestrator,
        execute_method="run_analyzing",
        required_dependencies=[]  # No dependencies - reads from shared DB
    ),
    
    "DashboardBuilder": AgentFactory(
        name="DashboardBuilder",
        factory_fn=create_dashboard_builder,
        execute_method="build_dashboard",
        required_dependencies=[]  # No dependencies - reads from shared DB
    )
}

# ============================================
# PARAMETERIZED FIXTURES
# ============================================

@pytest.fixture(params=AGENT_REGISTRY.values(), ids=lambda f: f.name)
def any_agent_factory(request):
    """Parameterized fixture - runs test for each agent"""
    return request.param

@pytest.fixture
def any_agent(any_agent_factory, dependency_provider):
    """
    Structure-only creation:
    ✅ data setup (via setup_test_data)
    ❌ no dependency trigger
    ❌ no execution
    """
    return any_agent_factory.create(dependency_provider)

@pytest.fixture
def executed_agent(any_agent_factory, dependency_provider):
    """
    Full execution with dependencies:
    ✅ triggers dependencies (they execute and cache)
    ✅ creates agent (reads from cache)
    ✅ executes agent
    """
    return any_agent_factory.create_and_execute(dependency_provider)

# ============================================
# STRUCTURE TESTS - No execution
# ============================================

class TestAllAgentsStructure:
    """Tests that run WITHOUT executing agents"""
    
    def test_agent_can_be_created(self, any_agent):
        """Agent should be creatable without dependencies"""
        assert any_agent is not None

    def test_agent_has_name(self, any_agent_factory):
        """Factory should have name"""
        assert isinstance(any_agent_factory.name, str)
        assert len(any_agent_factory.name) > 0

    def test_dependencies_declared(self, any_agent_factory):
        """Dependencies should be declared as list"""
        assert isinstance(any_agent_factory.required_dependencies, list)

    def test_dependencies_exist_in_registry(self, any_agent_factory):
        """All dependencies should exist in registry"""
        for dep in any_agent_factory.required_dependencies:
            assert dep in AGENT_REGISTRY, \
                f"Unknown dependency '{dep}' for {any_agent_factory.name}"
    
    def test_execute_method_exists(self, any_agent_factory, dependency_provider):
        """Agent should have specified execute method"""
        agent = any_agent_factory.create(dependency_provider)
        assert hasattr(agent, any_agent_factory.execute_method), \
            f"Agent missing execute method: {any_agent_factory.execute_method}"
        assert callable(getattr(agent, any_agent_factory.execute_method)), \
            f"Execute method {any_agent_factory.execute_method} is not callable"

# ============================================
# EXECUTION TESTS - With dependencies
# ============================================

class TestAllAgentsExecution:
    """
    Tests that EXECUTE agents with dependencies
    
    These tests verify that agents can execute successfully when their
    dependencies have been triggered and cached.
    """
    
    def test_agent_executes_successfully(self, executed_agent):
        """All agents should execute without crashing"""
        assert executed_agent is not None, "Execution returned None"
        assert hasattr(executed_agent, 'status'), "Result missing 'status' attribute"
        assert executed_agent.status in SUCCESSFUL_STATUSES, \
            f"Agent execution failed with status '{executed_agent.status}': {executed_agent.error}"
    
    def test_execution_returns_result(self, executed_agent):
        """Execution should return ExecutionResult with required fields"""
        assert hasattr(executed_agent, 'status'), "Missing 'status' attribute"
        assert hasattr(executed_agent, 'name'), "Missing 'name' attribute"
        assert hasattr(executed_agent, 'duration'), "Missing 'duration' attribute"
    
    def test_execution_has_sub_results(self, executed_agent):
        """Agent execution should have sub-results (phases)"""
        if hasattr(executed_agent, 'type') and executed_agent.type == "agent":
            assert hasattr(executed_agent, 'sub_results'), "Missing 'sub_results' attribute"
            assert len(executed_agent.sub_results) > 0, \
                "Agent should have sub-results (phases)"
    
    def test_execution_completes(self, executed_agent):
        """Execution should be complete - all phases successful"""
        if hasattr(executed_agent, 'is_complete'):
            assert executed_agent.is_complete(), \
                f"Execution incomplete for {executed_agent.name} - some phases missing or failed"
    
    def test_no_critical_errors(self, executed_agent):
        """Successful execution should have no critical errors"""
        if hasattr(executed_agent, 'has_critical_errors'):
            assert not executed_agent.has_critical_errors(), \
                f"Critical errors found in {executed_agent.name}: {executed_agent.get_failed_paths()}"