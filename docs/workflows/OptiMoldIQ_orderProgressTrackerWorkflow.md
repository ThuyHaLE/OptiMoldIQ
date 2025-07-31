# OrderProgressTracker Workflow Documentation

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           OrderProgressTracker                              │
│                         Production Status Pipeline                          │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        🔧 INITIALIZATION PHASE                              │
├─────────────────────────────────────────────────────────────────────────────┤
│ • Load configuration files (schemas, annotations)                           │
│ • Validate and load 3 core datasets                                        │
│ • Setup shift mappings and data type definitions                           │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      📊 DATA PROCESSING PIPELINE                           │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Detailed Workflow Steps

### Phase 1: Initialization & Data Loading

```
┌──────────────────────────────────────┐
│        Class Constructor             │
│    OrderProgressTracker()           │
└──────────────┬───────────────────────┘
               │
               ├─ Load path_annotations.json
               ├─ Load databaseSchemas.json
               ├─ Validate file paths
               │
               ▼
┌──────────────────────────────────────┐
│     Load Core Datasets              │
├──────────────────────────────────────┤
│ 📄 productRecords_df                │
│ 📄 purchaseOrders_df                │
│ 📄 moldSpecificationSummary_df      │
└──────────────┬───────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│   @validate_init_dataframes          │
│   Schema Validation                  │
└──────────────────────────────────────┘
```

### Phase 2: Production Status Processing

```
                    pro_status() Method Called
                            │
                            ▼
    ┌────────────────────────────────────────────────────────┐
    │                 Step 1: Data Merging                   │
    │ Merge: purchaseOrders + moldSpecificationSummary       │
    │ Result: ordersInfo_df                                  │
    └────────────────────┬───────────────────────────────────┘
                         │
                         ▼
    ┌────────────────────────────────────────────────────────┐
    │              Step 2: Extract Production Records        │
    │ Method: _extract_product_records()                     │
    ├────────────────────────────────────────────────────────┤
    │ 🔍 Separate working vs non-working records             │
    │ 📈 Compute production aggregations:                    │
    │    • moldedQuantity, totalMoldShot                     │
    │    • startedDate, endDate, totalDay, totalShift       │
    │    • machineHist, moldHist, moldCavity                 │
    │ 🗺️  Create mapping dictionaries:                       │
    │    • moldShotMap, machineQuantityMap                   │
    │    • dayQuantityMap, shiftQuantityMap                  │
    │    • materialComponentMap                              │
    │ 📋 Identify currently producing POs                    │
    └────────────────────┬───────────────────────────────────┘
                         │
                         ▼
    ┌────────────────────────────────────────────────────────┐
    │              Step 3: Status Processing                 │
    │ Method: _pro_status_processing()                       │
    ├────────────────────────────────────────────────────────┤
    │ 🧮 Calculate itemRemain = itemQuantity - moldedQuantity│
    │ 🏷️  Determine proStatus:                               │
    │    • PENDING: Not started or paused                    │
    │    • MOLDING: Currently in production                  │
    │    • MOLDED: Production completed                      │
    │ ⏰ Determine etaStatus:                                │
    │    • PENDING: Not completed yet                        │
    │    • ONTIME: Completed ≤ ETA                          │
    │    • LATE: Completed > ETA                            │
    │ 🔧 Apply data type conversions                         │
    │ 📅 Format datetime fields                              │
    └────────────────────┬───────────────────────────────────┘
                         │
                         ▼
    ┌────────────────────────────────────────────────────────┐
    │              Step 4: Paused Status Detection           │
    │ Method: _mark_paused_pending_pos()                     │
    ├────────────────────────────────────────────────────────┤
    │ 🔍 Identify POs with production gaps                   │
    │ 🏷️  Mark stalled POs as 'PAUSED'                       │
    └────────────────────┬───────────────────────────────────┘
                         │
                         ▼
    ┌────────────────────────────────────────────────────────┐
    │              Step 5: Latest Info Enrichment           │
    │ Method: _get_latest_po_info()                          │
    ├────────────────────────────────────────────────────────┤
    │ 🕐 Get latest machine and mold info per PO             │
    │ 📊 Add: lastestMachineNo, lastestMoldNo               │
    └────────────────────┬───────────────────────────────────┘
                         │
                         ▼
    ┌────────────────────────────────────────────────────────┐
    │              Step 6: Warning Integration               │
    │ Methods: _get_change() + _add_warning_notes_column()   │
    ├────────────────────────────────────────────────────────┤
    │ 📂 Read ValidationOrchestrator change log              │
    │ 📄 Extract latest Excel file path                      │
    │ ⚠️  Load po_mismatch_warnings sheet                    │
    │ 🏷️  Add warningNotes column to production status       │
    └────────────────────┬───────────────────────────────────┘
                         │
                         ▼
    ┌────────────────────────────────────────────────────────┐
    │              Step 7: Data Preparation                  │
    │ Method: _pro_status_fattening()                        │
    ├────────────────────────────────────────────────────────┤
    │ 📊 Create flattened views for Excel export:            │
    │    • materialComponentMap → Material breakdown         │
    │    • moldShotMap → Shot analysis by mold              │
    │    • machineQuantityMap → Production by machine       │
    │    • dayQuantityMap → Daily production summary        │
    └────────────────────┬───────────────────────────────────┘
                         │
                         ▼
    ┌────────────────────────────────────────────────────────┐
    │              Step 8: Excel Export                      │
    │ Method: save_output_with_versioning()                  │
    ├────────────────────────────────────────────────────────┤
    │ 📁 Output Directory: agents/shared_db/OrderProgressTracker │
    │ 📊 Create multi-sheet Excel file:                      │
    │    • productionStatus (main report)                    │
    │    • materialComponentMap                              │
    │    • moldShotMap                                       │
    │    • machineQuantityMap                                │
    │    • dayQuantityMap                                    │
    │    • notWorkingStatus                                  │
    │    • [warning sheets if available]                     │
    │ 🏷️  Filename: auto_status_YYYYMMDD_HHMMSS.xlsx        │
    └────────────────────────────────────────────────────────┘
```

