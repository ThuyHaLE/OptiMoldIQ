# OptiMoldIQ Documentation Map

- Last Updated: [2025.11.09]
- Purpose: Quick guide to find the right documentation

---

## **Where to Start**
Legend: ✅ Complete | 🔄  In Progress | 📝 Planned

### New to OptiMoldIQ?
**Core Concepts** (30 min): 
- **[business-problem](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/OptiMoldIQ-business-problem.md)** - Why this system exists 📝
- **[dataset](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/OptiMoldIQ-dataset.md)** ✅ - Data you'll work with
- **[dbSchema](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/OptiMoldIQ-dbSchema.md)** ✅ - How everything connects
- **[systemDiagram-ASCII](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/OptiMoldIQ-systemDiagram-ASCII.md)** ✅
- **[agentsBreakDown](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/OptiMoldIQ-agentsBreakDown.md)** ✅ - Key components

**Workflows** (15 min each):
- **[dataPipelineOrchestratorWorkflow](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/workflows/OptiMoldIQ_dataPipelineOrchestratorWorkflow.md)** ✅
- **[validationOrchestratorWorkflow](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/workflows/OptiMoldIQ_validationOrchestratorWorkflow.md)** ✅
- **[orderProgressTrackerWorkflow](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/workflows/OptiMoldIQ_orderProgressTrackerWorkflow.md)** ✅
- **[hybridSuggestOptimizerWorkflow](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/workflows/OptiMoldIQ_hybridSuggestOptimizerWorkflow.md)** ✅
- **[producingProcessorWorkflow](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/workflows/OptiMoldIQ_producingProcessorWorkflow.md)** ✅
- **[OptiMoldIQ_pendingProcessorWorkflow](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/workflows/OptiMoldIQ_pendingProcessorWorkflow.md)** ✅

**Output Examples**:
- **[dashboardBuilder](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/agents_output_overviews/dashboardBuilder)** ✅
  - **[dayLevelDataPlotter Overview](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/agents_output_overviews/dashboardBuilder/DayLevelDataPlotter/dayLevelDataPlotter_output_overviews.md)** ✅
  - **[monthLevelDataPlotter Overview](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/agents_output_overviews/dashboardBuilder/DayLevelDataPlotter/monthLevelDataPlotter_output_overviews.md)** ✅
  - **[yearLevelDataPlotter Overview](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/agents_output_overviews/dashboardBuilder/DayLevelDataPlotter/yearLevelDataPlotter_output_overviews.md)** ✅
- **[dataChangeAnalyzer](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/agents_output_overviews/dataChangeAnalyzer)** ✅
  - **[UpdateHistMachineLayout Overview](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/agents_output_overviews/dataChangeAnalyzer/UpdateHistMachineLayout/updateHistMachineLayout_output_overviews.md)** ✅
  - **[UpdateHistMoldOverview Overview](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/agents_output_overviews/dataChangeAnalyzer/UpdateHistMoldOverview/updateHistMoldOverview_output_overviews.md)** ✅
- **[optiMoldIQWorkflow Overview](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/agents_output_overviews/optiMoldIQWorkflow_output_overviews.md)** ✅
- **[orderProgressTracker Overview](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/agents_output_overviews/orderProgressTracker_output_overviews.md)** ✅

### Need to Modify Something?
Jump to the ([Module Map](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/)) below to find your component. 🔄 

## **Module Map**

### 🚀 dataPipelineOrchestrator
> Manage a comprehensive two-phase data pipeline process (collect → load). And provide robust error handling with automated recovery mechanisms and notification systems

**Start here**: [dataPipelineOrchestrator Overview](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/dataPipelineOrchestrator/OptiMoldIQ_dataPipelineOrchestrator_overview.md) ✅

**Components**:
- **[dataCollector](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/dataPipelineOrchestrator/OptiMoldIQ_dataCollector_review.md)** ✅
- **[dataLoader](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/dataPipelineOrchestrator/OptiMoldIQ_dataLoader_review.md)** ✅

