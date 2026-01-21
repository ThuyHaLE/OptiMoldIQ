> Status: Introduced in v2  
> Purpose: Introduce analytics and visualization as first-class domains

# DashboardBuilder

## 1. Agent Info
- **Name**: DashboardBuilder
- **Purpose**: 
The DashboardBuilder module is a multi-level analytics and visualization system designed to generate production intelligence dashboards at daily, monthly, and yearly resolutions.
- **Owner**: 
- **Status**: Active
- **Location**: `agents/dashboardBuilder/`

---

## 2. What it does

- It provides a unified interface (Facade Layer) for dashboard visualization operations, orchestrating two main functional groups:
    - `MultiLevelPerformancePlotter` – handles time-level (day/month/year) data visualization and dashboard generation for performance metrics.
    - `HardwareChangePlotter` – focuses on visualizing hardware change detection and history tracking (machine layouts and machine-mold pairs).

- **Architecture:**
```
┌─────────────────────────────────────────┐
│ DashboardBuilder (Facade Layer)         │
│  ├─ Auto-Configuration                  │
│  ├─ Unified Execution Control           │
│  └─ Centralized Logging                 │
└─────────────┬───────────────────────────┘
              │
              ├──────────────────────┬──────────────────────┐
              │                      │                      │
              ▼                      ▼                      ▼
┌──────────────────────────┐ ┌─────────────────────┐ ┌──────────────────┐
│ MultiLevelPerf...        │ │ HardwareChange...   │ │ Logging System   │
│  ├─ DayLevelPlotter      │ │  ├─ MachineLayout.. │ │  ├─ Auto Config  │
│  ├─ MonthLevelPlotter    │ │  └─ MachineMold...  │ │  ├─ Results Log  │
│  └─ YearLevelPlotter     │ └─────────────────────┘ │  └─ Change Log   │
└──────────────────────────┘                         └──────────────────┘
```

- **Integration with AnalyticsOrchestrator:**
```
┌──────────────────────────────────────────────────┐
│         AnalyticsOrchestrator                    │
│  (Data Processing & Analytics)                   │
│   ├─ MultiLevelPerformanceAnalyzer               │
│   │   ├─ DayLevelDataProcessor                   │
│   │   ├─ MonthLevelDataProcessor                 │
│   │   └─ YearLevelDataProcessor                  │
│   └─ HardwareChangeAnalyzer                      │
│       ├─ MachineLayoutTracker                    │
│       └─ MachineMoldPairTracker                  │
└──────────────────┬───────────────────────────────┘
                   │
                   │ (Processed Data)
                   │
                   ▼
┌──────────────────────────────────────────────────┐
│         DashboardBuilder                         │
│  (Visualization & Dashboard Generation)          │
│   ├─ MultiLevelPerformancePlotter                │
│   │   ├─ DayLevelDataPlotter                     │
│   │   ├─ MonthLevelDataPlotter                   │
│   │   └─ YearLevelDataPlotter                    │
│   └─ HardwareChangePlotter                       │
│       ├─ MachineLayoutPlotter                    │
│       └─ MachineMoldPairPlotter                  │
└──────────────────────────────────────────────────┘
```

---

## 3. Key Features

### 3.1 Unified Interface
- Single entry point (`build_dashboards()`) for all visualization operations
- Clean facade pattern hiding internal complexity
- Consistent error handling and logging across all components

### 3.2 Auto-Configuration System
- Automatically propagates enable flags from parent to child components:
  - `enable_multi_level_plotter` → `performance_plotflow_config.enable_day_level_plotter` / `enable_month_level_plotter` / `enable_year_level_plotter`
  - `enable_hardware_change_plotter` → `hardware_change_plotflow_config.enable_machine_layout_plotter` / `enable_machine_mold_pair_plotter`
- Cascades configuration to nested `AnalyticsOrchestrator` for data processing
- Forces appropriate logging settings at each level
- Provides detailed configuration summary for debugging

### 3.3 Flexible Execution Modes
- **Nothing enabled**: Gracefully skips processing
- **Hardware Change Plotter only**: Runs only hardware change visualization
- **Multi-Level Plotter only**: Runs only performance dashboard generation
- **Both enabled**: Executes both plotters independently

