# OrderProgressTracker

## 🎯 Overview

The `OrderProgressTracker` is a comprehensive production monitoring system that tracks manufacturing progress, analyzes production efficiency, and generates detailed status reports. It processes production records, purchase orders, and mold specifications to provide real-time insights into manufacturing operations.

### Core Capabilities
- **📊 Production Progress Tracking**: Monitor order completion status and remaining quantities
- **🏭 Resource Utilization Analysis**: Track machine and mold usage across shifts and days  
- **⏰ Schedule Performance Monitoring**: Compare actual vs. expected delivery dates
- **⚠️ Quality Issue Integration**: Incorporate validation warnings from quality control systems
- **📈 Multi-dimensional Reporting**: Generate comprehensive Excel reports with multiple analytical views

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              DATA SOURCES                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│  📊 productRecords_df          📋 purchaseOrders_df                        │
│  (Production Records)          (Purchase Orders)                            │
│                                                                             │
│  🔧 moldSpecificationSummary_df   ⚠️ ValidationOrchestrator                │
│  (Mold Specifications)            (Quality Warnings)                       │
└─────────────────────┬───────────────────┬───────────────────────────────────┘
                      │                   │
                      ▼                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        🎯 OrderProgressTracker                             │
│                         (Main Processing Engine)                           │
│                                                                             │
│  • Data Integration & Validation                                           │
│  • Production Status Analysis                                              │
│  • Resource Utilization Tracking                                          │
│  • Quality Warning Integration                                             │
└─────────────────────┬───────────────────┬───────────────────────────────────┘
                      │                   │
                      ▼                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            OUTPUT PRODUCTS                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│  📊 Multi-Sheet Excel Report     🔌 Structured Data Dictionary             │
│  (Production Dashboard)          (API Integration)                         │
│                                                                             │
│  • Production Status Overview    • JSON/Dict Format                        │
│  • Resource Analysis Sheets      • Programmatic Access                     │
│  • Quality Warning Reports       • Real-time Integration                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Detailed Processing Workflow

### Phase 1: System Initialization

```
    🚀 OrderProgressTracker.__init__()
                    │
                    ▼
    ┌─────────────────────────────────────┐
    │     📂 Load Configuration Files     │
    │  • path_annotations.json            │
    │  • databaseSchemas.json             │
    └─────────────────┬───────────────────┘
                      │
                      ▼
    ┌─────────────────────────────────────┐
    │      🔍 Validate File Paths         │
    │  • Check file existence             │
    │  • Verify read permissions          │
    └─────────────────┬───────────────────┘
                      │
                      ▼
    ┌─────────────────────────────────────┐
    │      📊 Load Core Datasets          │
    │  • productRecords_df                │
    │  • purchaseOrders_df                │
    │  • moldSpecificationSummary_df      │
    └─────────────────┬───────────────────┘
                      │
                      ▼
    ┌─────────────────────────────────────┐
    │     ✅ Schema Validation            │
    │  • Column presence check            │
    │  • Data type validation             │
    │  • @validate_init_dataframes        │
    └─────────────────┬───────────────────┘
                      │
                      ▼
    ┌─────────────────────────────────────┐
    │   ⚙️ Setup Processing Parameters    │
    │  • Shift mapping configuration      │
    │  • Data type definitions            │
    │  • Output field specifications      │
    └─────────────────────────────────────┘
```

**Key Components:**
- **Configuration Management**: Load database schemas and file path annotations
- **Data Validation**: Ensure all required files exist and schemas match
- **Shift Mapping Setup**: Configure production shift start times
- **Data Type Definitions**: Set up column types for consistent processing

### Phase 2: Production Data Processing

