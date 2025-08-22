# MoldStabilityIndexCalculator

## 1. Agent Info

- **Name**: MoldStabilityIndexCalculator
- **Purpose**:
  - Analyze mold performance and stability based on historical production data
  - Calculate cavity and cycle time stability indices using statistical methods
  - Generate balanced hourly capacity metrics for production planning optimization
  - Provide reliability assessments for mold utilization and maintenance scheduling
- **Owner**: 
- **Status**: Active
- **Location**: `agents/autoPlanner/initialPlanner/historyBasedProcessor/`

---

## 2. What it does

The `MoldStabilityIndexCalculator` processes **historical production records** and **mold specification data** to generate comprehensive stability assessments for manufacturing molds. It evaluates mold reliability through multi-dimensional analysis of cavity utilization and cycle time performance, providing critical input for production capacity planning and mold maintenance optimization.

The calculator integrates statistical scoring methods, weighted performance metrics, and historical data confidence analysis to deliver robust stability indices that reflect real-world mold performance under production conditions.

### Key Features

- **Dual Stability Assessment**
  - `Cavity Stability Index`: Evaluates consistency and accuracy of cavity utilization
  - `Cycle Stability Index`: Analyzes cycle time performance against standard specifications
  - Statistical scoring with configurable weight distributions
  
- **Capacity Calculation Engine**
  - Theoretical capacity based on standard specifications
  - Effective capacity adjusted by stability performance
  - Balanced capacity incorporating historical data confidence
  - Trust coefficient for data reliability weighting
  
- **Multi-Dimensional Cavity Analysis**
  - `Accuracy Rate`: Percentage of cavity values matching standards (40% weight)
  - `Consistency Score`: Statistical variation measurement (30% weight)  
  - `Utilization Rate`: Actual vs standard cavity usage ratio (20% weight)
  - `Data Completeness`: Historical record sufficiency penalty (10% weight)
  
- **Comprehensive Cycle Analysis**
  - `Accuracy Score`: Deviation from standard cycle times (30% weight)
  - `Consistency Score`: Cycle time variation stability (25% weight)
  - `Range Compliance`: Adherence to ±20% tolerance limits (25% weight)
  - `Outlier Penalty`: Extreme deviation detection and penalty (10% weight)
  - `Data Completeness`: Record volume adequacy assessment (10% weight)
  
- **Historical Data Integration**
  - Bootstrap-style confidence weighting based on record volume
  - Dynamic trust coefficient calculation (α) for data reliability
  - Balanced capacity combining statistical and theoretical approaches
  
- **Production Performance Metrics**
  - Theoretical hourly capacity from specifications
  - Stability-adjusted effective capacity calculations  
  - Efficiency and loss factor integration
  - Comprehensive measurement statistics and date ranges

---

## 3. Architecture Overview

```
                    ┌─────────────────────────────┐
                    │ MoldStabilityIndex          │
                    │ Calculator (Main Engine)    │
                    └─────────────┬───────────────┘
                                  │
          ┌───────────────────────┼───────────────────────┐
          │                       │                       │
          v                       v                       v
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Production      │    │ Mold Information│    │ Database Schema │
│ Records History │    │ & Specifications│    │ Validation      │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                                 v
                    ┌─────────────────────────┐
                    │ Data Preprocessing      │
                    │ & Aggregation Engine    │
                    └─────────────┬───────────┘
                                  │
        ┌─────────────────────────┼─────────────────────────┐
        │                         │                         │
        v                         v                         v
┌───────────────┐      ┌──────────────────┐      ┌─────────────────┐
│ Cavity        │      │ Cycle Time       │      │ Capacity        │
│ Stability     │      │ Stability        │      │ Calculation     │
│ Calculator    │      │ Calculator       │      │ Engine          │
└───────┬───────┘      └─────────┬────────┘      └─────────┬───────┘
        │                        │                         │
        └────────────────────────┼─────────────────────────┘
                                 │
                                 v
                    ┌─────────────────────────┐
                    │ Trust Coefficient       │
                    │ & Balance Engine        │
                    └─────────────┬───────────┘
                                  │
                                  v
                    ┌─────────────────────────┐
                    │ Results Aggregation     │
                    │ & Export Engine         │
                    └─────────────────────────┘
```

