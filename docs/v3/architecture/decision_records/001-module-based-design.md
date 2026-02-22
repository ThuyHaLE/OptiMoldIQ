# ADR 001: Module-Based Architecture

## Status

Accepted

## Context

The system needs to run multiple business agents, each with its own logic and configuration. The agents were initially built independently, which made it difficult to scale as their number increased and complicated integration into a unified workflow.

## Decision

All agents are wrapped as modules that share a common `BaseModule` contract.
Each module:

* Receives configuration via YAML, which can be overridden at runtime
* Is registered in `AVAILABLE_MODULES` for automatic discovery by the workflow
* Communicates with the rest of the system exclusively through the `BaseModule` interface

Configuration is centrally managed through the `ModuleRegistry`
(`configs/module_registry.yaml`), fully separated from the code.

## Consequences

### Positive:

* New agents only need to implement `BaseModule` — no changes to the workflow executor are required
* Configuration can be swapped per environment without rebuilding
* Each module can be tested independently
* The `ModuleRegistry` allows enabling/disabling modules without deployment

### Negative:

* Each new agent requires additional boilerplate (class + YAML + registry entry)
* Complex business logic must conform to the `BaseModule` contract

## Related

* `architecture/overview.md`
* `workflows/registry/registry.py`
* `configs/module_registry.yaml`
* `testing/test_suite_overview.md`