### 3.4 Robust Error Handling
- Each component runs in isolation via `_safe_process()`
- Failures in one component don't block others
- Comprehensive error logging with component-specific context

### 3.5 Integrated Data Processing
- Each plotter automatically triggers corresponding data processor via `AnalyticsOrchestrator`
- Seamless pipeline from raw data to final visualizations
- No manual coordination needed between processors and plotters

### 3.6 Centralized Logging
- Consolidated log file (`change_log.txt`) capturing:
  - Auto-configuration summary
  - Execution results from both plotters
  - Timestamp and configuration details
- Separate detailed logs from each plotter component

---

## 4. System Purpose

DashboardBuilder provides automated end-to-end generation of production dashboards with five complementary analytical scopes:

- **Daily insight** → Operational troubleshooting & short-term performance check
- **Monthly tracking** → PO progress monitoring, risk alerts, efficiency evaluation
- **Yearly trends** → Historical patterns, seasonal behaviors, and long-term capacity planning
- **Machine layout change** → Historical machine layout change
- **Machine-mold first pairing change** → Historical first pairing change

Each level contains its own visualization logic and reporting structure, but all share a unified data pipeline and configuration model.

---

## 5. Functional Groups Details

### 5.1 MultiLevelPerformancePlotter

**Purpose**: Handle three time-level data visualization and dashboard generation for comprehensive performance analysis.

**[→ See Documentation](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/v2/documentations/dashboardBuilder/multiLevelPerformancePlotter/OptiMoldIQ_multiLevelPerformancePlotter_overview.md)**

### 5.2 HardwareChangePlotter

**Purpose**: Visualize hardware change detection and history tracking for machine layouts and machine-mold relationships.

**[→ See Documentation](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/v2/documentations/dashboardBuilder/hardwareChangePlotter/OptiMoldIQ_hardwareChangePlotter_overview.md)**

---

## 6. Data Flow Architecture

```
┌───────────────────────────────────────────────┐
│            Raw Data Sources                   │
│  (Production Records, Purchase Orders,        │
│   Mold Info, Additional Inputs)               │
└───────────────────┬───────────────────────────┘
                    │
                    ▼
┌───────────────────────────────────────────────┐
│         AnalyticsOrchestrator                 │
│  (Auto-triggered by DashboardBuilder)         │
├───────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────┐  │
│  │  MultiLevelPerformanceAnalyzer          │  │
│  │   ├─ DayLevelDataProcessor              │  │
│  │   ├─ MonthLevelDataProcessor            │  │
│  │   └─ YearLevelDataProcessor             │  │
│  └─────────────────────────────────────────┘  │
│  ┌─────────────────────────────────────────┐  │
│  │  HardwareChangeAnalyzer                 │  │
│  │   ├─ MachineLayoutTracker               │  │
│  │   └─ MachineMoldPairTracker             │  │
│  └─────────────────────────────────────────┘  │
└───────────────────┬───────────────────────────┘
                    │ (Processed Data)
                    ▼
┌───────────────────────────────────────────────┐
│         DashboardBuilder                      │
├───────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────┐  │
│  │  MultiLevelPerformancePlotter           │  │
│  │   ├─ DayLevelDataPlotter                │  │
│  │   ├─ MonthLevelDataPlotter              │  │
│  │   └─ YearLevelDataPlotter               │  │
│  └─────────────────────────────────────────┘  │
│  ┌─────────────────────────────────────────┐  │
│  │  HardwareChangePlotter                  │  │
│  │   ├─ MachineLayoutPlotter               │  │
│  │   └─ MachineMoldPairPlotter             │  │
│  └─────────────────────────────────────────┘  │
└───────────────────┬───────────────────────────┘
                    │
                    ▼
┌───────────────────────────────────────────────┐
│         Output Artifacts                      │
│  ├─ PNG Dashboards                            │
│  ├─ Excel Reports (Multi-sheet)               │
│  ├─ Text Summaries                            │
│  ├─ Early Warning Reports                     │
│  └─ Historical Archives                       │
└───────────────────────────────────────────────┘

─────  : Data flows from one step to the next
▼      : Transformation or processing stage
│      : Hierarchical/vertical dependency
```