```
                    🎯 pro_status() Method Called
                                │
                                ▼
    ┌─────────────────────────────────────────────────────────────────────────┐
    │                     Step 1: Data Integration                            │
    │  📋 Merge: purchaseOrders + moldSpecificationSummary                   │
    │  📊 Result: ordersInfo_df (comprehensive order information)            │
    └─────────────────────────┬───────────────────────────────────────────────┘
                              │
                              ▼
    ┌─────────────────────────────────────────────────────────────────────────┐
    │                   Step 2: Production Record Analysis                   │
    │  🔍 _extract_product_records()                                         │
    │                                                                         │
    │  Input Processing:                                                      │
    │  • Separate working vs non-working records                             │
    │  • Calculate shift start timestamps                                    │
    │  • Identify currently producing orders                                 │
    │                                                                         │
    │  Aggregation Metrics:                                                  │
    │  • moldedQuantity, totalMoldShot, startedDate, endDate                │
    │  • totalDay, totalShift, machineHist, moldHist                        │
    │                                                                         │
    │  Mapping Dictionaries:                                                 │
    │  • moldShotMap, machineQuantityMap, dayQuantityMap                     │
    │  • shiftQuantityMap, materialComponentMap                              │
    └─────────────────────────┬───────────────────────────────────────────────┘
                              │
                              ▼
    ┌─────────────────────────────────────────────────────────────────────────┐
    │                   Step 3: Status Classification                        │
    │  🏷️ _pro_status_processing()                                           │
    │                                                                         │
    │  Production Status Logic:                                               │
    │  • PENDING: Not started or paused                                      │
    │  • MOLDING: Currently in production                                    │
    │  • MOLDED: Production completed                                        │
    │                                                                         │
    │  ETA Performance Analysis:                                              │
    │  • ONTIME: Completed ≤ ETA                                            │
    │  • LATE: Completed > ETA                                               │
    │  • PENDING: Not yet completed                                          │
    └─────────────────────────┬───────────────────────────────────────────────┘
                              │
                              ▼
    ┌─────────────────────────────────────────────────────────────────────────┐
    │                  Step 4: Temporal Analysis Enhancement                 │
    │  ⏰ _mark_paused_pending_pos() + _get_latest_po_info()                 │
    │                                                                         │
    │  • Detect production gaps and mark stalled POs as 'PAUSED'            │
    │  • Get most recent machine and mold assignments                        │
    │  • Track production continuity across shifts                           │
    └─────────────────────────┬───────────────────────────────────────────────┘
                              │
                              ▼
    ┌─────────────────────────────────────────────────────────────────────────┐
    │                   Step 5: Quality Warning Integration                  │
    │  ⚠️ _get_change() + _add_warning_notes_column()                        │
    │                                                                         │
    │  • Read ValidationOrchestrator change logs                             │
    │  • Extract latest Excel file with quality warnings                     │
    │  • Load po_mismatch_warnings and aggregate by PO                       │
    │  • Add warningNotes column to production status                        │
    └─────────────────────────┬───────────────────────────────────────────────┘
                              │
                              ▼
    ┌─────────────────────────────────────────────────────────────────────────┐
    │                  Step 6: Multi-View Report Generation                  │
    │  📊 _pro_status_fattening() + save_output_with_versioning()           │
    │                                                                         │
    │  Create Flattened Data Views:                                          │
    │  • materialComponentMap → Material usage analysis                      │
    │  • moldShotMap → Detailed mold utilization metrics                     │
    │  • machineQuantityMap → Production quantity by machine                 │
    │  • dayQuantityMap → Time-series production data                        │
    │                                                                         │
    │  Export Multi-Sheet Excel Report:                                      │
    │  • auto_status_YYYYMMDD_HHMMSS.xlsx                                   │
    │  • Multiple analytical worksheets                                      │
    └─────────────────────────────────────────────────────────────────────────┘
```

#### Step 1: Data Integration
```python
# Merge core datasets to create comprehensive order information
ordersInfo_df = merge(purchaseOrders + moldSpecificationSummary)
```

#### Step 2: Production Record Analysis
**Input Processing:**
- Separate productive vs. non-productive records
- Calculate shift start timestamps
- Identify currently producing orders

**Aggregation Metrics:**
```python
Production_Metrics = {
    'moldedQuantity': sum(itemGoodQuantity),
    'totalMoldShot': sum(moldShot),
    'startedDate': min(recordDate),
    'endDate': max(recordDate),
    'totalDay': count_unique(recordDate),
    'totalShift': count(dateShiftCombined)
}
```

**Mapping Dictionaries:**
- `moldShotMap`: Shots by mold per PO
- `machineQuantityMap`: Production by machine per PO  
- `dayQuantityMap`: Daily production totals
- `shiftQuantityMap`: Production by shift
- `materialComponentMap`: Material usage breakdown

#### Step 3: Production Status Classification

```
Production Status Flow:
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   PENDING   │ ───▶ │   MOLDING    │ ───▶ │   MOLDED    │
│(Not started)│      │(In progress) │      │ (Complete)  │
└─────────────┘      └──────┬───────┘      └─────────────┘
                            │
                            ▼
                     ┌─────────────┐
                     │   PAUSED    │
                     │(Stalled)    │
                     └─────────────┘

ETA Status Flow:
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   PENDING   │      │   ONTIME     │      │    LATE     │
│(Not complete)│      │(Finish ≤ ETA)│      │(Finish > ETA)│
└─────────────┘      └──────────────┘      └─────────────┘
```

