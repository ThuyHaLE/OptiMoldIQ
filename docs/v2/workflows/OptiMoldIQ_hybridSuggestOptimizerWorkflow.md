>Status: Inherited from v1  
>No structural or behavioral changes in v2.

# HybridSuggestOptimizer

## 1. Overview

The **HybridSuggestOptimizer** is a sophisticated optimization engine that combines historical data analysis with real-time compatibility matching to suggest optimal mold-machine configurations for manufacturing operations. It orchestrates capacity estimation, priority matrix calculation, and provides comprehensive optimization results with data quality validation.

---

## 2. Architecture

### 2.1 Core Components

1. **HybridSuggestOptimizer** -- Main optimization coordinator class
2. **ItemMoldCapacityOptimizer** -- Capacity estimation engine using historical data
3. **MoldMachinePriorityMatrixCalculator** -- Priority matrix generation with feature weights
4. **FeatureWeights** -- Configuration management for optimization parameters
5. **OptimizationResult** -- Structured container for optimization outputs

### 2.2 Two-Phase Optimization Workflow

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                           [ HybridSuggestOptimizer ]                                           │
│                   Orchestrates the complete optimization process                               │
└───────────────────────────────────────┬─────────────────────────────────────────────────────────┘
                ┌───────────────────────┴─────────────────────────────────────────┐
                ▼ Phase 1                                                         ▼                 
        ┌──────────────────────┐                                        ┌──────────────────────┐
        │ ItemMoldCapacity     │                                        │ MoldMachinePriority  │
        │ Optimizer            │────── Phase 2 ───────────────────────⯈│ MatrixCalculator     │
        └──────────────────────┘                                        └──────────────────────┘
               │                                                                        │
               ▼                                                                        ▼
    📊 Estimate Mold Capacities                                          🎯 Calculate Priority Matrix
    • Load stability index data                                           • Apply feature weights
    • Analyze historical performance                                      • Compute compatibility scores
    • Calculate theoretical/effective capacity                            • Generate mold-machine rankings
    • Validate capacity estimates                                         • Identify optimal pairings
```

### 2.3 Detailed Phase Breakdown

#### Phase 1: Mold Capacity Estimation

  ----------------------------------------------------------------------------------------------------------
  Step         Process                                  Details
  ------------ ---------------------------------------- ----------------------------------------------------
  1            Load Stability Index                     Process mold stability metrics from historical data

  2            Historical Data Analysis                 Analyze cavity rates, cycle times, NG rates

  3            Capacity Calculation                     Compute theoretical, effective, and balanced capacity

  4            Quality Validation                       Identify invalid molds based on data quality

  5            Output Generation                        Generate capacity
                                                        DataFrame with metadata
  -----------------------------------------------------------------------------------------------------------

**Success Criteria:** Valid capacity estimates with quality metrics.
**Failure Modes:** Missing stability data, corrupted historical records, schema validation errors.

**Input Sources:**
- `mold_stability_index.xlsx` → Historical stability metrics
- `moldSpecificationSummary.parquet` → Mold-item compatibility data
- `moldInfo.parquet` → Detailed mold specifications

**Output:**
- `mold_estimated_capacity_df` → Capacity estimates per mold
- `estimated_capacity_invalid_molds` → List of problematic molds

#### Phase 2: Priority Matrix Calculation

  ------------------------------------------------------------------------------------------------------------------
  Step        Process                                    Details
  ----------- ------------------------------------------ -----------------------------------------------------------
  1           Load Feature Weights                       Load historical feature weights from Excel

  2           Weight Validation                          Validate weight ranges, completeness, and sum

  3           Compatibility Analysis                     Analyze mold-machine compatibility using weighted features

  4           Priority Scoring                           Calculate weighted priority scores for each pairing

  5           Matrix Generation                          Generate comprehensive priority matrix with rankings
  -------------------------------------------------------------------------------------------------------------------

**Success Criteria:** Complete priority matrix with valid compatibility scores.
**Failure Modes:** Invalid feature weights, insufficient capacity data, calculation errors.

**Input Sources:**
- `weights_hist.xlsx` → Historical feature weights
- `mold_estimated_capacity_df` → Output from Phase 1
- Historical production performance data

**Output:**
- `mold_machine_priority_matrix` → Compatibility priority scores
- `priority_matrix_invalid_molds` → List of excluded molds

---

## 3. Class HybridSuggestOptimizer

### 3.1 Constructor

```python
HybridSuggestOptimizer(
    databaseSchemas_data: dict,
    sharedDatabaseSchemas_data: dict,
    source_path: str = 'agents/shared_db/DataLoaderAgent/newest',
    annotation_name: str = "path_annotations.json",
    default_dir: str = "agents/shared_db",
    folder_path: str = "agents/OrderProgressTracker",
    target_name: str = "change_log.txt",
    mold_stability_index_folder: str = "agents/MoldStabilityIndexCalculator/mold_stability_index",
    mold_stability_index_target_name: str = "change_log.txt",
    mold_machine_weights_hist_path: str = "agents/MoldMachineFeatureWeightCalculator/weights_hist.xlsx",
    efficiency: float = 0.85,
    loss: float = 0.03
)
```

**Parameters:**
- `databaseSchemas_data`: Database schema configurations for validation
- `sharedDatabaseSchemas_data`: Shared database schema configurations
- `source_path`: Base path for data source files
- `annotation_name`: JSON file containing path mappings
- `efficiency`: Expected production efficiency (default 85%)
- `loss`: Expected production loss rate (default 3%)

### 3.2 Key Methods

#### `process() -> OptimizationResult`

Main entry point that executes the complete optimization workflow.

**Process Flow:**
1. Load mold stability index data
2. Execute Phase 1 (Mold Capacity Estimation)
3. Validate capacity estimation results
4. Execute Phase 2 (Priority Matrix Calculation)
5. Validate priority matrix results
6. Return comprehensive optimization results

**Returns:**
```python
@dataclass
class OptimizationResult:
    estimated_capacity_invalid_molds: List[str]        # Molds with capacity issues
    priority_matrix_invalid_molds: List[str]           # Molds with priority issues
    mold_estimated_capacity_df: pd.DataFrame           # Capacity estimates
    mold_machine_priority_matrix: pd.DataFrame         # Priority matrix