---

## 7. Configuration

### 7.1 DashboardBuilderConfig
Main configuration class that controls the entire builder.

**Enable Flags (Parent Level)**:
  ```python
  enable_multi_level_plotter: bool = False
  enable_hardware_change_plotter: bool = False
  ```

**Multi-Level Plotter Sub-flags**:
  ```python
  enable_multi_level_day_level_plotter: bool = False
  enable_multi_level_month_level_plotter: bool = False
  enable_multi_level_year_level_plotter: bool = False
  ```

**Hardware Change Plotter Sub-flags**:
  ```python
  enable_hardware_change_machine_layout_plotter: bool = False
  enable_hardware_change_machine_mold_pair_plotter: bool = False
  ```

**General Settings**:
  ```python
  save_dashboard_builder_log: bool = False
  dashboard_builder_dir: str = 'agents/shared_db/DashboardBuilder'
  ```

**Dependencies**:
  ```python
  performance_plotflow_config: PerformancePlotflowConfig
  hardware_change_plotflow_config: HardwareChangePlotflowConfig
  ```

### 7.2 Auto-Configuration Behavior
The builder automatically configures child components when `build_dashboards()` is called:

1. **Multi-Level Performance Plotter** (if enabled):
   - `performance_plotflow_config.enable_day_level_plotter = enable_multi_level_day_level_plotter`
   - `performance_plotflow_config.enable_month_level_plotter = enable_multi_level_month_level_plotter`
   - `performance_plotflow_config.enable_year_level_plotter = enable_multi_level_year_level_plotter`
   - `performance_plotflow_config.save_multi_level_performance_plotter_log = True` (forced)

2. **Hardware Change Plotter** (if enabled):
   - `hardware_change_plotflow_config.enable_machine_layout_plotter = enable_hardware_change_machine_layout_plotter`
   - `hardware_change_plotflow_config.enable_machine_mold_pair_plotter = enable_hardware_change_machine_mold_pair_plotter`
   - `hardware_change_plotflow_config.save_hardware_change_plotter_log = False` (forced disabled)

3. **Cascading to AnalyticsOrchestrator**:
   - Each plotter config contains an `analytics_orchestrator_config`
   - When plotters are enabled, corresponding analyzers are auto-enabled
   - Data processing happens transparently before visualization

> **Note**: Manual settings in `performance_plotflow_config` and `hardware_change_plotflow_config` will be overridden by the builder's enable flags.

### 7.3 Configuration Hierarchy

  ```
  DashboardBuilderConfig (Top Level)
    │
    ├─ PerformancePlotflowConfig
    │   ├─ Enable Flags (day/month/year plotters)
    │   ├─ Visualization Configs
    │   ├─ Parallel Processing Settings
    │   └─ AnalyticsOrchestratorConfig
    │       ├─ PerformanceAnalyticflowConfig
    │       │   ├─ DayLevelDataProcessor Config
    │       │   ├─ MonthLevelDataProcessor Config
    │       │   └─ YearLevelDataProcessor Config
    │       └─ (Optional) ChangeAnalyticflowConfig
    │
    └─ HardwareChangePlotflowConfig
        ├─ Enable Flags (layout/pair plotters)
        ├─ Visualization Configs
        ├─ Parallel Processing Settings
        └─ AnalyticsOrchestratorConfig
            ├─ ChangeAnalyticflowConfig
            │   ├─ MachineLayoutTracker Config
            │   └─ MachineMoldPairTracker Config
            └─ (Optional) PerformanceAnalyticflowConfig
  ```

---