### 🚀 validationOrchestrator
> (1) Coordinate multiple validation processes (static, dynamic, and required field validation). (2) Ensure manufacturing data quality and schema consistency across datasets. And (3) Provide consolidated reporting and version-controlled validation results

**Start here**: [validationOrchestrator Overview](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/validationOrchestrator/OptiMoldIQ_validationOrchestrator_overview.md) ✅

**Components**:
- **[dynamicCrossDataValidator](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/validationOrchestrator/OptiMoldIQ_dynamicCrossDataValidator_overview.md)** ✅
- **[poRequiredCriticalValidator](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/validationOrchestrator/OptiMoldIQ_poRequiredCriticalValidator_overview.md)** ✅
- **[staticCrossDataChecker](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/validationOrchestrator/OptiMoldIQ_staticCrossDataChecker_overview.md)** ✅

### 🚀 orderProgressTracker
> (1) Track and analyze production progress of manufacturing orders in real-time. (2) Monitor production status transitions and completion rates against delivery schedules. And (3) Provide comprehensive production analytics and consolidated reporting with validation integration.

**Start here**: [orderProgressTracker Overview](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/orderProgressTracker/OptiMoldIQ_orderProgressTracker_overview.md) ✅

**Components**:
- **[processDashboardReports](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/orderProgressTracker/OptiMoldIQ_processDashboardReports_overview.md)** ✅

### 🚀 autoPlanner
> production planning for mold manufacturing environments

**Start here**: [autoPlanner Overview](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/autoPlanner) 🔄

**Components**:
- **[initialPlanner](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/autoPlanner/initialPlanner)** ✅
  > (1) comprehensive manufacturing data processing by integrating production status analysis with advanced optimization algorithms. It transforms raw production data into actionable manufacturing plans through a multi-stage pipeline that handles data loading, optimization execution, production analysis, and plan generation with robust error handling and quality validation. And (2) mold-machine assignment optimization for pending production orders through a sophisticated two-tier optimization strategy. It transforms pending production data into actionable manufacturing assignments by combining historical performance patterns with technical compatibility analysis, ensuring optimal resource allocation while maintaining production quality and efficiency standards. 
  - **[moldMachineFeatureWeightCalculator](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/autoPlanner/initialPlanner/historyBasedProcessor/OptiMoldIQ_moldMachineFeatureWeightCalculator_review.md)** ✅
  - **[moldStabilityIndexCalculator](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/autoPlanner/initialPlanner/historyBasedProcessor/OptiMoldIQ_moldStabilityIndexCalculator_review.md)** ✅
  - **[compatibilityBasedMoldMachineOptimizer](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/autoPlanner/initialPlanner/OptiMoldIQ_compatibilityBasedMoldMachineOptimizer_review.md)** ✅
  - **[histBasedMoldMachineOptimizer](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/autoPlanner/initialPlanner/OptiMoldIQ_histBasedMoldMachineOptimizer_review.md)** ✅
  - **[hybridSuggestOptimizer](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/autoPlanner/initialPlanner/OptiMoldIQ_hybridSuggestOptimizer_review.md)** ✅
  - **[itemMoldCapacityOptimizer](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/autoPlanner/initialPlanner/OptiMoldIQ_itemMoldCapacityOptimizer_review.md)** ✅
  - **[moldMachinePriorityMatrixCalculator](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/autoPlanner/initialPlanner/moldMachinePriorityMatrixCalculator_review.md)** ✅
  - **[pendingProcessor](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/autoPlanner/initialPlanner/OptiMoldIQ_pendingProcessor_review.md)** ✅
  - **[producingProcessor](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/autoPlanner/initialPlanner/OptiMoldIQ_producingProcessor_review.md)** ✅

- **[planRefiner](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations)** 📝
  
### 🚀 optiMoldMaster
> manufacturing operations management. It automates daily data pipeline processing, validation, progress tracking, and production planning for mold manufacturing environments.

