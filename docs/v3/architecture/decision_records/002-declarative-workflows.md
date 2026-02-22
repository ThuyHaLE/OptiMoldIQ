# ADR 002: Declarative Workflow Execution

## Status

Accepted (Partial — healing mechanism pending)

## Context

The system needs a way to orchestrate multiple modules in sequence, with control over what happens when a module fails.
Hardcoding execution order in Python makes the pipeline difficult to modify without redeployment.

## Decision

Workflows are defined entirely in JSON and executed sequentially according to their declared order. Each module in the workflow can be independently configured with its own dependency policy and required/optional behavior.

The executor reads the JSON and executes modules in order:

* `required: true` → the workflow stops immediately if the module fails
* `required: false` → the module is skipped and the workflow continues
* `dependency_policy` → defines how dependencies are validated before execution (see ADR 003)

The executor maintains an execution cache per workflow run — if the same module appears multiple times within a workflow (or across runs using the same executor instance), the result is reused instead of being executed again. The cache can be cleared manually by setting `clear_cache=True`.

OptiMoldIQ (the master orchestrator) additionally provides:

* Auto-discovery of workflows from `workflows/definitions/*.json`
* Full validation of workflow JSON (including dependency policies) at initialization time — fail fast instead of failing during execution
* Workflow chaining: execute multiple workflows sequentially with configurable `stop_on_failure`
* Lazy-loading of executors per workflow type to reuse execution cache


## Consequences

### Positive:

* Pipeline changes do not require code modifications — only JSON updates
* Execution order is easy to read and review
* Workflows can be created and managed by non-developers

### Negative:

* The execution cache may return stale results if not cleared between runs — `clear_cache=True` must be used when a fresh run is required
* No parallel execution — modules always run sequentially; long pipelines block until each module completes
* Auto-discovery validates workflow JSON at init time, but cannot validate that module names exist in AVAILABLE_MODULES until execution begins

## Future Work

* Per-module retry policy (`max_retries`, `retry_delay`)
* Healing hooks when a module fails (`on_failure: notify | retry | fallback_module`)
* Conditional branching based on the output of previous modules

## Related

* `workflows/executor.py`
* `docs/v3/reference/workflow_schema.md`
* `docs/v3/architecture/decision_records/001-module-based-design.md`
* `docs/v3/architecture/decision_records/003-dependency-policies.md`