---

## 4. Pre-requisites Checklist

Before running the calculator, ensure:

- [ ] **DataLoader output available**: Latest parquet files in `agents/shared_db/DataLoaderAgent/newest`
- [ ] **Path annotations accessible**: `path_annotations.json` with correct file paths
- [ ] **Core datasets available**: productRecords, moldInfo with proper schema compliance
- [ ] **Production history data**: Minimum 30 records per mold for reliable analysis
- [ ] **Database schema files**: databaseSchemas.json with validated column definitions
- [ ] **Write permissions**: Full access to `agents/shared_db/MoldStabilityIndexCalculator/`
- [ ] **Python dependencies**: pandas, numpy, loguru, pathlib
- [ ] **Statistical requirements**: Sufficient data volume for stability calculation reliability
- [ ] **Mold specification data**: Complete moldInfo with standard cavity and cycle time values

---

## 5. Error Handling Scenarios

| Scenario | Data Load | Preprocessing | Stability Calculation | Capacity Generation | Final Status | Action Required |
|----------|-----------|---------------|----------------------|-------------------|--------------|-----------------|
| Happy Path | ✅ Success | ✅ Success | ✅ Success | ✅ Success | `success` | None |
| Missing Data Files | ❌ Failed | - | - | - | `failed` | Check input data sources |
| Schema Validation Error | ✅ Success | ❌ Failed | - | - | `failed` | Validate column requirements |
| Insufficient Data Volume | ✅ Success | ✅ Success | ⚠️ Warning | ✅ Success | `partial_success` | Review minimum record thresholds |
| Invalid Standard Values | ✅ Success | ✅ Success | ⚠️ Warning | ✅ Success | `partial_success` | Check mold specifications |
| Zero Cycle Time/Cavity | ✅ Success | ✅ Success | ⚠️ Warning | ✅ Success | `partial_success` | Validate mold configuration |

---

## 6. Processing Pipeline

```
Data Loading → Schema Validation → Data Preprocessing → 
Stability Calculation → Capacity Analysis → Trust Weighting → Report Generation
```

**Detailed Steps**:

1. **Data Loading & Validation**
   - Load productRecords and moldInfo from parquet files
   - Apply schema validation decorators for column compliance
   - Validate file accessibility and data structure integrity

2. **Data Preprocessing & Aggregation**
   - Filter records with valid moldShot values (> 0)
   - Calculate cycle time: 28800 seconds / moldShot
   - Group by moldNo and recordDate for aggregated analysis
   - Create lists of cavity and cycle measurements per record

3. **Mold-Specific Analysis Loop**
   - Process each unique moldNo individually
   - Extract standard cavity and cycle specifications
   - Aggregate all historical cavity and cycle measurements
   - Calculate comprehensive measurement statistics

4. **Cavity Stability Index Calculation**
   - **Accuracy Rate**: Match percentage against standard cavity
   - **Consistency Score**: Coefficient of variation analysis
   - **Utilization Rate**: Average cavity vs standard ratio
   - **Data Completeness**: Record volume adequacy penalty
   - Apply weighted scoring formula with configured weights

5. **Cycle Time Stability Index Calculation**
   - **Accuracy Score**: Mean deviation from standard cycle time
   - **Consistency Score**: Cycle time variation coefficient
   - **Range Compliance**: ±20% tolerance adherence rate
   - **Outlier Penalty**: Extreme deviation (>100%) detection
   - **Data Completeness**: Historical data sufficiency assessment
   - Apply weighted scoring with multi-dimensional criteria

