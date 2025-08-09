# Historical Insight Addition Phase

## Overview

The *Historical Insight Addition Phase* is the second stage of the **OptiMoldIQ** system, responsible for processing historical production data into actionable insights and populating a shared database for optimal production planning. The workflow consists of two specialized agents executed sequentially:

```
Shared Database → HistoryProcessor → FeatureWeightCalculator → Insight Repository
```

---

## Key Components

### 1. `HistoryProcessor`
**Purpose**: Analyze historical production data to evaluate mold performance and stability

**Operations**:
- **Phase 1**: Evaluate mold performance and stability metrics
- **Phase 2**: Calculate key performance indicators and normalized productivity

**Analysis Criteria**:
- Accuracy assessment
- Consistency measurement  
- Compliance with standard operational limits
- Data completeness validation

**Key Performance Indicators**:
- Theoretical output calculations
- Actual output measurements
- Efficiency metrics
- Normalized productivity

**Output**:
- Mold stability index with comprehensive performance metrics
- Stability assessment reports based on active cavities and cycle times

📋 *Details: [historyProcessor documentation](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/autoPlanner/initialPlanner/OptiMoldIQ_historyProcessor_review.md)*

---

### 2. `FeatureWeightCalculator`
**Purpose**: Sophisticated manufacturing analytics for confidence-based feature weighting

**Operations**:
- Historical data statistical analysis using bootstrap methods
- Confidence-based feature importance computation
- Key performance indicator identification
- Predictive reliability assessment for production outcomes

**Statistical Framework**:
- **Bootstrap Analysis**: 500 bootstrap samples for robust inference
- **Confidence Intervals**: 95% confidence level for statistical reliability
- **Minimum Sample Requirements**: Ensures validity with minimum 10 samples
- **Scaling Methods**: Absolute scaling for consistent feature comparison

**Output**:
- Feature weight reports with confidence metrics
- Manufacturing process optimization insights
- Predictive analytics for production planning
  
📋 *Details: [featureWeightCalculator documentation](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/autoPlanner/OptiMoldIQ_featureWeightCalculator_review.md)*

---

## System Configuration

### Operational Parameters
```
Efficiency Factor: 0.85
Loss Factor: 0.03
```

### Mold Stability Thresholds
```
Cavity Stability Threshold: 0.6
Cycle Stability Threshold: 0.4
Total Records Threshold: 30
```

### Feature Weight Configuration
```
Scaling Method: Absolute
Confidence Weight: 0.3
Bootstrap Samples: 500
Confidence Level: 95%
Minimum Sample Size: 10
```

### Target Optimization Parameters
```
Shift NG Rate: Minimize
Shift Cavity Rate: 1.0
Shift Cycle Time Rate: 1.0  
Shift Capacity Rate: 1.0
```

---

## Data Flow

### Input
- **Shared Database**: Standardized production data from Shared Database Building phase
- **Path Annotations**: `path_annotations.json` for data source mapping
- **Database Schemas**: Configuration and validation schemas
- **Order Progress Data**: Production tracking and change logs

### Processing Steps
1. **Historical Analysis**: Process historical production data for mold performance
2. **Stability Calculation**: Calculate mold stability index with defined thresholds
3. **Feature Weighting**: Compute confidence-based feature importance using statistical methods
4. **Insight Generation**: Create comprehensive analytical reports and insights

### Output Directory Structure

```
./shared_db/
├── HistoryProcessor
|   └── mold_stability_index/
|       ├──historical_db
|       ├──newest
|       |  └── mold_stability_index.xlsx
|       └── change_log.txt
└── FeatureWeightCalculator
       ├── historical_db/
       ├── newest/
       |   └── confidence_report.txt
       ├── weights_hist.xlsx
       └── change_log.txt
```

## Workflow Diagrams

📊 **Detailed workflows**:
- [historyProcessor Workflow](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/workflows/OptiMoldIQ_historyProcessorWorkflow.md)  
- [featureWeightCalculator Workflow](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/workflows/OptiMoldIQ_featureWeightCalculatorWorkflow.md)  
  
---

## Implementation Code

### HistoryProcessor Setup
```python
from agents.autoPlanner.initialPlanner.history_processor import HistoryProcessor

history_processor = HistoryProcessor(
    source_path = f"{shared_db_dir}/DataLoaderAgent/newest",
    annotation_name = 'path_annotations.json',
    databaseSchemas_path = f"{mock_db_dir}/databaseSchemas.json",
    folder_path = f"{shared_db_dir}/OrderProgressTracker",
    target_name = "change_log.txt",
    default_dir = shared_db_dir,
    efficiency = 0.85,
    loss = 0.03,
)

# Calculate mold stability index
history_processor.calculate_and_save_mold_stability_index(
    cavity_stability_threshold = 0.6,
    cycle_stability_threshold = 0.4,
    total_records_threshold = 30
)
```