**Start here**: [optiMoldMaster Overview](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/optiMoldMaster/OptiMoldIQ_optiMoldMaster_review.md) ✅

### 🚀 analyticsOrchestrator
> coordinates multiple analytics submodules for manufacturing data processing, tracking, and historical updates.

**Start here**: [analyticsOrchestrator Overview](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/analyticsOrchestrator/OptiMoldIQ_analyticsOrchestrator_overview.md) ✅

**Components**:
- **[dataChangeAnalyzer](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/analyticsOrchestrator/dataChangeAnalyzer/OptiMoldIQ_dataChangeAnalyzer_overview.md)** ✅
  - **[machineLayoutTracker](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/analyticsOrchestrator/dataChangeAnalyzer/OptiMoldIQ_machineLayoutTracker_overview.md)** ✅
  - **[machineMoldPairTracker](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/analyticsOrchestrator/dataChangeAnalyzer/machineMoldPairTracker_overview.md)** ✅
  - **[updateHistMachineLayout](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/analyticsOrchestrator/dataChangeAnalyzer/updateHistMachineLayout_overview.md)** ✅
  - **[updateHistMoldOverview](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/analyticsOrchestrator/dataChangeAnalyzer/OptiMoldIQ_updateHistMoldOverview_overview.md)** ✅

- **[multiLevelDataAnalytics](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/analyticsOrchestrator/multiLevelDataAnalytics)** ✅
  - **[dayLevelDataProcessor](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/analyticsOrchestrator/multiLevelDataAnalytics/OptiMoldIQ_dayLevelDataProcessor_overview.md)** ✅
  - **[monthLevelDataProcessor](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/analyticsOrchestrator/multiLevelDataAnalytics/OptiMoldIQ_monthLevelDataProcessor_overview.md)** ✅
  - **[yearLevelDataProcessor](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/analyticsOrchestrator/multiLevelDataAnalytics/OptiMoldIQ_yearLevelDataProcessor_overview.md)** ✅

### 🚀 dashboardBuilder
> a multi-level analytics and visualization system designed to generate production intelligence dashboards at daily, monthly, and yearly resolutions. It provides a unified pipeline that extracts, validates, aggregates, and visualizes factory production records (machine, mold, item, and PO-based data) into structured analytical outputs.

**Start here**: [dashboardBuilder Overview](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/dashboardBuilder/OptiMoldIQ_dashboardBuilder_overview.md) ✅

**Components**:
- **[dayLevelDataPlotter](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/dashboardBuilder/OptiMoldIQ_dayLevelDataPlotter_overview.md)** ✅
- **[monthLevelDataPlotter](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/dashboardBuilder/OptiMoldIQ_monthLevelDataPlotter_overview.md)** ✅
- **[yearLevelDataPlotter](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/dashboardBuilder/OptiMoldIQ_yearLevelDataPlotter_overview.md)** ✅

---

## How Modules Connect
    ```
    📁 Raw Data Files (Excel/CSV)
        ↓
    📥 dataPipelineOrchestrator
        ├─ dataCollector → Collect from multiple sources
        └─ dataLoader → Load & structure data
        ↓
    ✅ validationOrchestrator
        ├─ staticCrossDataChecker → Schema validation
        ├─ dynamicCrossDataValidator → Cross-reference checks
        └─ poRequiredCriticalValidator → Critical field validation
        ↓
    🔀 Parallel Processing Branches
        ├─ 📊 orderProgressTracker → Monitor order status & progress
        ├─ 🎯 autoPlanner → Optimize production assignments
        │   ├─ initialPlanner → Generate initial plans
        │   └─ planRefiner → Refine & optimize (planned)
        └─ 📈 analyticsOrchestrator → Process multi-level analytics
            └─ dataChangeAnalyzer → Track changes over time (including dashboard)
        ↓
    📊 analyticsOrchestrator/multiLevelDataAnalytics + dashboardBuilder
        ├─ dayLevelDataProcessor + dayLevelDataPlotter → Daily operational dashboards
        ├─ monthLevelDataProcessor + monthLevelDataPlotter → Monthly PO tracking & alerts
        └─ yearLevelDataProcessor + yearLevelDataPlotter → Annual trends & planning
        ↓
    📤 Outputs
        ├─ Excel reports with multi-sheet analytics
        ├─ PNG/PDF dashboard visualizations
        ├─ TXT summary reports & early warnings
        └─ Historical archives with version control
    ```