6. **Capacity Calculation & Balancing**
   - Calculate theoretical hourly capacity from specifications
   - Generate stability-weighted effective capacity
   - Apply efficiency/loss factors for estimated capacity
   - Compute trust coefficient (α) based on data volume
   - Balance effective and estimated capacity using trust weighting

7. **Results Compilation & Export**
   - Aggregate all stability metrics and capacity calculations
   - Include comprehensive measurement statistics
   - Generate versioned Excel reports with detailed breakdowns
   - Save structured data for downstream planning integration

---

## 7. Input & Output

- **Input**: 
  - Production records with moldShot, cavity, and timing data (productRecords_df)
  - Mold specifications with standard cavity and cycle parameters (moldInfo_df)
  - Database schema definitions for validation
  - Configuration parameters for efficiency and loss factors
  
- **Output**: 
  - Cavity and cycle stability indices (0-1 scale)
  - Multiple capacity metrics (theoretical, effective, estimated, balanced)
  - Comprehensive measurement statistics and data quality metrics
  - Historical data range and record volume information
  - Versioned Excel reports with detailed analysis
  
- **Format**: 
  - Structured DataFrame with normalized stability scores
  - Capacity values in pieces per hour
  - Statistical metadata for confidence assessment
  - Timestamped reports for audit and tracking

---

## 8. Configuration Parameters

### 8.1 Stability Calculation Constants

```python
SECONDS_PER_HOUR = 3600           # Time conversion factor
CYCLE_TIME_TOLERANCE = 0.2        # ±20% acceptable cycle deviation
EXTREME_DEVIATION_THRESHOLD = 1.0  # 100% outlier threshold
```

### 8.2 Performance & Efficiency Parameters

```python
efficiency = 0.85                 # 85% expected efficiency rate
loss = 0.03                      # 3% allowable production loss
total_records_threshold = 30      # Minimum records for reliability
```

### 8.3 Cavity Stability Weight Distribution

```python
CAVITY_STABILITY_WEIGHTS = {
    'accuracy_rate_weight': 0.4,        # 40% - Standard matching accuracy
    'consistency_score_weight': 0.3,    # 30% - Statistical consistency
    'utilization_rate_weight': 0.2,     # 20% - Capacity utilization
    'data_completeness_weight': 0.1     # 10% - Data volume adequacy
}
```

### 8.4 Cycle Stability Weight Distribution

```python
CYCLE_STABILITY_WEIGHTS = {
    'accuracy_score_weight': 0.3,       # 30% - Standard deviation accuracy
    'consistency_score_weight': 0.25,   # 25% - Variation consistency
    'range_compliance_weight': 0.25,    # 25% - Tolerance compliance
    'outlier_penalty_weight': 0.1,      # 10% - Extreme value penalty
    'data_completeness_weight': 0.1     # 10% - Record sufficiency
}
```

### 8.5 Threshold Configuration

```python
cavity_stability_threshold = 0.6     # Cavity weight in overall stability
cycle_stability_threshold = 0.4      # Cycle weight in overall stability
total_records_threshold = 30         # Minimum records for full confidence
```

---

## 9. Statistical Engine

### 9.1 Cavity Stability Logic

```python
# Accuracy: Exact match percentage
correct_count = sum(1 for val in cavity_values if val == standard_cavity)
accuracy_rate = correct_count / len(cavity_values)

# Consistency: Coefficient of variation
cv = np.std(cavity_values) / np.mean(cavity_values)
consistency_score = max(0, 1 - cv)

# Utilization: Average vs standard ratio
avg_active_cavity = np.mean(cavity_values)
utilization_rate = min(1.0, avg_active_cavity / standard_cavity)

# Data completeness penalty
data_completeness = min(1.0, total_records / threshold)
```

### 9.2 Cycle Stability Logic

