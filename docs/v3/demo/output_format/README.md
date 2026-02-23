# Output Format

This section documents the output format of each module in OptiMoldIQ. Before diving into individual module outputs, this page explains the **shared conventions** that apply to every module uniformly.

---

## Shared Database Structure

Every module writes its output to a shared database located at `tests/shared_db/`. The directory mirrors the module hierarchy of the system:

```
tests/shared_db/
├── <Agent>/
│   ├── change_log.txt
│   ├── <SubAgent>/                  ← may nest multiple levels
│   │   ├── change_log.txt
│   │   ├── historical_db/
│   │   └── newest/
│   │       └── <timestamped output files>
│   └── ...
└── ...
```

---

## Conventions

### `newest/`

Contains the output files from the **most recent run** of the module. When a module runs, it writes all output files here — the previous contents are first moved to `historical_db/` before new files are written.

Other modules that depend on this module's output always read from `newest/`. They use the module's `change_log.txt` to determine whether new data is available and to resolve the current output paths.

### `historical_db/`

Each time a module runs, the previous contents of `newest/` are archived here automatically. This provides a full history of past outputs for auditing or debugging. Modules do not read from `historical_db/` during normal operation.

### `change_log.txt`

A plain-text append-only log that records each run. The log exists at **every level of the hierarchy** — leaf modules and orchestrators alike maintain their own `change_log.txt`.

The content differs by level:

**Leaf module** `change_log.txt` — records file paths saved during that run:
```
[2026-02-18 08:22:00] Saving new version...

  ⤷ Moved old file: .../newest/... → .../historical_db/...
  ⤷ Saved new file: .../newest/20260218_0822_<module>_result.xlsx
  ⤷ Saved report:   .../newest/20260218_0822_<module>_report.txt
```

**Orchestrator** `change_log.txt` — records the full execution context including config, execution tree, processing summary, and export log of all child modules:
```
============================================================
<config header>

--Processing Summary--

⤷ <AgentID> results:

EXECUTION TREE:
...
============================================================

--Summary & Export Log--

SUMMARY:
...

EXPORT LOG:
...
============================================================
```

---

## Timestamp Naming Convention

All output files are prefixed with a timestamp indicating when the run occurred:

```
{YYYYMMDD}_{HHMM}_{module_name}_{suffix}.{ext}
```

For example:
```
20260218_0822_day_level_data_processor_result.xlsx
```

| Part | Example | Description |
|---|---|---|
| `YYYYMMDD` | `20260218` | Date of the run |
| `HHMM` | `0822` | Time of the run (24-hour) |
| `module_name` | `day_level_data_processor` | Snake-case module name |
| `suffix` | `result`, `report` | File role (see below) |

The timestamp is generated as:

```python
timestamp_file = timestamp_now.strftime("%Y%m%d_%H%M")
```

### Common suffixes

| Suffix | Format | Description |
|---|---|---|
| `result` | `.xlsx` | Structured tabular output — the primary machine-readable output |
| `report` | `.txt` | Human-readable summary of the run |

Some modules produce additional files beyond `result` and `report` — these are documented in each module's output page.

---

## Special Case: Cumulative Files

A small number of modules maintain files that are **not** subject to the `newest/` → `historical_db/` versioning cycle. These files live directly under the module directory and are appended to (not replaced) on each run.

The only current example is `weights_hist.xlsx` in `MoldMachineFeatureWeightCalculator`, which accumulates the history of feature weight changes across all runs. See the [AutoPlanner output page](AutoPlanner/auto_planner.md) for details.

---

## Module Output Pages

- [DataPipelineOrchestrator](DataPipelineOrchestrator/data_pipeline_orchestrator.md)
- [AnalyticsOrchestrator](AnalyticsOrchestrator/analytics_orchestrator.md)
- [AutoPlanner](AutoPlanner/auto_planner.md)
- [OrderProgressTracker](OrderProgressTracker/order_progress_tracker.md)
- [ValidationOrchestrator](ValidationOrchestrator/validation_orchestrator.md)
- [DashboardBuilder](DashboardBuilder/dashboard_builder.md)