```

#### `_estimate_mold_capacities(mold_stability_index: pd.DataFrame) -> Tuple[List[str], pd.DataFrame]`

Executes Phase 1: Mold capacity estimation using historical data analysis.

**Process:**
1. Initialize ItemMoldCapacityOptimizer with stability data
2. Process mold specifications and historical performance
3. Calculate theoretical, effective, and balanced capacities
4. Identify and report invalid molds
5. Return capacity estimates with quality metrics

#### `_calculate_priority_matrix(feature_weights: pd.Series, capacity_df: pd.DataFrame) -> pd.DataFrame`

Executes Phase 2: Priority matrix calculation using weighted features.

**Process:**
1. Initialize MoldMachinePriorityMatrixCalculator
2. Apply feature weights to performance metrics
3. Calculate compatibility scores for mold-machine pairs
4. Generate comprehensive priority matrix
5. Return matrix with invalid mold identification

#### `validate_configuration() -> bool`

Validates system configuration before optimization execution:

```python
validation_checks = [
    0 < efficiency <= 1,     # Efficiency range check
    0 <= loss < 1,          # Loss rate range check
    paths_exist(),          # File path validation
    schemas_valid()         # Schema configuration check
]
return all(validation_checks)
```

---

## 4. Data Quality & Validation

### 4.1 Multi-Layer Validation Strategy

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Schema        │    │   Data Quality  │    │   Result        │
│   Validation    │    │   Checks        │    │   Validation    │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          ▼                      ▼                      ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ @validate_init_ │    │ Range & Type    │    │ Invalid Mold    │
│ dataframes      │    │ Validation      │    │ Identification  │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          ▼                      ▼                      ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Column & Type   │    │ Missing Data    │    │ Quality Report  │
│ Verification    │    │ Handling        │    │ Generation      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 4.2 Validation Checkpoints

#### Schema Validation (Initialization)
- **Static DB Validation**: `moldSpecificationSummary_df`, `moldInfo_df`
- **Shared DB Validation**: `mold_stability_index`, `mold_estimated_capacity`
- **Column Verification**: Required columns present and correctly typed

#### Data Quality Validation (Processing)
- **Stability Index Quality**: Completeness, consistency, reasonable ranges
- **Feature Weight Quality**: Numeric values, non-negative, reasonable sums
- **Capacity Estimation Quality**: Valid ranges, logical relationships

#### Result Validation (Output)
- **Capacity DataFrame**: Schema compliance, data completeness
- **Priority Matrix**: Dimensional consistency, score validity
- **Invalid Mold Tracking**: Comprehensive error categorization

### 4.3 Invalid Mold Management

**Categorization System:**
```python
# Invalid mold reasons
invalid_reasons = {
    'insufficient_data': 'Not enough historical data points',
    'stability_issues': 'Inconsistent performance metrics', 
    'specification_mismatch': 'Spec conflicts with historical data',
    'calculation_error': 'Mathematical computation failed',
    'quality_threshold': 'Below minimum quality standards'
}
```

**Handling Strategy:**
1. **Identification**: Detect invalid molds during processing
2. **Categorization**: Classify invalidity reasons
3. **Isolation**: Separate from valid optimization results
4. **Reporting**: Detailed logging for manual review
5. **Recovery**: Attempt data correction where possible

---

## 5. Feature Weight Management

### 5.1 Weight Configuration System

```
┌─────────────────────────────────────────────────────────────────┐
│                    Feature Weight Hierarchy                     │
├─────────────────────────────────────────────────────────────────┤
│ shiftCapacityRate_weight    : 0.4 (40%) - PRIMARY PRIORITY     │
│ shiftCavityRate_weight      : 0.25 (25%) - EFFICIENCY METRIC   │
│ shiftCycleTimeRate_weight   : 0.25 (25%) - SPEED METRIC        │
│ shiftNGRate_weight          : 0.1 (10%) - QUALITY METRIC       │
└─────────────────────────────────────────────────────────────────┘
```

### 5.2 Weight Loading & Fallback Strategy

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Load Historical │    │ Validate        │    │ Apply or        │
│ Weights         │    │ Weights         │    │ Use Defaults    │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          ▼                      ▼                      ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ weights_hist    │    │ Range Check:    │    │ Validated:      │
│ .xlsx exists?   │    │ • Non-negative  │    │ Use historical  │
│                 │    │ • Sum ∈ [0.5,2] │    │ weights         │
│ YES: Load data  │    │ • All required  │    │                 │
│ NO: Use defaults│    │   columns       │    │ Invalid:        │
└─────────────────┘    └─────────────────┘    │ Fallback to     │
                                              │ defaults        │
                                              └─────────────────┘
```

