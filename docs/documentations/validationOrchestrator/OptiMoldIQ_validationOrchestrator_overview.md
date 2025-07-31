# ValidationOrchestrator Agent Documentation

## Overview

`ValidationOrchestrator` is the main agent responsible for orchestrating and executing validation processes for production data. It acts as a conductor, coordinating three different types of validation to ensure data integrity and consistency across the production system.

## System Architecture

### Role of the ValidationOrchestrator
- **Parent Agent**: Coordinates sub-validation agents
- **Data Validator**: Validates data from multiple sources
- **Result Consolidator**: Aggregates and exports validation reports

### Coordinated Sub-Agents
1. **StaticCrossDataChecker**: Validates data against static reference datasets
2. **PORequiredCriticalValidator**: Validates required fields in purchase orders
3. **DynamicCrossDataValidator**: Validates cross-references among dynamic datasets

### Workflow
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
- See details: [Workflow](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/workflows/OptiMoldIQ_validationOrchestratorWorkflow.md)

## Data Structure

### Dynamic Data (frequently updated)
- **productRecords**: Daily production records
- **purchaseOrders**: Customer purchase orders

### Static Data (reference data)
- **itemInfo**: Master information about items
- **resinInfo**: Resin/material information
- **machineInfo**: Production machine information
- **moldInfo**: Mold details
- **moldSpecificationSummary**: Mold specification summary
- **itemCompositionSummary**: Item composition summary

## Types of Validation

### 1. Static Cross-Data Validation
**Purpose**: Check consistency between dynamic data and static references

**Examples**:
- Does `Item ID` in `productRecords` exist in `itemInfo`?
- Is the `Machine ID` valid as per `machineInfo`?
- Does the `Resin code` match the entries in `resinInfo`?

**See details**: [StaticCrossDataChecker](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations\validationOrchestrator\OptiMoldIQ_staticCrossDataChecker_overview.md)

### 2. Purchase Order Required Field Validation
**Purpose**: Ensure all required fields in purchase orders are filled correctly

**Examples**:
- `Customer ID` must not be empty
- `Order quantity` must be greater than 0
- `Delivery date` must be specified

**See details**: [PORequiredCriticalValidator](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations\validationOrchestrator\OptiMoldIQ_poRequiredCriticalValidator_overview.md)

### 3. Dynamic Cross-Data Validation
**Purpose**: Check consistency among dynamic datasets

**Examples**:
- Do purchase orders and production records align?
- Is the production quantity appropriate for the order?
- Is the production timeline reasonable?

**See details**: [DynamicCrossDataValidator](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations\validationOrchestrator\OptiMoldIQ_dynamicCrossDataValidator_overview.md)

## Usage

### Basic Initialization
```python
# Using default configuration
orchestrator = ValidationOrchestrator()

# Run validations and save results
orchestrator.run_validations_and_save_results()
```

### Custom Configuration Initialization
```python
orchestrator = ValidationOrchestrator(
    source_path='path/to/your/data',
    annotation_name='custom_annotations.json',
    databaseSchemas_path='path/to/schemas.json',
    default_dir='output/directory'
)
```

### Run Validation Without Saving Files
```python
results = orchestrator.run_validations()
# Process results as needed
```

### Output Structure
#### Return Format
```python
results = {
    'static_mismatch': {
        'purchaseOrders': DataFrame,      # Static validation errors in PO
        'productRecords': DataFrame       # Static validation errors in production
    },
    'po_required_mismatch': DataFrame,    # Missing required PO fields
    'dynamic_mismatch': {
        'invalid_items': DataFrame,       # Invalid items
        'info_mismatches': DataFrame      # Cross-reference mismatches
    },
    'combined_all': {
        'item_invalid_warnings': DataFrame,  # Consolidated item warnings
        'po_mismatch_warnings': DataFrame    # Consolidated PO warnings
    }
}
```
#### Output Files
- Excel files: Saved with automatic versioning
- Directory: agents/shared_db/ValidationOrchestrator/
- File name: validation_orchestrator_v{version}.xlsx
  
### Advanced Features
#### Schema Validation
- Automatically checks DataFrame schemas on initialization
- Uses @validate_init_dataframes decorator
- Ensures all required columns are present

#### Error Handling
- Detailed logging with loguru
- Graceful error handling during file loading
- Validation pipeline continues even if a sub-agent fails

#### Data Loading
- Automatic loading of .parquet files
- Path resolution via annotation files
- Memory-efficient DataFrame management

#### Use Cases
##### 1. Daily Data Validation
```python
# Validate new daily data
orchestrator = ValidationOrchestrator(
    source_path='daily_data/2024-01-15'
)
orchestrator.run_validations_and_save_results()
```

##### 2. Historical Data Analysis
```python
# Analyze historical data
orchestrator = ValidationOrchestrator(
    source_path='historical_data/2023'
)
results = orchestrator.run_validations()
# Analyze trends and patterns
```

##### 3. Data Quality Monitoring
```python
# Monitor data quality in real-time
orchestrator = ValidationOrchestrator()
results = orchestrator.run_validations()

# Check number of errors
total_errors = len(results['combined_all']['po_mismatch_warnings'])
if total_errors > threshold:
    send_alert(f"Data quality issues detected: {total_errors} errors")
```

#### Troubleshooting
##### Common Errors
###### 1. FileNotFoundError
```python
# Error: Path to 'productRecords' not found
# Solution: Check `path_annotations.json` and ensure files exist
```
###### 2. Schema Mismatch
```python
# Error: DataFrame columns don't match expected schema
# Solution: Update `databaseSchemas.json` or verify data source
```

###### 3. Memory Issues
```python
# Error: Out of memory when loading large datasets
# Solution: Process data in chunks or increase memory allocation
```

#### Debug Tips
- Enable debug logging: Set log level to DEBUG
- Check data shapes: Look at log output for DataFrame shapes
- Validate schemas: Run schema validation separately
- Test individual validators: Run each sub-agent independently

#### Performance Optimization
##### Recommendations
- Data Partitioning: Split large datasets into smaller chunks
- Parallel Processing: Run validators in parallel where possible
- Caching: Cache static reference data
- Incremental Validation: Only validate newly changed data

##### Memory Management
- Lazy loading of DataFrames
- Automatic cleanup after validation
- Efficient pandas operations

#### Configuration Management
##### Key Configuration Files
- databaseSchemas.json: Defines schemas for all tables
- path_annotations.json: Maps paths to data files
- Agent configs: Individual configurations for each validator agent

##### Best Practices
- Version control: Track schema file changes
- Environment-specific configs: Separate configs for dev/staging/prod
- Validation rules: Document all validation rules
- Change management: Establish process for schema updates

#### Monitoring and Alerting

##### Key Metrics
- Error count: Number of validation errors
- Processing time: Time taken to complete validation
- Data completeness: Percentage of missing data
- Success rate: Pass rate for validations

##### Alert Conditions
- Error count exceeds threshold
- Processing time is too long
- Critical validation failures
- Data pipeline failures