## 8. Usage Example

  ```python
  from agents.dashboardBuilder.dashboard_builder import (
      DashboardBuilderConfig, 
      DashboardBuilder
  )
  from agents.dashboardBuilder.dashboardBuilderConfigs.performance_plotflow_config import (
      PerformancePlotflowConfig
  )
  from agents.dashboardBuilder.dashboardBuilderConfigs.hardware_change_plotflow_config import (
      HardwareChangePlotflowConfig
  )
  from agents.analyticsOrchestrator.analyticsConfigs.analytics_orchestrator_config import (
      AnalyticsOrchestratorConfig
  )
  from agents.analyticsOrchestrator.analyticsConfigs.performance_analyticflow_config import (
      PerformanceAnalyticflowConfig
  )

  # Configure analytics processor (for data processing)
  performance_analytic_config = PerformanceAnalyticflowConfig(
      record_date="2019-01-15",
      record_month="2019-01",
      record_year="2019",
      source_path="tests/shared_db/DataLoaderAgent/newest",
      databaseSchemas_path="database/databaseSchemas.json"
  )

  analytics_config = AnalyticsOrchestratorConfig(
      performance_config=performance_analytic_config,
      # Sub-component settings will be auto-configured
  )

  # Configure performance plotter
  performance_plotflow_config = PerformancePlotflowConfig(
      analytics_orchestrator_config=analytics_config,
      enable_parallel=True,
      max_workers=None,  # Auto-detect
      # Sub-component settings will be auto-configured
  )

  # Configure hardware change plotter
  hardware_change_plotflow_config = HardwareChangePlotflowConfig(
      analytics_orchestrator_config=analytics_config,
      enable_parallel=True,
      # Sub-component settings will be auto-configured
  )

  # Configure dashboard builder with enable flags
  config = DashboardBuilderConfig(
      # Enable both plotters
      enable_multi_level_plotter=True,
      enable_hardware_change_plotter=True,
      
      # Multi-level plotter sub-components
      enable_multi_level_day_level_plotter=True,
      enable_multi_level_month_level_plotter=True,
      enable_multi_level_year_level_plotter=True,
      
      # Hardware change plotter sub-components
      enable_hardware_change_machine_layout_plotter=True,
      enable_hardware_change_machine_mold_pair_plotter=True,
      
      # Dependencies
      performance_plotflow_config=performance_plotflow_config,
      hardware_change_plotflow_config=hardware_change_plotflow_config,
      
      # Output settings
      save_dashboard_builder_log=True,
      dashboard_builder_dir='tests/shared_db/DashboardBuilder'
  )

  # Execute dashboard generation
  builder = DashboardBuilder(config)
  results, log_entries = builder.build_dashboards()

  # Access results
  performance_dashboards = results["multi_level_plotter"]
  hardware_dashboards = results["hardware_change_plotter"]
  ```

---

## 9. Output Structure

### 9.1 Return Value
  ```python
  results = {
      "multi_level_plotter": {
          "results": {...},  # Performance dashboard results
          "log_entries_str": "..."  # Detailed log string
      },
      "hardware_change_plotter": {
          "results": {...},  # Hardware change visualization results
          "log_entries_str": "..."  # Detailed log string
      }
  }
  ```

### 9.2 Log File Structure
Saved to `{dashboard_builder_dir}/change_log.txt`:
  ```
  ================================================================================
  Dashboard Builder Execution Log
  ================================================================================
  Execution Time: 2025-11-29 14:30:00
  Configuration:
    - Multi-Level Plotter: Enabled
    - Hardware Change Plotter: Enabled

  --Auto-Configuration--
  ⤷ Input Configs:
    ⤷ enable_multi_level_plotter: True
    ⤷ enable_hardware_change_plotter: True
    ...

  ⤷ Applied Changes:
    ⤷ PerformancePlotflowConfig:
        ⤷ enable_day_level_plotter: True
        ...

  ================================================================================
  Multi-Level Performance Plotter Results
  ================================================================================
  [Detailed performance dashboard logs]

  ================================================================================
  Hardware Change Plotter Results
  ================================================================================
  [Detailed hardware change visualization logs]
  ```

### 9.3 Output Artifacts

