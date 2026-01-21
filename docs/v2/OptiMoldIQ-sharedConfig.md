> Status: Introduced in v2
> Purpose: Standardize agent-level data access and output resolution

# Purpose
> Provide a single source of truth for all shared paths and resources across agents and modules.

# Design Intent
- Shared database is accessed by multiple independent agents
- Path duplication is prohibited
- All agents resolve required resources via a shared configuration contract

# Key Principles
- Centralized path definition
- Agent-level read-only access
- No agent owns filesystem topology
- Configuration is resolved once, reused everywhere

# How Agents Use It (1–2 dòng)
> Agents declare required configuration fields.
> The runtime injects a validated shared configuration instance.