```python
# Accuracy: Mean relative deviation
deviations = [abs(val - standard_cycle) / standard_cycle for val in cycle_values]
accuracy_score = max(0, 1 - np.mean(deviations))

# Range compliance: ±20% tolerance
in_range_count = sum(1 for val in cycle_values 
                    if abs(val - standard_cycle) / standard_cycle <= 0.2)
range_compliance = in_range_count / len(cycle_values)

# Outlier detection: >100% deviation
extreme_outliers = sum(1 for val in cycle_values 
                      if abs(val - standard_cycle) / standard_cycle > 1.0)
outlier_penalty = max(0, 1 - (extreme_outliers / len(cycle_values)))
```

### 9.3 Capacity Balancing Algorithm

```python
# Trust coefficient based on data volume
alpha = max(0.1, min(1.0, total_records / total_records_threshold))

# Theoretical capacity calculation
theoretical_capacity = SECONDS_PER_HOUR / standard_cycle * standard_cavity

# Stability-adjusted capacity
overall_stability = (cavity_stability * 0.6) + (cycle_stability * 0.4)
effective_capacity = theoretical_capacity * overall_stability

# Efficiency-based estimation
estimated_capacity = theoretical_capacity * (efficiency - loss)

# Final balanced capacity
balanced_capacity = alpha * effective_capacity + (1 - alpha) * estimated_capacity
```

---

## 10. Directory Structure

```
agents/shared_db                                              
└── MoldStabilityIndexCalculator/ 
    ├── historical_db/                                      
    ├── newest/ 
    |   └── YYYYMMDD_HHMM_mold_stability_index.xlsx
    └── change_log.txt     
```

---

## 11. Data Schema & Output Structure

### 11.1 Input Schema Requirements

```python
# productRecords_df required columns
productRecords_schema = {
    'moldNo': 'object',           # Mold identifier
    'recordDate': 'datetime64',   # Production date
    'moldShot': 'int64',         # Shot count per shift
    'moldCavity': 'int64'        # Active cavity count
}

# moldInfo_df required columns  
moldInfo_schema = {
    'moldNo': 'object',              # Mold identifier
    'moldName': 'object',            # Mold name/description
    'moldCavityStandard': 'int64',   # Standard cavity count
    'moldSettingCycle': 'float64',   # Standard cycle time (seconds)
    'acquisitionDate': 'datetime64', # Mold acquisition date
    'machineTonnage': 'float64'      # Required machine tonnage
}
```

### 11.2 Output DataFrame Structure

```python
stability_results = {
    'moldNo': str,                        # Mold identifier
    'moldName': str,                      # Mold description
    'acquisitionDate': datetime,          # Acquisition date
    'machineTonnage': float,              # Tonnage requirement
    'moldCavityStandard': int,            # Standard cavity count
    'moldSettingCycle': float,            # Standard cycle time
    
    'cavityStabilityIndex': float,        # Cavity stability (0-1)
    'cycleStabilityIndex': float,         # Cycle stability (0-1)
    
    'theoreticalMoldHourCapacity': float, # Theoretical pieces/hour
    'effectiveMoldHourCapacity': float,   # Stability-adjusted capacity
    'estimatedMoldHourCapacity': float,   # Efficiency-adjusted capacity
    'balancedMoldHourCapacity': float,    # Final balanced capacity
    
    'totalRecords': int,                  # Historical record count
    'totalCavityMeasurements': int,       # Total cavity measurements
    'totalCycleMeasurements': int,        # Total cycle measurements
    'firstRecordDate': datetime,          # Earliest record date
    'lastRecordDate': datetime            # Latest record date
}
```

---

## 12. Dependencies

- **DataLoaderAgent**: Provides processed production and mold specification data
- **Database Schemas**: Ensures data type consistency and validation compliance
- **External Libraries**: pandas, numpy, pathlib, loguru for data processing and logging
- **Validation Decorators**: Schema compliance verification for input DataFrames
- **File System Access**: Path annotations and parquet file reading capabilities

---

## 13. How to Run