### FeatureWeightCalculator Setup
```python
from agents.autoPlanner.feature_weight_calculator import FeatureWeightCalculator

# Load mold stability index
mold_stability_index_folder = f"{shared_db_dir}/HistoryProcessor/mold_stability_index"
mold_stability_index_target_name = "change_log.txt"

# Calculate and save feature weights for mold-machine priority matrix
FeatureWeightCalculator(
    source_path = f"{shared_db_dir}/DataLoaderAgent/newest",
    annotation_name = 'path_annotations.json',
    databaseSchemas_path = f"{mock_db_dir}/databaseSchemas.json",
    folder_path = f"{shared_db_dir}/OrderProgressTracker",
    target_name = "change_log.txt",
    default_dir = shared_db_dir,
    efficiency = 0.85,
    loss = 0.03,
    scaling = 'absolute',
    confidence_weight = 0.3,
    n_bootstrap = 500,
    confidence_level = 0.95,
    min_sample_size = 10,
    feature_weights = None,
    targets = {'shiftNGRate': 'minimize',
                'shiftCavityRate': 1.0,
                'shiftCycleTimeRate': 1.0,
                'shiftCapacityRate': 1.0}
).calculate_and_save_report(mold_stability_index_folder,
                            mold_stability_index_target_name)
```

---

## Trigger Mechanism

### Trigger Logic

The Historical Insight Addition Phase is triggered **monthly** with automatic execution:

```python
# Monthly automated execution
def monthly_insight_generation():
    # 1. Run HistoryProcessor
    history_processor.calculate_and_save_mold_stability_index(
        cavity_stability_threshold = 0.6,
        cycle_stability_threshold = 0.4,
        total_records_threshold = 30
    )
    
    # 2. Run FeatureWeightCalculator
    feature_calculator = FeatureWeightCalculator(...)
    feature_calculator.calculate_and_save_report(
        mold_stability_index_folder,
        mold_stability_index_target_name
    )
    
    return "Historical insights generated and saved to shared database"

# Automated scheduling
schedule.every().month.do(monthly_insight_generation)
```

### Execution Flow
1. **HistoryProcessor** analyzes historical data and generates mold stability insights
2. **FeatureWeightCalculator** processes the stability data and computes feature weights
3. **Auto-Save Functionality**: All reports automatically saved to shared database
4. **Shared Database Population**: Insights become available for downstream planning phases

This automated approach ensures consistent insight generation without manual intervention.

---

## Key Benefits

- **Data-Driven Insights**: Transforms raw historical data into actionable production intelligence
- **Statistical Reliability**: Bootstrap-based analysis ensures robust statistical conclusions
- **Automated Processing**: Monthly execution eliminates manual intervention requirements
- **Shared Intelligence**: Creates centralized repository of insights for production planning
- **Performance Optimization**: Identifies key performance indicators for manufacturing excellence
- **Predictive Capability**: Enables forecasting of production outcomes based on historical patterns

---

## Quality Assurance

### Data Validation
- **Completeness Checks**: Ensures all required historical data elements are present
- **Statistical Integrity**: Validates calculation accuracy and bootstrap analysis results
- **Threshold Compliance**: Monitors adherence to defined stability and confidence thresholds
- **Consistency Assessment**: Maintains consistency across different analytical methods

### Performance Monitoring
- **Processing Time Tracking**: Monitors monthly execution duration and performance
- **Resource Utilization**: Tracks computational resource usage during analysis
- **Success Rate Monitoring**: Ensures reliable completion of insight generation
- **Error Detection**: Identifies and logs processing anomalies or failures

---

## Integration Points

### Upstream Dependencies
- **Shared Database Building Phase**: Provides standardized historical production data
- **DataLoaderAgent**: Supplies foundational data through newest directory
- **OrderProgressTracker**: Provides production progress and change tracking

### Downstream Consumers
- **Production Planning Phases**: Utilizes generated insights for optimal planning decisions
- **Mold-Machine Priority Matrix**: Leverages feature weights for priority calculations
- **Decision Support Systems**: Consumes insights for strategic manufacturing decisions
- **Performance Dashboards**: Displays historical trends and predictive analytics