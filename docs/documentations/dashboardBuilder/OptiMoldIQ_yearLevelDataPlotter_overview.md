# YearLevelPlotter

- **Purpose**:
  
    - Generate comprehensive annual Purchase Order (PO) performance dashboards with year-wide analysis covering monthly trends, yearly aggregations, machine efficiency patterns, and mold utilization metrics across entire fiscal year operations.

- **Core responsibilities**: 
  
    - Process and aggregate yearly PO records through integrated data pipeline with historical trend analysis.
    - Generate 9 distinct visualization types covering `monthly performance`, `year performance`, `machine-based year view`, `mold-based year view`, and detailed month-view dashboards by field.
    - Track finished and unfinished PO status with capacity analysis and annual delivery performance.
    - Create monthly trend dashboards showing completion rates, backlog evolution, and seasonal patterns.
    - Produce machine-level year-view analysis with utilization patterns and efficiency trends across 12 months.
    - Create mold-level year-view dashboards tracking annual shot counts, cavity usage, and quality performance.
    - Generate detailed month-view dashboards for specific fields (machine/mold) with up to 10 items per page (multi-page support).
    - Manage parallel/sequential plotting execution based on system resources with optimization for 9 plot types.
    - Archive historical visualization files while maintaining latest versions with timestamp tracking.
    - Export comprehensive PO analysis data to Excel with multiple sheet perspectives.
    - Generate text-based final summary statistics for annual management review.

- **Input**:
  
    - `record_year`: Target year for analysis in `YYYY` format (string, required).
    - `analysis_date` (optional): Date of analysis execution (defaults to current date, format: `YYYY-MM-DD`).
    - `source_path` (optional): Directory containing input data files (default: `agents/shared_db/DataLoaderAgent/newest`).
    - `annotation_name` (optional): JSON file mapping data paths (default: `path_annotations.json`).
    - `databaseSchemas_path` (optional): Database schema configuration file (default: `database/databaseSchemas.json`).
    - `default_dir` (optional): Base output directory (default: `agents/shared_db`).
    - `visualization_config_path` (optional): Visualization styling configuration (default: auto-detected).
    - `enable_parallel` (optional): Enable parallel plotting (default: `True`).
    - `max_workers` (optional): Maximum parallel workers (default: auto-detected from system specs, capped at 10).

- **Output**: ([→ see overviews](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/agents_output_overviews/dashboardBuilder/YearLevelPlotter))
  
    - Excel file: Extracted records with 5 sheets (`finished POs`, `unfinished POs`, `short unfinished summary`, `all progress`, `filtered records`).
    - TXT report: `Final summary` statistics with annual performance KPIs.
    - PNG visualizations: 9+ comprehensive dashboards (2 PO performance views, 2 year views, 5 detailed month-view series) with multi-page outputs for month-view dashboards.
    - Change log tracking all file versions and operations with timestamps.
    - Archived historical versions in `historical_db/` subdirectory.

- **Main Methods**:
  
| Method                                    | Description                                                                                                           |
| ----------------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| `plot_all()`                              | Main orchestrator: processes PO data, generates all visualizations, saves reports, manages archiving, updates log.   |
| `_setup_parallel_config()`                | Analyzes system resources (CPU cores, RAM) and configures optimal parallel processing, capped at 10 workers.         |
| `_setup_schemas()`                        | Loads database schema configuration for column validation and data integrity checks.                                   |
| `_load_base_dataframes()`                 | Loads required base DataFrames (`productRecords`) from annotated paths with error handling.                             |
| `_load_single_dataframe()`                | Helper method to load individual DataFrame with comprehensive error checking and logging.                              |
| `_validate_record_year()`                 | Validates record_year format matches `YYYY` pattern using regex validation.                                              |
| `_prepare_data()`                         | Creates filtered dataframes for visualization: short unfinished summary and combined progress tracking.               |
| `_prepare_plot_tasks()`                   | Creates list of 9 plotting tasks with data tuples, functions, and output paths for parallel/sequential execution.     |
| `_execute_plots_parallel()`               | Executes plotting tasks using ProcessPoolExecutor with concurrent futures and progress tracking.                      |
| `_execute_plots_sequential()`             | Fallback method for sequential plot generation when parallel processing is disabled or fails.                          |
| `_plot_single_chart()`                    | Static worker function to create individual plot with multi-page support and timing/error handling.                   |

- **Data flow**:
  
    - Input year validation (YYYY format) → regex format check
    - `YearLevelDataProcessor` initialization with year and analysis date
    - Raw production records → PO processing pipeline → `finished`/`unfinished` DataFrames
    - productRecords_df filtering by date and year → `filtered_df` with recordMonth column
    - Data preparation → `short_unfinished_df` and `all_progress_df` creation
    - Task preparation (9 plot types) → parallel/sequential execution router
    - Visualization generation (with multi-page support for month-view dashboards) → file saving with timestamps
    - Report generation (final summary) → TXT file export
    - Excel export with 5 sheets → newest directory
    - Archive old files → historical_db migration
    - Change log update with detailed operation history

- **Parallel Processing Logic**:
  
    - **System Detection**:
        - Automatically detects CPU cores using `multiprocessing.cpu_count()`
        - Measures available RAM using `psutil.virtual_memory()`
        - Logs system specifications for debugging and optimization
    
    - **Worker Optimization for Year-Level**:
        - Single-core systems: Parallel disabled, 1 worker
        - Dual-core (Colab-style): 2 workers if RAM ≥ 8GB, else 1 worker
        - Multi-core systems: Uses 75% of available cores (with RAM-based limits)
        - **Caps workers at 10** (number of year-level plot types) to avoid over-parallelization
        - More aggressive than month-level (10 vs 3) due to higher number of independent plots
    
    - **Execution Strategy**:
        - Uses `ProcessPoolExecutor` for CPU-bound matplotlib operations
        - Submits all tasks via `concurrent.futures` with future tracking
        - Collects results as completed with individual timing metrics
        - Handles multi-page plot outputs (saves each page separately for month-view dashboards)
        - Graceful fallback to sequential processing on errors
        - Comprehensive error handling and logging for each worker

- **Data Processing Pipeline**:
  
    1. **YearLevelDataProcessor Integration**:
        - Initializes with record_year (YYYY) and analysis_date
        - Calls `product_record_processing()` to generate:
            - `analysis_timestamp`: Datetime of analysis execution
            - `adjusted_record_year`: Validated and adjusted year string
            - `finished_df`: Completed PO records with full annual metrics
            - `unfinished_df`: In-progress PO records with capacity analysis
            - `final_summary`: Statistical summary dictionary with annual KPIs
    
    2. **Record Filtering**:
        - Filters `productRecords_df` by `analysis_timestamp` (records before analysis date)
        - Filters by `record year` matching `adjusted_record_year`
        - Creates `filtered_df` with `recordMonth` column (`YYYY-MM` format) for monthly aggregation
        - Used for `machine-level` and `mold-level` `year-view` and `month-view` dashboards
    
    3. **Data Preparation** (`_prepare_data()`):
        - Creates `short_unfinished_df`: Subset of unfinished_df with essential columns only
        - Creates `all_progress_df`: Concatenation of finished and unfinished progress columns
        - Both used for monthly and yearly performance dashboards

