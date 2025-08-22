# OrderProgressTracker

## Agent Info

- **Name**: OrderProgressTracker
- **Purpose**:
  - Track and analyze production progress of manufacturing orders in real-time
  - Monitor production status transitions and completion rates against delivery schedules
  - Provide comprehensive production analytics and consolidated reporting with validation integration
- **Owner**: 
- **Status**: Active
- **Location**: `agents/orderProgressTracker/`

---

## What it does

The `OrderProgressTracker` processes **dynamic production records** and **purchase order data** against **static mold specifications** to provide comprehensive production status reporting and analytics. It tracks production lifecycle from order receipt through completion, monitoring machine utilization, mold performance, and delivery schedule compliance.

The tracker integrates with validation systems to provide quality-assured production insights and maintains detailed historical tracking for operational decision-making.

### Key Features

- **Real-Time Status Tracking**
  - `PENDING`: Orders awaiting production start
  - `MOLDING`: Currently in production (latest shift activity)  
  - `MOLDED`: Production completed
  - `PAUSED`: Production temporarily halted
  
- **ETA Compliance Monitoring**
  - `PENDING`: Orders not yet completed
  - `ONTIME`: Delivered on or before scheduled date
  - `LATE`: Delivered after scheduled date
  
- **Multi-Dimensional Analytics**
  - Production aggregation by `shift`, `machine`, `mold`, and `day`
  - Material component `tracking` and `validation`
  - Machine utilization and performance metrics
  
- **Validation Integration**
  - `Incorporates warnings` from ValidationOrchestrator
  - Cross-references data quality issues with production records
  
- **Versioned Reporting**
  - `Multi-sheet Excel` exports with automated versioning
  - Historical tracking of production status snapshots
  
### Optional

`ProcessDashboardReports` processes multi-sheet Excel files to track `OrderProgressTracker` outputs and returns structured results for dashboards and reports with built-in validation.

→ See details: [ProcessDashboardReports](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/orderProgressTracker/OptiMoldIQ_processDashboardReports_overview.md)

---

## Architecture Overview

```
                    ┌─────────────────────────┐
                    │   OrderProgressTracker  │
                    │   (Main Coordinator)    │
                    └───────────────┬─────────┘
                                    │
            ┌───────────────────────┼───────────────────────┐
            │                       │                       │
            v                       v                       v
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│  Purchase Orders │    │ Product Records  │    │ Mold Specifications│
│   (Static Info)  │    │ (Production Data)│    │  (Reference Data) │
└─────────┬────────┘    └─────────┬────────┘    └─────────┬────────┘
          │                       │                       │
          └───────────────────────┼───────────────────────┘
                                  │
                                  v
                    ┌─────────────────────────┐
                    │   Data Merging &        │
                    │   Aggregation Engine    │
                    └───────────────┬─────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        │                           │                           │
        v                           v                           v
┌──────────────┐         ┌──────────────────┐         ┌──────────────────┐
│ Status Logic │         │ Shift Management │         │ Mapping Creation │
│ Engine       │         │ & Timeline       │         │ (Mold/Machine)   │
└──────┬───────┘         └─────────┬────────┘         └─────────┬────────┘
       │                           │                           │
       └───────────────────────────┼───────────────────────────┘
                                   │
                                   v
                    ┌─────────────────────────┐
                    │  Validation Integration │
                    │  & Warning Consolidation│
                    └───────────────┬─────────┘
                                    │
                                    v
                    ┌─────────────────────────┐
                    │   Multi-Sheet Excel     │
                    │   Report Generation     │
                    └─────────────────────────┘
```
→ See details: [Workflow](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/workflows/OptiMoldIQ_orderProgressTrackerWorkflow.md)
---

## Pre-requisites Checklist

Before running the tracker, ensure:

- [ ] **DataLoader output available**: Latest parquet files in `agents/shared_db/DataLoaderAgent/newest`
- [ ] **Path annotations accessible**: `path_annotations.json` with correct file paths
- [ ] **Core datasets available**: productRecords, purchaseOrders, moldSpecificationSummary
- [ ] **Database schema file**: `database/databaseSchemas.json` with proper data type definitions
- [ ] **Validation logs available**: ValidationOrchestrator change logs (optional but recommended)
- [ ] **Write permissions**: Full access to `agents/shared_db/OrderProgressTracker/`
- [ ] **Python dependencies**: pandas, pyarrow, loguru, pathlib, datetime
- [ ] **Disk space**: At least 3x input data size for aggregations and Excel export

---

## Error Handling Scenarios

