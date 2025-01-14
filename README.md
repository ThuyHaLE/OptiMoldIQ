```
OptiMoldIQ/
├── data/
│   ├── DATABASE/ (admin mode)
│   │   ├── MACHINE_INFO.xlsx       # Machine information
│   │   ├── MOLD_INFO.xlsx          # Mold information based on each plastic part/item
│   │   ├── PLASTIC_INFO.xlsx       # Plastic information based on each plastic part/item
│   │   └── PRO_STATUS.xlsx         # Total production report. This file will be updated daily
│   │
│   ├── UPDATED_DATA/
│   │   ├── PO_list.xlsx        #Production orders
│   │   │
│   │   ├── MAIN_DATA/
│   │   │   ├── main_data_YYYYMMDD.xlsx    # Daily created main data from daily_data + PRO_STATUS
│   │   │   └── main_data_template.xlsx     # Template for new main data files
│   │   │
│   │   └── DAILY_DATA/
│   │       ├── daily_production_YYYYMMDD.xlsx  # Daily updated production data
│   │       └── daily_production_template.xlsx    # Template for daily updates
│   │
│   └── processed/                  # Folder for processed data files if needed
│       └── merged_data.csv         # Example file: after merging or processing
│
├── backup/
│   ├── PO_list_200904.xlsx
│   ├── pro_status_backup_2024-10-30.xlsx     # Backup with timestamp for PRO_STATUS
│   ├── pro_status_backup_2024-10-29.xlsx     # Previous version of PRO_STATUS
│   ├── daily_data_2024-10-30.csv              # Daily data backup
│   └── daily_data_2024-10-29.csv              # Previous versions of daily data
│
├── archive/
│   └── 2024/
│       ├── daily_data_2024-09-01.csv # Archived daily production data
│       └── daily_data_2024-09-02.csv
│
│
├── src/
│   ├── __init__.py                 # Makes src a Python package
│   ├── main.py                     # Main script to run the project
│   ├── data_loader.py              # Module for loading data from Excel or DB
│   ├── data_processing.py          # Module for processing/merging data
│   ├── production_planning.py      # Logic for creating production plans
│   ├── scheduling.py               # Scheduling algorithms and prioritization
│   ├── plastic_usage.py            # Plastic usage calculations and forecasting
│   └── utils.py                    # Helper functions (e.g., for calculations)
│
├── output/
│   ├── planning/
│   │   ├── production_plan/            # Folder for storing generated production plans
│   │   │   └── production_plan.csv     # Production plan for each machine
│   │   ├── mold_plan/                  # Folder for mold plan outputs
│   │   │   └── mold_plan.csv           # Mold plan for each machine
│   │   ├── plastic_plan/               # Folder for plastic plan outputs
│   │   │   └── plastic_plan.csv        # Plastic plan for each machine/day
│   └── daily reports/
│           └── dashboard
│
├── logs/
│   └── project.log                 # Log file for tracking script outputs and issues
│
└── tests/
    ├── __init__.py
    ├── test_data_loader.py         # Tests for data loading functions
    ├── test_production_planning.py # Tests for production planning logic
    ├── test_scheduling.py          # Tests for scheduling algorithms
    └── test_plastic_usage.py       # Tests for plastic usage calculations
```