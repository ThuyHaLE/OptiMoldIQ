# updateHistMachineLayout output overview

## Excel Report (1 file):

### Machine-based Mold change layout 
- *Filename*: `Machine_level_change_layout_pivot.xlsx`
- *Description*: Pivot table showing machine positions across all detected layout change dates
- *Example*:
    ```
    | 2024-11-06 | 2024-11-15 | 2025-01-20 | machineName | machineCode |
    |------------|------------|------------|-------------|-------------|
    | NO.01      | NO.01      | NO.03      | MC          | MC01        |
    | NO.02      | NO.05      | NO.05      | MC          | MC02        |
    | NO.03      | NO.03      | NO.01      | MC          | MC03        |
    ```
    → Shows `MC01` moved from position `01` to `03`, `MC02` moved from `02` to `05`, and `MC03` moved from `03` to `01` over time.

## PNG Visualizations (3 files): 

### 1. Machine-based layout change Dashboard
- *Filename*: `Machine_change_layout_timeline.png`
- *Purpose*:
    - Timeline plot showing all machines' position changes
    - Color-coded by machine with legend
    - Adaptive layout for large machine counts (up to multi-column legends)
    - Y-axis shows all machine numbers, X-axis shows dates

### 2. Top 15 machines with most layout changes Dashboard
- *Filename*: `Top_machine_change_layout.png`
- *Purpose*:
    - Bar chart of top 15 machines with most layout changes
    - Includes statistics: total changes and average changes per machine
    - Color-coded bars for visual distinction

### 3. Machine-based layout change timeline Dashboard
- *Filename*: `Machine_level_change_layout_details.png`
- *Purpose*:
    - Grid of individual subplots (one per machine)
    - Shows detailed change timeline for each machine
    - Highlights machines exceeding change threshold (≥5 changes) with red borders
    - Adaptive grid layout: max 2 columns for readability
    - Annotated data points showing machine number at each change