- **Visualization Outputs** (12+ files total):
    
    1. **{timestamp}_extracted_records_{year}.xlsx**: 

        - 2 sheets (`finished_df`, `unfinished_df`) generated by: `YearLevelDataProcessor` ([→ see detail](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/analyticsOrchestrator/multiLevelDataAnalytics/OptiMoldIQ_yearLevelDataProcessor_overview.md)) 

        - *Summary of Relationships*:
            | Sheet | Derived From | Aggregation Level | Primary Use |
            |-------|--------------|-------------------|-------------|
            | `finished_df` | `purchaseOrders_df` + `productRecords_df` | PO-level (Purchase Order) | Track completed orders, measure on-time delivery performance |
            | `unfinished_df` | `purchaseOrders_df` + `productRecords_df` + `moldInfo_df` + `moldSpecificationSummary_df` | PO-level with mold capacity analysis | Identify production bottlenecks, forecast lead times, detect capacity risks |

        - *1.1. Sheet 1 — `finished_df`*: 

          - *Description*: Contains all purchase orders that have been fully completed (`itemRemainQuantity ≤ 0`) as of the analysis date. This sheet focuses on delivery performance evaluation and includes orders that may have overproduction.
        
          - *Processing Logic*:
            - Filter purchase orders with `poETA` within the target `record_year` and merge with historical backlog orders
            - Merge with production records aggregated by `poNote` to get total produced quantities (`itemGoodQuantity`)
            - Calculate `itemRemainQuantity = itemQuantity - itemGoodQuantity` (capped at 0 for overproduction cases)
            - Flag orders where `itemRemainQuantity ≤ 0` as `poStatus = 'finished'`
            - Classify delivery performance: `etaStatus = 'ontime'` if `lastRecord ≤ poETA`, else `'late'`
            - Track overproduction: `overproduction_quantity = abs(itemRemainQuantity)` when negative
          
          - *Key Columns*:
              | Column | Description |
              |--------|-------------|
              | `poNo` | Purchase order number (unique identifier) |
              | `poReceivedDate` | Date when PO was received |
              | `poETA` | Expected delivery date for the PO |
              | `itemCode` / `itemName` / `itemCodeName` | Product identification (code, name, combined format) |
              | `itemQuantity` | Total ordered quantity |
              | `itemGoodQuantity` | Total quantity successfully produced |
              | `itemRemainQuantity` | Remaining quantity to produce (≤ 0 for finished orders) |
              | `overproduction_quantity` | Excess quantity produced beyond order requirement |
              | `poStatus` | Production status ('finished') |
              | `etaStatus` | Delivery timeliness ('ontime' or 'late') |
              | `firstRecord` / `lastRecord` | First and last production record dates |
              | `moldHistNum` | Number of unique molds used during production |
              | `moldHist` | List of molds used (slash-separated) |
              | `is_backlog` | Boolean flag indicating if order was carried over from previous years |
      
        - *1.2. Sheet 2 — `unfinished_df`*: 

          - *Description*: Contains purchase orders that are either in progress or not yet started, with detailed capacity analysis per mold group. This sheet is critical for production planning, identifying bottlenecks, and forecasting completion risks.
         
          - *Processing Logic*:
            - Combine orders with `poStatus = 'in_progress'` (has production history) and `'not_started'` (no history yet)
            - For **not_started orders**: estimate capacity using `moldSpecificationSummary_df` (available mold list per item)
            - For **in_progress orders**: calculate capacity based on actual `moldHist` (molds already used)
            - Merge mold technical specs (`moldCavityStandard`, `moldSettingCycle`) from `moldInfo_df`
            - Calculate per-mold and total item capacity: `moldMaxHourCapacity = (3600 / moldSettingCycle) * moldCavityStandard`
            - Sort by `moldList` and `poReceivedDate`, then compute cumulative metrics:
                 - `accumulatedQuantity`: cumulative remaining quantity per mold group
                 - `accumulatedRate`: progress ratio within mold group
            - Estimate lead times:
                 - `avgEstimatedLeadtime`: time needed using average mold capacity
                 - `totalEstimatedLeadtime`: time needed using all molds simultaneously
                 - `avgCumsumLT` / `totalCumsumLT`: cumulative lead time across all orders in same mold group
            - Calculate remaining time windows:
                 - `poOTD`: Order-to-Delivery time (poETA - poReceivedDate)
                 - `poRLT`: Remaining Lead Time (poETA - analysis_timestamp, 0 if past ETA)
            - Detect capacity issues:
                 - `overAvgCapacity`: cumulative lead time exceeds remaining time (single mold scenario)
                 - `overTotalCapacity`: exceeds even with all molds (critical overcapacity)
                 - `capacityWarning`: combined flag for any capacity risk
                 - `capacitySeverity`: 'normal', 'high', or 'critical'
            - Classify ETA status considering both completion and capacity:
                  - 'ontime': finished on time OR in progress with sufficient capacity
                  - 'late': finished late OR in progress but insufficient capacity
                  - 'expected_ontime': not started but capacity sufficient
           
          - *Key Columns*:
               | Column | Description |
               |--------|-------------|
               | `poNo` | Purchase order number |
               | `poReceivedDate` / `poETA` | Order received date and expected delivery date |
               | `itemCodeName` | Combined item identifier (code + name) |
               | `itemQuantity` | Total ordered quantity |
               | `itemGoodQuantity` | Quantity produced so far (may be null for not_started) |
               | `itemNGQuantity` | Defective quantity produced |
               | `itemRemainQuantity` | Remaining quantity to produce (> 0) |
               | `poStatus` | 'in_progress' or 'not_started' |
               | `completionProgress` | Production completion rate (0.0 to 1.0) |
               | `moldNum` / `moldList` | Number of molds and their identifiers (slash-separated) |
               | `moldHistNum` / `moldHist` | Number and list of molds actually used (for in_progress orders) |
               | `totalItemCapacity` | Combined hourly production capacity of all molds |
               | `avgItemCapacity` | Average hourly capacity per mold |
               | `accumulatedQuantity` | Cumulative remaining quantity in the same mold group |
               | `accumulatedRate` | Position ratio within mold group (0.0 to 1.0) |
               | `totalRemainByMold` | Total remaining quantity across all orders using same mold(s) |
               | `avgEstimatedLeadtime` | Estimated days needed (single mold average capacity) |
               | `totalEstimatedLeadtime` | Estimated days needed (all molds working simultaneously) |
               | `avgCumsumLT` / `totalCumsumLT` | Cumulative lead time considering queue of orders on same molds |
               | `poOTD` | Order-to-Delivery timespan (timedelta) |
               | `poRLT` | Remaining Lead Time until ETA (timedelta, 0 if overdue) |
               | `overAvgCapacity` / `overTotalCapacity` | Boolean flags for capacity violations |
               | `is_overdue` | Boolean flag: past ETA or insufficient time remaining |
               | `etaStatus` | Delivery risk assessment ('ontime', 'late', 'expected_ontime', 'unknown') |
               | `capacityWarning` | Boolean flag for any capacity concern |
               | `capacitySeverity` | Risk level ('normal', 'high', 'critical') |
               | `capacityExplanation` | Human-readable severity description |
               | `is_backlog` | Boolean flag for orders carried over from previous years |
       
    - 3 sheets (`short_unfinished_df`, `all_progress_df`, `filtered_df`) generated by `YearLevelPlotter`: 

        - *Summary of Relationships*:
            | Sheet              | Derived From               | Aggregation Level | Primary Use                            |
            | ------------------ | -------------------------- | ----------------- | -------------------------------------- |
            | `short_unfinished_df` | `unfinished_df `            | PO-level          | Display unfinished POs with key columns for early warning |
            | `all_progress_df`    | `finished_df` + `unfinished_df` | PO-level        | Track overall progress of all POs (both finished and unfinished) |
            | `filtered_df`        | `productRecords_df`         | Record-level      | Analyze daily records within the target year before analysis date |

        - *1.3. Sheet 3 — `short_unfinished_df`*: 

          - *Description*: Contains unfinished purchase orders with selected essential columns for monitoring and early warning purposes. This is a simplified view of `unfinished_df` focusing on critical operational metrics.
        
          - *Processing Logic*:
            - Filters 19 essential columns (`REQUIRED_UNFINISHED_SHORT_COLUMNS`) from the full `unfinished_df` (which has 36 columns)
            - Removes detailed capacity calculation columns, mold lists, and intermediate metrics
            - Retains only actionable information needed for daily monitoring and alerts

          - *Key Columns* (18 columns from `REQUIRED_UNFINISHED_SHORT_COLUMNS`):
              | Column | Description |
              |--------|-------------|
              | **Order Identification** | |
              | poNo | Purchase order number (unique identifier) |
              | poETA | Expected delivery date |
              | itemCodeName | Combined product identifier (code + name) |
              | **Quantity Metrics** | |
              | itemQuantity | Total ordered quantity |
              | itemGoodQuantity | Quantity successfully produced so far |
              | itemNGQuantity | Defective quantity produced |
              | itemRemainQuantity | Remaining quantity to produce (> 0) |
              | **Status & Progress** | |
              | is_backlog | Boolean flag: order carried over from previous periods |
              | proStatus | Production status (e.g., 'in_production', 'pending') |
              | poStatus | Purchase order status ('in_progress' or 'not_started') |
              | completionProgress | Production completion rate (0.0 to 1.0) |
              | moldHistNum | Number of unique molds used during production |
              | **Delivery & Risk Assessment** | |
              | etaStatus | Delivery risk ('ontime', 'late', 'expected_ontime', 'unknown') |
              | is_overdue | Boolean flag: past ETA or insufficient time remaining |
              | **Capacity Warning Flags** | |
              | overAvgCapacity | Boolean: exceeds capacity using average single mold |
              | overTotalCapacity | Boolean: exceeds capacity even with all molds (critical) |
              | capacityWarning | Boolean: any capacity concern detected |
              | capacitySeverity | Risk level ('normal', 'high', 'critical') |
              | capacityExplanation | Human-readable severity description |
      
        - *1.4. Sheet 4 — `all_progress_df`*: 
          
          - *Description*: Comprehensive progress tracking dataset combining both finished and unfinished purchase orders. Provides a unified view of all orders in the target year for comparative analysis and overall performance monitoring.

          - *Processing Logic*:
            - Extracts 11 common columns (`REQUIRED_PROGRESS_COLUMNS`) from both `finished_df` and `unfinished_df`
            - Concatenates vertically to create a complete order list
            - Resets index for continuous row numbering
            - Enables cross-status comparison and aggregated reporting
          
          - *Key Columns* (11 columns from `REQUIRED_PROGRESS_COLUMNS`):
              | Column | Description |
              |--------|-------------|
              | **Order Identification** | |
              | poNo | Purchase order number (unique across both finished and unfinished) |
              | itemCodeName | Combined product identifier |
              | poETA | Expected delivery date |
              | **Order Classification** | |
              | is_backlog | Boolean: carried over from previous periods |
              | poStatus | Current status ('finished', 'in_progress', 'not_started') |
              | proStatus | Production status detail |
              | **Quantity Tracking** | |
              | itemQuantity | Total ordered quantity |
              | itemGoodQuantity | Total good quantity produced |
              | itemNGQuantity | Total defective quantity |
              | **Performance Metrics** | |
              | etaStatus | Delivery performance ('ontime', 'late', 'expected_ontime', 'unknown') |
              | moldHistNum | Number of unique molds used (indicates production complexity) |
          
          - *Usage Notes*:
            - Ideal for calculating aggregate metrics like total completion rate, on-time delivery percentage
            - Allows filtering and grouping by `poStatus` to compare finished vs unfinished orders
            - `moldHistNum` helps identify multi-mold orders that require more coordination

        - *1.5. Sheet 5 — `filtered_df`*: 
          
          - *Description*: Daily production records filtered for the target year up to the analysis date. This is the most granular view, showing individual production transactions rather than aggregated PO summaries.
        
          - *Processing Logic*:
            - Filters `productRecords_df` (raw daily production logs) by two conditions:
              - `recordDate` must be strictly before the analysis timestamp date
              - `recordDate.year` must equal the adjusted record year
            - Adds a derived column `recordMonth` (YYYY-MM format) for easy month-level grouping
            - Retains all original columns from `productRecords_df` for detailed analysis
          
          - *Key Columns* (all columns from `productRecords_df` + 1 new column):
              | Column | Description |
              |--------|-------------|
              | **Date & Time** | |
              | recordDate | Date of the production record (datetime) |
              | recordMonth | **Derived** month in YYYY-MM format (added by plotter) |
              | **Order & Product Info** | |
              | poNo / poNote | Purchase order identifiers |
              | itemCode / itemName / itemCodeName | Product identifiers |
              | **Production Quantities** | |
              | itemGoodQuantity | Good quantity produced in this record |
              | itemNGQuantity | Defective quantity in this record |
              | itemTotalQuantity | Total quantity attempted (good + NG) |
              | **Production Details** | |
              | moldCode / moldName | Mold used for this production run |
              | machineCode / machineName | Machine used |
              | operatorCode / operatorName | Operator responsible |
              | shiftCode / shiftName | Work shift |
              | **Process Metrics** | |
              | cycleTime | Actual cycle time per piece |
              | cavityUsed | Number of cavities used |
              | runTime / downTime | Production and non-production time |
              | **Quality & Status** | |
              | qualityStatus | Pass/Fail quality check |
              | recordStatus | Record validity status |
              | remarks / notes | Additional comments |
            
          - *Usage Notes*:
            - Used for time-series analysis, trend detection, and yearly/monthly performance tracking
            - Enables drill-down from PO-level summaries to individual production events
            - Supports visualization of production velocity, quality trends, and resource utilization
            - All records are historical (before analysis date), ensuring data consistency
            - **Scope**: Covers entire year, not just a single month

        - *Data Flow Relationships*:
          ```
                  ┌─────────────────────────────────────────────────────────────────┐
                  │                     Raw Data Sources                             │
                  └─────────────────────────────────────────────────────────────────┘
                                              │
                          ┌───────────────────┼───────────────────┬─────────────────┐
                          │                   │                   │                 │
                          ▼                   ▼                   ▼                 ▼
                  productRecords_df   purchaseOrders_df   moldInfo_df   moldSpecificationSummary_df
                          │                   │                   │                 │
                          │                   │                   └─────────┬───────┘
                          │                   │                             │
                          │                   ▼                             │
                          │         YearLevelDataProcessor                  │
                          │                   │                             │
                          │                   │ (merge with mold data)      │
                          │                   │ <───────────────────────────┘
                          │                   │
                          │       ┌───────────┴────────────┐
                          │       │                        │
                          │       ▼                        ▼
                          │   finished_df             unfinished_df
                          │   (PO completed:          (PO in-progress or not_started:
                          │   itemRemainQuantity ≤ 0)  itemRemainQuantity > 0)
                          │   [Sheet 1]               [Sheet 2]
                          │       │                        │
                          │       │                        │
                          ▼       │                        │
                  YearLevelPlotter│                        │
                          │       │                        │
                          ▼       │                        ▼
                  filtered_df    │              short_unfinished_df
                  (record-level  │              (19 essential columns)
                  for entire year)│              [Sheet 3]
                  [Sheet 5]      │                        
                                  │                        
                                  └────────┬───────────────┘
                                          │
                                          ▼
                                  all_progress_df
                                  (11 common columns:
                                  finished + unfinished)
                                  [Sheet 4]

          Legend:
          ───── : Data transformation/filtering
          │     : Derivation/aggregation relationship
          └──┬──┘: Merge/concatenation operation
          <────: Reference/lookup relationship
          ```
          
        - *Sheet Selection Guide*:
            | Use Case                                    | Recommended Sheet      | Reason                          |
            | ------------------------------------------- | ---------------------- | ------------------------------- |
            | Monitoring dashboard                        | short_unfinished_df    | Focused on actionable alerts    |
            | Capacity planning & bottleneck analysis     | unfinished_df          | Full capacity calculation details |
            | Overall month performance report            | all_progress_df        | Unified finished + unfinished view |
            | Time-series production trend analysis       | filtered_df            | Record-level granularity        |
            | On-time delivery rate calculation           | finished_df            | Completed orders only           |
            | Early warning system (overdue/capacity)     | short_unfinished_df    | Pre-filtered risk indicators    |

    **TXT Report (1 file)**:

    1. **{timestamp}_final_summary_{year}.txt**: 
        
        - `final_summary` generated by: `YearLevelDataProcessor` ([→ see detail](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/analyticsOrchestrator/multiLevelDataAnalytics/OptiMoldIQ_yearLevelDataProcessor_overview.md))  

        - *Description*: A comprehensive text report providing high-level overview of manufacturing performance for the target year. This file serves as an executive summary for quick assessment of production status, delivery performance, and capacity risks. The summary is structured in two main sections: validation parameters and analysis results.

        - *Content Structure*:
        
          **Section 1: VALIDATION SUMMARY**
          - Confirms the temporal scope of analysis (year-level)
          - Documents any automatic adjustments made to analysis parameters
          - Ensures transparency in data availability constraints
          
          **Section 2: ANALYSIS RESULTS**
          - Quantifies overall production performance metrics
          - Highlights capacity warnings and bottleneck risks
          - Tracks backlog orders requiring attention
          - Provides monthly breakdown of production progress
        
        - *Key Metrics*:
            | Metric                            | Meaning                                          |
            | --------------------------------- | ------------------------------------------------ |
            | **VALIDATION SUMMARY SECTION** | |
            | Record year (requested)           | The originally requested target year for analysis (format: YYYY) |
            | Record year (adjusted)            | The actual year used after validation (only shown if different from requested) |
            | Analysis date (validated)         | The final cutoff date for including production records (format: YYYY-MM-DD) |
            | Adjusted from                     | Original analysis date before automatic adjustment (only shown if adjusted due to data availability) |
            | **ANALYSIS SUMMARY SECTION** | |
            | Record year (requested)           | Restatement of the target year being analyzed |
            | Analysis date (validated)         | Same as validated analysis date, restated for clarity |
            | **TOTAL PRODUCTION PROGRESS** | |
            | Production progress               | Overall production completion: good_quantity / total_quantity (X,XXX / Y,YYY - Z.ZZ%) |
            | Finished POs                      | Count and percentage of completed orders (X/Y - Z.ZZ%) |
            | In-progress POs                   | Count and percentage of orders currently in production (X/Y - Z.ZZ%) |
            | Not-start POs                     | Count and percentage of orders not yet started (X/Y - Z.ZZ%) |
            | **TEMPORAL SCOPE** | |
            | Unique months in poReceivedDate   | List of all months when POs were received (format: ['YYYY-MM', ...]) |
            | Unique months in poETA            | List of all ETA months covered in the analysis (format: ['YYYY-MM', ...]) |
            | **MONTHLY PRODUCTION PROGRESS** | |
            | ETA period: YYYY-MM               | Production progress for each ETA month: good_quantity/total_quantity (Z.ZZ%) |
            | (BACKLOG) flag                    | Indicates if the month contains backlog orders from previous periods |
            | Finished POs (per month)          | Count and percentage of completed orders for that ETA month |
            | In-progress POs (per month)       | Count and percentage of in-progress orders for that ETA month |
            | Not-start POs (per month)         | Count and percentage of not-started orders for that ETA month |
    
    **PNG Visualizations (9+ files, potentially multi-page)**:
    
    **1. Monthly Performance Dashboard**:
    
    - *Filename*: `monthly_performance_dashboard_{year}.png`
    
    - *Generated by*: `monthly_performance_plotter()`
    
    - *Purpose*: Provides comprehensive year-over-year analysis of production and delivery performance broken down by month, enabling identification of seasonal patterns, capacity bottlenecks, and monthly trends in order fulfillment.

    - *Input Features*:
        | Feature                            | Description                                                                 |
        | ---------------------------------- | --------------------------------------------------------------------------- |
        | `unfinished_df`                    | DataFrame containing active/incomplete POs with required columns            |
        | `poNo`                             | Purchase Order number (primary identifier)                                  |
        | `itemCodeName`                     | Product code and name (for item identification)                             |
        | `moldHistNum`                      | Mold history number (tracking mold usage)                                   |
        | `itemQuantity`                     | Total ordered quantity                                                      |
        | `itemGoodQuantity`                 | Quantity of good/accepted items produced                                    |
        | `itemNGQuantity`                   | Quantity of defective/rejected items                                        |
        | `itemRemainQuantity`               | Remaining quantity to be produced                                           |
        | `completionProgress`               | Completion percentage (0-100%)                                              |
        | `proStatus`                        | Production status (e.g., In Progress, Completed, Pending)                   |
        | `poStatus`                         | Purchase Order status                                                       |
        | `poETA`                            | Expected Time of Arrival/delivery date                                      |
        | `etaStatus`                        | ETA compliance status (On-time, Early, Late)                                |
        | `is_overdue`                       | Boolean flag indicating overdue status                                      |
        | `is_backlog`                       | Boolean flag indicating backlog status                                      |
        | `overAvgCapacity`                  | Flag for orders exceeding average capacity                                  |
        | `overTotalCapacity`                | Flag for orders exceeding total capacity                                    |
        | `capacityWarning`                  | Capacity warning indicator                                                  |
        | `capacitySeverity`                 | Severity level of capacity issues                                           |
        | `capacityExplanation`              | Detailed explanation of capacity concerns                                   |
        | `all_progress_df`                  | DataFrame with all POs (finished + unfinished) for trend analysis           |
        | `record_year`                      | Target year for analysis (string format, e.g., "2024")                      |
        | `analysis_timestamp`               | Date when analysis was performed (datetime object)                          |
        | `visualization_config_path` *(optional)* | Path to custom JSON config for style and layout overrides             |

    - *Processing Logic*:
        - Validation: Ensures dataframe contains all required columns via `validate_dataframe()`.
        - Configuration Loading: Loads default or external visualization config via `load_visualization_config()`.
        - Visualization Setup: figure layout (9-row × 2-column grid layout via `row_nums`, `column_nums`).  

    - *Plotting Workflow*:
        - Sequentially populates subplots with specialized analytics visualizations:
            | Plot Function                        | Purpose / Insight                                                                                                                                                                                |
            | ------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
            | **`plot_progress_bar()`**            | Visualizes **overall monthly production completion** using a gradient progress bar — computes total `itemGoodQuantity / itemQuantity` and styles it with color-coded progress tiers (red→green). |
            | **`plot_late_items_bar()`**          | Highlights **items with `etaStatus = 'late'`** by plotting their `itemRemainQuantity` in a horizontal bar chart — helps identify delayed items and visualize their completion progress vs remaining quantity. Bars are color-coded by `poStatus` for quick differentiation. |
            | **`plot_kpi_cards()`**               | Summarizes **key KPI metrics** in colored dashboard cards — e.g., total POs, backlog, finished, in-progress, not-started, late POs, and progress averages. Provides a compact high-level snapshot of production status and quality.                                         |
            | **`plot_monthly_po_quantity()`**     | Shows **monthly PO trends** with a combined bar + line chart — bars represent the number of POs per month, line shows total `itemQuantity`. Includes year boundary markers and month-over-month comparison to track production volume fluctuations.                          |
            | **`plot_monthly_eta_status()`**      | Analyzes **monthly ETA performance** by displaying stacked bars grouped by `proStatus` (finished/unfinished) and segmented by `etaStatus` (late/ontime/expected_ontime) — uses hatching patterns to distinguish production status and percentage labels to show late ratios. |
            | **`plot_ng_rate_distribution()`**    | Visualizes **monthly distribution of NG (defect) rates** across 6 bins (Not Progress, 0-20%, 20-40%, 40-60%, 60-80%, 80-100%) — uses background boxes with pattern overlays to show PO count per NG rate category, helping identify quality trends and problem months.      |
          - Each subplot is styled consistently using theme-defined font sizes (`sizes`), colors (`colors`), and spacing parameters.
          - All axes, legends, and labels are harmonized for a clean, presentation-ready layout.

    - *Output Features*:
        | Output                                   | Type                       | Description                                                    |
        | ---------------------------------------- | -------------------------- | -------------------------------------------------------------- |
        | `monthly_performance_dashboard_{year}.png` | `.png` image             | Complete multi-panel dashboard visualization                   |
        | `Figure` object                          | `matplotlib.figure.Figure` | Returned figure handle (for display or saving)                 |
        | **Progress Overview Panel**              | Bar chart                  | Aggregate completion status with percentage breakdown          |
        | **Monthly PO Quantity Trends**           | Time series/bar chart      | Total orders, completed vs incomplete by month                 |
        | **Monthly ETA Status Distribution**      | Stacked/grouped bar chart  | On-time delivery rates, early/late patterns by month           |
        | **NG Rate Analysis**                     | Line/bar chart             | Quality performance by month, defect rate trends               |
        | **Late Items Summary**                   | Horizontal bar chart       | Current overdue POs by severity with aging analysis            |
        | **KPI Cards**                            | Text boxes with metrics    | Key metrics (total POs, completion %, avg lead time, quality)  |
        | **Dashboard Title**                      | Figure suptitle            | Year and analysis timestamp displayed at top                   |
        | **Legend**                               | Auto-generated             | Color coding for statuses, categories, and severity levels     |
        
    **2. Year Performance Dashboard**:
    
    - *Filename*: `year_performance_dashboard_{year}.png`

    - *Generated by*: `year_performance_plotter()`

    - *Purpose*: Provides comprehensive annual analysis of production and delivery performance across the entire year, enabling identification of overall trends, capacity utilization patterns, quality metrics, and year-end fulfillment status. This dashboard offers a holistic view of yearly operations for strategic decision-making.

    - *Input Features*:
        | Feature                            | Description                                                                 |
        | ---------------------------------- | --------------------------------------------------------------------------- |
        | `unfinished_df`                    | DataFrame containing active/incomplete POs with required columns            |
        | `poNo`                             | Purchase Order number (primary identifier)                                  |
        | `itemCodeName`                     | Product code and name (for item identification)                             |
        | `moldHistNum`                      | Mold history number (tracking mold usage)                                   |
        | `itemQuantity`                     | Total ordered quantity                                                      |
        | `itemGoodQuantity`                 | Quantity of good/accepted items produced                                    |
        | `itemNGQuantity`                   | Quantity of defective/rejected items                                        |
        | `itemRemainQuantity`               | Remaining quantity to be produced                                           |
        | `completionProgress`               | Completion percentage (0-100%)                                              |
        | `proStatus`                        | Production status (e.g., In Progress, Completed, Pending)                   |
        | `poStatus`                         | Purchase Order status                                                       |
        | `poETA`                            | Expected Time of Arrival/delivery date                                      |
        | `etaStatus`                        | ETA compliance status (On-time, Early, Late)                                |
        | `is_overdue`                       | Boolean flag indicating overdue status                                      |
        | `is_backlog`                       | Boolean flag indicating backlog status                                      |
        | `overAvgCapacity`                  | Flag for orders exceeding average capacity                                  |
        | `overTotalCapacity`                | Flag for orders exceeding total capacity                                    |
        | `capacityWarning`                  | Capacity warning indicator                                                  |
        | `capacitySeverity`                 | Severity level of capacity issues                                           |
        | `capacityExplanation`              | Detailed explanation of capacity concerns                                   |
        | `all_progress_df`                  | DataFrame with all POs (finished + unfinished) for comprehensive analysis   |
        | `record_year`                      | Target year for analysis (string format, e.g., "2024")                      |
        | `analysis_timestamp`               | Date when analysis was performed (datetime object)                          |
        | `visualization_config_path` *(optional)* | Path to custom JSON config for style and layout overrides             |

    - *Processing Logic*:
        - Validation: Ensures dataframe contains all required columns via `validate_dataframe()`.
        - Configuration Loading: Loads default or external visualization config via `load_visualization_config()`.
        - Visualization Setup: Creates figure layout (10-row × 3-column grid layout via `row_nums`, `column_nums`).

    - *Plotting Workflow*:
        - Sequentially populates subplots with specialized analytics visualizations:
            | Plot Function                        | Purpose / Insight                                                                                                                                                                                |
            | ------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
            | **`plot_progress_bar()`**            | Visualizes **overall monthly production completion** using a gradient progress bar — computes total `itemGoodQuantity / itemQuantity` and styles it with color-coded progress tiers (red→green). |
            | **`plot_po_status_pie()`**           | Shows **distribution of ETA statuses** (`etaStatus`) for POs under a specific `poStatus` (e.g., *in-progress*, *finished*, *not-started*), revealing on-time vs delayed proportions.             |
            | **`plot_backlog_analysis()`**        | Compares **backlog vs non-backlog PO counts**, highlighting how many orders are pending backlog (`is_backlog = True`) versus active.                                                             |
            | **`plot_overdue_analysis()`**        | Displays **overdue vs on-time breakdown** of POs (`is_overdue`) segmented by their `poStatus` — identifies which stages have most overdue orders.                                                |
            | **`plot_capacity_warning_matrix()`** | Generates a **heatmap of capacity issues**, cross-tabulating `capacityWarning` vs `capacitySeverity` to show where and how severe capacity constraints are.                                      |
            | **`plot_top_items_bar()`**         | Displays **Top 10 items with the largest remaining quantities** (`itemRemainQuantity`) in a horizontal bar chart. Also annotates each bar with its completion rate (`completionProgress`) and quantity, revealing which unfinished items dominate the workload. |
            | **`plot_capacity_severity()`**     | Shows **distribution of capacity severity levels** (`capacitySeverity`) across POs, using color-coded bars to highlight how many orders fall into each severity class (e.g., *low*, *medium*, *high*).                                                          |
            | **`plot_progress_distribution()`** | Analyzes **how POs are distributed across completion ranges** (`completionProgress`), grouping them into progress bins (0–25%, 25–50%, 50–75%, 75–100%) to visualize production progress spread.                                                                |
            | **`plot_mold_nums()`**             | Summarizes **mold usage diversity** among *finished* POs, showing how many orders were completed using each `moldHistNum` — a quick indicator of mold workload and utilization.                                                                                 |
            | **`plot_late_items_bar()`**          | Highlights **items with `etaStatus = 'late'`** by plotting their `itemRemainQuantity` in a horizontal bar chart — helps identify delayed items and visualize their completion progress vs remaining quantity. Bars are color-coded by `poStatus` for quick differentiation. |
            | **`plot_top_ng_items_bar()`**        | Displays **Top 10 items with the highest NG rate** (`itemNGQuantity / (itemGoodQuantity + itemNGQuantity)`), enabling detection of quality issues. Each bar shows NG% and total quantity, color-coded by `poStatus`.                                                        |
            | **`plot_ng_rate()`**                 | Visualizes **distribution of NG rate bins (0–20%, 20–40%, …)** using a stylized bar chart with patterned overlays. Highlights how many POs fall into each NG quality band, with “Not Progress” bin representing unstarted or zero-output orders.                            |
            | **`plot_kpi_cards()`**               | Summarizes **key KPI metrics** in colored dashboard cards — e.g., total POs, backlog, finished, in-progress, not-started, late POs, and progress averages. Provides a compact high-level snapshot of production status and quality.                                         |
        - Each subplot is styled consistently using theme-defined font sizes (`sizes`), colors (`colors`), and spacing parameters.
        - All axes, legends, and labels are harmonized for a clean, presentation-ready layout.

    - *Output Features*:
        | Output                                   | Type                       | Description                                                    |
        | ---------------------------------------- | -------------------------- | -------------------------------------------------------------- |
        | `year_performance_dashboard_{year}.png`  | `.png` image               | Complete multi-panel annual dashboard visualization           |
        | `Figure` object                          | `matplotlib.figure.Figure` | Returned figure handle (for display or saving)                 |
        | **Progress Overview Panel**              | Bar chart                  | Aggregate annual completion status with percentage breakdown   |
        | **PO Status Pie Charts (3x)**            | Pie charts                 | Distribution of in-progress, not-started, and finished POs     |
        | **Backlog Analysis**                     | Bar/line chart             | Backlog trends and patterns throughout the year                |
        | **Overdue Analysis**                     | Bar chart                  | Count and aging of overdue POs by severity                     |
        | **Capacity Warning Matrix**              | Heatmap                    | Visual matrix of capacity constraints and warning levels       |
        | **Top Items by Volume**                  | Horizontal bar chart       | Highest-volume items ranked by total quantity                  |
        | **Capacity Severity Distribution**       | Pie/bar chart              | Breakdown of capacity issues by severity level                 |
        | **Progress Distribution**                | Histogram                  | Distribution of completion percentages across all POs          |
        | **Mold Usage Statistics**                | Bar chart                  | Frequency analysis of mold assignments                         |
        | **Late Items Summary**                   | Horizontal bar chart       | Current overdue POs ranked by remaining quantity               |
        | **Annual NG Rate Trend**                 | Line/area chart            | Quality performance trend showing defect rates over time       |
        | **Top NG Items**                         | Horizontal bar chart       | Items with highest defect rates requiring attention            |
        | **KPI Cards**                            | Text boxes with metrics    | Key annual metrics (total POs, completion %, quality, backlog) |
        | **Dashboard Title**                      | Figure suptitle            | Year and analysis timestamp displayed at top                   |
        | **Legend**                               | Auto-generated             | Color coding for statuses, categories, and severity levels     |

    **3. Machine Based Year View Dashboard**:
    
    - *Filename*: `machine_based_year_view_dashboard_{year}.png`
    
    - *Generated by*: `machine_based_year_view_dashboard_plotter()`

    - *Purpose*: Provides comprehensive machine-level performance analysis across the entire year, enabling comparison of production efficiency, utilization rates, quality metrics, and operational patterns across different machines. This dashboard facilitates equipment performance benchmarking and capacity planning decisions.

    - *Input Features*:
        | Feature                            | Description                                                                 |
        | ---------------------------------- | --------------------------------------------------------------------------- |
        | `df`                               | DataFrame containing machine-based production records                       |
        | `recordDate`                       | Date of production record (for temporal analysis)                           |
        | `workingShift`                     | Shift identifier (e.g., Day, Night, Morning)                                |
        | `machineNo`                        | Machine number (unique identifier)                                          |
        | `machineCode`                      | Machine code/name (used for display labels)                                 |
        | `itemCode`                         | Product item code                                                           |
        | `itemName`                         | Product item name                                                           |
        | `colorChanged`                     | Flag indicating color changeover occurred                                   |
        | `moldChanged`                      | Flag indicating mold changeover occurred                                    |
        | `machineChanged`                   | Flag indicating machine changeover occurred                                 |
        | `poNote`                           | Purchase Order notes/remarks                                                |
        | `moldNo`                           | Mold identification number                                                  |
        | `moldShot`                         | Number of mold shots/cycles performed                                       |
        | `moldCavity`                       | Number of cavities in the mold                                              |
        | `itemTotalQuantity`                | Total quantity produced (good + NG)                                         |
        | `itemGoodQuantity`                 | Quantity of good/accepted items                                             |
        | `itemBlackSpot`                    | Quantity with black spot defects                                            |
        | `itemOilDeposit`                   | Quantity with oil deposit defects                                           |
        | `itemScratch`                      | Quantity with scratch defects                                               |
        | `itemCrack`                        | Quantity with crack defects                                                 |
        | `itemSinkMark`                     | Quantity with sink mark defects                                             |
        | `itemShort`                        | Quantity with short shot defects                                            |
        | `itemBurst`                        | Quantity with burst defects                                                 |
        | `itemBend`                         | Quantity with bending defects                                               |
        | `itemStain`                        | Quantity with stain defects                                                 |
        | `otherNG`                          | Quantity with other defect types                                            |
        | `plasticResin`                     | Plastic resin material name                                                 |
        | `plasticResinCode`                 | Plastic resin material code                                                 |
        | `plasticResinLot`                  | Plastic resin lot/batch number                                              |
        | `colorMasterbatch`                 | Color masterbatch material name                                             |
        | `colorMasterbatchCode`             | Color masterbatch material code                                             |
        | `additiveMasterbatch`              | Additive masterbatch material name                                          |
        | `additiveMasterbatchCode`          | Additive masterbatch material code                                          |
        | `recordMonth`                      | Month of the record (for monthly aggregation)                               |
        | `fig_title`                        | Dashboard title text (string parameter)                                     |
        | `visualization_config_path` *(optional)* | Path to custom JSON config for style and layout overrides             |

    - *Processing Logic*:
        - Validation: Ensures dataframe contains all required columns via `validate_dataframe()`.
        - Configuration Loading: Loads default or external visualization config via `load_visualization_config()`.
        - Data Preparation:
          - Calls `process_machine_based_data()` to aggregate per-machine metrics (productive vs non-productive).
            - Purpose: 
              - Performs a complete preprocessing and aggregation pipeline for machine-based production data.
              - Cleans, enriches, and summarizes productivity metrics (productive vs non-productive) for dashboard visualization.
            - Processing Logic:
              - Enriches dataset with derived features (`itemComponent`, `recordInfo`, `recordMonth`) using `add_new_features()`.
              - Identifies and aggregates non-productive shifts/days via `process_not_progress_records()`.
              - Filters productive records only for main statistics.
              - Computes aggregated KPIs per machine (or per month × machine) using `calculate_aggregations()`.
              - Merges all results with `merge_by_fields()` into one unified summary table.
        - Visualization Setup: Creates 3-row × 3-column subplot grid with shared y-axes per row for consistent comparison across machines.

    - *Plotting Workflow*:
        - Populates 9 subplots with machine-comparison visualizations:
            | Plot Function / Chart Type     | Purpose / Insight                                                                                                                                                                                |
            | ------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
            | **Working Days Bar Chart**  | Displays **total working days vs not-progress days** per machine using horizontal stacked bars — bars split into `workingDays` (lightgreen) and `notProgressDays` (salmon) to show machine utilization and idle time patterns. |
            | **Working Shifts Bar Chart** | Shows **total working shifts vs not-progress shifts** per machine — similar stacked bar format to working days, helping identify shift-level utilization efficiency and downtime patterns across machines. |
            | **PO Numbers Bar Chart**    | Visualizes **number of purchase orders processed** per machine using horizontal bars (lightcoral) — indicates workload distribution and order handling capacity across the machine fleet. |
            | **Total Quantity Bar Chart** | Displays **total production volume** (`totalQuantity`) per machine using horizontal bars (coral) — shows absolute output capacity and identifies high-volume vs low-volume machines for capacity planning. |
            | **Average NG Rate Chart**   | Shows **average defect rate percentage** (`avgNGRate`) per machine using horizontal bars (tomato) — critical quality metric for identifying machines with quality issues requiring maintenance or process adjustments. |
            | **Good vs Total Quantity**  | Compares **good quantity vs total quantity** per machine using grouped horizontal bars — `totalQuantity` (coral) vs `goodQuantity` (lightgreen) to visualize quality yield and production efficiency side-by-side. |
            | **Mold Numbers Bar Chart**  | Displays **number of different molds used** (`moldNums`) per machine using horizontal bars (mediumpurple) — indicates machine flexibility and tooling diversity, useful for setup time analysis. |
            | **Item Components Chart**   | Shows **number of unique item components** (`itemComponentNums`) produced per machine using horizontal bars (teal) — reflects product mix complexity and machine versatility in handling different SKUs. |
            | **Total Mold Shots Chart**  | Visualizes **total mold cycles/shots** (`totalMoldShot`) per machine using horizontal bars (mediumseagreen) — key wear-and-tear indicator for predictive maintenance and mold life tracking. |
        - Each subplot includes:
            - Value labels on bars via `add_value_labels()` helper function
            - Consistent title styling with `sizes["title"]` and bold font weight
            - Hidden x-axis tick labels for cleaner appearance
            - Legends positioned below charts for row 1 and row 2 grouped comparisons
            - Machine codes displayed on shared y-axes for row consistency

    - *Output Features*:
        | Output                                   | Type                       | Description                                                    |
        | ---------------------------------------- | -------------------------- | -------------------------------------------------------------- |
        | `combined_summary`                       | `pd.DataFrame`             | Aggregated machine-level metrics used for plotting             |
        | `Figure` object                          | `matplotlib.figure.Figure` | Returned figure handle (for display or saving)                 |
        | **Working Days Comparison**              | Horizontal bar chart       | Machine utilization showing in-progress vs not-progress days   |
        | **Working Shifts Comparison**            | Horizontal bar chart       | Shift-level utilization across machines                        |
        | **PO Numbers Distribution**              | Horizontal bar chart       | Order count handled by each machine                            |
        | **Total Quantity Produced**              | Horizontal bar chart       | Absolute production volume per machine                         |
        | **Average NG Rate**                      | Horizontal bar chart       | Quality performance (defect percentage) by machine             |
        | **Good vs Total Quantity**               | Grouped horizontal bars    | Side-by-side comparison of total output vs good output         |
        | **Mold Numbers**                         | Horizontal bar chart       | Number of different molds used per machine                     |
        | **Item Components**                      | Horizontal bar chart       | Product variety/complexity handled per machine                 |
        | **Total Mold Shots**                     | Horizontal bar chart       | Cumulative mold cycles for maintenance planning                |
        | **Dashboard Title**                      | Figure suptitle            | Custom title from `fig_title` parameter                        |
        | **Value Labels**                         | Text annotations           | Numeric values displayed on all bars for precise readings      |
        | **Legends**                              | Chart legends              | Color coding for in-progress vs not-progress, good vs total    |
        | **Shared Y-Axes**                        | Row-wise sharing           | Consistent machine ordering across row visualizations          |    

    **4. Mold Based Year View Dashboard**:
    
    - *Filename*: `mold_based_year_view_dashboard_{year}.png`
    
    - *Generated by*: `mold_based_year_view_dashboard_plotter()`

    - *Purpose*: Provides comprehensive mold-level performance analysis across the entire year, enabling comparison of production efficiency, quality metrics, utilization patterns, and wear tracking across different molds. This dashboard facilitates mold performance benchmarking, maintenance scheduling, and tooling investment decisions based on usage intensity and quality output.

    - *Input Features*:
        | Feature                            | Description                                                                 |
        | ---------------------------------- | --------------------------------------------------------------------------- |
        | `df`                               | DataFrame containing mold-based production records                          |
        | `recordDate`                       | Date of production record (for temporal analysis)                           |
        | `workingShift`                     | Shift identifier (e.g., Day, Night, Morning)                                |
        | `machineNo`                        | Machine number used with the mold                                           |
        | `machineCode`                      | Machine code/name for cross-reference                                       |
        | `itemCode`                         | Product item code produced by the mold                                      |
        | `itemName`                         | Product item name                                                           |
        | `colorChanged`                     | Flag indicating color changeover occurred                                   |
        | `moldChanged`                      | Flag indicating mold changeover occurred                                    |
        | `machineChanged`                   | Flag indicating machine changeover occurred                                 |
        | `poNote`                           | Purchase Order notes/remarks                                                |
        | `moldNo`                           | Mold identification number (primary grouping key)                           |
        | `moldShot`                         | Number of mold shots/cycles performed                                       |
        | `moldCavity`                       | Number of cavities in the mold                                              |
        | `itemTotalQuantity`                | Total quantity produced (good + NG)                                         |
        | `itemGoodQuantity`                 | Quantity of good/accepted items                                             |
        | `itemBlackSpot`                    | Quantity with black spot defects                                            |
        | `itemOilDeposit`                   | Quantity with oil deposit defects                                           |
        | `itemScratch`                      | Quantity with scratch defects                                               |
        | `itemCrack`                        | Quantity with crack defects                                                 |
        | `itemSinkMark`                     | Quantity with sink mark defects                                             |
        | `itemShort`                        | Quantity with short shot defects                                            |
        | `itemBurst`                        | Quantity with burst defects                                                 |
        | `itemBend`                         | Quantity with bending defects                                               |
        | `itemStain`                        | Quantity with stain defects                                                 |
        | `otherNG`                          | Quantity with other defect types                                            |
        | `plasticResin`                     | Plastic resin material name                                                 |
        | `plasticResinCode`                 | Plastic resin material code                                                 |
        | `plasticResinLot`                  | Plastic resin lot/batch number                                              |
        | `colorMasterbatch`                 | Color masterbatch material name                                             |
        | `colorMasterbatchCode`             | Color masterbatch material code                                             |
        | `additiveMasterbatch`              | Additive masterbatch material name                                          |
        | `additiveMasterbatchCode`          | Additive masterbatch material code                                          |
        | `recordMonth`                      | Month of the record (for monthly aggregation)                               |
        | `visualization_metric`             | List of metrics to visualize (e.g., `['totalShots', 'avgNGRate', ...]`)    |
        | `fig_title`                        | Dashboard title text (string parameter)                                     |
        | `visualization_config_path` *(optional)* | Path to custom JSON config for style and layout overrides             |

    - *Processing Logic*:
        - Validation: Ensures dataframe contains all required columns via `validate_dataframe()`.
        - Configuration Loading: Loads default or external visualization config via `load_visualization_config()`.
        - Data Preparation:  
            - Invokes `process_mold_based_data()` to summarize mold-level metrics.  
              - Purpose: Aggregate and compute productivity and quality statistics per mold (optionally by month).  
              - Processing Logic:  
                - Filters out invalid rows where `itemTotalQuantity <= 0`.  
                - Selects relevant columns for analysis (mold, machine, shot, cavity, quantities).  
                - Groups by `moldNo` (or `(recordMonth, moldNo)` if `group_by_month=True`).  
                - Computes key indicators:  
                  - `totalShots`: Sum of `moldShot`.  
                  - `machineNums` / `machineList`: Machines using the mold.  
                  - `cavityNums`, `avgCavity`, `cavityList`: Mold design details.  
                  - `totalQuantity`, `goodQuantity`, `totalNG`, `totalNGRate`: Quality performance metrics.  
                - Sorts molds by total shot count (descending) for clear visual ranking.  
                - Returns summarized table ready for plotting.  
        - Mold Indexing: Creates `mold_index_map` dictionary to assign numeric indices (1, 2, 3, ...) to molds for x-axis labeling.
        - Visualization Setup: Creates dynamic N-row × 1-column subplot grid where N = length of `visualization_metric` list.

    - *Plotting Workflow*:
        - Dynamically generates one subplot per metric in `visualization_metric` list:
            | Chart Component              | Implementation Details                                                                                                                                                                           |
            | ---------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
            | **Metric Bar Charts**        | Each metric displayed as **horizontal comparison bar chart** with bars representing individual molds — bar height corresponds to metric value (e.g., `totalShots`, `avgNGRate`, `goodQuantity`). |
            | **Color Coding**             | Each mold assigned unique color from palette with lightening applied — colors maintained consistently across all metric subplots via `mold_colors` list for easy cross-metric comparison.         |
            | **Reference Lines**          | Dashed horizontal lines show **max value** (dash-dot, `-.`) and **min value** (dashed, `--`) across all molds — provides visual benchmarking against best/worst performers in each metric.        |
            | **Value Labels**             | Numeric values displayed on top of each bar via `format_value_short()` — minimum values highlighted in red (`#C0392B`), others in dark gray (`#333`) with white stroke for readability.          |
            | **X-Axis Labeling**          | Molds labeled by numeric index (1, 2, 3, ...) instead of full mold numbers — saves space and improves readability, with full mapping provided in legend.                                          |
            | **Y-Axis Scaling**           | Dynamic scaling with `ylim = [0, metric_max * 1.2]` to accommodate value labels — y-axis ticks hidden for cleaner appearance since values are labeled directly on bars.                           |
            | **Grid Styling**             | Light grid on both axes (`#eee` color) with top/right/left spines hidden — bottom spine in light gray (`#CCC`) for minimalist border, background in light gray (`#FAFAFA`).                       |
            | **Special Formatting**       | For `totalShots` metric: value labels rotated 30° and left-aligned to prevent overlap on tall bars.                                                                                              |

    - *Output Features*:
        | Output                                   | Type                       | Description                                                    |
        | ---------------------------------------- | -------------------------- | -------------------------------------------------------------- |
        | `combined_summary`                       | `pd.DataFrame`             | Aggregated mold-level metrics used for plotting                |
        | `Figure` object                          | `matplotlib.figure.Figure` | Returned figure handle (for display or saving)                 |
        | **Dynamic Metric Charts**                | Vertical bar charts        | One chart per metric in `visualization_metric` list            |
        | **Mold Comparison Bars**                 | Colored bars               | Each mold represented by unique color across all metrics       |
        | **Max/Min Reference Lines**              | Horizontal dashed lines    | Visual benchmarking indicators on each metric chart            |
        | **Value Labels**                         | Text annotations           | Formatted values displayed on bars with highlighting           |
        | **Numeric Mold Indices**                 | X-axis labels              | Simplified numbering (1, 2, 3...) for cleaner presentation     |
        | **Mold Index Legend**                    | Bottom legend              | Maps numeric indices back to full mold numbers                 |
        | **Main Title**                           | Figure suptitle            | Custom title from `fig_title` parameter                        |
        | **Metric Subtitle**                      | Figure text                | List of visualized metrics for dashboard context               |
        | **Grid & Styling**                       | Visual formatting          | Light grids, hidden spines, background colors for polish       |
        | **Flexible Layout**                      | N×1 subplot grid           | Dynamically sized based on number of metrics requested         |
    
    **5-9. Field-Based Month View Dashboards** (5 types, each potentially multi-page):
    
    All use `field_based_month_view_dashboard_plotter()` with different configurations:
    - *Purpose*:
      - Generates a multi-page (adjust number of items per page (e.g. `subfig_per_page=10`) and save files as: `..._page1.png`, `..._page2.png`, etc.), month-level dashboard that visualizes multiple production metrics per machine or per mold across an entire year.
      - The dashboard supports metric comparison across months, usage/quality trend monitoring, and performance tracking for each field value (`machineCode` or `moldNo`).
      - It is designed for yearly utilization monitoring (12 months as separate subplots), quality drift detection, and production planning insights.
    
    - *Input Features*:
        | Feature                                         | Description                                                                                                                                 |
        | ----------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
        | `df`                                            | Input DataFrame containing machine-level or mold-level production data                                                                      |
        | `recordDate`                                    | Date of production entry                                                                                                                    |
        | `workingShift`                                  | Shift indicator (Day/Night/etc.)                                                                                                            |
        | `machineNo`                                     | Machine number                                                                                                                              |
        | `machineCode`                                   | Machine identifier (primary key if `field='machineCode'`)                                                                                   |
        | `itemCode`, `itemName`                          | Produced item information                                                                                                                   |
        | `colorChanged`, `moldChanged`, `machineChanged` | Changeover indicators                                                                                                                       |
        | `poNote`                                        | Production order notes                                                                                                                      |
        | `moldNo`                                        | Mold number (primary key if `field='moldNo'`)                                                                                               |
        | `moldShot`, `moldCavity`                        | Mold cycle and cavity data                                                                                                                  |
        | `itemTotalQuantity`, `itemGoodQuantity`         | Quantity metrics                                                                                                                            |
        | Defect columns                                  | `itemBlackSpot`, `itemOilDeposit`, `itemScratch`, `itemCrack`, `itemSinkMark`, `itemShort`, `itemBurst`, `itemBend`, `itemStain`, `otherNG` |
        | Resin & Material fields                         | `plasticResin`, `plasticResinCode`, `plasticResinLot`, `colorMasterbatch`, `additiveMasterbatch`                                            |
        | `recordMonth`                                   | Month in format `YYYY-MM` (required for grouping)                                                                                           |
        | `visualization_metric`                          | List of metrics to visualize (must exist in `AVAILABLE_METRICS[field]`)                                                                     |
        | `fig_title`                                     | Main figure title                                                                                                                           |
        | `field`                                         | `'machineCode'` or `'moldNo'`                                                                                                               |
        | `subfig_per_page`                               | Number of item-specific charts per output page                                                                                              |
        | `visualization_config_path` *(optional)*        | Override config JSON path                                                                                                                   |
    
    - *Processing Logic*:
      - Validation:
        - Ensures df contains all required columns using `validate_dataframe()`.
        - Ensures all requested metrics exist for the selected field (`machineCode` or `moldNo`).
      - Configuration Loading: Loads default or external visualization config via `load_visualization_config()`.
      - Data Preparation:
        - Depending on selected field:
          | Field         | Processing Function            |
          | ------------- | ------------------------------ |
          | `machineCode` | `process_machine_based_data()` |
          | `moldNo`      | `process_mold_based_data()`    |
        - Both processing functions:
          - Group data by (`recordMonth`, field)
          - Compute metric aggregates:
            - Quantities (`totalQuantity`, `goodQuantity`)
            - Shots / cavity metrics
            - NG metrics (`totalNG`, `totalNGRate`)
            - Counts (`poNums`, `itemNums`, `machineNums`, etc.)
          - Output: `combined_summary`
      - Month Range Construction:
        - Extracts target year from recordMonth
        - Generates full month sequence (Jan → Dec)
        - Expands range if input contains cross-year data (backlogs)
        - Ensures consistent x-axis across all dashboards
      - Pagination:
        - Calculates number of pages = ceil(`total_items` / `subfig_per_page`)
        - Creates one figure per page, each containing:
          - N = `subfig_per_page` rows
          - Shared x-axis
          - Page-level titles and metric indicator
      - Metric Scaling Logic
        - Some metrics involve very large numbers
        - These are scaled down internally using:
            ```
            LARGE_METRICS = {
                'totalQuantity': 10000,
                'goodQuantity': 10000,
                'totalMoldShot': 10000,
                'totalNG': 1000,
                'totalShots': 1000
            }
            ```
        - Bars plot scaled values
        - Labels display actual numbers via `format_value_short()`
    
    - *Plotting Workflow*:
        - Each item (machine or mold) gets its own subplot:
          | Component                      | Logic                                                             |
          | ------------------------------ | ----------------------------------------------------------------- |
          | **Background metric boxes**    | Light-colored reference rectangles showing per-metric peak values |
          | **Dashed max reference lines** | Horizontal dashed lines marking each metric’s maximum             |
          | **Colored metric bars**        | Actual monthly values, grouped by metric and month                |
          | **Value labels**               | Auto-rotated or compressed based on space availability            |
          | **Month separators**           | Vertical dotted separators between months                         |
          | **Field label (left side)**    | MachineCode / MoldNo displayed as subplot y-label                 |
          | **X-axis**                     | Only drawn for the last subplot on each page                      |

    - *Output Features*:
        | Output                      | Type                             | Description                                           |
        | --------------------------- | -------------------------------- | ----------------------------------------------------- |
        | `combined_summary`          | `pd.DataFrame`                   | Aggregated per-field per-month metrics                |
        | `figs`                      | `List[Figure]`                   | List of generated paginated dashboard figures         |
        | **Multi-Page Dashboard**    | Visualization                    | Each page contains ≤ N items (machines or molds)      |
        | **Grouped Bar Trends**      | Time-series bar charts           | Monthly trend per metric                              |
        | **Dynamic Scaling**         | Intelligent y-limits             | Ensures visibility across different metric magnitudes |
        | **Reference Indicators**    | Dashed lines + background blocks | Shows performance ceilings                            |
        | **Consistent Monthly Axis** | Standardized 12-month format     | Supports cross-item comparison                        |
        | **Styled Layout**           | Custom theme                     | Seaborn + rcParams + spacing config                   |

    Field-Based Dashboard Details:
    - **5. Machine Working Days Dashboard**:
      - Filename: `machine_working_days_dashboard_{year}.png` (+ pages)
      - Metrics: `workingDays`, `notProgressDays`, `workingShifts`, `notProgressShifts`
      - Shows monthly working day patterns for each machine
      - Identifies idle periods and utilization gaps
    
    - **6. Machine PO/Item Dashboard**:
      - Filename: `machine_po_item_dashboard_{year}.png` (+ pages)
      - Metrics: `poNums`, `itemNums`, `moldNums`, `itemComponentNums`, `avgNGRate`
      - Tracks monthly PO/item diversity and quality per machine
      - Shows production variety and complexity trends
    
    - **7. Machine Quantity Dashboard**:
      - Filename: `machine_quantity_dashboard_{year}.png` (+ pages)
      - Metrics: `totalQuantity`, `goodQuantity`, `totalMoldShot`
      - Monthly production volume trends per machine
      - Identifies peak production months and capacity patterns
    
    - **8. Mold Shots Dashboard**:
      - Filename: `mold_shots_dashboard_{year}.png` (+ pages)
      - Metrics: `totalShots`, `cavityNums`, `avgCavity`, `machineNums`, `totalNGRate`
      - Monthly shot count patterns per mold
      - Tracks cavity usage and machine compatibility over 12 months
    
    - **9. Mold Quantity Dashboard**:
      - Filename: `mold_quantity_dashboard_{year}.png` (+ pages)
      - Metrics: `totalQuantity`, `goodQuantity`, `totalNG`
      - Monthly production volume and quality per mold
      - Identifies high-volume molds and quality issues

