# ✅ Milestone 04: Framework Release

- **Status**: ✅ Completed
- **Date**: February 2026
- **Dependencies**: ✅ Milestone 03 (Analytics & Dashboard System)
- **Nature of Update**: Non-breaking Formalization
  - *Preserves*: All M01–M03 functionality and business logic
  - *Adds*: Framework runtime, public execution contracts, test infrastructure
  - *Architecture*: Backward-compatible framework layer over existing agents

---

## Overview

Milestone 04 formalizes the structural and conceptual foundation established in Milestone 03 into a **stable, reusable execution framework**.

**Key Principle: Formalizes without replacing.**

All business logic from Milestones 01–03 remains intact and unchanged. Milestone 04 introduces the runtime contracts, tooling, and infrastructure that allow the system to be extended, tested, and maintained as a framework rather than a collection of scripts.

No new planning logic, analytics logic, or visualization logic is introduced. This milestone is entirely concerned with **execution contracts, orchestration formalization, and system-level observability**.

---

## Scope

Milestone 04 introduces the following:

### 1. BaseModule Contract (Framework Foundation)

All agents are formally wrapped as modules inheriting from `BaseModule` — the abstract contract that enforces a consistent interface across the entire system.

```python
class BaseModule(ABC):
    @property
    @abstractmethod
    def module_name(self) -> str: ...

    @property
    def dependencies(self) -> Dict[str, str]: ...

    @abstractmethod
    def execute(self) -> ModuleResult: ...

    def safe_execute(self) -> ModuleResult: ...
```

Every module now exposes:
- A declared `module_name` identifier
- An explicit `dependencies` map (`dep_name → resource_path`)
- A `ModuleResult` return contract (`status`, `data`, `message`, `errors`)
- Error-safe execution via `safe_execute()`

### 2. ModuleRegistry — Single Source of Truth

The registry combines two layers:
- **Python class registry** (`AVAILABLE_MODULES` in `modules/__init__.py`) — what exists
- **YAML config registry** (`configs/module_registry.yaml`) — how it's configured

Resolution order at instantiation time:
1. `override_config_path` if provided at call time
2. `config_path` from YAML registry
3. `None` → module uses its own `DEFAULT_CONFIG_PATH`

This enables environment-specific config swapping without code changes.

### 3. Declarative Workflow Definitions

Workflows are defined as JSON files in `workflows/definitions/`. The orchestrator auto-discovers and validates all definitions at init time — no registration step required.

```json
{
  "workflow_name": "update_database_strict",
  "modules": [
    {
      "module": "DataPipelineModule",
      "dependency_policy": "strict",
      "required": true
    },
    {
      "module": "ValidationModule",
      "dependency_policy": "hybrid",
      "required": false
    }
  ]
}
```

Available workflows at release:

| Workflow | Description |
|---|---|
| `update_database_strict` | Full pipeline, strict dependency enforcement |
| `update_database_hybrid` | Full pipeline, hybrid dependency fallback |
| `update_database_flexible` | Full pipeline, flexible dependency tolerance |
| `track_order_progress` | Order progress tracking only |
| `extract_historical_features` | Historical feature extraction only |
| `process_initial_planning` | Initial production planning only |
| `analyze_production_records` | Analytics orchestration only |
| `build_production_dashboard` | Dashboard generation only |

### 4. Dependency Policy System

Policies control **where** a module looks for its dependencies and **how old** the data can be. Each module in a workflow declares its own policy independently.

| Policy | Current Run | Shared Database | Use Case |
|---|:---:|:---:|---|
| `strict` | ✅ | ❌ | All inputs must come from the current run |
| `flexible` | ✅ | ✅ | Tolerates data from previous runs |
| `hybrid` | ✅ (preferred) | ✅ (fallback) | Prefers current run, falls back to database |

Policies are validated against `POLICY_SCHEMAS` before instantiation — invalid configs fail immediately at workflow load time, not at execution time.

### 5. WorkflowExecutor — Execution Engine

The executor implements a sequential execution loop with per-module policy enforcement:

For each module in a workflow:
1. Check execution cache — reuse result if already run
2. Instantiate module via `ModuleRegistry`
3. Build dependency policy via `DependencyPolicyFactory`
4. Validate dependencies — stop or skip on failure depending on `required`
5. Call `safe_execute()` — cache result on success

### 6. OptiMoldIQ Orchestrator — Top-Level Entry Point