### 13.1 Basic Usage

```python
# Initialize calculator with default parameters
calculator = MoldStabilityIndexCalculator()

# Run stability analysis
stability_results = calculator.process()

# Process and save to Excel with versioning
calculator.process_and_save_result()
```

### 13.2 Custom Configuration

```python
# Custom efficiency and threshold parameters
calculator = MoldStabilityIndexCalculator(
    efficiency=0.90,                    # Higher efficiency expectation
    loss=0.02,                         # Lower acceptable loss rate
    source_path='custom/data/path',     # Alternative data source
    default_dir='custom/output/path'    # Custom output directory
)

# Run with custom thresholds
results = calculator.process(
    cavity_stability_threshold=0.7,     # Higher cavity weight
    cycle_stability_threshold=0.3,      # Lower cycle weight
    total_records_threshold=50          # Higher data requirement
)
```

### 13.3 Advanced Configuration

```python
# Initialize with custom paths and parameters
calculator = MoldStabilityIndexCalculator(
    source_path='agents/shared_db/DataLoaderAgent/custom',
    databaseSchemas_path='database/customSchemas.json',
    efficiency=0.88,
    loss=0.025
)

# Process with detailed configuration
results = calculator.process(
    cavity_stability_threshold=0.65,
    cycle_stability_threshold=0.35,
    total_records_threshold=40
)

# Generate detailed reports
calculator.process_and_save_result(
    cavity_stability_threshold=0.65,
    cycle_stability_threshold=0.35,
    total_records_threshold=40
)
```

---

## 14. Result Structure

```python
{
    # Per-mold stability assessment
    "moldNo": ["MOLD001", "MOLD002", ...],
    "cavityStabilityIndex": [0.85, 0.92, ...],
    "cycleStabilityIndex": [0.78, 0.88, ...],
    
    # Capacity analysis results
    "theoreticalMoldHourCapacity": [1200, 800, ...],
    "effectiveMoldHourCapacity": [980, 720, ...],
    "balancedMoldHourCapacity": [995, 735, ...],
    
    # Data quality metrics
    "totalRecords": [45, 67, ...],
    "totalCavityMeasurements": [180, 268, ...],
    "totalCycleMeasurements": [180, 268, ...]
}
```

---

## 15. Configuration Paths

- **source_path**: `agents/shared_db/DataLoaderAgent/newest` (processed parquet files)
- **annotation_name**: `path_annotations.json` (file path mappings)
- **databaseSchemas_path**: `database/databaseSchemas.json` (data schema definitions)
- **default_dir**: `agents/shared_db` (base output directory)
- **output_dir**: `agents/shared_db/MoldStabilityIndexCalculator` (specific output location)
- **prefix**: `mold_stability_index` (output file prefix)

---

## 16. Monitoring & Alerts

### 16.1 Key Performance Indicators

- **Stability Distribution**: Range and distribution of cavity/cycle stability indices
- **Data Coverage**: Percentage of molds with sufficient historical data
- **Capacity Accuracy**: Alignment between theoretical and balanced capacity metrics
- **Historical Trends**: Stability index changes over time for individual molds
- **Outlier Detection**: Identification of molds with unusual performance patterns

### 16.2 Data Quality Metrics

- **Record Volume**: Distribution of historical record counts per mold
- **Measurement Completeness**: Availability of cavity and cycle data
- **Standard Compliance**: Percentage of measurements within acceptable ranges
- **Temporal Coverage**: Time span and recency of historical data
- **Missing Data Impact**: Effect of data gaps on stability calculations

### 16.3 Operational Monitoring

- **Monthly Recalculation**: Automated updates with new production data
- **Threshold Alerts**: Notifications for molds below stability thresholds
- **Capacity Validation**: Cross-verification with actual production performance
- **Maintenance Correlation**: Stability trends vs maintenance schedules
- **Planning Integration**: Usage of stability indices in downstream applications