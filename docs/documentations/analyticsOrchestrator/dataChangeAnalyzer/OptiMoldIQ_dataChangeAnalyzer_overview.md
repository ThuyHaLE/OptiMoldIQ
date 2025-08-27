# DataChangeAnalyzer

## 1. Agent Info
- **Name**: DataChangeAnalyzer
- **Purpose**: 
  - Analyze and track changes in machine layout configurations and machine-mold pairing relationships
  - Provide intelligent parallel processing with system resource optimization
  - Generate historical tracking reports and visualizations for production insights
- **Owner**: 
- **Status**: Active
- **Location**: `agents/analyticsOrchestrator/dataChangeAnalyzer/`

---

## 2. What it does
The `DataChangeAnalyzer` monitors critical changes in manufacturing operations by tracking two key aspects: (1) machine layout modifications that affect production floor organization, and (2) machine-mold pair changes that impact production scheduling and capacity planning. It features intelligent parallel processing that automatically adapts to available system resources for optimal performance.

---

## 3. Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ ProductRecords  │ -> │ DataChange       │ -> │ Historical      │
│ Data Loading    │    │ Analyzer         │    │ Reports &       │
│                 │    │ (Parallel)       │    │ Visualizations  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         v                       v                       v
   ┌─────────────┐        ┌─────────────┐        ┌─────────────┐
   │ Machine     │        │ Resource    │        │ Layout      │
   │ Layout      │        │ Monitoring  │        │ Changes &   │
   │ Tracking    │        │ & Worker    │        │ Mold Pairs  │
   │             │        │ Management  │        │ Updates     │
   └─────────────┘        └─────────────┘        └─────────────┘
```

---

## 4. Pre-requisites Checklist
Before running the analyzer, ensure:

- [ ] **Data sources accessible**: ProductRecords, MoldInfo, MachineInfo DataFrames
- [ ] **Schema file available**: `database/databaseSchemas.json`
- [ ] **Path annotations exist**: `path_annotations.json` with valid DataFrame paths
- [ ] **Output directories writable**: Full access to layout and mold overview output dirs
- [ ] **System resources**: At least 2GB available RAM for parallel processing
- [ ] **Python dependencies**: loguru, pandas, pathlib, multiprocessing, psutil, concurrent.futures
- [ ] **CPU availability**: Minimum 2 cores for parallel execution

---

## 5. Parallel Processing Scenarios

| Resource Status | CPU Usage | Available RAM | Workers Used | Processing Mode | Performance Impact |
|----------------|-----------|---------------|--------------|-----------------|-------------------|
| Optimal | <50% | >4GB | max_workers | Parallel | 40-60% faster |
| Good | 50-80% | 2-4GB | max_workers/2 | Parallel | 20-40% faster |
| Limited | >80% | 1-2GB | max_workers/4 | Parallel | 10-20% faster |
| Constrained | >90% | <1GB | 1 | Sequential | Baseline |
| Force Mode | Any | Any | min_workers | Parallel | Variable |

---

## 6. Input & Output
- **Input**: Product records, machine info, mold info DataFrames via parquet files
- **Output**: Change detection results, updated historical reports, and visualization plots
- **Format**: JSON change logs, parquet data updates, and analysis summary dictionaries

---

## 7. Simple Workflow
```
Data Loading → Resource Check → Parallel Analysis (Layout + Machine-Mold Pairs) → Change Detection → Report Updates → Summary Generation
```

**Detailed Steps:**
1. **Initialization**: Load DataFrames and validate data schemas
2. **Resource Assessment**: Check CPU, memory, and determine optimal worker count
3. **Parallel Analysis**: Simultaneously analyze layout changes and machine-mold pair changes
4. **Change Detection**: Identify new changes based on latest record date
5. **Report Updates**: Generate updated historical reports and visualizations if changes detected
6. **Summary**: Provide comprehensive analysis results with processing metrics

---

## 8. Directory Structure

```
agents/shared_db/
├── UpdateHistMachineLayout/                     # Machine layout outputs
|   ├── historical_db/
|   ├── newest/                                  # Layout visualizations
|   |   ├── YYYYMMDD_HHMM_Machine_change_layout_timeline.png
|   |   ├── YYYYMMDD_HHMM_Machine_level_change_layout_details.png
|   |   ├── YYYYMMDD_HHMM_Machine_level_change_layout_pivot.xlsx
|   |   └── YYYYMMDD_HHMM_Top_machine_change_layout.png
|   ├── change_log.txt
│   └── layout_changes.json                     # Layout change tracking
└── UpdateHistMoldOverview/                     # Mold overview outputs  
    ├── historical_db/
    ├── newest/                                 # Layout visualizations
    |   ├── YYYYMMDD_HHMM_Bottom_molds_tonnage.png
    |   ├── YYYYMMDD_HHMM_Comparison_of_acquisition_and_first_use.png
    |   ├── YYYYMMDD_HHMM_Machine_mold_first_run_pair.xlsx
    |   ├── YYYYMMDD_HHMM_Mold_machine_first_run_pair.xlsx
    |   ├── YYYYMMDD_HHMM_Number_of_molds_first_run_on_each_machine.png
    |   ├── YYYYMMDD_HHMM_Time_Gap_of_acquisition_and_first_use.png
    |   ├── YYYYMMDD_HHMM_Tonage_machine_mold_not_matched.xlsx
    |   ├── YYYYMMDD_HHMM_Tonnage_distribution.png    
    |   ├── YYYYMMDD_HHMM_Tonnage_proportion.png  
    |   ├── YYYYMMDD_HHMM_Top_Bottom_molds_gap_time_analysis.png
    |   └── YYYYMMDD_HHMM_Top_molds_tonnage.png
    ├── machine_molds/                          # Machine-mold pair data
    │   └── YYYY-MM-DD_machine_molds.json       # Series of json of pair tracking data (by date has pair change)
    └── change_log.txt
