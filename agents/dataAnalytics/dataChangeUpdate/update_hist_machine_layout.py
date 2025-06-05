from agents.dashboardBuilder.visualize_data.decorators import validate_init_dataframes
from agents.utils import load_latest_file_from_folder, save_output_with_versioning
from loguru import logger
import pandas as pd
from pathlib import Path

# Decorator to validate the required columns in input DataFrame
@validate_init_dataframes({"productRecords_df": [
    'machineNo', 'itemName', 'itemTotalQuantity', 'itemGoodQuantity',
    'recordDate', 'workingShift', 'moldNo', 'moldShot'
]})
class UpdateHistMachineLayout():
    def __init__(self, data_source: str, 
                 default_dir="agents/shared_db"):
        
        self.logger = logger.bind(class_="UpdateHistMachineLayout")

        # Load the most recent Excel file from the folder
        self.data = load_latest_file_from_folder(data_source)
        
        # Extract productRecords DataFrame
        self.productRecords_df = self.data.get('productRecords')
        if self.productRecords_df is None:
            self.logger.error("❌ Sheet 'productRecords' not found.")
            raise ValueError("Sheet 'productRecords' not found.")

        # Setup output directory and file prefix
        self.default_dir = Path(default_dir)
        self.output_dir = self.default_dir / "UpdateHistMachineLayout"
        self.filename_prefix = "update_hist_machine_layout_record"

        # Detect layout changes over time
        self.layout_changes = self._record_hist_layout_changes(self.productRecords_df)
        logger.debug("Layout changes updated: {}", self.layout_changes)
        # Start update process
        self.update()

    def update(self, **kwargs):
        hist_machine_layout_record = pd.DataFrame()

        # Iterate through each layout change and update historical layout record
        for hist_name, change_info in self.layout_changes.items():
            layout_change_df = self._machine_layout_record(self.productRecords_df, 
                                                           change_info['recordDate'], 
                                                           change_info['workingShift'])
            logger.debug("Machine Layout Recorded: {}", layout_change_df.columns)
            if hist_machine_layout_record.empty:
                hist_machine_layout_record = layout_change_df.copy()
                logger.debug("This is the first updated layout")
            else:
                logger.debug("Historical machine layouts updating...")
                hist_machine_layout_record = self._update_hist_machine_layout_record(
                    hist_machine_layout_record, layout_change_df
                )

        logger.debug("Hitorical Machine Layouts Updated: {}", hist_machine_layout_record.columns)

        # Save the result with version control
        logger.info("Start excel file exporting...")
        save_output_with_versioning(
            {"Sheet1": hist_machine_layout_record},
            self.output_dir,
            self.filename_prefix,
        )

    @staticmethod
    def _machine_layout_record(df, recordDate, workingShift):
        # Filter data for given date and shift, remove duplicates
        df = df[(df['recordDate'] == recordDate) & (df['workingShift'] == workingShift)].drop_duplicates()
        
        # Convert recordDate to datetime
        df['recordDate'] = pd.to_datetime(df['recordDate'])

        # Take the first record per machineCode
        df_first = df.groupby('machineCode').first().reset_index()

        # Extract machineName from machineCode using regex
        df_first['machineName'] = df_first['machineCode'].str.extract(r'([A-Z]+[0-9]*)')

        # Convert date to string format for column naming
        df_first['date_str'] = df_first['recordDate'].dt.strftime('%Y-%m-%d')

        # Pivot table: machineCode as rows, each date as a column
        pivot = df_first.pivot(index='machineCode', columns='date_str', values='machineNo').reset_index()

        # Add machineName back
        pivot['machineName'] = df_first.set_index('machineCode').loc[pivot['machineCode']]['machineName'].values

        # Reorder columns
        cols = [col for col in pivot.columns if col not in ['machineCode', 'machineName']]
        return pivot[cols + ['machineName', 'machineCode']].reset_index(drop=True)

    @staticmethod
    def _update_hist_machine_layout_record(df_old, df_new):
        # Identify date columns (excluding machine metadata)
        date_cols = sorted(set(df_old.columns).union(df_new.columns) - {'machineName', 'machineCode'})

        # Merge the two layout records
        merged = pd.merge(df_old, df_new, on='machineCode', how='outer', suffixes=('_old', '_new'))

        # Update layout for each date
        for date in date_cols:
            old_col = f"{date}_old" if date in df_old.columns else None
            new_col = f"{date}_new" if date in df_new.columns else None

            if date in df_old.columns:
                merged.rename(columns={date: old_col}, inplace=True)
            else:
                merged[old_col] = None

            if date in df_new.columns:
                merged.rename(columns={date: new_col}, inplace=True)
            else:
                merged[new_col] = None

            # Prefer new data over old
            merged[date] = merged[new_col].combine_first(merged[old_col])

        # Update machineName (prefer new name)
        merged['machineName'] = merged['machineName_new'].combine_first(merged['machineName_old'])

        # Return final table with updated layout info
        final = merged[date_cols + ['machineName', 'machineCode']].copy().reset_index(drop=True)

        return final

    @staticmethod
    def _record_hist_layout_changes(df):
        # Convert dates and extract machineName from machineCode
        df['recordDate'] = pd.to_datetime(df['recordDate'])
        df['machineName'] = df['machineCode'].str.extract(r'([A-Z]+[0-9]*)')

        # Keep relevant columns, drop duplicates
        df = df[['recordDate', 'workingShift', 'machineNo', 'machineName', 'machineCode']].drop_duplicates()

        # Create a unique shift key like 'YYYY-MM-DD-S1'
        df['date_str'] = df['recordDate'].dt.strftime('%Y-%m-%d')
        df['shift_key'] = df['date_str'] + '-S' + df['workingShift'].astype(str)

        layout_dict = {}       # Stores layout string per shift
        layout_changes = {}    # Stores shifts where layout changes happened

        # Generate layout strings per shift
        for shift_key in sorted(df['shift_key'].unique()):
            shift_df = df[df['shift_key'] == shift_key]

            layout_string = '|'.join(
                shift_df[['machineCode', 'machineNo', 'machineName']]
                .drop_duplicates()
                .sort_values(by='machineCode')
                .apply(lambda row: f"{row['machineCode']}-{row['machineNo']}-{row['machineName']}", axis=1)
                .tolist()
            )

            layout_dict[shift_key] = layout_string

        # Detect changes between shifts by comparing layout strings
        prev_layout = None
        change_index = 1
        
        for shift_key, current_layout in layout_dict.items():
            if current_layout != prev_layout:
                layout_changes[f'layout_change_{change_index}'] = {
                    'recordDate': shift_key.split("-S")[0],
                    'workingShift': int(shift_key.split("-S")[1])
                }
                change_index += 1
            prev_layout = current_layout

        return layout_changes