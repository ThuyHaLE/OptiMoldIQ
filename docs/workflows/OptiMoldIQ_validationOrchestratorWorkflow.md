# ValidationOrchestrator Workflow

## I. High-Level Architecture

```
                            ┌─────────────────────────────────────┐
                            │      ValidationOrchestrator         │
                            │   (Main Coordinator Agent)          │
                            └─────────────────────────────────────┘
                                           │
                            ┌──────────────┼──────────────┐
                            │              │              │
                            ▼              ▼              ▼
                ┌──────────────────┐ ┌──────────────┐ ┌──────────────────┐
                │ StaticValidator  │ │ POValidator  │ │ DynamicValidator │
                │   (Agent 1)      │ │  (Agent 2)   │ │   (Agent 3)      │
                └──────────────────┘ └──────────────┘ └──────────────────┘
                            │              │              │
                            └──────────────┼──────────────┘
                                           │
                                           ▼
                                 ┌─────────────────┐
                                 │ Results Merger  │
                                 │ & Excel Export  │
                                 └─────────────────┘
```

## II. Data Flow Overview

### Phase 1: Initialization & Data Loading
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           INITIALIZATION PHASE                             │
│                                                                             │
│ 1. Load Configuration Files                                                 │
│    ├── databaseSchemas.json (Column definitions)                           │
│    └── path_annotations.json (File locations)                              │
│                                                                             │
│ 2. Load Data Files (8 Parquet Files)                                       │
│    ├── Dynamic Data:                                                       │
│    │   ├── productRecords.parquet                                          │
│    │   └── purchaseOrders.parquet                                          │
│    └── Static Reference Data:                                              │
│        ├── itemInfo.parquet                                                │
│        ├── resinInfo.parquet                                               │
│        ├── machineInfo.parquet                                             │
│        ├── moldInfo.parquet                                                │
│        ├── moldSpecificationSummary.parquet                                │
│        └── itemCompositionSummary.parquet                                  │
│                                                                             │
│ 3. Schema Validation (@validate_init_dataframes)                           │
│    └── Ensure all required columns exist                                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Phase 2: Parallel Validation Execution
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          VALIDATION PHASE                                  │
│                                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐            │
│  │ StaticValidator │  │   POValidator   │  │DynamicValidator │            │
│  │                 │  │                 │  │                 │            │
│  │ Validates:      │  │ Validates:      │  │ Validates:      │            │
│  │ • Item codes    │  │ • PO existence  │  │ • Cross-refs    │            │
│  │ • Resin codes   │  │ • Field matches │  │ • Logic rules   │            │
│  │ • Compositions  │  │ • Data quality  │  │ • Consistency   │            │
│  │                 │  │                 │  │                 │            │
│  │ ↓ Outputs:      │  │ ↓ Outputs:      │  │ ↓ Outputs:      │            │
│  │ Static warnings │  │ PO warnings     │  │Dynamic warnings │            │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘            │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Phase 3: Results Consolidation
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        CONSOLIDATION PHASE                                 │
│                                                                             │
│ Input: 3 Warning DataFrames                                                 │
│ ├── Static warnings (from Agent 1)                                         │
│ ├── PO warnings (from Agent 2)                                             │
│ └── Dynamic warnings (from Agent 3)                                        │
│                                                                             │
│ Process:                                                                    │
│ 1. Merge all warnings into unified format                                  │
│ 2. Add metadata (timestamp, severity, source)                              │
│ 3. Generate summary statistics                                              │
│                                                                             │
│ Output:                                                                     │
│ └── Excel file with versioning (validation_orchestrator_v{N}.xlsx)         │
└─────────────────────────────────────────────────────────────────────────────┘
```

## III. Detailed Agent Workflows

### Agent 1: StaticCrossDataChecker
```
┌─────────────────────────────────────────────────────────────────────┐
│                        StaticValidator Workflow                     │
│                                                                     │
│ Input: productRecords + purchaseOrders + Static Reference Data     │
│                                                                     │
│ For each dataset (productRecords, purchaseOrders):                 │
│                                                                     │
│ Step 1: Data Preprocessing                                          │
│ ├── Rename poNote → poNo                                           │
│ ├── Remove null values                                              │
│ └── Standardize data types                                          │
│                                                                     │
│ Step 2: Item Validation                                             │
│ ├── Check (itemCode + itemName) exists in itemInfo                 │
│ └── Generate warnings for mismatches                                │
│                                                                     │
│ Step 3: Resin Validation                                            │
│ ├── Validate plasticResin against resinInfo                        │
│ ├── Validate colorMasterbatch against resinInfo                    │
│ ├── Validate additiveMasterbatch against resinInfo                 │
│ └── Generate warnings for each mismatch                             │
│                                                                     │
│ Step 4: Composition Validation                                      │
│ ├── Build full composition string                                   │
│ ├── Check against itemCompositionSummary                           │
│ └── Generate warnings for invalid compositions                      │
│                                                                     │
│ Output: DataFrame with columns:                                     │
│ [poNo, warningType, mismatchType, requiredAction, message]         │
└─────────────────────────────────────────────────────────────────────┘
```

### Agent 2: PORequiredCriticalValidator
```
┌─────────────────────────────────────────────────────────────────────┐
│                       POValidator Workflow                          │
│                                                                     │
│ Input: productRecords + purchaseOrders                             │
│                                                                     │
│ Step 1: Data Preparation                                            │
│ ├── Clean productRecords (rename poNote → poNo)                    │
│ ├── Remove records with null poNo                                   │
│ └── Identify overlapping columns between datasets                   │
│                                                                     │
│ Step 2: PO Existence Check                                          │
│ ├── Find PO numbers in productRecords                              │
│ ├── Check if they exist in purchaseOrders                          │
│ └── Generate warnings for missing POs                               │
│                                                                     │
│ Step 3: Field Consistency Check                                     │
│ ├── Merge datasets on poNo                                         │
│ ├── Compare overlapping fields (vectorized)                        │
│ ├── Identify mismatched values                                      │
│ └── Generate warnings with context                                  │
│                                                                     │
│ Step 4: Results Compilation                                         │
│ ├── Combine existence + consistency warnings                        │
│ ├── Add metadata (date, shift, machineNo)                          │
│ └── Format consistent warning structure                             │
│                                                                     │
│ Output: DataFrame with structured warnings                          │
└─────────────────────────────────────────────────────────────────────┘
```

### Agent 3: DynamicCrossDataValidator
```
┌─────────────────────────────────────────────────────────────────────┐
│                    DynamicValidator Workflow                        │
│                                                                     │
│ Input: productRecords + Machine/Mold/Composition References        │
│                                                                     │
│ Step 1: Production Data Preparation                                 │
│ ├── Filter out records with null poNote                            │
│ ├── Generate item_composition from resin components                 │
│ └── Merge with machineInfo for tonnage data                        │
│                                                                     │
│ Step 2: Reference Data Preparation                                  │
│ ├── Build mold-machine compatibility matrix                        │
│ ├── Create item-composition lookup table                           │
│ └── Generate valid combinations reference                           │
│                                                                     │
│ Step 3: Multi-Level Validation                                      │
│ ├── Level 1: Item Code/Name validation                             │
│ ├── Level 2: Item-Mold compatibility                               │
│ ├── Level 3: Mold-Machine tonnage matching                         │
│ └── Level 4: Item composition consistency                           │
│                                                                     │
│ Step 4: Invalid Data Detection                                      │
│ ├── Check for null values in critical columns                      │
│ ├── Identify incomplete records                                     │
│ └── Flag data quality issues                                        │
│                                                                     │
│ Output: Two DataFrames                                              │
│ ├── invalid_warnings: Data quality issues                          │
│ └── mismatch_warnings: Logic consistency issues                     │
└─────────────────────────────────────────────────────────────────────┘
```

## IV. Data Structure Standards

### Common Warning Format
All agents output warnings in this standardized format:

| Column | Description | Example |
|--------|-------------|---------|
| `poNo` | Purchase Order Number | "PO-2024-001" |
| `warningType` | Category of warning | "STATIC_MISMATCH" |
| `mismatchType` | Specific issue type | "ITEM_CODE_INVALID" |
| `requiredAction` | Recommended fix | "UPDATE_ITEM_MASTER" |
| `message` | Detailed description | "Item ABC123 not found in itemInfo" |
| `severity` | Issue priority | "HIGH", "MEDIUM", "LOW" |
| `source_agent` | Which agent found it | "StaticValidator" |
| `timestamp` | When found | "2024-01-15 10:30:00" |

### Results Structure
```python
final_results = {
    'static_mismatch': {
        'purchaseOrders': DataFrame,    # Issues in PO data vs static refs
        'productRecords': DataFrame     # Issues in production vs static refs
    },
    'po_required_mismatch': DataFrame,  # PO existence and field issues
    'dynamic_mismatch': {
        'invalid_items': DataFrame,     # Data quality issues
        'info_mismatches': DataFrame    # Logic consistency issues
    },
    'combined_all': {
        'item_invalid_warnings': DataFrame,  # All data quality issues
        'po_mismatch_warnings': DataFrame    # All PO-related issues
    },
    'summary_stats': {
        'total_warnings': int,
        'warnings_by_type': dict,
        'warnings_by_severity': dict
    }
}
```

## V. Execution Flow

### Sequential Steps
1. **Initialize** → Load configs and validate schemas
2. **Load Data** → Read all 8 parquet files into memory
3. **Run Validations** → Execute 3 agents in parallel (if possible)
4. **Merge Results** → Combine warnings into unified structure
5. **Generate Report** → Create Excel output with versioning
6. **Log Summary** → Record execution statistics

### Error Handling Strategy
```
┌─────────────────────────────────────────────────────────────────┐
│                    Error Handling Flow                          │
│                                                                 │
│ Level 1: File Loading Errors                                   │
│ ├── Missing parquet files → Stop execution, log error          │
│ ├── Schema validation fails → Stop execution, log details      │
│ └── Permission issues → Stop execution, suggest fix            │
│                                                                 │
│ Level 2: Agent Execution Errors                                │
│ ├── Agent fails → Continue with other agents, log warning      │
│ ├── Partial data → Process available data, flag incomplete     │
│ └── Memory issues → Implement chunking, reduce batch size      │
│                                                                 │
│ Level 3: Output Generation Errors                              │
│ ├── Excel write fails → Try alternative format, log error     │
│ ├── Directory issues → Create directories, retry               │
│ └── Versioning conflicts → Auto-increment, warn user           │
└─────────────────────────────────────────────────────────────────┘
```

## VI. Performance Optimization

### Memory Management
- **Lazy Loading**: Load data only when needed
- **Chunked Processing**: Process large datasets in chunks
- **Memory Cleanup**: Delete intermediate DataFrames after use
- **Efficient Joins**: Use appropriate join strategies

### Parallel Execution
- Run agents independently when possible
- Use threading for I/O operations
- Implement timeout mechanisms
- Monitor resource usage

### Caching Strategy
- Cache static reference data
- Reuse loaded schemas across agents
- Implement result caching for repeated runs
- Store intermediate results for debugging

## VII. Monitoring & Alerts

### Key Metrics
- **Execution Time**: Total and per-agent timing
- **Warning Counts**: By type and severity
- **Data Quality Score**: Percentage of clean records
- **Success Rate**: Completed validations vs total

### Alert Conditions
- High error count (>threshold)
- Execution time exceeds limit
- Critical validations fail
- Data pipeline interrupted