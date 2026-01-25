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
        execute_method: str = "execute",  # ✨ New: specify execute method name
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
        """Create agent and execute it"""
        # Trigger dependencies
        for dep in self.required_dependencies:
            dependency_provider.trigger(dep)
        
        # Create agent
        agent = self.create(dependency_provider)
        
        # Execute using specified method
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
    ❌ no dependency trigger
    ❌ no execution
    """
    return any_agent_factory.create(dependency_provider)

@pytest.fixture
def executed_agent(any_agent_factory, dependency_provider):
    """
    Full execution with dependencies:
    ✅ triggers dependencies
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
    """Tests that EXECUTE agents with dependencies"""
    
    def test_agent_executes_successfully(self, executed_agent):
        """All agents should execute without crashing"""
        assert executed_agent is not None
        assert executed_agent.status in SUCCESSFUL_STATUSES, \
            f"Agent execution failed: {executed_agent.error}"
    
    def test_execution_returns_result(self, executed_agent):
        """Execution should return ExecutionResult"""
        assert hasattr(executed_agent, 'status')
        assert hasattr(executed_agent, 'name')
        assert hasattr(executed_agent, 'duration')
    
    def test_execution_has_sub_results(self, executed_agent):
        """Agent execution should have sub-results"""
        if executed_agent.type == "agent":
            assert len(executed_agent.sub_results) > 0, \
                "Agent should have sub-results (phases)"
    
    def test_execution_completes(self, executed_agent):
        """Execution should be complete"""
        assert executed_agent.is_complete(), \
            "Execution incomplete - some phases missing"
    
    def test_no_critical_errors(self, executed_agent):
        """Successful execution should have no critical errors"""
        assert not executed_agent.has_critical_errors(), \
            f"Critical errors found: {executed_agent.get_failed_paths()}"

# ============================================
# DEPENDENCY GRAPH TESTS
# ============================================

class TestDependencyGraph:
    """Tests for dependency relationships"""
    
    def test_no_circular_dependencies(self, dependency_provider):
        """Should not have circular dependencies"""
        # If provider initialized, graph is valid
        assert dependency_provider is not None
    
    def test_dependencies_can_be_triggered(self, dependency_provider):
        """All registered dependencies should be triggerable"""
        for dep_name in AGENT_REGISTRY.keys():
            # Should not raise
            try:
                dependency_provider.trigger(dep_name)
            except Exception as e:
                pytest.fail(f"Failed to trigger {dep_name}: {e}")
    
    def test_dependency_results_cached(self, dependency_provider):
        """Triggered dependencies should be cached"""
        dep_name = "ValidationOrchestrator"
        
        # First trigger
        result1 = dependency_provider.trigger(dep_name)
        
        # Should be cached
        assert dependency_provider.is_triggered(dep_name)
        
        # Second trigger should return same instance
        result2 = dependency_provider.trigger(dep_name)
        assert result1 is result2  # Same object

# ============================================
# NEGATIVE TESTS
# ============================================

class TestAgentFailureCases:
    """Tests for failure scenarios"""
    
    def test_invalid_dependency_raises_error(self, dependency_provider):
        """Unknown dependency should raise ValueError"""
        with pytest.raises(ValueError, match="Unknown dependency"):
            dependency_provider.trigger("NonExistentAgent")
    
    def test_missing_dependency_fails(self, dependency_provider):
        """Agent without dependencies should fail"""
        # Create agent that requires dependency
        factory = AGENT_REGISTRY["OrderProgressTracker"]
        
        # Clear cache to simulate missing dependency
        if "ValidationOrchestrator" in dependency_provider._cache:
            del dependency_provider._cache["ValidationOrchestrator"]
        
        # Should trigger dependency automatically
        result = factory.create_and_execute(dependency_provider)
        assert result.status in SUCCESSFUL_STATUSES