```python
from optiMoldMaster.opti_mold_master import OptiMoldIQ

orchestrator = OptiMoldIQ()

# Run a single workflow
result = orchestrator.execute("update_database_strict")

# Run multiple workflows in sequence
result = orchestrator.execute_chain(
    ["update_database_strict", "analyze_production_records"],
    stop_on_failure=True
)

# Force re-execution, bypassing cache
result = orchestrator.execute("update_database_strict", clear_cache=True)
```

### 7. Test Infrastructure

Milestone 04 introduces a formal test suite covering all framework layers.

| Layer | Test Type | Coverage |
|---|---|---|
| `BaseModule` + all modules | Unit + Integration | 82% |
| `WorkflowExecutor` | Integration | — |
| `DependencyPolicies` | Unit | — |
| Full workflow execution | End-to-end | — |

**Test suite summary:** 90 passed, 1 skipped — 187s

Test fixtures provide three levels of isolation:
- `module_fixture_factory` — module in isolation, no real dependencies
- `module_context_factory` — module with real upstream dependencies pre-executed
- `module_dependency_executor` — full workflow execution

---

## System Evolution

```
M01: Data Pipeline
  ↓
M02: Production Planning Workflow
  ↓
M03: Analytics & Dashboards (Framework-Ready State)
  ↓
M04: Framework Release ← YOU ARE HERE
  ↓
M05: UI Release & Task Orchestration
```

---

## What's Preserved from Milestone 03

All upstream phases remain unchanged and fully operational:

1. **Phase 1**: Data Pipeline
2. **Phase 2**: Shared Database Build & Validation
3. **Phase 2.5**: Historical Insights
4. **Phase 3**: Production Planning
5. **Phase 4A**: Analytics (analyticsOrchestrator)
6. **Phase 4B**: Dashboards (dashboardBuilder)

---

## What's Added in Milestone 04

| Component | Description |
|---|---|
| `modules/base_module.py` | `BaseModule` ABC + `ModuleResult` contract |
| `modules/__init__.py` | `AVAILABLE_MODULES` registry + `get_module()` factory |
| `workflows/executor.py` | `WorkflowExecutor` sequential execution engine |
| `workflows/registry/registry.py` | `ModuleRegistry` — two-layer config resolution |
| `workflows/dependency_policies/` | `strict` / `flexible` / `hybrid` + factory + schema validation |
| `workflows/definitions/` | 8 workflow JSON definitions |
| `optiMoldMaster/opti_mold_master.py` | Top-level orchestrator with auto-discovery |
| `configs/module_registry.yaml` | Central YAML config registry |
| `tests/` | Full test suite: unit, integration, end-to-end |
| `docs/v3/` | Complete framework documentation |

---

## Framework Contract Summary

As of Milestone 04, the following contracts are stable and public:

**Module contract** — any module that inherits `BaseModule` and is registered in `AVAILABLE_MODULES` + `module_registry.yaml` is automatically available for use in any workflow.

**Workflow contract** — any valid JSON file placed in `workflows/definitions/` is auto-discovered, validated, and immediately executable by the orchestrator.

**Dependency policy contract** — any policy registered in `POLICY_SCHEMAS` and `AVAILABLE_POLICIES` is immediately usable in workflow definitions.

---

## Architectural Intent

OptiMoldIQ is designed as:
- A workflow-driven system
- With agents acting as execution runtimes
- And modules serving as reusable, testable logic units

Design priorities maintained through this milestone:
- Determinism over heuristics
- Observability before optimization
- Backward compatibility over rapid iteration

---

## Non-Goals of Milestone 04

- No new business logic (planning, analytics, or visualization)
- No parallel execution (planned for M05)
- No retry or healing hooks (planned for M05)
- No conditional workflow branching (planned for M05)
- No dynamic module loading at runtime

---

## What Changes After Milestone 04

From Milestone 05 onward, all new capabilities must be implemented as:
- Optional workflow modules
- Downstream consumers of M03 analytics outputs
- Strategy, policy, or orchestration layers

Planned for Milestone 05:
- **API Wrapper** — thin JSON layer over OptiMoldIQ: triggers workflow runs and serves shared database outputs as JSON, without exposing raw xlsx files to consumers
- **Control Panel (UI)** — local interface to trigger workflows and visualize results from shared database, replacing CLI for non-developer users
- Task orchestration layer
- Per-module retry policy (`max_retries`, `retry_delay`)
- Healing hooks (`on_failure: notify | retry | fallback_module`)
- Conditional workflow branching
- Parallel execution for independent modules

> This document is intended for architects and system maintainers.
> Business logic documentation is in `docs/v3/`. Framework usage is in `docs/v3/guides/getting_started.md`.