| Scenario | Data Load | Status Processing | Aggregation | Validation Integration | Final Status | Action Required |
|----------|-----------|-------------------|-------------|----------------------|--------------|-----------------|
| Happy Path | ✅ Success | ✅ Success | ✅ Success | ✅ Success | `success` | None |
| Missing Data | ❌ Failed | - | - | - | `failed` | Check DataLoader output |
| Schema Mismatch | ✅ Success | ❌ Failed | - | - | `failed` | Validate schema definitions |
| No Production | ✅ Success | ❌ Failed | ❌ Failed | ✅ Success | `failed` | Check production records |
| Validation Missing | ✅ Success | ✅ Success | ✅ Success | ⚠️ Warning | `partial_success` | Check ValidationOrchestrator |
| Shift Logic Error | ✅ Success | ⚠️ Warning | ✅ Success | ✅ Success | `partial_success` | Review shift mappings |

---

## Processing Pipeline

### Step-by-Step Workflow

```
Data Loading → Order Merging → Production Extraction → Status Processing → 
Pause Detection → Latest Info → Warning Integration → Excel Export
```

**Detailed Steps**:

1. **Data Loading & Validation**
   - Load productRecords, purchaseOrders, moldSpecificationSummary from parquet
   - Validate schema compliance using decorator
   - Check file existence and data integrity

2. **Order Information Merging**
   - Merge purchase orders with mold specifications on itemCode
   - Create comprehensive order baseline with delivery schedules

3. **Production Data Extraction**
   - Separate working vs non-working production records
   - Identify currently producing orders from latest shift analysis
   - Create aggregation mappings for all dimensions

4. **Production Status Processing**
   - Calculate remaining quantities and completion rates
   - Apply status logic (PENDING/MOLDING/MOLDED)
   - Determine ETA compliance status
   - Handle data type conversions and formatting

5. **Pause Detection Analysis**
   - Compare pending orders against latest shift activity
   - Mark stalled production as PAUSED status
   - Update status based on production timeline gaps

6. **Latest Information Retrieval**
   - Extract most recent machine and mold assignments
   - Provide current production context for active orders

7. **Validation Warning Integration**
   - Read ValidationOrchestrator change logs
   - Aggregate and map validation warnings to production orders
   - Add warning notes to production status records

8. **Multi-Sheet Excel Export**
   - Generate comprehensive production dashboard
   - Create detailed analysis sheets for each dimension
   - Apply versioning and save with timestamp

---

## Input & Output

- **Input**: 
  - Dynamic datasets (productRecords, purchaseOrders)
  - Static reference data (moldSpecificationSummary)
  - Validation logs (change_log.txt)
  - Configuration files (path_annotations.json, databaseSchemas.json)
  
- **Output**: 
  - Multi-sheet Excel report with versioning
  - Structured dictionary with all analysis DataFrames
  - Comprehensive production status dashboard
  
- **Format**: 
  - Excel workbook with 6+ sheets
  - Versioned filename: `auto_status_v{N}.xlsx`
  - Hierarchical data structure for programmatic access

---

## Status Logic Engine

### Production Status Classification

```python
# Default state
proStatus = 'PENDING' 

# Completion check
if itemRemain == 0:
    proStatus = 'MOLDED'
    actualFinishedDate = endDate

# Active production check  
if poNo in producing_po_list and itemRemain > 0:
    proStatus = 'MOLDING'

# Stalled production check
if pending_order_not_active_in_latest_shift:
    proStatus = 'PAUSED'
```

### ETA Compliance Classification

```python
# Default state
etaStatus = 'PENDING'

# On-time delivery
if actualFinishedDate <= poETA and itemRemain == 0:
    etaStatus = 'ONTIME'

# Late delivery
if actualFinishedDate > poETA and itemRemain == 0:
    etaStatus = 'LATE'
```

### Shift Management System

| Shift Code | Start Time | Description |
|------------|------------|-------------|
| "1" | 06:00 | Morning Shift |
| "2" | 14:00 | Afternoon Shift |
| "3" | 22:00 | Night Shift |
| "HC" | 08:00 | Administrative Shift |

**Latest Shift Determination Logic**:
1. Combine recordDate + shift start time → precise timestamps
2. Find maximum timestamp across all production records
3. Extract orders active in this latest shift → "MOLDING" candidates
4. Compare pending orders against latest shift activity → "PAUSED" identification

---

## Directory Structure

```
agents/shared_db                                              
└── OrderProgressTracker/ 
    ├── historical_db/                                                                     
    ├── newest/                                                                                    
    |   └──  YYYYMMDD_HHMM_auto_status.xlsx                
    └── change_log.txt                                                       
```

---

## Data Schema & Output Structure

### Main Production Status Fields