```
                                                  ┌──────────────────────────┐
                                                  |     DashboardBuilder     |
                                                  |     (Entry Point)        |
                                                  └──────────────┬───────────┘
            ┌──────────────────────────┬─────────────────────────┼──────────────────────────┬───────────────────────────┐
            ▼                          ▼                         ▼                          ▼                           ▼
┌────────────────────────┐ ┌────────────────────────┐ ┌────────────────────────┐ ┌────────────────────────┐ ┌────────────────────────┐
| DayLevel               | | MonthLevel             | | YearLevel              | | MachineLayout          | | MachineMoldPair        |
├────────────────────────┤ ├────────────────────────┤ ├────────────────────────┤ ├────────────────────────┤ ├────────────────────────┤
| 📊 PROCESSOR OUTPUTS  | | 📊 PROCESSOR OUTPUTS   | | 📊 PROCESSOR OUTPUTS   | | 📊 TRACKER OUTPUTS     | | 📊 TRACKER OUTPUTS    |
| DayLevelDataProcessor/ | | MonthLevelDataProc../  | | YearLevelDataProc../   | | MachineLayoutTracker/  | | MachineMoldPairTrack./ |
├────────────────────────┤ ├────────────────────────┤ ├────────────────────────┤ ├────────────────────────┤ ├────────────────────────┤
| 📊 PLOTTER OUTPUTS    | | 📊 PLOTTER OUTPUTS     | | 📊 PLOTTER OUTPUTS     | | 📊 PLOTTER OUTPUTS     | | 📊 PLOTTER OUTPUTS     |
| DayLevelDataPlotter/   | | MonthLevelDataPlotter/ | | YearLevelPlotter/      | | MachineLayoutPlotter/  | | MachineMoldPairPlotter/|
└────────────────────────┘ └────────────────────────┘ └────────────────────────┘ └────────────────────────┘ └────────────────────────┘
```

**[→ See Documentation](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/v2/agents_output_overviews/dashboardBuilder)**

---

## 10. Core Responsibilities

### 10.1 Unified Data Processing Pipeline
- Automatically trigger `AnalyticsOrchestrator` for data processing
- Load and validate processed datasets
- Normalize time-based fields (day, month, year)
- Consume machine-, mold-, and item-level aggregated data
- Retrieve efficiency, completion, and utilization metrics

### 10.2 Automatic Dashboard Generation
Depending on level (day/month/year), the engine generates from 3 to 9+ dashboard types, including:
- Yield and scrap overviews
- Machine efficiency and status analysis
- Mold performance and shot-count distribution
- Item-level QC and production metrics
- Monthly trend lines, backlog evolution, and PO completion
- Annual aggregates and long-term patterns

### 10.3 Parallel Visualization Execution
- Optional multiprocessing for handling heavy workloads
- Auto selection of worker count based on system hardware
- Graceful fallback to sequential execution

### 10.4 Output Management & File Tracking
- Auto-generated filenames with timestamp versioning
- Historical file archiving (historical_db/)
- Comprehensive change log tracking:
  - created files
  - overridden versions
  - update timestamps
- Excel exports with multi-sheet structured outputs
- Text-based summary reports (for month/year analytics)

---

## 11. Best Practices

1. **Use Parent Enable Flags**: Control sub-components through builder-level flags rather than modifying child configs directly

2. **Configure Data Sources First**: Ensure `AnalyticsOrchestratorConfig` has correct data paths and dates before enabling plotters

3. **Check Log Output**: Review the auto-configuration summary to verify your settings were applied correctly

4. **Enable Parallel Processing**: Use `enable_parallel=True` for faster dashboard generation, especially for year-level analysis

5. **Error Isolation**: Components run independently - check individual results even if one fails

6. **Resource Management**: Both plotters can run concurrently safely due to isolated error handling

7. **Date Configuration**: Ensure appropriate dates are set in `PerformanceAnalyticflowConfig` before enabling corresponding plotters

---

## 12. Troubleshooting

**Issue**: Sub-components not running as expected
- **Solution**: Check that parent enable flag is `True` AND corresponding sub-flag is `True`

**Issue**: Configuration not applied
- **Solution**: Review auto-configuration log section to see what was actually applied

**Issue**: Missing output files
- **Solution**: Verify `save_dashboard_builder_log=True` and check directory permissions

**Issue**: Partial failures
- **Solution**: Check individual component results - builder continues execution even if one component fails

**Issue**: Data not processed before plotting
- **Solution**: Verify `AnalyticsOrchestratorConfig` is properly configured within plotter configs

**Issue**: Slow visualization generation
- **Solution**: Enable parallel processing and check `max_workers` setting