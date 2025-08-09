# Hybrid Suggest Optimizing Phase

## Overview

The *Hybrid Suggest Optimization Phase* is the third stage of the **OptiMoldIQ** system, responsible for combining historical data analysis with mold-machine compatibility matching to suggest optimal production configurations. This phase provides the foundation for data-driven decision making in manufacturing systems regarding mold selection, machine allocation, and production planning.

```
Historical Insights + Current Data → HybridSuggestOptimizer → Capacity Estimates + Priority Matrix
```

---

## Key Components
 
### 1. `HybridSuggestOptimizer`
**Purpose**: Orchestrate hybrid optimization workflow combining multiple optimization strategies

**Operations**:
- **Phase 1**: Historical-based mold capacity estimation using stability index data
- **Phase 2**: Feature weight-based mold-machine priority matrix calculation for optimal assignments

**Optimization Strategies**:
- Historical performance analysis for capacity estimation
- Statistical weighting for mold-machine compatibility assessment
- Multi-criteria decision making for production planning
- Configuration validation and error handling

**Key Performance Calculations**:
- `historical stability data`
  - Theoretical capacity: `3600 / cycle_time * cavity_count`
  - Effective capacity: `theoretical_capacity * stability_score`
  - Estimated capacity: `theoretical_capacity * (efficiency - loss)`
  - Balanced capacity: `α * effective_capacity + (1-α) * estimated_capacity`