### 5.3 Weight Validation Logic

```python
def _validate_feature_weights(weights: pd.Series) -> bool:
    validation_steps = [
        # 1. Completeness check
        all(col in weights.index for col in FeatureWeights.REQUIRED_COLUMNS),
        
        # 2. Type validation
        all(pd.api.types.is_numeric_dtype(type(weights[col])) 
            for col in FeatureWeights.REQUIRED_COLUMNS),
        
        # 3. Range validation
        all(weights[col] >= 0 for col in FeatureWeights.REQUIRED_COLUMNS),
        
        # 4. Sum validation (allow flexibility around 1.0)
        0.5 <= weights[FeatureWeights.REQUIRED_COLUMNS].sum() <= 2.0
    ]
    return all(validation_steps)
```

---

## 6. Optimization Pipeline States

### 6.1 Pipeline State Management

| State | Capacity Phase | Priority Phase | Result Status | Action Required |
|-------|----------------|----------------|---------------|-----------------|
| **🎯 Optimal** | ✅ High quality data | ✅ Complete matrix | `success` | Production ready |
| **⚠️ Degraded** | ⚠️ Some invalid molds | ✅ Partial matrix | `partial_success` | Monitor quality |
| **🔄 Recovery** | ✅ Fallback data | ⚠️ Default weights | `degraded_mode` | Update weights |
| **❌ Failed** | ❌ Insufficient data | ❌ Cannot calculate | `failed` | Data collection |

### 6.2 State Transition Logic