- **File Management**:
  
    - Creates two subdirectories: `newest/` for current versions, `historical_db/` for archives
    - Timestamps all files in format: `YYYYMMDD_HHMM_{filename}_{year}`
    - Before saving new files, moves ALL existing files from `newest/` to `historical_db/`
    - Maintains `change_log.txt` with detailed history of file operations and timestamps
    - Supports Excel (via openpyxl), PNG, and TXT exports through unified pipeline
    - **Multi-page handling**: Automatically saves multi-page plots as separate PNG files with `_page{N}` suffix
    - Excel export contains 5 sheets with different aggregation perspectives
    - TXT report saved for management review (final summary only)
    - **Potentially generates 20+ PNG files** if all month-view dashboards have multiple pages

- **Error handling**:
  
    - Comprehensive logging at each processing step using loguru logger with class binding
    - Exception handling in parallel worker functions with traceback capture
    - Graceful fallback from parallel to sequential execution on worker failures
    - File operation error handling with descriptive context messages
    - DataFrame loading validation with FileNotFoundError for missing paths
    - Excel writing error handling with sheet-level diagnostics
    - Individual plot failure tracking with success/failure counters
    - Record year format validation with regex checking (YYYY pattern)
    - Multi-page plot handling with iteration error protection
    - Report generation failures logged as warnings (non-blocking)
    - All errors logged with timestamps and execution context