```

---

## 9. Dependencies
- **MachineLayoutTracker**: Tracks and analyzes machine layout configuration changes
- **MachineMoldPairTracker**: Monitors machine-mold pairing relationship changes  
- **UpdateHistMachineLayout**: Generates updated layout reports and visualizations
- **UpdateHistMoldOverview**: Creates comprehensive mold overview reports
- **psutil**: System resource monitoring for intelligent worker allocation
- **concurrent.futures**: Parallel execution management with ProcessPoolExecutor/ThreadPoolExecutor
- **loguru**: Structured logging with performance and resource usage tracking

---

## 10. How to Run

### 10.1 Basic Usage (Auto Resource Detection)
```python
# Initialize with default settings (auto-detects 2+ workers)
analyzer = DataChangeAnalyzer(
    source_path=f'{shared_db_dir}/DataLoaderAgent/newest', 
    annotation_name="path_annotations.json",
    databaseSchemas_path=f"{mock_db_dir}/databaseSchemas.json",
    machine_layout_output_dir=f"{shared_db_dir}/UpdateHistMachineLayout",
    mold_overview_output_dir=f"{shared_db_dir}/UpdateHistMoldOverview"
)

# Run analysis (automatically chooses parallel/sequential)
analyzer.analyze_changes()

# Check results
summary = analyzer.get_analysis_summary()
print(f"Layout changes: {summary['has_new_layout_change']}")
print(f"Mold pair changes: {summary['has_new_pair_change']}")
```

### 10.2 Custom Parallel Configuration
```python
# High-performance setup for powerful systems
analyzer = DataChangeAnalyzer(
    source_path=f'{shared_db_dir}/DataLoaderAgent/newest',
    # ... other paths ...
    min_workers=4,           # Require at least 4 workers
    max_workers=8,           # Don't exceed 8 workers  
    parallel_mode="process"  # Use process-based parallelism
)

analyzer.analyze_changes()
```

### 10.3 Resource-Constrained Environment
```python
# Lightweight setup for limited systems
analyzer = DataChangeAnalyzer(
    source_path=f'{shared_db_dir}/DataLoaderAgent/newest',
    # ... other paths ...
    min_workers=2,           # Minimum requirement
    max_workers=3,           # Conservative limit
    parallel_mode="thread"   # Thread-based (lower memory)
)

# Force parallel even if resources seem limited
analyzer.analyze_changes(force_parallel=True)
```

### 10.4 Development/Testing Mode
```python
# Debug mode with detailed resource logging
import logging
logging.getLogger("DataChangeAnalyzer").setLevel(logging.DEBUG)

