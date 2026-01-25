# Universal Agent Test Template

> **Version:** 1.0  
> **Last Updated:** January 2026  
> **Purpose:** Standard template for testing any agent in OptiMoldIQ

---

## 📋 Quick Start Checklist

Before writing tests, ask yourself:

- [ ] What dependencies does this agent need?
- [ ] What's the main execute method name?
- [ ] Does it have custom configuration parameters?
- [ ] Is it critical/high-risk? (determines edge case testing)
- [ ] What's the expected output structure?

---

## 🎯 Test Philosophy

### **Three-Tier Testing Strategy**

| Tier | What | When | Effort |
|------|------|------|--------|
| **Tier 1: Core** | BaseAgentTests + Happy path | Always | Low (80% coverage) |
| **Tier 2: Integration** | Dependency tests + Config variants | Production-ready | Medium (95% coverage) |
| **Tier 3: Edge Cases** | Error handling + Edge cases | Critical agents only | High (99% coverage) |

**Default:** Start with Tier 1, add Tier 2 when stabilizing, Tier 3 only if critical.

---

## 📁 File Structure

```
tests/agents_tests/specific_agents/test_your_agent.py
```

---

## 🔧 Template Code

### **Tier 1: Core Tests (ALWAYS)**

```python
# tests/agents_tests/specific_agents/test_your_agent.py

import pytest
from tests.agents_tests.base_agent_tests import BaseAgentTests
from tests.agents_tests.conftest import DependencyProvider

class TestYourAgent(BaseAgentTests):
    """
    Test YourAgent - [Brief description of what agent does]
    Inherits all structural tests from BaseAgentTests
    
    Dependencies:
        - [List dependencies, or "None"]
    
    Purpose:
        - [What does this agent do?]
        - [Key responsibilities]
    
    Test Strategy:
        1. Structure tests from BaseAgentTests (inherited - FREE)
        2. Business logic: [what to test]
        3. Output validation: [expected output]
    """
    
    # ============================================
    # FIXTURES - Required by BaseAgentTests
    # ============================================
    
    @pytest.fixture
    def agent_instance(self, dependency_provider: DependencyProvider):
        """
        Create YourAgent instance
        
        [Add notes about dependencies, special setup, etc.]
        """
        from agents.yourPackage.your_agent import YourAgent, YourConfig
        
        # ✅ Trigger dependencies if needed
        # dependency_provider.trigger("RequiredAgent1")
        # dependency_provider.trigger("RequiredAgent2")
        
        return YourAgent(
            config=YourConfig(
                # Your config parameters here
                shared_source_config=dependency_provider.get_shared_source_config()
            )
        )
    
    @pytest.fixture
    def execution_result(self, agent_instance):
        """
        Execute YourAgent
        
        ⚠️ IMPORTANT: No assertions here!
        Let validated_execution_result fixture handle validation
        """
        # ✅ Just return the result - no assertions!
        return agent_instance.your_execute_method()
    
    # ============================================
    # BUSINESS LOGIC TESTS - Happy Path
    # ============================================
    
    def test_has_expected_structure(self, validated_execution_result):
        """Should have expected structure"""
        # If composite agent (has sub-phases)
        assert validated_execution_result.is_composite, \
            "YourAgent should be composite (have sub-phases)"
        
        assert len(validated_execution_result.sub_results) > 0, \
            "Should have at least one sub-phase"
        
        # Check for expected phase names
        phase_names = {r.name for r in validated_execution_result.sub_results}
        expected_phases = {
            "ExpectedPhase1",
            "ExpectedPhase2"
        }
        
        assert expected_phases.issubset(phase_names), \
            f"Missing expected phases. Found: {phase_names}"
    
    def test_produces_expected_output(self, validated_execution_result):
        """Should produce expected output format"""
        # Check data structure
        assert "result" in validated_execution_result.data, \
            "Missing 'result' in execution data"
        
        result_data = validated_execution_result.data["result"]
        
        assert "payload" in result_data, \
            "Missing 'payload' in result data"
        
        # Add specific output checks based on your agent
    
    def test_no_critical_failures(self, validated_execution_result):
        """Should not have critical failures"""
        assert not validated_execution_result.has_critical_errors(), \
            f"Agent has critical errors: {validated_execution_result.get_failed_paths()}"
    
    # ============================================
    # CONFIGURATION TESTS
    # ============================================
    
    def test_configuration_applied(self, agent_instance):
        """Configuration should be applied correctly"""
        config = agent_instance.config
        
        # Add checks for your config parameters
        # Example:
        # assert config.some_parameter == expected_value
        pass
```