- **Multi-Page Plot Handling**:
  
    - **Monthly performance plotter** may return tuple: `(summary, [fig1, fig2, ...])`
    - **Year performance plotter** may return tuple: `(summary, [fig1, fig2, ...])`
    - **Field-based month-view plotters** return multiple pages when field has >10 unique values:
        - Example: 25 machines → 3 pages (10 + 10 + 5 machines)
        - Each page shows up to 10 items with 12 monthly subplots each
    - `_plot_single_chart()` detects list of figures and saves each as separate page
    - Page files named: `{timestamp}_{name}_{year}_page1.png`, `_page2.png`, etc.
    - Each figure closed individually after saving to prevent memory leaks
    - Enables comprehensive dashboards that can display dozens of machines/molds with monthly trends
    - All pages logged separately in change log for traceability

- **PO Status Tracking (Annual Perspective)**:
  
    - **Finished POs**: Completed production within the year, full annual metrics available
    - **Unfinished POs**: In-progress orders at end of analysis date with:
        - Capacity warnings (Critical/High/Medium/Low severity)
        - Progress tracking (completion percentage, accumulated quantity)
        - Lead time estimates (average and total)
        - Overdue flags and ETA status monitoring
        - Capacity vs. demand analysis (over capacity indicators)
    - **Monthly Progress Dashboard**: Shows completion trends across 12 months
    - **Yearly Progress Dashboard**: Cumulative view of annual performance
    - **Backlog Tracking**: Identifies carried-over orders from previous year
    - **ETA Compliance**: Monitors annual on-time delivery performance