**Master Coordinator**: optiMoldMaster orchestrates the entire workflow

## Quick Reference

### Most Used Docs
**Start Here** (New users):

1. [System Diagram](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/OptiMoldIQ-systemDiagram-ASCII.md) ✅
2. [Agents Breakdown](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/OptiMoldIQ-agentsBreakDown.md) ✅
3. [Dashboard Examples](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/agents_output_overviews/dashboardBuilder) ✅

**Daily Work** (Active development):

4. [optiMoldMaster](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/optiMoldMaster/OptiMoldIQ_optiMoldMaster_review.md) ✅
5. [dashboardBuilder](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/dashboardBuilder/OptiMoldIQ_dashboardBuilder_overview.md) ✅
6. [initialPlanner](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/autoPlanner/initialPlanner) ✅

**Technical Reference**:

7. [DB Schema](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/OptiMoldIQ-dbSchema.md) ✅
8. [Dataset Structure](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/OptiMoldIQ-dataset.md) ✅

---

## Common Tasks

### Adding New Features
- **Add metric to dashboard** → [dayLevelDataProcessor](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/analyticsOrchestrator/multiLevelDataAnalytics/OptiMoldIQ_dayLevelDataProcessor_overview.md) + [dayLevelDataPlotter](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/dashboardBuilder/OptiMoldIQ_dayLevelDataPlotter_overview.md)
- **Modify optimization logic** → [hybridSuggestOptimizer](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/autoPlanner/initialPlanner/OptiMoldIQ_hybridSuggestOptimizer_review.md)
- **Add data source** → [dataCollector](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/dataPipelineOrchestrator/OptiMoldIQ_dataCollector_review.md) + [dataLoader](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/dataPipelineOrchestrator/OptiMoldIQ_dataLoader_review.md)

### Understanding Workflows
- **Data flow** → [dataPipelineOrchestrator Workflow](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/workflows/OptiMoldIQ_dataPipelineOrchestratorWorkflow.md)
- **Validation process** → [validationOrchestrator Workflow](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/workflows/OptiMoldIQ_validationOrchestratorWorkflow.md)
- **Production optimization** → [hybridSuggestOptimizer Workflow](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/workflows/OptiMoldIQ_hybridSuggestOptimizerWorkflow.md)

### Troubleshooting
- **Data loading issues** → [dataPipelineOrchestrator Overview](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/dataPipelineOrchestrator/OptiMoldIQ_dataPipelineOrchestrator_overview.md)
- **Validation errors** → [validationOrchestrator Overview](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/validationOrchestrator/OptiMoldIQ_validationOrchestrator_overview.md)
- **Dashboard generation** → [dashboardBuilder Overview](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/dashboardBuilder/OptiMoldIQ_dashboardBuilder_overview.md)

---

## Documentation Tips

- 🔍 **Use Ctrl+F** to search this page for keywords
- 📊 **Start with workflows** to understand end-to-end processes
- 🎯 **Check output examples** to see what each module produces
- ✅ **Focus on Complete (✅) docs** when learning
- 🔄 **In Progress (🔄) docs** may have incomplete sections
- 📝 **Planned (📝) features** are in the roadmap

---

## Contributing to Documentation

When updating docs, remember to:
1. Update the status indicator (✅🔄📝)
2. Update "Last Updated" date at the top
3. Keep descriptions concise (1-2 sentences)
4. Include practical examples where possible
5. Link to related documentation

---

**Quick Navigation**: Use `Ctrl+F` to search | [Back to Top](#optimoldiq-documentation-map)