## Key Data Transformations

### Input Data Sources
```
productRecords_df     ──┐
                        ├─► Production Analysis
purchaseOrders_df     ──┤
                        │
moldSpecificationSummary_df ──┘
```

### Status Determination Logic
```
Production Status Flow:
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│   PENDING   │───▶│   MOLDING    │───▶│   MOLDED    │
│(Not started)│    │(In progress) │    │ (Complete)  │
└─────────────┘    └──────┬───────┘    └─────────────┘
                          │
                          ▼
                   ┌─────────────┐
                   │   PAUSED    │
                   │(Stalled)    │
                   └─────────────┘

ETA Status Logic:
• actualFinishedDate ≤ poETA → ONTIME
• actualFinishedDate > poETA → LATE  
• No actualFinishedDate → PENDING
```

## Output Structure

### Excel File Organization
```
📋 auto_status_YYYYMMDD_HHMMSS.xlsx
├── 📊 productionStatus (Main dashboard)
├── 🧪 materialComponentMap (Material analysis)
├── 🔧 moldShotMap (Mold utilization)
├── 🏭 machineQuantityMap (Machine performance)
├── 📅 dayQuantityMap (Daily production)
├── ⚠️ notWorkingStatus (Idle records)
└── 🚨 [Warning sheets] (Validation issues)
```

### Key Performance Indicators
```
For each Purchase Order:
├── 📊 Production Progress: itemRemain / itemQuantity
├── ⏱️ Production Duration: totalDay, totalShift
├── 🔧 Resource Utilization: machineHist, moldHist
├── 📅 Schedule Performance: proStatus, etaStatus
└── ⚠️ Quality Issues: warningNotes
```

## Error Handling & Validation

### Pre-execution Checks
- ✅ File path validation
- ✅ Schema compliance verification
- ✅ Required column presence
- ✅ Data type compatibility

### Runtime Safety
- 🛡️ Empty DataFrame handling
- 🛡️ Missing value management
- 🛡️ Date parsing error recovery
- 🛡️ Division by zero protection

## Usage Example

```python
# Initialize tracker with default settings
tracker = OrderProgressTracker()

# Generate comprehensive production report
tracker.pro_status()

# Output saved automatically to:
# agents/shared_db/OrderProgressTracker/auto_status_YYYYMMDD_HHMMSS.xlsx
```

## Integration Points

### Upstream Dependencies
- **DataLoaderAgent**: Provides core production datasets
- **ValidationOrchestrator**: Supplies quality warnings
- **Database Schemas**: Defines data structure contracts

### Downstream Consumers
- **Production Managers**: Status dashboards
- **Quality Control**: Warning analysis
- **Planning Systems**: Capacity utilization reports