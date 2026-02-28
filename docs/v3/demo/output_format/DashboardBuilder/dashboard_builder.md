# DashboardBuilder Output

The `DashboardBuilder` runs two visualization workflows: **HardwareChangeVisualizationService** (visualizing machine layout and mold-machine pairing history) and **MultiLevelPerformanceVisualizationService** (visualizing production performance at day, month, and year granularity).

Each pipeline produces an `_result.xlsx` containing the data prepared for visualization, and a `visualized_results/` folder containing the rendered dashboard images.

---

## HardwareChangeVisualizationService

### MachineLayoutVisualizationPipeline

#### `machine_layout_visualization_pipeline_result.xlsx`

**Sheet: `melted_layout_change_df`** — Flattened timeline of machine slot assignments, one row per machine per layout change event.

| Column | Type | Description |
|---|---|---|
| `machineCode` | `str` | Machine identifier |
| `machineName` | `str` | Machine model name |
| `changedDate` | `datetime` | Date this slot assignment took effect |
| `machineNo` | `str` | Machine slot assigned (e.g. `NO.03`) |
| `machineNo_numeric` | `int` | Numeric version of `machineNo` for chart ordering |

#### `visualized_results/`

| File | Description |
|---|---|
| `Machine_layout_change_dashboard.png` | Overview of all machine slot changes across the timeline |
| `Individual_machine_layout_change_times_dashboard.png` | Per-machine breakdown of how many times each machine changed slots |

---

### MoldMachinePairVisualizationPipeline

#### `mold_machine_pair_visualization_pipeline_result.xlsx`

**Sheet: `first_mold_usage`** — First production date for each mold and how long it sat unused after acquisition.

| Column | Type | Description |
|---|---|---|
| `moldNo` | `str` | Mold identifier |
| `acquisitionDate` | `datetime` | Date mold was acquired |
| `firstDate` | `datetime` | First date the mold was used in production |
| `daysDifference` | `int` | Days between acquisition and first use |

**Sheet: `first_paired_mold_machine`** — First date each mold was paired with each machine.

| Column | Type | Description |
|---|---|---|
| `firstDate` | `datetime` | First date this mold-machine pair ran together |
| `machineCode` | `str` | Machine identifier |
| `moldNo` | `str` | Mold identifier |
| `acquisitionDate` | `datetime` | Date mold was acquired |

**Sheet: `mold_tonnage_summary`** — Summary of which machine tonnage classes each mold has been used on.

| Column | Type | Description |
|---|---|---|
| `moldNo` | `str` | Mold identifier |
| `usedMachineTonnage` | `str` | JSON list of machine types used (e.g. `['MD100S', 'MD130S']`) |
| `usedTonnageCount` | `int` | Number of distinct machine tonnage classes used |

#### `visualized_results/`

| File | Description |
|---|---|
| `Mold_utilization_dashboard.png` | Overview of mold utilization across the fleet |
| `Mold_machine_first_pairing_dashboard.png` | First pairing dates between molds and machines |
| `Machine_tonage_based_mold_utilization_dashboard.png` | Mold utilization broken down by machine tonnage class |

---

## MultiLevelPerformanceVisualizationService

### DayLevelVisualizationPipeline

#### `day_level_visualization_pipeline_result.xlsx`

