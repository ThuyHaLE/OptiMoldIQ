# AnalyticsOrchestrator

## 1. Agent Info
- **Name**: AnalyticsOrchestrator
- **Purpose**: 
The AnalyticsOrchestrator module coordinates multiple analytics submodules for manufacturing data processing, tracking, and historical updates.
- **Owner**: 
- **Status**: Active
- **Location**: `agents/analyticsOrchestrator/`

---

## 2. What it does
  
- It provides a unified interface (Facade Layer) for analytics operations, orchestrating two main functional groups:
    - `HardwareChangeAnalyzer` – focuses on change detection and history tracking for hardware components (machine layouts and machine-mold pairs).
    - `MultiLevelPerformanceAnalyzer` – handles time-level (day/month/year) data summarization and aggregation for performance metrics.

- **Architecture:**
  ```
  ┌─────────────────────────────────────────┐
  │ AnalyticsOrchestrator (Facade Layer)    │
  │  ├─ Auto-Configuration                  │
  │  ├─ Unified Execution Control           │
  │  └─ Centralized Logging                 │
  └─────────────┬───────────────────────────┘
                │
                ├──────────────────────┬──────────────────────┐
                │                      │                      │
                ▼                      ▼                      ▼
  ┌──────────────────────────┐ ┌─────────────────────┐ ┌──────────────────┐
  │ HardwareChangeAnalyzer   │ │ MultiLevelPerf...   │ │ Logging System   │
  │  ├─ MachineLayoutTracker │ │  ├─ DayLevel...     │ │  ├─ Auto Config  │
  │  └─ MachineMoldPair...   │ │  ├─ MonthLevel...   │ │  ├─ Results Log  │
  └──────────────────────────┘ │  └─ YearLevel...    │ │  └─ Change Log   │
                               └─────────────────────┘ └──────────────────┘
  ```

---

## 3. Key Features

### 3.1 Unified Interface
- Single entry point (`run_analytics()`) for all analytics operations
- Clean facade pattern hiding internal complexity
- Consistent error handling and logging across all components

### 3.2 Auto-Configuration System
- Automatically propagates enable flags from parent to child components:
  - `enable_hardware_change_analysis` → `change_config.enable_machine_layout_tracker` / `enable_machine_mold_pair_tracker`
  - `enable_multi_level_analysis` → `performance_config.enable_day_level_processor` / `enable_month_level_processor` / `enable_year_level_processor`
- Forces logging to be enabled when parent modules are active
- Provides detailed configuration summary for debugging

### 3.3 Flexible Execution Modes
- **Nothing enabled**: Gracefully skips processing
- **Hardware Change Analysis only**: Runs only change detection
- **Multi-Level Analysis only**: Runs only performance analytics
- **Both enabled**: Executes hardware change analysis first, then performance analytics

### 3.4 Robust Error Handling
- Each component runs in isolation via `_safe_process()`
- Failures in one component don't block others
- Comprehensive error logging with component-specific context

### 3.5 Centralized Logging
- Consolidated log file (`change_log.txt`) capturing:
  - Auto-configuration summary
  - Execution results from both analyzers
  - Timestamp and configuration details
- Separate detailed logs from each analyzer component

---

## 4. Functional Groups Details

### 4.1 HardwareChangeAnalyzer
**Purpose**: Orchestrate and coordinate the detection of data changes in production records, specifically tracking machine layout changes and machine-mold pair relationships over time.

**Documentation**: [dataChangeAnalyzer Overview](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/analyticsOrchestrator/dataChangeAnalyzer/OptiMoldIQ_dataChangeAnalyzer_overview.md)

### 4.2 MultiLevelPerformanceAnalyzer
**Purpose**: Handle three time-level data summarization and aggregation for comprehensive performance analysis.

- **DayLevel**: 
  - Process and analyze daily production records
  - Aggregate production data by mold and item
  - Classify production changes (mold changes, color changes, machine idle states)
  - Calculate defect rates and efficiency metrics across machines, shifts, and products

- **MonthLevel**: 
  - Analyze monthly manufacturing operations and purchase order fulfillment
  - Track backlog orders from previous months
  - Estimate production capacity based on mold specifications
  - Detect capacity constraints and identify at-risk orders
  - Classify order status (finished, in-progress, not-started) and timeliness (ontime, late)

- **YearLevel**: 
  - Analyze yearly manufacturing operations and purchase order fulfillment
  - Track backlog orders from previous years
  - Estimate production capacity based on mold specifications
  - Detect capacity constraints and identify at-risk orders
  - Classify order status (finished, in-progress, not-started) and timeliness (ontime, late)

**Documentation**: [multiLevelPerformanceAnalyzer Overview](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/analyticsOrchestrator/multiLevelPerformanceAnalyzer/OptiMoldIQ_multiLevelPerformanceAnalyzer_overview.md)

---

## 5. Configuration

### 5.1 AnalyticsOrchestratorConfig
Main configuration class that controls the entire orchestrator.

**Enable Flags (Parent Level)**:
```python
enable_hardware_change_analysis: bool = False
enable_multi_level_analysis: bool = False
```

**Hardware Change Analysis Sub-flags**:
```python
enable_hardware_change_machine_layout_tracker: bool = False
enable_hardware_change_machine_mold_pair_tracker: bool = False
```

**Multi-Level Analysis Sub-flags**:
```python
enable_multi_level_day_level_processor: bool = False
enable_multi_level_month_level_processor: bool = False
enable_multi_level_year_level_processor: bool = False
```