📋 *Details: [HistBasedItemMoldOptimizer.calculate_mold_stability_index() document](#2-histbaseditemmoldoptimizer)*
- `feature_weight`
  - 'shiftNGRate': 'minimize',         # Minimize NG rate
  - 'shiftCavityRate': [0.0 - 1.0],    # Target cavity utilization
  - 'shiftCycleTimeRate': [0.0 - 1.0], # Target cycle time efficiency
  - 'shiftCapacityRate': [0.0 - 1.0]   # Target capacity utilization
📋 *Details: [featureWeightCalculator documentation](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/autoPlanner/OptiMoldIQ_featureWeightCalculator_review.md)*

**Output**:
- Invalid molds list with insufficient data/compatibility
- Comprehensive mold capacity estimates with multiple metrics
- Weighted priority matrix for mold-machine assignments

### 2. `HistBasedItemMoldOptimizer`
**Purpose**: Process mold information and estimate production capacities based on `historical stability data`

**Operations**:
- Mold specification validation and compatibility checking
- Historical stability data integration and analysis
- Multi-factor capacity calculation with trust coefficients
- Invalid mold identification and filtering

**Analysis Framework**:
- **Stability Integration**: Combines cavity and cycle time stability indices
- **Trust Coefficient**: `α = max(0.1, min(1.0, total_records / threshold))`
- **Capacity Balancing**: Weighted combination of historical and theoretical estimates
- **Data Quality Assessment**: Validates completeness and consistency

**Output**:
- Validated mold capacity estimates with confidence metrics
- Data quality indicators for each mold
- Invalid mold classifications with reasons
  
📋 *Details: [histBasedItemMoldOptimizer documentation](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/autoPlanner/OptiMoldIQ_histBasedItemMoldOptimizer_review.md)*

### 3. `HistoryProcessor` (Priority Matrix Module)
**Purpose**: Generate mold-machine priority matrix using historical performance data and `feature weights`

**Operations**:
- Historical production data preparation and filtering
- Mold-machine performance metrics calculation
- Weighted scoring based on multiple performance factors
- Priority ranking generation for optimal assignments

**Priority Calculation Framework**:
- **Performance Metrics**: NG rate, cavity rate, cycle time rate, capacity rate
- **Weighted Scoring**: `total_score = Σ(metric_value * feature_weight)`
- **Priority Ranking**: Converts scores to rankings (1 = highest priority)
- **Matrix Generation**: Creates comprehensive mold-machine compatibility matrix

**Output**:
- Priority matrix with molds as rows, machines as columns
- Performance-based rankings for each mold-machine combination
- Historical performance insights for decision support

📋 *Details: [historyProcessor priority matrix documentation](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/autoPlanner/initialPlanner/OptiMoldIQ_historyProcessor_review.md)*

---

## System Configuration

### Operational Parameters
```
Efficiency Factor: 0.85 (85% expected production efficiency)
Loss Factor: 0.03 (3% expected production loss rate)
```

### Feature Weight Distribution
```
Capacity Rate Weight: 0.4 (40% - highest priority)
Cavity Rate Weight: 0.25 (25%)
Cycle Time Rate Weight: 0.25 (25%)
NG Rate Weight: 0.1 (10%)
```

### Data Quality Thresholds
```
Total Records Threshold: 30 (minimum for reliable analysis)
Trust Coefficient Range: 0.1 - 1.0
Stability Index Range: 0.0 - 1.0
```

### Validation Parameters
```
Efficiency Range: 0 < efficiency ≤ 1
Loss Range: 0 ≤ loss < 1
Weight Sum Target: ≈ 1.0 (allows flexibility 0.5-2.0)
```

---

## Data Flow

### Input
- **Mold Stability Index**: Historical performance consistency metrics from HistoryProcessor
- **Feature Weights**: Performance metric importance from FeatureWeightCalculator
- **Production Records**: Historical production data with item, mold, machine information
- **Mold Specifications**: Detailed mold information and compatibility mappings
- **Machine Information**: Machine specifications and capabilities

### Processing Steps
1. **Configuration Validation**: Verify all paths, parameters, and data accessibility
2. **Data Loading**: Load stability index, feature weights, and production data
3. **Capacity Estimation**: Calculate mold capacities using historical stability data
4. **Priority Matrix Generation**: Create weighted priority rankings for mold-machine pairs
5. **Result Compilation**: Package results into structured OptimizationResult container

---

## Workflow Diagrams

📊 **Detailed workflows**:
- [hybridSuggestOptimizer Workflow](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/workflows/OptiMoldIQ_hybridSuggestOptimizerWorkflow.md)  

---

## Implementation Code

### HybridSuggestOptimizer Setup
```python
from agents.autoPlanner.hybrid_suggest_optimizer import HybridSuggestOptimizer

# Initialize optimizer with production parameters
optimizer = HybridSuggestOptimizer(
    source_path=f"{shared_db_dir}/DataLoaderAgent/newest",
    annotation_name='path_annotations.json',
    databaseSchemas_path=f"{mock_db_dir}/databaseSchemas.json",
    folder_path=f"{shared_db_dir}/OrderProgressTracker",
    target_name="change_log.txt",
    mold_stability_index_folder=f"{shared_db_dir}/HistoryProcessor/mold_stability_index",
    mold_stability_index_target_name="change_log.txt",
    mold_machine_weights_hist_path=f"{shared_db_dir}/FeatureWeightCalculator/weights_hist.xlsx",
    efficiency=0.85,  # 85% efficiency target
    loss=0.03        # 3% loss allowance
)
```

### Optimization Execution
```python
def execute_hybrid_suggest_optimization():
    # Validate configuration before processing
    if optimizer.validate_configuration():
        logger.info("Configuration validated successfully")
        
        # Get and log configuration summary
        summary = optimizer.get_optimization_summary()
        logger.info("Configuration Summary: {}", summary)
        
        # Execute optimization process
        result = optimizer.process()
        
        # Process results for production planning
        optimization_results = {
            'invalid_molds': result.invalid_molds,
            'capacity_data': result.mold_estimated_capacity_df,
            'priority_matrix': result.mold_machine_priority_matrix,
            'timestamp': datetime.now()
        }
        
        logger.info("Optimization completed successfully!")
        logger.info("Invalid molds: {}", len(result.invalid_molds))
        logger.info("Capacity data shape: {}", result.mold_estimated_capacity_df.shape)
        logger.info("Priority matrix shape: {}", result.mold_machine_priority_matrix.shape)
        
        return optimization_results
    else:
        logger.error("Configuration validation failed")
        return None

# Execute optimization
optimization_results = execute_hybrid_suggest_optimization()
```

---

## Result Structure

### OptimizationResult Container
```python
@dataclass
class OptimizationResult:
    invalid_molds: List[str]                    # Molds with insufficient data
    mold_estimated_capacity_df: pd.DataFrame    # Comprehensive capacity estimates
    mold_machine_priority_matrix: pd.DataFrame  # Priority rankings for assignments
```

### Capacity DataFrame Columns
- **Basic Information**: `moldNo`, `moldName`, `acquisitionDate`, `machineTonnage`
- **Specifications**: `moldCavityStandard`, `moldSettingCycle`
- **Stability Indices**: `cavityStabilityIndex`, `cycleStabilityIndex`
- **Capacity Estimates**: `theoreticalMoldHourCapacity`, `effectiveMoldHourCapacity`, `estimatedMoldHourCapacity`, `balancedMoldHourCapacity`
- **Data Quality Metrics**: `totalRecords`, `totalCavityMeasurements`, `totalCycleMeasurements`
- **Time Range**: `firstRecordDate`, `lastRecordDate`

### Priority Matrix Structure
- **Rows**: Mold identifiers (moldNo)
- **Columns**: Machine codes (machineCode)
- **Values**: Priority rankings (1 = highest priority, 0 = incompatible)

---

## Trigger Mechanism

### Trigger Logic

The Hybrid Suggest Optimization Phase is triggered **on-demand** for production planning scenarios:

```python
# On-demand execution for production planning
def trigger_optimization_for_planning():
    # 1. Validate system readiness
    if optimizer.validate_configuration():
        
        # 2. Execute hybrid optimization
        result = optimizer.process()
        
        # 3. Prepare results for downstream planning
        planning_data = {
            'capacity_estimates': result.mold_estimated_capacity_df,
            'priority_matrix': result.mold_machine_priority_matrix,
            'invalid_molds': result.invalid_molds,
            'generation_timestamp': datetime.now()
        }
        
        return planning_data
    
    return None

# Integration with production planning workflow
def production_planning_workflow():
    optimization_data = trigger_optimization_for_planning()
    if optimization_data:
        # Use optimization results for production planning
        return plan_production(optimization_data)
    else:
        # Handle optimization failure
        return handle_planning_fallback()
```

### Execution Flow
1. **Configuration Validation** ensures all required data and parameters are available
2. **Hybrid Optimization** combines capacity estimation with priority matrix generation
3. **Result Packaging** structures output for downstream consumption
4. **Planning Integration** provides optimized data for production scheduling

This on-demand approach ensures optimization results are fresh and relevant for immediate planning decisions.

---

## Key Benefits

- **Data-Driven Optimization**: Combines historical performance with current production needs
- **Multi-Criteria Decision Making**: Considers capacity, compatibility, and performance simultaneously
- **Statistical Reliability**: Uses proven stability indices and confidence-weighted feature importance
- **Flexible Configuration**: Adapts to different production environments and requirements
- **Comprehensive Validation**: Ensures data quality and system reliability before processing
- **Integrated Intelligence**: Seamlessly combines multiple optimization strategies for superior results

---

## Quality Assurance

### Data Validation
- **Schema Compliance**: All DataFrames validated against expected database schemas
- **Range Checking**: Numeric parameters validated within realistic operational bounds
- **Completeness Verification**: Missing data identified and handled with appropriate fallbacks
- **Consistency Assessment**: Cross-validates data relationships and dependencies

### Performance Monitoring
- **Processing Time Tracking**: Monitors optimization execution duration and performance bottlenecks
- **Resource Utilization**: Tracks memory usage and computational efficiency during processing
- **Success Rate Analysis**: Measures optimization completion rates and identifies failure patterns
- **Result Quality Assessment**: Validates optimization output against expected ranges and patterns

### Error Handling and Recovery
- **Configuration Failures**: Clear error messages with suggested corrections
- **Missing Data Handling**: Graceful degradation with default values and fallback mechanisms
- **Processing Errors**: Comprehensive exception handling with detailed logging
- **Result Validation**: Post-processing checks ensure output data integrity

---

## Integration Points

### Upstream Dependencies
- **Historical Insight Addition Phase**: Provides mold stability indices and feature weights
- **Shared Database Building Phase**: Supplies standardized production and specification data
- **DataLoaderAgent**: Provides foundational data through newest directory structure
- **OrderProgressTracker**: Supplies current production status and change tracking

### Downstream Consumers
- **Production Planning Phases**: Utilizes capacity estimates and priority matrices for scheduling
- **Machine Assignment Systems**: Leverages priority rankings for optimal resource allocation
- **Decision Support Dashboards**: Displays optimization insights for manufacturing management
- **Performance Analysis Tools**: Uses optimization data for continuous improvement initiatives