Data prepared for day-level dashboards. Sheets mirror `day_level_data_processor_result.xlsx` from `AnalyticsOrchestrator` — see [AnalyticsOrchestrator — day_level_data_processor_result](../AnalyticsOrchestrator/analytics_orchestrator.md#day_level_data_processor_resultxlsx) for full schema.

| Sheet | Description |
|---|---|
| `filtered_df` | Full job-level records for the requested date |
| `mold_based_record_df` | Aggregated by mold per shift |
| `item_based_record_df` | Aggregated by product across the full day |

#### `visualized_results/`

One set of charts per requested date (filename suffix: `_{YYYY-MM-DD}.png`).

| File pattern | Description |
|---|---|
| `change_times_all_types_fig_{date}.png` | Change event counts by type (mold, machine, color) |
| `item_based_overview_dashboard_{date}.png` | Production overview grouped by product |
| `mold_based_overview_dashboard_{date}.png` | Production overview grouped by mold |
| `machine_level_yield_efficiency_chart_{date}.png` | Yield and efficiency metrics per machine |
| `machine_level_mold_analysis_chart_{date}.png` | Mold performance analysis per machine |
| `shift_level_yield_efficiency_chart_{date}.png` | Yield and efficiency metrics per shift |
| `shift_level_detailed_yield_efficiency_chart_{date}.png` | Detailed shift-level yield and efficiency breakdown |
| `shift_level_mold_efficiency_chart_{date}.png` | Mold efficiency metrics per shift |

---

### MonthLevelVisualizationPipeline

#### `month_level_visualization_pipeline_result.xlsx`

**Sheet: `all_progress_df`** — Summary progress status for all POs in the requested month.

| Column | Type | Description |
|---|---|---|
| `poNo` | `str` | Purchase order number |
| `itemCodeName` | `str` | Combined label: `{itemCode}({itemName})` |
| `is_backlog` | `bool` | Whether this PO carried over from a prior period |
| `poStatus` | `str` | PO status (`finished`, `not_started`, etc.) |
| `poETA` | `datetime` | PO due date |
| `itemQuantity` | `int` | Order target quantity |
| `itemGoodQuantity` | `float` | Good quantity produced |
| `itemNGQuantity` | `float` | NG quantity produced |
| `etaStatus` | `str` | Delivery status (`ontime`, `late`, `expected_ontime`, etc.) |
| `proStatus` | `str` | Production status (`finished`, `unfinished`) |
| `moldHistNum` | `float` | Number of distinct molds used |

**Sheet: `short_unfinished_df`** — Subset of unfinished POs with capacity warning fields for chart rendering.

| Column | Type | Description |
|---|---|---|
| `poNo` | `str` | Purchase order number |
| `poETA` | `datetime` | PO due date |
| `itemQuantity` | `int` | Order target quantity |
| `itemGoodQuantity` | `float` | Good quantity produced |
| `itemNGQuantity` | `float` | NG quantity produced |
| `is_backlog` | `bool` | Whether this PO is a backlog |
| `itemCodeName` | `str` | Combined label |
| `proStatus` | `str` | Production status |
| `poStatus` | `str` | PO status |
| `moldHistNum` | `float` | Number of molds used |
| `itemRemainQuantity` | `int` | Remaining quantity to produce |
| `completionProgress` | `float` | Completion rate (0–1) |
| `etaStatus` | `str` | Projected delivery status |
| `overAvgCapacity` | `bool` | Whether demand exceeds average mold capacity |
| `overTotalCapacity` | `bool` | Whether demand exceeds total mold capacity |
| `is_overdue` | `bool` | Whether PO is already overdue |
| `capacityWarning` | `bool` | Whether a capacity warning is raised |
| `capacitySeverity` | `str` | Severity level (`normal`, `warning`, `critical`) |
| `capacityExplanation` | `str` | Human-readable capacity assessment |

**Sheet: `filtered_records`** — Raw production records for the requested month, with an added `recordMonth` column.

Same columns as `productRecords.parquet` (see [DataPipelineOrchestrator](../DataPipelineOrchestrator/data_pipeline_orchestrator.md#productrecordsparquet)), plus:

| Column | Type | Description |
|---|---|---|
| `recordMonth` | `str` | Month of the record (`YYYY-MM`) |

#### `visualized_results/`

One set of charts per requested month (filename suffix: `_{YYYY-MM}.png`).

| File pattern | Description |
|---|---|
| `month_performance_dashboard_{month}.png` | Overall monthly production performance overview |
| `machine_based_dashboard_{month}.png` | Performance breakdown per machine |
| `mold_based_dashboard_{month}.png` | Performance breakdown per mold |

---

### YearLevelVisualizationPipeline

#### `year_level_visualization_pipeline_result.xlsx`

Shares the same sheet structure as `month_level_visualization_pipeline_result.xlsx`. Year-level filters by the requested year; `recordMonth` in `filtered_records` still contains `YYYY-MM` values for monthly grouping within the year view.

| Sheet | Description |
|---|---|
| `all_progress_df` | Summary progress for all POs in the requested year |
| `short_unfinished_df` | Unfinished POs with capacity warning fields |
| `filtered_records` | Raw production records for the requested year |

#### `visualized_results/`

One set of charts per requested year. Multi-page dashboards are split into `_page{N}.png` files.

| File pattern | Description |
|---|---|
| `year_performance_dashboard_{year}.png` | Overall yearly production performance overview |
| `monthly_performance_dashboard_{year}.png` | Month-by-month performance breakdown within the year |
| `machine_based_year_view_dashboard_{year}.png` | Per-machine performance overview for the year |
| `machine_quantity_dashboard_{year}_page{N}.png` | Per-machine production quantities (paginated) |
| `machine_po_item_dashboard_{year}_page{N}.png` | Per-machine PO and item breakdown (paginated) |
| `machine_working_days_dashboard_{year}_page{N}.png` | Per-machine working days (paginated) |
| `mold_based_year_view_dashboard_{year}.png` | Per-mold performance overview for the year |
| `mold_quantity_dashboard_{year}_page{N}.png` | Per-mold production quantities (paginated) |
| `mold_shots_dashboard_{year}_page{N}.png` | Per-mold shot counts (paginated) |
