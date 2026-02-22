# Agent Test Suite Documentation

## 📚 Table of Contents

1. [Overview](#overview)
2. [Test Suite Structure](#test-suite-structure)
3. [Core Infrastructure](#core-infrastructure)
4. [File Descriptions](#file-descriptions)
5. [Running Tests](#running-tests)
6. [Test Coverage](#test-coverage)

---

## Overview

The agent test suite validates 6 agents and their business logic components. Unlike the workflow and module tests, agent tests execute **real business logic against a mock database** — no mocking of agents themselves. The suite is session-scoped to avoid redundant re-execution of expensive dependency chains.

- **749 tests, ~49 minutes** — dominated by real agent execution
- **70% overall coverage** across 12,256 statements
- **Session-scoped caching** — each agent's dependencies execute once per test session

### Current Test Results

```
Name                                              Stmts   Miss  Cover
---------------------------------------------------------------------
agents/dataPipelineOrchestrator/...               ~480     ~30   93%
agents/validationOrchestrator/...                 ~863     ~71   90%
agents/orderProgressTracker/...                   ~649     ~99   86%
agents/autoPlanner/...                           ~2126    ~306   85%
agents/analyticsOrchestrator/...                 ~1644    ~228   85%
agents/dashboardBuilder/ (plotters)              ~3800   ~3400   ~11%
---------------------------------------------------------------------
TOTAL                                            12256   3650    70%
====== 749 passed, 2 warnings in 2925.23s (0:48:45) ======
```

The low overall coverage is driven entirely by dashboard plotter files (10–35% each). These are visualization-only leaf nodes that generate matplotlib/chart output — their execution paths require a fully populated analytics database to hit, which the current test setup doesn't provide for every plotter variant.

---

## Test Suite Structure

```
tests/
├── conftest.py                              # (project root)
└── agents_tests/
    ├── conftest.py                          # DependencyProvider + shared fixtures
    ├── base_agent_tests.py                  # BaseAgentTests ABC
    ├── test_all_agents_structure.py         # AgentFactory registry + structure/execution tests
    ├── universal_template.md                # Template for new agent test files
    ├── specific_agents/
    │   ├── test_analytics_orchestrator.py
    │   ├── test_auto_planner.py
    │   ├── test_dashboard_builder.py
    │   ├── test_data_pipeline_orchestrator.py
    │   ├── test_order_progress_tracker.py
    │   └── test_validation_orchestrator.py
    └── business_logic_tests/
        ├── conftest.py
        ├── collectors/
        ├── configs/
        ├── formatters/
        ├── healers/
        │   └── conftest.py
        ├── notifiers/
        ├── planners/
        ├── processors/
        ├── reports/
        ├── tools/
        ├── utils/
        └── validators/
```

### Execution Flow

```mermaid
graph TD
    A[test session starts] --> B[DependencyProvider created]
    B --> C[TestAllAgentsStructure]
    C -->|create only, no exec| D[any_agent fixture]

    B --> E[TestAllAgentsExecution]
    E -->|trigger deps + create + exec| F[executed_agent fixture]

    B --> G[specific_agents/]
    G -->|dependency_provider.trigger()| H[agent-specific assertions]

    B --> I[business_logic_tests/]
    I -->|dependency_provider.trigger()| J[component-level assertions]

    F --> K[session cleanup]
    H --> K
    J --> K
    K --> L[shared_db removed]
```

---

## Core Infrastructure

### `DependencyProvider` (`conftest.py`)

The central state manager for the entire agent test session. Handles dependency execution ordering, result caching, and cleanup.

```python
provider = DependencyProvider()

# Get config (no execution)
config = provider.get_shared_source_config()

# Trigger a specific agent (executes + validates)
provider.trigger("DataPipelineOrchestrator")

# Trigger multiple (in order)
provider.trigger_all_dependencies([
    "DataPipelineOrchestrator",
    "ValidationOrchestrator"
])

# Reset shared_db between tests
provider.clear_all_dependencies()

# Full cleanup (removes shared_db entirely)
provider.cleanup()
```

**Key design decisions:**

- `db_dir="tests/mock_database"` — all agents read from a static mock DB, not production data
- `default_dir="tests/shared_db"` — all agents write outputs here; downstream agents read from here
- `trigger()` validates the result before returning — if an upstream agent fails, the test fails immediately with the full error + traceback rather than a cryptic downstream error
- Session scope means `DataPipelineOrchestrator` runs once even if 50 tests depend on it

**Dependency chain:**

```
DataPipelineOrchestrator
    └── ValidationOrchestrator
            └── OrderProgressTracker
                    └── AutoPlanner

DataPipelineOrchestrator
    └── AnalyticsOrchestrator
    └── DashboardBuilder
```

### `DashboardBuilder` special case

`DashboardBuilder` uses `deepcopy` on `SharedSourceConfig` and overrides `analytics_orchestrator_dir` to point at `tests/shared_db/DashboardBuilder`. This prevents it from consuming `AnalyticsOrchestrator`'s live output directory, allowing both to coexist in the same session without interference.

---

### `BaseAgentTests` (`base_agent_tests.py`)

Abstract base class for all specific agent test files. Subclasses provide `agent_instance` and `execution_result` fixtures; the base class provides 16 structural tests that run automatically.

**Required fixtures in subclass:**

```python
class TestMyAgent(BaseAgentTests):

    @pytest.fixture
    def agent_instance(self, dependency_provider):
        # return agent instance (no execution)
        ...

    @pytest.fixture
    def execution_result(self, dependency_provider):
        # return agent.run_*() result
        ...
```

**Tests provided by base class:**

| Test | What it checks |
|---|---|
| `test_result_not_none` | Result is not `None` |
| `test_has_required_attributes` | `status`, `name`, `type`, `severity`, `duration`, `data`, `metadata`, `sub_results`, `warnings` all present |
| `test_status_is_valid` | Status is a valid `ExecutionStatus` enum value |
| `test_severity_is_valid` | Severity is a valid `PhaseSeverity` enum value |
| `test_duration_is_valid` | Duration is numeric and ≥ 0 |
| `test_data_structures` | `data` is dict, `metadata` is dict, `sub_results` is list, `warnings` is list |
| `test_composite_has_sub_results` | `type=="agent"` → `is_composite=True` and `len(sub_results) > 0` |
| `test_success_criteria` | `SUCCESS/DEGRADED/WARNING` → `has_critical_errors()` returns `False` |
| `test_failed_phases_have_error_info` | Failed phases have `error`, `warnings`, or `traceback` |
| `test_summary_stats_valid` | All summary fields present, `success + failed + skipped == total_executions` |
| `test_tree_structure_valid` | `get_depth() >= 1`, all sub-results have `name` and `status` |
| `test_get_path_works` | Valid paths return result, `"NonExistent.Path"` returns `None` |
| `test_flatten_works` | `flatten()` returns non-empty list, all items have `name` and `status` |
| `test_degraded_status_means_fallback_used` | DEGRADED phases have `data["fallback_used"]=True` and `"original_error"` in data |
| `test_warnings_present_for_degraded` | DEGRADED phases have at least one warning |

The base class uses `validated_execution_result` (defined in `conftest.py`) which pre-validates `status in SUCCESSFUL_STATUSES` before any test runs — so all structural assertions can assume the result is already in a good state.

---

### `AgentFactory` and `AGENT_REGISTRY` (`test_all_agents_structure.py`)

`AgentFactory` pairs an agent creation function with execution metadata:

```python
AgentFactory(
    name="AutoPlanner",
    factory_fn=create_auto_planner,        # creates instance, no execution
    execute_method="run_scheduled_components",
    required_dependencies=[
        "DataPipelineOrchestrator",
        "ValidationOrchestrator",
        "OrderProgressTracker"
    ]
)
```

`AGENT_REGISTRY` maps all 6 agents. `create_and_execute()` calls `trigger_all_dependencies()` before creating and running the agent, ensuring the dependency chain is satisfied in the correct order.

---

## File Descriptions

### `test_all_agents_structure.py`

Two test classes, one fixture set, no business logic assertions.

#### Fixtures

| Fixture | Scope | Description |
|---|---|---|
| `any_agent_factory` | function | Parametrized over all 6 `AgentFactory` entries |
| `any_agent` | function | Creates agent instance only — no dependency trigger, no execution |
| `executed_agent` | function | Triggers deps → creates agent → executes → returns result |

#### `TestAllAgentsStructure` (no execution)

Runs for all 6 agents via the `any_agent` fixture. These are the tests that run in **CI Job 1** (smoke).

| Test | What it checks |
|---|---|
| `test_agent_can_be_created` | `agent_factory.create(provider)` returns non-None |
| `test_agent_has_name` | `factory.name` is a non-empty string |
| `test_dependencies_declared` | `required_dependencies` is a list |
| `test_dependencies_exist_in_registry` | All declared deps exist as keys in `AGENT_REGISTRY` |
| `test_execute_method_exists` | Agent instance has the declared `execute_method` as a callable |

#### `TestAllAgentsExecution` (full execution)

Runs for all 6 agents via the `executed_agent` fixture. These are **disabled in CI** (agent-tests job has `if: false`).

| Test | What it checks |
|---|---|
| `test_agent_executes_successfully` | Status in `SUCCESSFUL_STATUSES`, not `None` |
| `test_execution_returns_result` | Result has `status`, `name`, `duration` |
| `test_execution_has_sub_results` | Agent-type results have `sub_results` with at least one entry |
| `test_execution_completes` | `is_complete()` returns `True` |
| `test_no_critical_errors` | `has_critical_errors()` returns `False` |

---

### `specific_agents/`

One file per agent. Each subclasses `BaseAgentTests` and adds agent-specific assertions on top of the 16 inherited structural tests.

The pattern for each file:

```python
class TestDataPipelineOrchestrator(BaseAgentTests):

    @pytest.fixture(scope="session")
    def execution_result(self, dependency_provider):
        # No deps needed - DataPipeline is the root
        provider.trigger("DataPipelineOrchestrator")
        return <result from provider cache>

    @pytest.fixture
    def agent_instance(self, dependency_provider):
        return create_data_pipeline_orchestrator(dependency_provider)

    # Agent-specific tests below...
    def test_collected_data_has_expected_keys(self, validated_execution_result):
        ...
```

Fixtures in specific agent files are typically `scope="session"` so the agent only executes once regardless of how many test methods the class has.

---

### `business_logic_tests/`

Tests for individual components (processors, validators, healers, etc.) that are too granular to test through the agent's top-level result. Each subdirectory maps to a component category:

| Directory | Components tested |
|---|---|
| `collectors/` | `DataCollector` |
| `configs/` | Config dataclasses for analyzers and visualization services |
| `formatters/` | `AutoPlannerAssignerFormatter` |
| `healers/` | `DataCollectorHealer`, `ProcessHealingMechanism`, `SchemaErrorHealer` |
| `notifiers/` | `ManualReviewNotifier` |
| `planners/` | `PendingOrderPlanner` |
| `processors/` | `DataPipelineProcessor`, `DynamicDataProcessor`, `StaticDataProcessor` |
| `reports/` | `ProcessDashboardReports` |
| `tools/` | `compatibility`, `mold_capacity`, `mold_machine_feature_weight`, `plan_matching` |
| `utils/` | Various utility modules across agents |
| `validators/` | `SchemaValidator` |

`business_logic_tests/conftest.py` provides component-level fixtures. `healers/conftest.py` provides healer-specific fixtures (typically involves injecting deliberately malformed data to trigger healing paths).

---

## Running Tests

```bash
# Structure tests only (fast, no execution) — mirrors CI Job 1
pytest tests/agents_tests/test_all_agents_structure.py::TestAllAgentsStructure -v

# Full structure + execution for all agents
pytest tests/agents_tests/test_all_agents_structure.py -v

# Specific agent
pytest tests/agents_tests/specific_agents/test_data_pipeline_orchestrator.py -v

# Business logic tests only
pytest tests/agents_tests/business_logic_tests/ -v

# All agent tests
pytest tests/agents_tests/ -v

# With coverage
pytest tests/agents_tests/ --cov=agents --cov-report=term-missing

# Stop on first failure (recommended for long runs)
pytest tests/agents_tests/ -x --tb=short

# Run only healer tests
pytest tests/agents_tests/business_logic_tests/healers/ -v
```

---

## Test Coverage

### Overall: 70% (12,256 stmts, 3,650 missed)

The gap is concentrated in one area.

**High coverage components (85–100%)**

| Component | Coverage | Notes |
|---|---|---|
| `dataPipelineOrchestrator` | ~93% avg | Core pipeline well tested |
| `validationOrchestrator` | ~90% avg | Validators well covered |
| `autoPlanner/tools/` | ~90% avg | Tool functions tested directly |
| `orderProgressTracker` | ~86% avg | Main paths covered |
| `analyticsOrchestrator` | ~85% avg | Processor edge cases are the gaps |

**Low coverage: Dashboard plotters (7–37%)**

Every file under `agents/dashboardBuilder/plotters/` has very low coverage. These files contain only rendering logic — they receive a fully-processed analytics dataframe and produce matplotlib figures. The test suite currently validates the pipeline and service layers above the plotters, but does not inject enough data variety to exercise all rendering branches within each plotter.

This is a known trade-off: plotter code is difficult to unit-test meaningfully (it produces visual output, not data), and the integration path through the full analytics pipeline only exercises the code paths relevant to the test fixture's data range.

**Remaining gaps in well-tested components:**

`autoPlanner/phases/initialPlanner/pending_order_planner.py` (75%) and `production_schedule_generator.py` (74%) — these contain complex scheduling branches that require specific order configurations to trigger. The missing lines are primarily exception handlers and edge-case scheduling paths.

`analyticsOrchestrator` processor files (83–86%) — missing lines are consistently the same pattern across `day_level`, `month_level`, and `year_level`: the `except` blocks inside data aggregation loops and the final summary-write paths that only execute when all upstream steps succeed with specific data shapes.

---

**Document Version**: 1.0  
**Last Updated**: February 2026  
**Test Framework**: pytest 7.x  
**Python Version**: 3.11+  
**Execution Time**: ~49 minutes (full suite with real agent execution)