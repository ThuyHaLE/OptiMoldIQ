English | [Tiếng Việt](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/README-vi.md)

# OptiMoldIQ: Intelligent Plastic Molding Planner

OptiMoldIQ is a smart production system designed to streamline and optimize the plastic molding process. It integrates multi-agent architecture to automate production scheduling, track resources, and provide actionable insights to improve efficiency and quality.

---
## Current Phase
OptiMoldIQ is in the **system design phase**, focusing on defining database structures, agent workflows, and system architecture.

---

## Business Problem
### Background
In plastic molding production, achieving optimal efficiency while maintaining high product quality is challenging due to the complexity of interconnected factors like:
- Mold utilization and machine maintenance.
- Resin inventory management.
- Production scheduling and yield optimization.

### Challenges
Poor management or lack of integration between components can lead to:
- Increased production downtime.
- Material waste or stock shortages.
- Unbalanced machine and mold utilization.
- Inconsistent product quality or high NG (non-good) rates.
- Reduced production yield and efficiency.

### Problem Statement
Current systems are:
- Manual or static, lacking real-time insights.
- Prone to inefficiencies in scheduling, resource tracking, and quality management.

## Key Goals
- **Integrated Planning and Monitoring**: Automate production scheduling and resource tracking.
- **Quality and Yield Insights**: Optimize cycle times while maintaining quality.
- **Proactive Maintenance and Restocking**: Prevent downtime and material shortages.
- **Visualization and Decision Support**: Build a centralized dashboard for actionable insights.

## Planned Solution
The OptiMoldIQ System uses a multi-agent architecture to tackle these challenges:
- **AutoStatus Agent**: Tracks real-time production progress.
- **InitialSched Agent**: Generates the initial production schedule.
- **FinalSched Agent**: Refines production schedules using tracking reports.
- **Resin Tracking Agent**: Monitors resin stock and consumption.
- **Mold Tracking Agent**: Tracks mold usage, maintenance.
- **Machine Tracking Agent**: Manages machine availability and lead times.
- **MaintenanceScheduler Agent**: Predictive scheduling to reduce downtime.
- **Quality Control Agent**: Tracks yield and NG rates.
- **YieldOptimization Agent**: Tracks the relationship between cycle time, yield, and NG rates to optimize yield.
- **DashBoardBuilderAgent**: Creates an interactive dashboard for data visualization.

## Current Status
- The business problem and solution design document is completed.
- Static database defined for molds, machines, and resins.
- Agent workflows outlined (e.g., AutoStatus Agent, InitialSched Agent).

### Next Steps
- Develop and test agent prototypes.
- Integrate reinforcement learning for yield optimization.
- Design and implement shared databases.

## Roadmap
- **Phase 1**: Define static and dynamic databases.
- **Phase 2**: Develop core agents and integrate static systems.
- **Phase 3**: Add reinforcement learning for optimization.
- **Phase 4**: Build and test the dashboard for visualization.

## Contributing
Contributions are welcome! To contribute:
- Fork the repository.
- Create a branch for your feature.
- Submit a pull request for review.

## License
This project is licensed under the MIT License. See [LICENSE](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/LICENSE) for details.

## Contact
For questions or collaboration, reach out via:
- [Email](mailto:thuyha.le0590@gmail.com)
- [GitHub](https://github.com/ThuyHaLE)

*This README will be updated regularly as the OptiMoldIQ system evolves through development.*
