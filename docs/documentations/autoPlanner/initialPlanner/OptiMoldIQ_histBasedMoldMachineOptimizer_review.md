# HistBasedMoldMachineOptimizer

## 1. Overview

`HistBasedMoldMachineOptimizer` is a manufacturing optimization component that performs intelligent mold-to-machine assignment using a two-phase greedy algorithm based on priority matrices and lead time constraints.

It ensures:
- **Constraint-based optimization** prioritizing unique matches and limited resources.
- **Load-balanced assignment** respecting machine capacity thresholds.
- **Real-time load tracking** with dynamic updates during assignment.
- **High performance** processing with vectorized operations and efficient data structures.

---

## 2. Class: `HistBasedMoldMachineOptimizer`

### 2.1 Initialization

```python
optimizer = HistBasedMoldMachineOptimizer(
    mold_machine_priority_matrix=...,
    mold_lead_times_df=...,
    producing_data=...,
    machine_info_df=...,
    max_load_threshold=30
)
```

- `mold_machine_priority_matrix`: Compatibility matrix between molds and machines (1=compatible, 0=incompatible).
- `mold_lead_times_df`: DataFrame containing mold numbers and their lead times.
- `producing_data`: Current production data with remaining times.
- `machine_info_df`: Machine specifications and information.
- `max_load_threshold`: Maximum allowed machine load in days (default: 30).

**Validation**:
- Automatic data type optimization (int8, int32) for memory efficiency.
- Pre-computed mappings for O(1) lookup performance.
- Statistics tracking for monitoring optimization progress.

### 2.2 Main Methods

`run_optimization() -> HistBasedOptimizationResult`

- Executes **two-phase optimization strategy**:
  - **Round 1**: Constraint-based greedy assignment
  - **Round 2**: Load-balanced assignment for remaining molds
- Combines results from both rounds into unified output.
- Provides comprehensive logging and performance metrics.

**Output Example**

```json
{
  "assigned_matrix": DataFrame with final assignments,
  "assignments": ["M001", "M002", "M003"],
  "unassigned_molds": ["M004", "M005"]
}
```

---

### 2.3 Processing Steps

#### **Round 1: Constraint-Based Greedy Assignment**

##### `constraint_based_optimized()`
- **Phase 1**: Processes molds with exactly one compatible machine (unique matches).
- **Phase 2**: Iteratively assigns remaining molds using constrained resource prioritization.

##### `find_unique_matches()`
- Identifies molds with only one machine option.
- Immediately assigns these to avoid bottlenecks.
- Formula: `machine_count = (priority_matrix != 0).sum(axis=1)`

##### `optimize_mold_machine_matching()`
- Main optimization loop with performance tracking.
- Prioritizes machines with minimal compatible molds (`target_suitable_count=1`).
- Uses vectorized operations for matrix updates.

**Strategy**: Handle constraints first to minimize conflicts in subsequent iterations.

#### **Round 2: Load-Balanced Assignment**

##### `load_balance_based_optimized()`
- Processes unassigned molds from Round 1.
- Calculates real-time machine loads: `total_load = producing_load + assigned_load`.
- Assigns molds to machines with lowest load under threshold.

##### Load Calculation Logic:
```python
def assign_with_threshold():
    for mold in unassigned_molds:
        available_machines = get_compatible_machines(mold)
        sorted_machines = sort_by_current_load(available_machines)
        
        for machine in sorted_machines:
            projected_load = current_load[machine] + mold_leadtime
            if projected_load <= max_threshold:
                assign(mold, machine)
                update_load_real_time()
                break
        
        # Fallback: assign to lowest load machine
        if not_assigned:
            assign_to_lowest_load_machine()
```

---

### 2.4 Helper Methods

#### Matrix Operations:
- `create_binary_priority_matrix()` → Converts priority matrix to binary format.
- `create_leadtime_matrix()` → Multiplies binary matrix with lead times.
- `calculate_machine_statistics()` → Efficiently computes machine load statistics.

#### Assignment Operations:
- `find_valid_pairs()` → Identifies valid mold-machine combinations.
- `assign_molds_to_machines()` → Batch updates assignment matrices.
- `_update_total_machine_load()` → Combines producing and pending loads.

