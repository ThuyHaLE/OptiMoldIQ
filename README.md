🌐 [English](README.md) | [Tiếng Việt](README-vi.md)

# OptiMoldIQ  
**Workflow-driven production planning, analytics, and observability system for plastic molding operations.**

---

## Project Status

- **Current stable milestone:** **Milestone 03 – Framework-ready**
- **Next milestone:** Milestone 04 – Framework Release

Legend: ✅ Complete | 🔄 In Progress | 📝 Planned

---

## Overview

**OptiMoldIQ** is a multi-agent manufacturing system designed to coordinate data pipelines, production planning, analytics, and visualization for injection molding operations.

The system evolves through clearly defined milestones, prioritizing:
- Deterministic business logic
- Observability before optimization
- Backward-compatible system evolution

Milestone 03 finalizes core behavior and normalizes agent execution models, preparing the system for framework formalization.

---

## System Evolution
```
M01: Core Data Pipeline
↓
M02: Production Planning Workflow
↓
M03: Analytics & Dashboards (Framework-ready) ← current
↓
M04: Formalizes these contracts into a reusable execution framework.
↓
M05: Task Orchestration & Policy Layers
```

---

## Architecture Overview

OptiMoldIQ follows a **workflow-driven, agent-based architecture**:

- **Agents** act as execution runtimes
- **Modules** encapsulate deterministic business logic
- **Analytics and dashboards** are downstream consumers
- No downstream component modifies upstream planning behavior

👉 Architecture details:
- [Project Directory](docs/v2/OptiMoldIQ-projectDirectory.md)
- [System diagram (ASCII)](docs/v2/OptiMoldIQ-systemDiagram-ASCII.md)
- [Agent breakdown](docs/v2/OptiMoldIQ-agentsBreakDown.md)
- [Agent descriptions](docs/v2/OptiMoldIQ-agentsDescriptions.md)
- [Shared configuration contract](docs/v2/OptiMoldIQ-sharedConfig.md)
- [Agent execution format](docs/v2/OptiMoldIQ-agentExecutionFormat.md)

--- 

## Business Context

OptiMoldIQ addresses common challenges in plastic molding production such as:
- Fragmented operational data
- Inefficient mold–machine utilization
- Limited observability across planning horizons

👉 Full context:
- [Business problem](docs/v2/OptiMoldIQ-business-problem.md)
- [Problem-driven solution](docs/v2/OptiMoldIQ-problem_driven_solution.md)

---

## Data Model

OptiMoldIQ operates on a **raw → shared database pipeline**, enabling consistent access across all agents.

👉 Database documentation:
- [Raw database](docs/v2/OptiMoldIQ-rawDatabase.md)
- [Shared database](docs/v2/OptiMoldIQ-sharedDatabase.md)
- [ERD & schema](docs/v2/OptiMoldIQ-dbSchema.md)

---

## Repository Structure (High-level)

```bash
.
├── agents/        # Normalized agent execution runtimes
├── modules/       # Deterministic business logic
├── database/      # Schemas and reference data
├── docs/          # Architecture, milestones, specifications
├── logs/          # Execution logs
└── README.md
```

---

## Milestones

### Milestone 01: Core Data Pipeline Agents (Completed July 2025)
> 👉 [Details](docs/v1/milestones/OptiMoldIQ-milestone_01.md)
> 
### Milestone 02: Initial Production Planning System (Completed August 2025)
> 👉 [Details](docs/v1/milestones/OptiMoldIQ-milestone_02.md)

### Milestone 03: Enhanced Production Planning with Analytics and Dashboard System (Implementation Complete November 2025, Documentation in Progress)
> 👉 [Details](docs/v2/milestones/OptiMoldIQ-milestone_03.md)

---

## Demo & Visualization

**🌐 OptiMoldIQ Lite (Interactive Demo)**

Explore workflow stages and dashboards without running the full system.

> 👉 [See](https://thuyhale.github.io/OptiMoldIQ/)

---

## Quickstart

A runnable example is available in the documentation.

> 👉 [See](docs/v2/quickstart.md)

--- 

## Contributing
Contributions are welcome! To contribute:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

---

## License
This project is licensed under the MIT License. See [LICENSE](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/LICENSE) for details.

---

## Contact
For questions or collaboration, reach out via:
- [Email](mailto:thuyha.le0590@gmail.com)
- [GitHub](https://github.com/ThuyHaLE)

*OptiMoldIQ is under continuous development — documentation and capabilities will expand with each milestone.*