**Status Definitions:**
- **PENDING**: Order received but production not started
- **MOLDING**: Currently in active production
- **PAUSED**: Production started but currently inactive
- **MOLDED**: Production completed

**Performance Indicators:**
- **ONTIME**: Delivered on or before ETA
- **LATE**: Delivered after ETA
- **PENDING**: Not yet completed

#### Step 4: Temporal Analysis Enhancement
- **Paused Order Detection**: Identify orders with production gaps
- **Latest Information Tracking**: Get most recent machine and mold assignments
- **Shift Timeline Analysis**: Track production continuity across shifts

#### Step 5: Quality Warning Integration
```
ValidationOrchestrator Pipeline:
┌─────────────────────┐    ┌──────────────────────┐    ┌─────────────────────┐
│  Read Change Log    │───▶│ Extract Latest Excel │───▶│  Load Warning       │
│  (change_log.txt)   │    │ File Path            │    │  Sheets             │
└─────────────────────┘    └──────────────────────┘    └──────┬──────────────┘
                                                              │
                                                              ▼
┌─────────────────────┐    ┌──────────────────────┐    ┌─────────────────────┐
│  Add Warning Notes  │◀───│   Aggregate by PO    │◀───│ Process po_mismatch │
│  to Production      │    │   (Group & Count)    │    │ _warnings Sheet     │
│  Status DataFrame   │    │                      │    │                     │
└─────────────────────┘    └──────────────────────┘    └─────────────────────┘
```

**Warning Processing:**
- Parse validation orchestrator output logs
- Extract mismatch warnings by PO
- Aggregate warning types and counts
- Append warning notes to production status

#### Step 6: Multi-View Report Generation

**Flattened Data Views:**
- **Material Component Analysis**: Break down material usage by PO
- **Mold Shot Analysis**: Detailed mold utilization metrics
- **Machine Performance**: Production quantity by machine
- **Daily Production**: Time-series production data

---

## 📊 Output Data Structure

### Excel Workbook Layout

```
📋 auto_status_YYYYMMDD_HHMMSS.xlsx
├── 📊 productionStatus          # Main production dashboard
│   ├── Order Information        # PO details, quantities, dates
│   ├── Production Metrics       # Progress, machine, mold data
│   ├── Status Classifications   # MOLDING/MOLDED/PENDING/PAUSED
│   ├── Performance Indicators   # ONTIME/LATE/PENDING
│   └── Quality Warnings         # Validation issues
├── 🧪 materialComponentMap      # Material usage analysis
├── 🔧 moldShotMap              # Mold utilization breakdown  
├── 🏭 machineQuantityMap       # Machine performance metrics
├── 📅 dayQuantityMap           # Daily production trends
├── ⚠️ notWorkingStatus         # Idle production records
└── 🚨 [Dynamic Warning Sheets]  # Quality control alerts
```

### Key Performance Indicators

**Per Purchase Order Metrics:**
```python
KPIs = {
    'completion_rate': (itemQuantity - itemRemain) / itemQuantity,
    'production_efficiency': moldedQuantity / totalMoldShot,
    'schedule_performance': actualFinishedDate vs poETA,
    'resource_utilization': len(machineHist), len(moldHist),
    'quality_score': absence of warningNotes
}
```

**Operational Dashboards:**
- **Production Status Summary**: Overview of all active orders
- **Resource Utilization**: Machine and mold efficiency metrics
- **Schedule Performance**: On-time delivery tracking
- **Quality Monitoring**: Warning trend analysis

---

## 🛡️ Error Handling & Data Quality

### Pre-Execution Validation
```python
Validation_Checks = [
    '✅ File path existence verification',
    '✅ Database schema compliance',
    '✅ Required column presence validation', 
    '✅ Data type compatibility checks',
    '✅ Referential integrity validation'
]
```

### Runtime Safety Mechanisms
```python
Safety_Features = [
    '🛡️ Empty DataFrame graceful handling',
    '🛡️ Missing value imputation strategies',
    '🛡️ Date parsing error recovery',
    '🛡️ Division by zero protection',
    '🛡️ Memory-efficient large dataset processing'
]
```

### Data Quality Monitoring
- **Completeness**: Track missing critical fields
- **Consistency**: Validate cross-table relationships  
- **Accuracy**: Flag potential data anomalies
- **Timeliness**: Monitor data freshness indicators

---

## 🔌 Integration Architecture