#### Data Processing:
- `_convert_producing_leadtime()` → Converts hours to days for consistency.
- `_create_candidate_lead_time_matrix()` → Generates matrices for unassigned molds.
- `_safe_replace_and_clip()` → Handles invalid numeric values.

---

## 3. Algorithm Strategy

### 3.1 Two-Phase Approach

**Round 1 - Constraint Resolution:**
```
1. Identify unique matches (molds with only 1 compatible machine)
2. Assign unique matches immediately
3. For remaining molds:
   - Find machines with minimal mold options
   - Assign greedily to reduce future conflicts
   - Update matrices after each assignment
```

**Round 2 - Load Balancing:**
```
1. Calculate current machine loads from production + Round 1
2. For each unassigned mold:
   - Sort compatible machines by current load
   - Assign to first machine under threshold
   - Update loads in real-time
3. Fallback to lowest-load machine if threshold exceeded
```

### 3.2 Optimization Techniques

- **Vectorized Operations**: Uses pandas/numpy for batch processing.
- **Efficient Data Types**: int8 for binary matrices, int32 for calculations.
- **Pre-computed Mappings**: Dictionary lookups for O(1) access.
- **Real-time Updates**: Dynamic load recalculation during assignment.
- **Early Termination**: Stops when no more valid assignments possible.

---

## 4. Data Safety & Performance

- **Copy-based Processing**: Works with DataFrame copies to prevent mutation.
- **Memory Optimization**: Uses appropriate data types (int8, int32) for large matrices.
- **Batch Operations**: Reduces overhead with vectorized pandas operations.
- **Iteration Limits**: Prevents infinite loops with reasonable maximum iterations.
- **Statistics Tracking**: Monitors performance metrics throughout execution.

---

## 5. Error Handling & Logging

- **Comprehensive Logging**: Detailed progress tracking with loguru.
- **Invalid Data Handling**: Graceful handling of missing or inconsistent data.
- **Performance Monitoring**: Execution time and success rate tracking.
- **Validation Checks**: Ensures data integrity before processing.
- **Fallback Strategies**: Alternative assignment methods when primary fails.

**Logging Levels:**
- `INFO`: Major phase completions and summary statistics
- `DEBUG`: Detailed assignment decisions and matrix updates
- `WARNING`: Data inconsistencies and fallback usage

---

## 6. Output & Reporting

### 6.1 HistBasedOptimizationResult

**Fields:**
- `assigned_matrix`: Final assignment matrix with lead times
- `assignments`: List of successfully assigned mold numbers
- `unassigned_molds`: Molds that couldn't be assigned

**Metrics Provided:**
- Total execution time per round
- Success rate (assigned/total molds)
- Number of optimization iterations
- Unique matches identified
- Load distribution across machines

### 6.2 Performance Statistics

```python
stats = {
    'start_time': timestamp,
    'iterations': count,
    'assignments_made': count,
    'unique_matches': count,
    'success_rate': percentage,
    'execution_time': seconds
}
```

---

## 7. Usage & Integration

### 7.1 Production Planning Integration
- **Capacity Planning**: Optimizes mold utilization across available machines.
- **Load Balancing**: Ensures even distribution of work across production lines.
- **Constraint Management**: Handles technical limitations and compatibility requirements.

### 7.2 Continuous Optimization
- **Real-time Updates**: Supports dynamic replanning as conditions change.
- **Historical Learning**: Can incorporate historical performance data.
- **Scalable Processing**: Handles large-scale manufacturing environments.

### 7.3 Extension Possibilities
- **Multi-objective Optimization**: Can be extended to consider cost, quality, or energy factors.
- **Machine Learning Integration**: Priority matrices could be learned from historical data.
- **Predictive Maintenance**: Integration with machine health monitoring systems.

---

## 8. Technical Specifications

**Algorithm Complexity:**
- Time Complexity: O(n×m×k) where n=molds, m=machines, k=iterations
- Space Complexity: O(n×m) for storing matrices
- Performance: Optimized for manufacturing-scale datasets (1000+ molds, 100+ machines)

**Dependencies:**
- pandas: DataFrame operations and data manipulation
- numpy: Numerical computations and array operations  
- loguru: Advanced logging and debugging
- dataclasses: Type-safe result containers