---

### **Tier 2: Integration Tests (Production-ready)**

Add these when preparing for production:

```python
class TestYourAgent(BaseAgentTests):
    # ... Tier 1 tests above ...
    
    # ============================================
    # DEPENDENCY INTEGRATION TESTS
    # ============================================
    
    def test_uses_dependency_data(self, dependency_provider, validated_execution_result):
        """Should use data from dependencies"""
        # Get cached dependency result
        dep_result = dependency_provider.get_result("RequiredAgent")
        
        assert dep_result is not None, \
            "RequiredAgent should be cached"
        
        # Verify dependency completed successfully
        assert dep_result.status in {"success", "degraded", "warning"}, \
            "Dependency should have completed successfully"
        
        # Add checks that agent actually used dependency data
        # Example: Check metadata, timestamps, or specific fields
    
    def test_dependency_triggered(self, dependency_provider):
        """Required dependencies should be triggered"""
        assert dependency_provider.is_triggered("RequiredAgent"), \
            "RequiredAgent dependency should be triggered"
    
    # ============================================
    # INTEGRATION TESTS
    # ============================================
    
    @pytest.mark.integration
    def test_output_directory_created(self, validated_execution_result, dependency_provider):
        """Output directory should be created"""
        from pathlib import Path
        
        shared_config = dependency_provider.get_shared_source_config()
        output_dir = Path(shared_config.your_agent_dir)
        
        assert output_dir.exists(), \
            f"Output directory not created: {output_dir}"
    
    # ============================================
    # PERFORMANCE TESTS
    # ============================================
    
    @pytest.mark.performance
    def test_execution_performance(self, validated_execution_result):
        """Should complete in reasonable time"""
        MAX_DURATION = 120.0  # Adjust based on agent complexity
        
        assert validated_execution_result.duration < MAX_DURATION, (
            f"Agent took {validated_execution_result.duration:.2f}s "
            f"(max {MAX_DURATION}s)"
        )


# ============================================
# OPTIONAL: Dependency Interaction Tests
# ============================================

class TestYourAgentDependencies:
    """
    Test YourAgent's interaction with dependencies
    Separate class to avoid interfering with BaseAgentTests
    """
    
    def test_fails_without_required_dependency(self, dependency_provider):
        """Should fail gracefully when required dependency is missing"""
        from agents.yourPackage.your_agent import YourAgent, YourConfig
        
        # DON'T trigger required dependency
        assert not dependency_provider.is_triggered("RequiredAgent"), \
            "RequiredAgent should not be triggered yet"
        
        # Create agent
        agent = YourAgent(
            config=YourConfig(
                shared_source_config=dependency_provider.get_shared_source_config()
            )
        )
        
        # Execute - should fail or degrade gracefully
        result = agent.your_execute_method()
        
        # Should either fail or use fallback
        assert result.status in {"failed", "degraded", "partial"}, \
            "Should fail or degrade without required dependency"
        
        if result.status == "failed":
            assert result.error is not None, \
                "Failed execution should have error message"
    
    def test_reuses_cached_dependency(self, dependency_provider):
        """Should reuse cached dependency result"""
        from agents.yourPackage.your_agent import YourAgent, YourConfig
        
        # Trigger dependency once
        dep_result_1 = dependency_provider.trigger("RequiredAgent")
        
        # Create and execute first instance
        config = YourConfig(
            shared_source_config=dependency_provider.get_shared_source_config()
        )
        
        agent1 = YourAgent(config=config)
        result1 = agent1.your_execute_method()
        
        # Trigger again - should return cached
        dep_result_2 = dependency_provider.trigger("RequiredAgent")
        
        # Should be same object (cached)
        assert dep_result_1 is dep_result_2, \
            "Should reuse cached dependency result"
        
        # Create second instance - should also use cached
        agent2 = YourAgent(config=config)
        result2 = agent2.your_execute_method()
        
        # Both should succeed
        assert result1.status in {"success", "degraded", "warning"}
        assert result2.status in {"success", "degraded", "warning"}


# ============================================
# OPTIONAL: Configuration Variations
# ============================================

class TestYourAgentConfigurations:
    """
    Test YourAgent with different configurations
    Separate from BaseAgentTests to avoid interference
    """
    
    def test_with_custom_config(self, dependency_provider):
        """Test with custom configuration"""
        from agents.yourPackage.your_agent import YourAgent, YourConfig
        
        # Trigger dependencies if needed
        dependency_provider.trigger("RequiredAgent")
        
        # Create with custom config
        agent = YourAgent(
            config=YourConfig(
                custom_param1=custom_value1,
                custom_param2=custom_value2,
                shared_source_config=dependency_provider.get_shared_source_config()
            )
        )
        
        result = agent.your_execute_method()
        
        # Should work with custom config
        assert result.status in {"success", "degraded", "warning"}
    
    @pytest.mark.parametrize("param1,param2", [
        (value1a, value2a),
        (value1b, value2b),
        (value1c, value2c),
    ])
    def test_config_parameter_combinations(self, dependency_provider, param1, param2):
        """Test different parameter combinations"""
        from agents.yourPackage.your_agent import YourAgent, YourConfig
        
        dependency_provider.trigger("RequiredAgent")
        
        agent = YourAgent(
            config=YourConfig(
                param1=param1,
                param2=param2,
                shared_source_config=dependency_provider.get_shared_source_config()
            )
        )
        
        result = agent.your_execute_method()
        
        # Should work with all parameter combinations
        assert result.status in {"success", "degraded", "warning"}
        
        # Verify parameters were applied
        assert agent.config.param1 == param1
        assert agent.config.param2 == param2
```

