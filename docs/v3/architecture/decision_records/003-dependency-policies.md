# ADR 003: Dependency Policies

## Status

Accepted

## Context

Modules read each other’s outputs via a shared filesystem/database.
Each module uses a change log to determine the latest data path for its dependency before execution.

An issue arises when an upstream dependency fails and the user chooses to skip it (`required: false`). The downstream module may still need to run — in this case, a mechanism is required to decide whether older data from a previous run is acceptable, and if so, how old is acceptable.

Additionally, different environments (development, production, partial re-runs) have different requirements regarding where data must come from and how fresh it must be.

## Decision

Each module in a workflow is assigned a dependency policy that controls two things:
**where to locate dependencies** (current workflow, database, or both) and **how old the data is allowed to be**.

Three policies are defined:

* `strict` — only accepts dependencies from the current workflow.
  Used for production pipelines where all data must be freshly generated.

* `flexible` — accepts dependencies from either the workflow or the database, with optional configuration for required dependencies and maximum data age.
  Used for development or partial re-runs.

* `hybrid` — prefers workflow outputs but falls back to the database if necessary.
  Emits a warning when database data is used instead of workflow data.
  Used for production pipelines running partial executions.

Policies are validated through `DependencyPolicyFactory` before the executor calls `module.execute()`. The result is returned as a `DependencyValidationResult` — the sole contract between the policy and the executor.

## Consequences

### Positive:

* Enables skipping failed upstream dependencies while still allowing downstream modules to run with older data
* Policies can be overridden per module in JSON — no need to modify module code
* `hybrid` + `max_age_days` provides explicit control over how much stale data is acceptable

### Negative:

* Developers must clearly understand the three policies to choose the appropriate one per module
* `flexible` can be overly permissive if `required_deps` and `max_age_days` are not configured — potentially allowing very old data without notice

## Related

* `workflows/dependency_policies/`
* `docs/v3/reference/dependency_policies.md`
* `docs/v3/architecture/decision_records/002-declarative-workflows.md`