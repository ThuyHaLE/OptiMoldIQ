> Status: Introduced in v2  
> Purpose: Provide a problem-driven rationale linking business constraints to system architecture, while keeping implementation details out of the README.

## 🔄 Problem–Driven Solution Overview

### Strategic Alignment

OptiMoldIQ directly addresses each business challenge through a set of orchestrated, data-driven systems:

| **Business Challenge** | **Strategic Goal / Orchestration Focus** |
| ---------------------- | ---------------------------------------- |
| Lack of real-time data and fragmented sources | **Data Operations Orchestration** → Automate data ingestion, validation, and real-time production tracking. |
| Inefficient or manual production planning | **Production Planning Orchestration** → Optimize mold–machine assignments through initial planning and refine plans using analytics insights and operational data. |
| Limited visibility into performance and trends | **Data Insight Analytics Orchestration** → Enable multi-level performance analytics (daily/monthly/yearly), historical change analysis for machines and molds, and auto-detection of layout evolution and operational patterns. |
| Poor coordination between production, maintenance, and materials | **Operational Task Orchestration** → Coordinate predictive maintenance (mold & machine tracking), resin inventory management, product quality monitoring, and yield optimization to prevent downtime and enhance efficiency. |
| Static and isolated reporting systems | **Reporting & Visualization Orchestration** → Generate multi-level static dashboards (daily/monthly/yearly reports, hardware change visualizations) and evolve toward dynamic, interactive web-based dashboard platforms. |

### Goals and Planned Solution

In response to the production challenges outlined above, the **OptiMoldIQ System** was built as a **multi-agent orchestration framework** that transforms fragmented manufacturing operations into a unified, data-driven ecosystem. These orchestration layers collectively form the operational backbone of OptiMoldIQ, enabling synchronized workflows from raw data collection to intelligent decision-making.

#### Data Operations Orchestration
- **Daily Data Ingestion Pipeline**: Automated collection and loading of production and operational data. ✅
- **Multi-Layer Validation**: Static, dynamic, and required-field checks to ensure data integrity. ✅
- **Production Tracking**: Monitor production progress and operational KPIs through daily batch updates. ✅

#### Production Planning Orchestration
- **Data Insights Generating** based on historical data. ✅
- **Multi-Stage Mold–Machine Planning**:
  - Initial planning leveraging historical patterns and compatibility analysis. ✅
  - Plan refinement using insights from analytics orchestration and operational task orchestration, including resin inventory and mold/machine maintenance. 📝 

#### High-Level Orchestrations

1. **Data Insight Analytics**: 

- **Analytics Orchestrator** (**analyticsOrchestrator**) 📝: Central analytics facade providing unified interface for coordinating multiple complementary analytics functions. It orchestrates comprehensive data insights for decision-making and downstream system components. **Operates in two modes: (1) Standalone analytics execution with direct output persistence, (2) Shared backend service for visualization layers.**

  **Functional Groups:**
  - **Historical Analytics** (**hardwareChangeAnalyzer**) ✅: Coordinates and executes historical change analyses for both machines and molds through two modules:
    - *MachineLayoutTracker*: Analyzes machine layout evolution over time to identify layout changes and activity patterns
    - *MachineMoldPairTracker*: Analyzes mold-machine relationships, first-run history, and mold utilization to identify operational trends
  
  - **Multi-Level Analytics** (**multiLevelPerformanceAnalyzer**) ✅: Orchestrates and executes comprehensive data processing pipeline across multiple time granularities through three hierarchical modules:
    - *DayLevelDataProcessor*: Processes daily production data with mold-based and item-based aggregations, generating real-time operational metrics and summary statistics
    - *MonthLevelDataProcessor*: Analyzes monthly production patterns, distinguishing finished and unfinished orders to track completion rates and identify trends
    - *YearLevelDataProcessor*: Performs annual production analysis, providing long-term insights into finished/unfinished orders and yearly performance summaries

  **Optional Groups:** (planning...)
  - **Advanced Analytics** (**crossLevelPerformanceAnalyzer**) 📝: Provides advanced data analytics capabilities supporting operational task orchestration and production planning refinement with cross-functional insights for decision-making optimization

2. **Visualization & Report Generating Layer**:

- **Dashboard Builder** (**dashboardBuilder**) 📝: Unified visualization facade providing both static reporting and interactive dashboard capabilities. It transforms analytics outputs into actionable visual insights **by orchestrating Analytics Orchestrator as a shared backend service (Mode 2)**.
  
  **Functional Groups:**
  - **Static Report Generator** (**multiLevelPerformanceVisualizationService**) ✅: Generates static dashboards, plots, and reports (PNG, TXT, XLSX) through three hierarchical modules:
    - *DayLevelDataVisualizationPipeline*: Generates daily operational dashboards with real-time metrics visualization, production summaries, and mold performance reports
    - *MonthLevelDataVisualizationPipeline*: Creates monthly trend dashboards tracking completion rates, production patterns, and month-to-date performance analysis
    - *YearLevelDataVisualizationPipeline*: Produces annual strategic dashboards with long-term trends, yearly summaries, and performance comparisons
  
  - **Hardware Change Visualization** (**hardwareChangeVisualizationService**) ✅: Visualizes hardware change detection and history tracking through two modules:
    - *MachineLayoutVisualizationPipeline*: Generates machine layout evolution visualizations and change reports
    - *MachineMoldPairVisualizationPipeline*: Creates mold-machine relationship visualizations and utilization reports

  **Optional Groups:** (planning...)
  - **Interactive Dashboard Platform** (**dynamicDashboardUI**) 📝: Web-based interactive dashboard with real-time data updates, advanced filtering, drill-down capabilities, and responsive visualizations

3. **Operational Task Coordinating Layer**: (planing...)

- Task Orchestrator (**taskOrchestrator**) 📝: The central coordination layer responsible for distributing, monitoring, and optimizing workflows across all operational coordinators:
  - Resin Coordinator (**resinCoordinator**) 📝: Manages resin inventory, tracks consumption levels, forecasts material demand, and optimizes raw material supply.
  - Maintenance Coordinator (**maintenanceCoordinator**) 📝: Oversees predictive maintenance for both molds and machines, automatically scheduling tasks to reduce downtime and extend equipment lifespan through 2 modules:
    - *MoldTracker* 📝: Tracks mold status, lifecycle, production and maintenance history.
    - *MachineTracker* 📝: Monitors machine conditions, performance metrics, activity schedules and maintenance history.
  - Product Quality Coordinator (**productQualityCoordinator**) 📝: Optimizes product quality through defect data analysis, operational parameter adjustments, and real-time quality monitoring.
  - Yield Optimizer (**yieldOptimizer**) 📝: Enhances production yield using performance analytics, scrap reduction strategies, and intelligent load balancing across resources.