---

### **Tier 3: Edge Cases (Critical agents only)**

Add these ONLY if agent is critical or has had production bugs:

```python
class TestYourAgentEdgeCases:
    """
    Edge case tests - only add when needed
    
    Add these if:
    - Agent caused production bug
    - Agent handles critical data (money, orders, etc.)
    - Agent has external dependencies (API, database)
    """
    
    def test_handles_empty_data(self, dependency_provider):
        """Should handle empty/no data gracefully"""
        # TODO: Implement when needed
        pass
    
    def test_handles_malformed_data(self, dependency_provider):
        """Should handle corrupted/invalid data"""
        # TODO: Implement when needed
        pass
    
    def test_handles_large_dataset(self, dependency_provider):
        """Should handle large datasets without timeout"""
        # TODO: Implement when needed
        pass
```

---

## 📚 Common Patterns

### **Pattern 1: Agent with NO Dependencies**

```python
class TestYourAgent(BaseAgentTests):
    @pytest.fixture
    def agent_instance(self, dependency_provider):
        """No dependencies - simple creation"""
        return YourAgent(
            config=YourConfig(
                shared_source_config=dependency_provider.get_shared_source_config()
            )
        )
    
    @pytest.fixture
    def execution_result(self, agent_instance):
        return agent_instance.execute()
```

**Examples:** ValidationOrchestrator, AnalyticsOrchestrator

---

### **Pattern 2: Agent with 1 Dependency**

```python
class TestYourAgent(BaseAgentTests):
    @pytest.fixture
    def agent_instance(self, dependency_provider):
        """Trigger single dependency"""
        dependency_provider.trigger("RequiredAgent")
        
        return YourAgent(
            config=YourConfig(
                shared_source_config=dependency_provider.get_shared_source_config()
            )
        )
    
    @pytest.fixture
    def execution_result(self, agent_instance):
        return agent_instance.execute()
```

**Examples:** OrderProgressTracker (depends on ValidationOrchestrator)

---

### **Pattern 3: Agent with Multiple Dependencies**

```python
class TestYourAgent(BaseAgentTests):
    @pytest.fixture
    def agent_instance(self, dependency_provider):
        """Trigger all required dependencies"""
        dependency_provider.trigger("RequiredAgent1")
        dependency_provider.trigger("RequiredAgent2")
        dependency_provider.trigger("RequiredAgent3")
        
        return YourAgent(
            config=YourConfig(
                shared_source_config=dependency_provider.get_shared_source_config()
            )
        )
    
    @pytest.fixture
    def execution_result(self, agent_instance):
        return agent_instance.execute()
```

**Examples:** InitialPlanner (depends on OrderProgressTracker + HistoricalFeaturesExtractor)

---

### **Pattern 4: Agent with Custom Config**

