# ProcessDashboardReports Class Documentation

## Overview

The `ProcessDashboardReports` class is a comprehensive data processing system designed for manufacturing production tracking and reporting. It extracts, processes, and structures production data from Excel files containing multiple sheets with different aspects of manufacturing operations.

## Key Features

- **Multi-sheet Excel Processing**: Handles complex Excel files with multiple related sheets
- **Production Tracking**: Monitors machine usage, mold operations, daily quantities, and production status
- **Data Validation**: Includes error handling and data validation warnings
- **Flexible Data Slicing**: Supports configurable data range limiting
- **Structured Output**: Returns consistently formatted data suitable for dashboards and reports

## Class Initialization

```python
from agents.dashboard_reports import ProcessDashboardReports

# Initialize with default settings
processor = ProcessDashboardReports()

# Initialize with custom Excel file
processor = ProcessDashboardReports(
    excel_file_path="path/to/production_data.xlsx",
    limit_range=(0, 50)  # Process first 50 records
)
```

### Constructor Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `excel_file_path` | str | None | Path to Excel file. If None, reads from change log |
| `folder_path` | str | 'agents/shared_db/OrderProgressTracker' | Folder containing change log |
| `target_name` | str | "change_log.txt" | Change log filename |
| `limit_range` | Tuple[Optional[int], Optional[int]] | (0, 30) | Data slice range (start, end) |

## Excel Sheet Structure

The class expects an Excel file with the following sheets:

### 1. productionStatus
**Purpose**: Main production status tracking
**Key Columns**: 
- `poReceivedDate`, `poNo`, `itemCode`, `itemName`
- `itemQuantity`, `itemRemain`, `proStatus`, `etaStatus`
- `machineHist`, `moldHist`, `totalMoldShot`

### 2. machineQuantityMap
**Purpose**: Machine capacity and quantity mappings
**Key Columns**: 
- `poNo`, `itemCode`, `itemName`, `machineCode`, `moldedQuantity`

### 3. moldShotMap
**Purpose**: Mold shot tracking and equipment usage
**Key Columns**: 
- `poNo`, `itemCode`, `itemName`, `moldNo`, `shotCount`

### 4. dayQuantityMap
**Purpose**: Daily production quantity tracking
**Key Columns**: 
- `poNo`, `itemCode`, `itemName`, `workingDay`, `moldedQuantity`

### 5. materialComponentMap
**Purpose**: Material and component mappings
**Key Columns**: 
- `poNo`, `itemCode`, `itemName`
- `plasticResinCode`, `colorMasterbatchCode`, `additiveMasterbatchCode`

### 6. notWorkingStatus
**Purpose**: Non-working time and downtime tracking

### 7. item_invalid_warnings
**Purpose**: Data validation warnings for items

### 8. po_mismatch_warnings
**Purpose**: Purchase order mismatch alerts

## Core Methods

### get_sheet_summary()

Returns an overview of all available sheets in the Excel file.

**Returns**: `Dict[str, Any]`
```python
{
    "total_sheets": 8,
    "sheet_names": ["productionStatus", "machineQuantityMap", ...],
    "sheet_details": {
        "productionStatus": {
            "Description": "Main production status tracking",
            "Dataframe review": {...}  # Sample data
        }
    }
}
```

### generate_all_reports()

Generates all available reports in a single call.

**Returns**: `Dict[str, Any]`
```python
{
    'sheet_summary': {...},
    'machine_quantity_map': [...],
    'mold_shot_map': [...],
    'day_quantity_map': [...],
    'production_status': [...],
    'material_component_map': [...]
}
```

### get_related_details_to_display_on_dashboard

#### 1. process_machine_quantity_map()

Groups production data by machine code and extracts machine details.

#### 2. process_mold_shot_map()

Tracks shot counts by mold number with mold detail separation.

#### 3. process_day_quantity_map()

Groups production quantities by working day.

#### 4. process_production_status()

Extracts comprehensive production status with tracking information.

#### 5. process_material_component_map()

Groups material components by production order and item.

#### Dashboard Demo:

- See details: [Dashboard Demo](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs\agents_output_overviews\orderProgressTracker_output_overviews.md)

## Usage Examples

### Basic Usage
```python
# Initialize processor
processor = ProcessDashboardReports("production_data.xlsx")

# Get overview of data
summary = processor.get_sheet_summary()
print(f"Processing {summary['total_sheets']} sheets")

# Process specific reports
machine_data = processor.process_machine_quantity_map()
production_status = processor.process_production_status()
```

### Generate Complete Dashboard Data
```python
# Generate all reports at once
all_reports = processor.generate_all_reports()

# Access specific report
for machine in all_reports['machine_quantity_map']:
    print(f"Machine {machine['machineNo']}: {len(machine['items'])} items")
```

### Custom Data Range
```python
# Process only first 10 records
processor = ProcessDashboardReports(
    excel_file_path="data.xlsx",
    limit_range=(0, 10)
)

# Process records 20-50
processor = ProcessDashboardReports(
    excel_file_path="data.xlsx", 
    limit_range=(20, 50)
)
```

## Error Handling

The class includes comprehensive error handling:

- **File Not Found**: Raises `FileNotFoundError` if Excel file doesn't exist
- **Invalid Excel**: Raises `ValueError` for corrupted or invalid Excel files
- **Missing Sheets**: Logs errors and returns empty lists for missing sheets
- **Missing Columns**: Validates required columns and reports missing ones
- **Data Type Issues**: Handles datetime formatting and data type conversions

## Logging

The class uses `loguru` for comprehensive logging:
- Info level: Successful operations and data loading
- Error level: File errors, missing columns, processing failures
- Debug information includes row counts and processing steps

## Data Format Standards

### poItemInfo Format
All items are formatted as: `"PO | ItemCode | ItemName"`

### Date Formatting
All dates are standardized to: `YYYY-MM-DD` format

### Machine Code Parsing
Machine codes are parsed to extract:
- `machineNo`: Base machine number (e.g., "NO.01")
- `details`: Additional machine specifications

### Mold Code Parsing
Mold codes are split into:
- `moldNo`: Base mold identifier
- `details`: Mold specifications (e.g., "M-001")

## Integration Notes

This class is designed to work with:
- Production tracking systems
- Manufacturing dashboards 
- Reporting and analytics tools
- Order progress monitoring systems