```
[Start] → Load Data → Validate Schemas
                         │
                         ▼
                    ┌─────────────┐
                    │ Data Valid? │
                    └─────┬───────┘
                      YES │ NO
                          ▼  └──→ [Fallback Mode]
                    ┌─────────────┐        │
                    │ Phase 1:    │        │
                    │ Capacity    │        │
                    │ Estimation  │        │
                    └─────┬───────┘        │
                          │                │
                          ▼                │
                    ┌─────────────┐        │
                    │ Capacity    │        │
                    │ Valid?      │        │
                    └─────┬───────┘        │
                      YES │ NO             │
                          ▼  └─────────────┼──→ [Failed]
                    ┌─────────────┐        │
                    │ Phase 2:    │        │
                    │ Priority    │        │
                    │ Matrix      │        │
                    └─────┬───────┘        │
                          │                │
                          ▼                │
                    ┌─────────────┐        │
                    │ Matrix      │        │
                    │ Valid?      │        │
                    └─────┬───────┘        │
                      YES │ NO             │
                          ▼  └─────────────┘
                    [Success/Partial Success]
```

---

## 7. Configuration

### 7.1 Directory Structure

```
agents                                 
├── database
|    ├── databaseSchemas.json          
|    └── sharedDatabaseSchemas.json    
└── shared_db                  
    ├── dynamicDatabase/                                         
    |   └── ...       
    ├── ValidationOrchestrator
    |   └── ...                                                 
    ├── DataLoaderAgent/                                                                      
    |   ├── newest/                                             
    |   |   ├── ...          
    |   |   └── path_annotations.json                             # File path mappings           
    |   └── change_log.txt                                              
    ├── OrderProgressTracker
    |     └── change_log.txt                                      # Progress tracking logs
    ├── MoldStabilityIndexCalculator/ 
    |    └── change_log.txt                                       # Stability index versions
    └── MoldMachineFeatureWeightCalculator/ 
        └── weights_hist.xlsx                                     # Feature weight history
```

### 7.2 Data Flow Overview

| Component | Input Files | Output Files | Purpose |
|-----------|-------------|--------------|---------|
| **ItemMoldCapacityOptimizer** | `mold_stability_index.xlsx`<br>`moldSpecificationSummary.parquet`<br>`moldInfo.parquet` | `mold_estimated_capacity_df`<br>`invalid_molds_list` | Estimate production capacities |
| **MoldMachinePriorityMatrixCalculator** | `weights_hist.xlsx`<br>`mold_estimated_capacity_df`<br>Historical production data | `mold_machine_priority_matrix`<br>`priority_invalid_molds` | Generate compatibility rankings |

---

## 8. Usage Examples

```python
# Basic optimization
optimizer = HybridSuggestOptimizer(
    databaseSchemas_data=db_schemas,
    sharedDatabaseSchemas_data=shared_schemas
)
result = optimizer.process()

# Check results
if len(result.estimated_capacity_invalid_molds) == 0:
    print("All molds have valid capacity estimates")
else:
    print(f"Invalid molds: {result.estimated_capacity_invalid_molds}")

# Access optimization data
capacity_df = result.mold_estimated_capacity_df
priority_matrix = result.mold_machine_priority_matrix
```

```python
# Custom configuration for high-efficiency production
optimizer = HybridSuggestOptimizer(
    databaseSchemas_data=db_schemas,
    sharedDatabaseSchemas_data=shared_schemas,
    efficiency=0.92,  # Higher efficiency target
    loss=0.015,       # Lower loss expectation
    source_path="production/data/path"
)

# Validate before running
if optimizer.validate_configuration():
    result = optimizer.process()
    success_rate = len(result.mold_estimated_capacity_df) / (
        len(result.mold_estimated_capacity_df) + 
        len(result.estimated_capacity_invalid_molds)
    )
    print(f"Optimization success rate: {success_rate:.2%}")
```

```python
# Development mode with detailed logging
import logging
logging.getLogger("HybridSuggestOptimizer").setLevel(logging.DEBUG)

optimizer = HybridSuggestOptimizer(db_schemas, shared_schemas)

# Test individual phases
stability_index = optimizer._load_mold_stability_index(
    optimizer.mold_stability_index_folder,
    optimizer.mold_stability_index_target_name
)

invalid_molds, capacity_df = optimizer._estimate_mold_capacities(stability_index)
print(f"Phase 1 - Invalid molds: {len(invalid_molds)}")

if len(capacity_df) > 0:
    feature_weights = optimizer._load_feature_weights(
        optimizer.mold_machine_weights_hist_path
    )
    priority_matrix, priority_invalid = optimizer._calculate_priority_matrix(
        feature_weights, capacity_df
    )
    print(f"Phase 2 - Priority matrix shape: {priority_matrix.shape}")
```