# Dependency Policies

Dependency policies control how a workflow step validates its dependencies before executing. Each policy defines where to look for a dependency (current workflow, database/filesystem, or both) and what to do when one is missing or stale.

---

## Overview

| Policy | Looks in Workflow | Looks in Database | Fails on missing |
|---|---|---|---|
| `strict` | ✅ | ❌ | Always |
| `flexible` | ✅ | ✅ | Configurable |
| `hybrid` | ✅ (preferred) | ✅ (fallback) | Always |

All policies return a `DependencyValidationResult` containing:

- **`resolved`** — dependencies that were found, mapped to their source (`workflow`, `database`, `workflow+database`)
- **`errors`** — blocking issues (will prevent execution)
- **`warnings`** — non-blocking issues (execution continues)
- **`valid`** — `True` if no errors

---

## `strict`

**"Every dependency must be produced by the current workflow run."**

The strictest policy. Only accepts dependencies that are present as upstream modules in the current workflow. Rejects anything sourced from a previous run or persisted database.

**When to use:** Pipelines where stale or externally-sourced data is never acceptable — e.g., real-time inference, audit-sensitive workflows.

**Config:**
```json
{ "dependency_policy": "strict" }
```

No parameters supported.

**Behavior:**

- Dependency found in workflow → `resolved`, source = `workflow`
- Dependency not in workflow → `errors`, reason = `workflow_violation`
- Database is never consulted

---

## `flexible`

**"Dependencies can come from anywhere — workflow or database — with optional constraints."**

The most permissive policy. Checks the current workflow first, then falls back to the database/filesystem. Supports optional constraints: a list of deps that *must* exist, and a maximum age for database-sourced deps.

**When to use:** Development, experimentation, or workflows where some steps produce outputs in earlier scheduled runs and re-execution of the full pipeline is impractical.

**Config:**
```json
{
  "dependency_policy": {
    "name": "flexible",
    "params": {
      "required_deps": ["preprocessed_data", "feature_store"],
      "max_age_days": 7
    }
  }
}
```

**Parameters:**

| Param | Type | Default | Description |
|---|---|---|---|
| `required_deps` | `list` | `None` | Dep names that must exist (in workflow or DB). If `None`, all declared deps are required. |
| `max_age_days` | `int` | `None` | Max age in days for database-sourced deps. Deps older than this produce an error. If `None`, no age limit. |

**Behavior:**

- Dependency found in workflow → `resolved`, source = `workflow`
- Dependency found in database (within age limit) → `resolved`, source = `database`
- Dependency in `required_deps` but not found anywhere → `errors`, reason = `not_found`
- Dependency found in database but too old → `errors`, reason = `too_old`
- Dependency not in `required_deps` and not found → `warnings` (non-blocking)

---

## `hybrid`

**"Prefer workflow, fall back to database — but always be transparent about it."**

Balances strictness and flexibility. Tries to resolve every dependency from the current workflow first. If a dependency is not in the workflow, it falls back to the database with an optional age check. Using the database fallback can optionally emit a warning.

**When to use:** Production pipelines that should ideally be self-contained but need to tolerate partial re-runs — e.g., a daily pipeline where only some stages re-execute.

**Config:**
```json
{
  "dependency_policy": {
    "name": "hybrid",
    "params": {
      "max_age_days": 3,
      "prefer_workflow": true
    }
  }
}
```

**Parameters:**

| Param | Type | Default | Description |
|---|---|---|---|
| `max_age_days` | `int` | `None` | Max age in days for the database fallback. Deps older than this produce an error. If `None`, no age limit. |
| `prefer_workflow` | `bool` | `True` | If `True`, emits a warning whenever a dep is resolved from the database instead of the workflow. Set to `False` to suppress these warnings in mixed-source pipelines. |

**Behavior:**

- Dependency found in workflow → `resolved`, source = `workflow`
- Dependency not in workflow, found in database (within age limit) → `resolved`, source = `database`; warning emitted if `prefer_workflow=True`
- Dependency not found anywhere → `errors`, reason = `not_found`
- Dependency found in database but too old → `errors`, reason = `too_old`

---

## Dependency Sources

Resolved dependencies are tagged with one of the following sources:

| Source | Value | Meaning |
|---|---|---|
| `DependencySource.WORKFLOW` | `"workflow"` | Found as an upstream module in the current run |
| `DependencySource.DATABASE` | `"database"` | Found on disk / in the database from a previous run |
| `DependencySource.WORKFLOW_DATABASE` | `"workflow+database"` | Verified in both (used for cross-validation scenarios) |
| `DependencySource.NONE` | `"none"` | Not resolved (always accompanies an error or warning) |

## Failure Reasons

When a dependency cannot be resolved, the issue is tagged with one of the following reasons:

| Reason | Value | Meaning |
|---|---|---|
| `DependencyReason.NOT_FOUND` | `"not_found"` | Dependency does not exist in any consulted source |
| `DependencyReason.TOO_OLD` | `"too_old"` | Dependency exists in the database but exceeds `max_age_days` |
| `DependencyReason.WORKFLOW_VIOLATION` | `"workflow_violation"` | Dependency exists but is not part of the current workflow (strict policy) |
| `DependencyReason.NONE` | `"none"` | No issue (used in resolved entries) |

---

## Quick Reference

```python
from workflows.dependency_policies import AVAILABLE_POLICIES, POLICY_SCHEMAS
from workflows.dependency_policies.factory import DependencyPolicyFactory

# List all policies
DependencyPolicyFactory.list_policies()
# → {"strict": "...", "flexible": "...", "hybrid": "..."}

# Inspect a policy's schema
DependencyPolicyFactory.get_schema("hybrid")
# → {"description": ..., "required_params": [], "optional_params": {...}, "defaults": {...}}

# Create a policy directly
policy = DependencyPolicyFactory.create({
    "name": "hybrid",
    "params": {"max_age_days": 3}
})

# Run validation
result = policy.validate(
    dependencies={"my_dep": "/data/outputs/my_dep"},
    workflow_modules=["upstream_module"]
)

print(result.valid)        # True / False
print(result.summary())    # dict with errors, warnings, resolved
```

---

## Adding a New Policy

See [Adding a New Dependency Policy](docs/v3/guides/adding_dependency_policy.md) for the step-by-step guide.