**General Settings**:
```python
save_analytics_orchestrator_log: bool = True
analytics_orchestrator_dir: str = 'agents/shared_db/AnalyticsOrchestrator'
```

**Dependencies**:
```python
performance_config: PerformanceAnalyticflowConfig
change_config: ChangeAnalyticflowConfig
```

### 5.2 Auto-Configuration Behavior
The orchestrator automatically configures child components when `run_analytics()` is called:

1. **Hardware Change Analysis** (if enabled):
   - `change_config.enable_machine_layout_tracker = enable_hardware_change_machine_layout_tracker`
   - `change_config.enable_machine_mold_pair_tracker = enable_hardware_change_machine_mold_pair_tracker`
   - `change_config.save_hardware_change_analyzer_log = True` (forced)

2. **Multi-Level Analysis** (if enabled):
   - `performance_config.enable_day_level_processor = enable_multi_level_day_level_processor`
   - `performance_config.enable_month_level_processor = enable_multi_level_month_level_processor`
   - `performance_config.enable_year_level_processor = enable_multi_level_year_level_processor`
   - `performance_config.save_multi_level_performance_analyzer_log = True` (forced)

> **Note**: Manual settings in `change_config` and `performance_config` will be overridden by the orchestrator's enable flags.

---

## 6. Usage Example

```python
  from agents.analyticsOrchestrator.analytics_orchestrator import (
      AnalyticsOrchestratorConfig, 
      AnalyticsOrchestrator
  )
  from agents.analyticsOrchestrator.analyticsConfigs.change_analyticflow_config import (
      ChangeAnalyticflowConfig
  )
  from agents.analyticsOrchestrator.analyticsConfigs.performance_analyticflow_config import (
      PerformanceAnalyticflowConfig
  )

  # Configure child analyzers
  change_config = ChangeAnalyticflowConfig(
      source_path="tests/shared_db/DataLoaderAgent/newest",
      databaseSchemas_path="database/databaseSchemas.json",
      # Sub-component settings will be auto-configured
  )

  performance_config = PerformanceAnalyticflowConfig(
      record_date="2019-01-15",
      record_month="2019-01",
      source_path="tests/shared_db/DataLoaderAgent/newest",
      # Sub-component settings will be auto-configured
  )

  # Configure orchestrator with enable flags
  config = AnalyticsOrchestratorConfig(
      # Enable both analyzers
      enable_hardware_change_analysis=True,
      enable_multi_level_analysis=True,
      
      # Hardware change sub-components
      enable_hardware_change_machine_layout_tracker=True,
      enable_hardware_change_machine_mold_pair_tracker=True,
      
      # Multi-level analysis sub-components
      enable_multi_level_day_level_processor=True,
      enable_multi_level_month_level_processor=True,
      enable_multi_level_year_level_processor=False,
      
      # Dependencies
      change_config=change_config,
      performance_config=performance_config,
      
      # Output settings
      save_analytics_orchestrator_log=True,
      analytics_orchestrator_dir='tests/shared_db/AnalyticsOrchestrator'
  )

  # Execute analytics
  orchestrator = AnalyticsOrchestrator(config)
  results, log_entries = orchestrator.run_analytics()

  # Access results
  hardware_results = results["change_hardware_analysis"]
  performance_results = results["multi_level_analytics"]
```

---

## 7. Output Structure

### 7.1 Return Value
```python
  results = {
      "change_hardware_analysis": {
          "results": {...},  # Hardware change detection results
          "log_entries_str": "..."  # Detailed log string
      },
      "multi_level_analytics": {
          "results": {...},  # Performance analytics results
          "log_entries_str": "..."  # Detailed log string
      }
  }
```

### 7.2 Log File Structure

Saved to `{analytics_orchestrator_dir}/change_log.txt`:

```
================================================================================
Analytics Orchestrator Execution Log
================================================================================
Execution Time: 2025-11-29 14:30:00
Configuration:
  - Hardware Change Analysis: Enabled
  - Multi-Level Analysis: Enabled

--Auto-Configuration--
⤷ Input Configs:
   ⤷ enable_hardware_change_analysis: True
   ⤷ enable_multi_level_analysis: True
   ...

⤷ Applied Changes:
   ⤷ ChangeAnalyticflowConfig:
      ⤷ enable_machine_layout_tracker: True
      ...

================================================================================
Hardware Change Analysis Results
================================================================================
[Detailed hardware change logs]

================================================================================
Multi-Level Performance Analysis Results
================================================================================
[Detailed performance analytics logs]
```

---

## 8. Best Practices

1. **Use Parent Enable Flags**: Control sub-components through orchestrator-level flags rather than modifying child configs directly

2. **Check Log Output**: Review the auto-configuration summary to verify your settings were applied correctly

3. **Error Isolation**: Components run independently - check individual results even if one fails

4. **Date Configuration**: Ensure appropriate dates are set in `performance_config` before enabling multi-level analysis

5. **Resource Management**: Both analyzers can run concurrently safely due to isolated error handling

---

## 9. Troubleshooting

**Issue**: Sub-components not running as expected
- **Solution**: Check that parent enable flag is `True` AND corresponding sub-flag is `True`

**Issue**: Configuration not applied
- **Solution**: Review auto-configuration log section to see what was actually applied

**Issue**: Missing output files
- **Solution**: Verify `save_analytics_orchestrator_log=True` and check directory permissions

**Issue**: Partial failures
- **Solution**: Check individual component results - orchestrator continues execution even if one component fails