### Upstream Data Dependencies

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            DATA PROVIDERS                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  📊 DataLoaderAgent                  ⚠️ ValidationOrchestrator              │
│  ├─ productRecords_df                ├─ change_log.txt                      │
│  ├─ purchaseOrders_df                ├─ po_mismatch_warnings.xlsx          │
│  └─ moldSpecificationSummary_df      └─ quality validation reports         │
│                                                                             │
│  📋 DatabaseSchemas                                                         │
│  ├─ databaseSchemas.json                                                   │
│  ├─ Column definitions                                                      │
│  ├─ Data type specifications                                               │
│  └─ Validation rules                                                       │
│                                                                             │
└─────────────────────────┬───────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    🎯 OrderProgressTracker                                 │
│                      (Processing Engine)                                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Dependency Details:**
- **DataLoaderAgent**: Provides cleaned production records, purchase orders, and mold specifications
- **ValidationOrchestrator**: Supplies data quality warnings and mismatch alerts
- **DatabaseSchemas**: Defines data structure contracts and validation rules

### Downstream Integration Points

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    🎯 OrderProgressTracker                                 │
│                      (Report Generator)                                    │
└─────────────────────────┬───────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            CONSUMERS                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  📊 Production Managers              📈 Planning Systems                    │
│  ├─ Status Dashboards                ├─ Capacity Reports                   │
│  ├─ Progress Tracking                ├─ Resource Planning                  │
│  └─ Performance Metrics              └─ Scheduling Optimization            │
│                                                                             │
│  ⚠️ Quality Control                  🔌 External APIs                      │
│  ├─ Warning Analysis                 ├─ Data Integration                   │
│  ├─ Trend Monitoring                 ├─ Real-time Updates                 │
│  └─ Issue Tracking                   └─ Third-party Systems               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 💻 Usage Examples

### Basic Implementation
```python
# Standard production report generation
tracker = OrderProgressTracker()
report_data = tracker.pro_status()

# Output: agents/shared_db/OrderProgressTracker/auto_status_YYYYMMDD_HHMMSS.xlsx
```

### Custom Configuration
```python
# Custom paths and settings
tracker = OrderProgressTracker(
    source_path='custom/data/path',
    databaseSchemas_path='custom/schema.json',
    default_dir='custom/output/directory'
)
production_report = tracker.pro_status()
```

### API Integration
```python
# Access structured data for API responses
tracker = OrderProgressTracker()
data = tracker.pro_status()

# Available data components:
api_response = {
    'production_status': data['productionStatus'],
    'material_analysis': data['materialComponentMap'],
    'machine_performance': data['machineQuantityMap'],
    'quality_warnings': data.get('po_mismatch_warnings', {})
}
```

---

## 📈 Performance Considerations

### Optimization Features
- **Vectorized Operations**: Pandas-optimized data transformations
- **Memory Management**: Efficient handling of large production datasets
- **Parallel Processing**: Concurrent aggregation calculations where applicable
- **Lazy Loading**: On-demand data loading for improved startup times

### Scalability Metrics
- **Data Volume**: Handles 100k+ production records efficiently
- **Processing Time**: Sub-minute report generation for typical datasets
- **Memory Usage**: Optimized for production server deployment
- **Concurrent Users**: Thread-safe design for multi-user environments

---

## 🔧 Maintenance & Troubleshooting

### Common Issues & Solutions

| Issue | Symptom | Solution |
|-------|---------|----------|
| Missing Data Files | FileNotFoundError | Verify path_annotations.json accuracy |
| Schema Mismatch | Validation Error | Update databaseSchemas.json |
| Empty Reports | No production data | Check productRecords_df data quality |
| Performance Issues | Slow processing | Optimize data filtering and indexing |

### Monitoring Recommendations
- **Log Analysis**: Regular review of processing logs for warnings
- **Data Quality Checks**: Automated validation of input data completeness
- **Performance Tracking**: Monitor processing times and resource usage
- **Output Validation**: Verify report accuracy with known test cases

---

## 📚 Technical Reference

### Key Constants & Configurations
```python
SHIFT_MAPPINGS = {
    "1": "06:00",  # Morning shift
    "2": "14:00",  # Afternoon shift  
    "3": "22:00",  # Night shift
    "HC": "08:00"  # Administrative shift
}

OUTPUT_FIELDS = [
    'poReceivedDate', 'poNo', 'itemCode', 'itemName', 'poETA',
    'itemQuantity', 'itemRemain', 'proStatus', 'etaStatus',
    'machineHist', 'moldHist', 'totalMoldShot', 'warningNotes'
]
```

### Data Type Specifications
- **Datetime Fields**: Converted to 'YYYY-MM-DD' string format
- **Quantity Fields**: Int64 with null handling
- **Mapping Fields**: Object type storing Python dictionaries
- **Status Fields**: String categoricals with predefined values