- **Year-Level vs Month-Level Differences**:
  
    - **No Early Warning Report**: Year-level focuses on historical analysis, not immediate capacity risks
    - **Monthly Trend Analysis**: Additional monthly_performance_plotter shows seasonal patterns
    - **Yearly Aggregate View**: year_performance_plotter shows cumulative annual metrics
    - **Month-View Dashboards**: 5 additional field-based month-view dashboards (machine and mold perspectives)
    - **RecordMonth Column**: Filtered_df enriched with YYYY-MM format for monthly aggregation
    - **More Visualizations**: 9+ plot types vs 3 in month-level
    - **Higher Parallelization**: Up to 10 workers vs 3 in month-level
    - **Larger Datasets**: Full year of data vs single month
    - **Multi-page Emphasis**: Month-view dashboards designed for multi-page output (10 items per page)

- **Field-Based Month View Dashboard System**:
  
    - **Generic Plotter**: `field_based_month_view_dashboard_plotter()` supports any grouping field
    - **Current Implementations**:
        - Machine perspective: 3 dashboards (working days, PO/item, quantity)
        - Mold perspective: 2 dashboards (shots, quantity)
    - **Layout**: 12 monthly subplots per item, up to 10 items per page
    - **Extensibility**: Can easily add new field-based dashboards by adding tasks in `_prepare_plot_tasks()`
    - **Performance**: Efficient aggregation using filtered_df with recordMonth column