```python
pro_status_fields = [
    # Order Information
    'poReceivedDate', 'poNo', 'itemCode', 'itemName', 'poETA', 'itemQuantity',
    
    # Progress Tracking  
    'itemRemain', 'startedDate', 'actualFinishedDate', 'proStatus', 'etaStatus',
    
    # Production Context
    'machineHist', 'itemType', 'moldList', 'moldHist', 'moldCavity', 
    'totalMoldShot', 'totalDay', 'totalShift',
    
    # Material Information
    'plasticResinCode', 'colorMasterbatchCode', 'additiveMasterbatchCode',
    
    # Analysis Mappings
    'moldShotMap', 'machineQuantityMap', 'dayQuantityMap', 'shiftQuantityMap', 
    'materialComponentMap'
]
```

### Excel Output Sheets

| Sheet Name | Content | Purpose |
|------------|---------|---------|
| **productionStatus** | Main dashboard with all KPIs | Executive overview and status monitoring |
| **materialComponentMap** | Material usage breakdown by PO | Quality control and inventory planning |
| **moldShotMap** | Mold utilization and shot counts | Maintenance planning and capacity analysis |
| **machineQuantityMap** | Machine productivity metrics | Performance monitoring and optimization |  
| **dayQuantityMap** | Daily production trends | Schedule planning and trend analysis |
| **notWorkingStatus** | Non-production records | Downtime analysis and efficiency tracking |
| **Validation Warnings** | Data quality issues | Quality assurance and data integrity |

→ See details: [Data Structure](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/agents_output_overviews/orderProgressTracker_output_overviews.md)
---

## Dependencies

- **DataLoaderAgent**: Provides processed parquet files with production and order data
- **ValidationOrchestrator**: Supplies data quality warnings and validation results
- **Database Schema**: Ensures consistent data types and field definitions
- **External Libraries**: pandas (data processing), loguru (logging), pathlib (file management)

---

## How to Run

### Basic Usage

```python
# Initialize tracker
tracker = OrderProgressTracker()

# Run complete analysis
result = tracker.pro_status()

# Access specific analysis
production_status = result['productionStatus']
material_analysis = result['materialComponentMap']
```

### Custom Configuration

```python
# Custom paths and settings
tracker = OrderProgressTracker(
    source_path="custom/data/path",
    databaseSchemas_path="custom/schemas.json",
    folder_path="custom/validation/logs",
    default_dir="custom/output"
)

# Run with custom parameters
result = tracker.pro_status()
```

### Development/Testing Mode

```python
# Enable debug logging
from loguru import logger
logger.add("debug.log", level="DEBUG")

# Initialize and run
tracker = OrderProgressTracker()
result = tracker.pro_status()

# Inspect intermediate results
print(f"Processing completed: {len(result)} output sheets")
```

---

## Result Structure

```python
{
    # Main production dashboard
    "productionStatus": pd.DataFrame,  # Complete status with 25+ columns
    
    # Detailed analysis breakdowns  
    "materialComponentMap": pd.DataFrame,  # Material usage by PO
    "moldShotMap": pd.DataFrame,           # Mold performance analysis
    "machineQuantityMap": pd.DataFrame,    # Machine productivity
    "dayQuantityMap": pd.DataFrame,        # Daily production trends
    
    # Supporting data
    "notWorkingStatus": pd.DataFrame,      # Downtime records
    
    # Quality assurance (if available)
    "po_mismatch_warnings": pd.DataFrame   # Validation issues
}
```

---

## Configuration Paths

- **source_path**: `agents/shared_db/DataLoaderAgent/newest` (processed parquet files)
- **annotation_name**: `path_annotations.json` (file path mappings)  
- **databaseSchemas_path**: `database/databaseSchemas.json` (data type definitions)
- **folder_path**: `agents/shared_db/ValidationOrchestrator` (validation logs)
- **target_name**: `change_log.txt` (validation warning source)
- **default_dir**: `agents/shared_db` (base output directory)
- **output_dir**: `agents/shared_db/OrderProgressTracker` (Excel reports and logs)

---

## Monitoring & Alerts

### Key Performance Indicators

- **Production Efficiency**: Percentage of orders ONTIME vs LATE
- **Throughput**: Orders completed per day/shift
- **Machine Utilization**: Active machines vs total capacity  
- **Quality Issues**: Validation warnings per order
- **Pipeline Health**: Data freshness and processing success rates

### Operational Monitoring

- **Daily Reports**: Automated generation of production status
- **Exception Handling**: Structured logging for debugging and recovery
- **Data Quality**: Integration with ValidationOrchestrator for early issue detection
- **Historical Tracking**: Versioned reports for trend analysis and audit trails