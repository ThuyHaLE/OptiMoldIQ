# updateHistMoldOverview output overview

## Excel Report (3 files):

### Not-matched Tonage Machine Mold 
- *Filename*: `Tonage_machine_mold_not_matched.xlsx`
- *Description*: Records where mold tonnage doesn't match machine tonnage

### Machine Perspective
- *Filename*: `Machine_mold_first_run_pair.xlsx`
- *Description*: Pivot showing first-run dates (machine perspective)

### Mold Perspective
- *Filename*: `Mold_machine_first_run_pair.xlsx`
- *Description*: Pivot showing first-run dates (mold perspective)

## PNG Visualizations (8 files): 

### 1. Mold-based Acquisition dates vs. first use dates Dashboard
- *Filename*: `Comparison_of_acquisition_and_first_use.png`
- *Purpose*:
    - Dual scatter plot comparing acquisition dates vs. first use dates
    - Each point represents one mold
    - Helps identify delays between purchase and deployment

### 2. Mold-based Time Gap of acquisition and first use Dashboard
- *Filename*: `Time_Gap_of_acquisition_and_first_use.png`
- *Purpose*:
    - Histogram showing distribution of gap times (in days)
    - Includes mean and median lines with statistics
    - 30 bins for detailed distribution view

### 3. Top 20 molds with longest acquisition-to-use gaps Dashboard
- *Filename*: `Top_Bottom_molds_gap_time_analysis.png`
- *Purpose*:
    - Dual horizontal bar chart (2 subplots)
    - Top: 20 molds with longest acquisition-to-use gaps (red)
    - Bottom: 20 molds with shortest gaps (green)
    - Shows moldNo labels for identification

### 4. Machine-based Number of molds first run Dashboard
- *Filename*: `Number_of_molds_first_run_on_each_machine.png`
- *Purpose*:
    - Bar chart showing unique mold count per machine
    - Color-coded bars for visual distinction
    - Red dashed line at 10 molds for reference
    - Sorted descending by mold count

### 5. Mold-based Top 20 molds with most tonnage Dashboard
- *Filename*: `Top_molds_tonnage.png`
- *Purpose*:
    - Bar chart of top 20 molds with most tonnage variety
    - Shows `usedTonnageCount` for each mold
    - Values displayed on top of bars
    - Color-coded for visual appeal

### 6. Mold-based Top 20 molds with least tonnage Dashboard
- *Filename*: `Bottom_molds_tonnage.png`
- *Purpose*:
    - Bar chart of bottom 20 molds with least tonnage variety
    - Highlights single-tonnage molds with red dashed line
    - Legend shows count of molds matching only 1 tonnage

### 7. Mold-based Distribution of used machine tonnage Dashboard
- *Filename*: `Tonnage_distribution.png`
- *Purpose*:
    - Histogram showing distribution of tonnage variety across all molds
    - Bins aligned to integer tonnage counts
    - Count labels on each bar
    - X-axis shows 1 to max tonnage types

### 8. Mold-based Machine Tonnage proportion Dashboard
- *Filename*: `Tonnage_proportion.png`
- *Purpose*:    
    - Pie chart showing proportional breakdown
    - Each slice represents molds using N tonnage types
    - Percentage labels with mold counts
    - Slight explosion effect for readability
    - Bold formatting for labels and percentages