```python
class TestYourAgent(BaseAgentTests):
    @pytest.fixture
    def agent_instance(self, dependency_provider):
        """Create with custom config parameters"""
        dependency_provider.trigger("RequiredAgent")
        
        return YourAgent(
            config=YourConfig(
                efficiency=0.85,      # Custom param
                loss=0.03,            # Custom param
                threshold=100,        # Custom param
                shared_source_config=dependency_provider.get_shared_source_config()
            )
        )
    
    @pytest.fixture
    def execution_result(self, agent_instance):
        return agent_instance.execute()
    
    # Test custom params applied
    def test_custom_params_applied(self, agent_instance):
        assert agent_instance.config.efficiency == 0.85
        assert agent_instance.config.loss == 0.03
```

**Examples:** HistoricalFeaturesExtractor

---

### **Pattern 5: Orchestrator/Complex Agent**

```python
class TestYourOrchestrator(BaseAgentTests):
    @pytest.fixture
    def agent_instance(self, dependency_provider):
        """Create orchestrator with multiple component configs"""
        return YourOrchestrator(
            config=YourOrchestratorConfig(
                shared_source_config=dependency_provider.get_shared_source_config(),
                
                # Component 1
                component1=ComponentConfig(
                    enabled=True,
                    save_result=True
                ),
                
                # Component 2
                component2=ComponentConfig(
                    enabled=True,
                    save_result=True,
                    custom_param="value"
                ),
                
                # Top-level config
                save_orchestrator_log=True
            )
        )
    
    @pytest.fixture
    def execution_result(self, agent_instance):
        return agent_instance.run_orchestration()
    
    # Test expected components exist
    def test_expected_components_exist(self, validated_execution_result):
        component_names = {r.name for r in validated_execution_result.sub_results}
        
        expected_components = {
            "Component1",
            "Component2"
        }
        
        assert expected_components.issubset(component_names)
```

**Examples:** AnalyticsOrchestrator, DashboardBuilder

---

## ⚠️ Common Mistakes to Avoid

### ❌ DON'T: Assert in `execution_result` fixture
```python
# ❌ WRONG
@pytest.fixture
def execution_result(self, agent_instance):
    result = agent_instance.execute()
    assert result.status == "success"  # DON'T DO THIS!
    return result
```

### ✅ DO: Let `validated_execution_result` handle validation
```python
# ✅ CORRECT
@pytest.fixture
def execution_result(self, agent_instance):
    return agent_instance.execute()

# Use validated_execution_result in tests
def test_something(self, validated_execution_result):
    # Already validated - just test business logic
    pass
```

---

### ❌ DON'T: Use `scope="class"`
```python
# ❌ WRONG
@pytest.fixture(scope="class")
def agent_instance(self, dependency_provider):
    # Won't work with instance methods
    pass
```

### ✅ DO: Use function scope (default)
```python
# ✅ CORRECT
@pytest.fixture
def agent_instance(self, dependency_provider):
    # Fresh instance for each test
    pass
```

---

### ❌ DON'T: Use old trigger API
```python
# ❌ OLD API
dependency_provider.trigger_validation_orchestrator(shared_config)
```

### ✅ DO: Use new generic API
```python
# ✅ NEW API
dependency_provider.trigger("ValidationOrchestrator")
```

---

### ❌ DON'T: Write edge cases prematurely
```python
# ❌ Waste of time if not needed
def test_handles_1_million_records(self, ...):
    pass

def test_handles_corrupted_utf8(self, ...):
    pass

def test_handles_leap_year_boundary(self, ...):
    pass
```

### ✅ DO: Start with happy path, add edge cases when bugs occur
```python
# ✅ Start simple
def test_produces_expected_output(self, validated_execution_result):
    # Happy path is enough for most agents
    pass

# Add edge case ONLY when it becomes a problem
# def test_handles_empty_data(self, ...):
#     """TODO: Add if we see empty data in production"""
#     pass
```

---

## 🎓 Step-by-Step Guide

### Step 1: Understand Your Agent
- [ ] What does it do?
- [ ] What dependencies does it need?
- [ ] What's the execute method name?
- [ ] What config parameters are required?

### Step 2: Copy Template
```bash
cp tests/agents_tests/universal_template.md tests/agents_tests/specific_agents/test_your_agent.py
```

### Step 3: Fill in Fixtures
- [ ] Update `agent_instance` with your agent import
- [ ] Trigger dependencies if needed
- [ ] Update config parameters
- [ ] Update `execution_result` with correct execute method