# Test resource checking without full analysis
analyzer = DataChangeAnalyzer(min_workers=1)
can_parallel, workers = analyzer._check_system_resources()
print(f"Can run parallel: {can_parallel}, Optimal workers: {workers}")
```

---

## 11. Result Structure
```json
{
    "latest_record_date": "2024-01-15",
    "has_new_layout_change": true,
    "layout_changes": {
        "2024-01-15": {
            "machines_moved": 3,
            "new_positions": ["A1", "B3", "C2"],
            "impact_score": 0.75
        }
    },
    "machine_layout_output_dir": "/agents/shared_db/UpdateHistMachineLayout",
    "has_new_pair_change": false,
    "new_pairs": [],
    "mold_overview_output_dir": "/agents/shared_db/UpdateHistMoldOverview",
    "parallel_config": {
        "min_workers": 2,
        "max_workers": 4,
        "parallel_mode": "process"
    }
}
```

---

## 12. Configuration Parameters
- **source_path**: Path to newest DataLoader outputs with DataFrame files
- **annotation_name**: JSON file containing DataFrame file path mappings
- **databaseSchemas_path**: Schema definitions for data validation
- **machine_layout_output_dir**: Output directory for layout change reports
- **mold_overview_output_dir**: Output directory for mold overview reports  
- **min_workers**: Minimum worker count required for parallel execution
- **max_workers**: Maximum worker count limit (defaults to CPU count)
- **parallel_mode**: "process" for CPU-intensive or "thread" for I/O-intensive

---

## 13. Common Issues & Solutions

| Problem | Symptoms | Quick Fix | Prevention |
|---------|----------|-----------|------------|
| Sequential fallback | Parallel never runs | Check system resources with `psutil` | Increase available RAM, lower min_workers |
| Resource detection fails | Warning about resource check | Update psutil library | Use `force_parallel=True` for testing |
| DataFrame loading fails | FileNotFoundError on startup | Verify path_annotations.json paths | Run DataLoader first to generate files |
| Worker spawn errors | ProcessPoolExecutor exceptions | Switch to `parallel_mode="thread"` | Check system ulimits and permissions |
| Memory errors | Process killed during analysis | Reduce max_workers or use threads | Monitor memory usage, clean up large DataFrames |
| Slow parallel performance | Parallel slower than sequential | Profile with fewer workers | Check I/O bottlenecks, consider thread mode |

---

## 14. Monitoring & Observability

### 14.1 Log Levels & Indicators
- **🚀 INFO**: Analysis startup and configuration
- **📊 INFO**: Resource assessment and worker allocation
- **⚡ INFO**: Parallel execution progress and task completion
- **✅ INFO**: Change detection results and update completion
- **⚠️ WARNING**: Resource constraints and sequential fallbacks
- **❌ ERROR**: Critical failures in data loading or analysis
- **🔧 DEBUG**: Detailed resource metrics and worker management

### 14.2 Key Metrics to Track
- **Parallel Execution Rate**: Percentage of runs using parallel processing
- **Resource Utilization**: CPU and memory usage during analysis
- **Processing Time Improvement**: Parallel vs sequential performance gains
- **Change Detection Accuracy**: False positives/negatives in change identification
- **Worker Efficiency**: Task completion time per worker
- **System Resource Trends**: Resource availability patterns over time

### 14.3 Health Checks
```python
# System readiness check
def analyzer_health_check():
    try:
        analyzer = DataChangeAnalyzer()
        can_parallel, workers = analyzer._check_system_resources()
        
        return {
            "data_sources_accessible": all([
                analyzer.productRecords_df is not None,
                analyzer.moldInfo_df is not None, 
                analyzer.machineInfo_df is not None
            ]),
            "parallel_capability": can_parallel,
            "optimal_workers": workers,
            "cpu_usage": psutil.cpu_percent(),
            "available_memory_gb": psutil.virtual_memory().available / (1024**3),
            "service_status": "healthy" if can_parallel else "degraded"
        }
    except Exception as e:
        return {"service_status": "failed", "error": str(e)}

# Performance benchmark
def analyzer_performance_test():
    import time
    analyzer = DataChangeAnalyzer(min_workers=1)
    
    # Sequential timing
    start = time.time()
    analyzer._analyze_changes_sequential()
    sequential_time = time.time() - start
    
    # Parallel timing (if available)  
    can_parallel, workers = analyzer._check_system_resources()
    if can_parallel:
        start = time.time()
        analyzer._analyze_changes_parallel(workers)
        parallel_time = time.time() - start
        improvement = (sequential_time - parallel_time) / sequential_time * 100
    else:
        parallel_time = "N/A"
        improvement = 0
        
    return {
        "sequential_time": f"{sequential_time:.2f}s",
        "parallel_time": f"{parallel_time:.2f}s" if parallel_time != "N/A" else "N/A", 
        "performance_improvement": f"{improvement:.1f}%"
    }
```

---

## 15. Performance Tuning Guidelines

### 15.1 Choosing Parallel Mode
- **Process Mode**: Use for CPU-intensive analysis, better for large DataFrames
- **Thread Mode**: Use for I/O-heavy operations, lower memory overhead
- **Auto-detection**: Let system resources determine the optimal mode

### 15.2 Worker Count Optimization
- **Conservative**: `min_workers=2, max_workers=cpu_count//2`
- **Aggressive**: `min_workers=3, max_workers=cpu_count`
- **Memory-limited**: `min_workers=2, max_workers=3` with thread mode

### 15.3 Resource Monitoring Best Practices
- Monitor CPU usage trends during parallel execution
- Track memory consumption patterns with different worker counts
- Log resource check results for capacity planning
- Set up alerts for consistent sequential fallbacks