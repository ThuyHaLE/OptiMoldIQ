# tests/agents_tests/test_all_agents_structure.py

import pytest
from typing import Callable, List, Optional
from tests.agents_tests.conftest import DependencyProvider

# ============================================
# AGENT FACTORY with dependency declaration
# ============================================

class AgentFactory:
    def __init__(
        self,
        name: str,
        factory_fn: Callable,
        required_dependencies: Optional[List[str]] = None
    ):
        self.name = name
        self.factory_fn = factory_fn
        self.required_dependencies = required_dependencies or []

    def create(self, dependency_provider: DependencyProvider):
        # Load dependencies generically
        for dep in self.required_dependencies:
            dependency_provider.trigger(dep)

        return self.factory_fn(dependency_provider)
        
# ============================================
# AGENT REGISTRY with dependency info
# ============================================

def create_validation_orchestrator(provider):
    from agents.validationOrchestrator.validation_orchestrator import ValidationOrchestrator
    return ValidationOrchestrator(
        shared_source_config=provider.get_shared_source_config()
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
    from agents.autoPlanner.phases.initialPlanner.initial_planner import InitialPlannerConfig, InitialPlanner

    config = provider.get_shared_source_config()
    return InitialPlanner(
        config = InitialPlannerConfig(
            shared_source_config = config
            )
        )

# Registry with dependency metadata
AGENT_REGISTRY = {

    "ValidationOrchestrator": AgentFactory(
        name="ValidationOrchestrator",
        factory_fn=create_validation_orchestrator,
        required_dependencies=[]  # No deps
    ),

    "OrderProgressTracker": AgentFactory(
        name="OrderProgressTracker",
        factory_fn=create_order_tracker,
        required_dependencies=["ValidationOrchestrator"]
    ),
    
    "HistoricalFeaturesExtractor": AgentFactory(
        name="HistoricalFeaturesExtractor",
        factory_fn=create_historical_extractor,
        required_dependencies=["OrderProgressTracker"]  # Has deps
    ),

    "InitialPlanner": AgentFactory(
        name="InitialPlanner",
        factory_fn=create_initial_planner,
        required_dependencies=["OrderProgressTracker", "HistoricalFeaturesExtractor"]  # Has deps
    )
}

# ============================================
# PARAMETERIZED FIXTURES
# ============================================

@pytest.fixture(params=AGENT_REGISTRY.values())
def any_agent_factory(request):
    return request.param

@pytest.fixture
def any_agent(any_agent_factory, dependency_provider):
    """
    Structure-only creation:
    ❌ no dependency trigger
    ❌ no execution
    """
    return any_agent_factory.factory_fn(dependency_provider)

# ============================================
# TESTS - Run on ALL agents
# ============================================

class TestAllAgentsStructure:

    def test_agent_can_be_created(self, any_agent):
        assert any_agent is not None

    def test_agent_has_name(self, any_agent_factory):
        assert isinstance(any_agent_factory.name, str)

    def test_dependencies_declared(self, any_agent_factory):
        assert isinstance(any_agent_factory.required_dependencies, list)

    def test_dependencies_are_known(self, any_agent_factory):
        known = {"ValidationOrchestrator", "OrderProgressTracker", "HistoricalFeaturesExtractor"}
        for dep in any_agent_factory.required_dependencies:
            assert dep in known, f"Unknown dependency: {dep}"