### Step 4: Write Business Logic Tests
- [ ] Test expected structure
- [ ] Test expected output
- [ ] Test configuration applied
- [ ] Add 2-5 happy path tests

### Step 5: Register in AGENT_REGISTRY (if needed)
Add to `test_all_agents_structure.py`:
```python
AGENT_REGISTRY["YourAgent"] = AgentFactory(
    name="YourAgent",
    factory_fn=create_your_agent,
    execute_method="your_execute_method",
    required_dependencies=["RequiredAgent1", "RequiredAgent2"]
)
```

### Step 6: Run Tests
```bash
# Run specific agent tests
pytest tests/agents_tests/specific_agents/test_your_agent.py -v

# Run all agent tests
pytest tests/agents_tests/ -v

# Run with markers
pytest tests/agents_tests/ -m "not performance" -v
```

---

## 📊 Test Maturity Levels

| Level | Tests | When | Agents |
|-------|-------|------|--------|
| **Level 1: Basic** | BaseAgentTests + 2-5 happy path | MVP, low-risk agents | Most agents |
| **Level 2: Standard** | + Dependency tests + Config tests | Production-ready | Important agents |
| **Level 3: Comprehensive** | + Edge cases + Performance | Critical, has bugs | AnalyticsOrchestrator, payment, orders |

**Start at Level 1, grow to Level 2/3 as needed.**

---

## 🔍 Quick Reference

### Available Fixtures (from conftest.py)
- `dependency_provider` - Manage dependencies
- `validated_execution_result` - Auto-validated execution result
- `execution_summary` - Summary statistics
- `all_sub_results` - Flattened tree of all results

### Available Marks
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.performance` - Performance benchmarks

### Useful Methods
- `result.get_path("Phase.SubPhase")` - Get nested result
- `result.get_failed_paths()` - Get list of failed paths
- `result.has_critical_errors()` - Check for critical errors
- `result.summary_stats()` - Get execution statistics
- `dependency_provider.trigger("AgentName")` - Trigger dependency
- `dependency_provider.is_triggered("AgentName")` - Check if triggered
- `dependency_provider.get_result("AgentName")` - Get cached result

---

## 📖 Examples

See these files for complete examples:
- `test_validation_orchestrator.py` - No dependencies
- `test_order_progress_tracker.py` - With 1 dependency
- `test_historical_features_extractor.py` - Custom config + multiple deps
- `test_initial_planner.py` - Multiple dependencies
- `test_analytics_orchestrator.py` - Orchestrator pattern
- `test_dashboard_builder.py` - Complex multi-service agent

---

## 🚀 Quick Start: 3-Minute Test

```python
import pytest
from tests.agents_tests.base_agent_tests import BaseAgentTests

class TestYourAgent(BaseAgentTests):
    @pytest.fixture
    def agent_instance(self, dependency_provider):
        from agents.yourPackage.your_agent import YourAgent, YourConfig
        return YourAgent(
            config=YourConfig(
                shared_source_config=dependency_provider.get_shared_source_config()
            )
        )
    
    @pytest.fixture
    def execution_result(self, agent_instance):
        return agent_instance.execute()
```

Done! This gives you ~20 structural tests for free. Add business logic tests as needed.

---

## 💡 Pro Tips

1. **Start small** - BaseAgentTests + 2-3 happy path tests is enough
2. **Don't over-test** - Edge cases are expensive, add only when needed
3. **Use markers** - Separate integration/performance tests
4. **Reuse fixtures** - Use `validated_execution_result` everywhere
5. **Document assumptions** - Add docstrings explaining what you're testing
6. **Test behavior, not implementation** - Focus on outputs, not internals

---

## 🆘 Help & Support

**Getting test failures?**
1. Check error message from `validated_execution_result`
2. Look at execution tree: `format_execution_tree(result)`
3. Check failed paths: `result.get_failed_paths()`

**Not sure what to test?**
1. Start with structure (already covered by BaseAgentTests)
2. Add happy path (agent works with normal data)
3. Stop there unless agent is critical

**Need help?**
- See existing tests in `specific_agents/`
- Check `base_agent_tests.py` for inherited tests
- Review `conftest.py` for available fixtures

---

**Remember:** Good tests are simple, focused, and maintainable. Don't overthink it! 🎯