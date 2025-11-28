import json
import os
from loguru import logger
from typing import Dict, Tuple, Optional
import pandas as pd
from pathlib import Path
from agents.decorators import validate_init_dataframes
from agents.utils import read_change_log, load_annotation_path
from datetime import datetime
import shutil

# Decorator to validate DataFrames are initialized with the correct schema
@validate_init_dataframes(lambda self: {
    "df": list(self.databaseSchemas_data['dynamicDB']['productRecords']['dtypes'].keys())
})

class MachineLayoutTracker:
    """Class to track machine layout changes over time"""

    def __init__(self,
                 productRecords_df: pd.DataFrame,
                 databaseSchemas_path: str = 'database/databaseSchemas.json',
                 output_dir: str = 'agents/shared_db/HardwareChangeAnalyzer/MachineLayoutTracker',
                 change_log_name: str = "change_log.txt"):

        self.logger = logger.bind(class_="MachineLayoutTracker")

        # Load database schema and database paths annotation
        self.databaseSchemas_data = load_annotation_path(Path(databaseSchemas_path).parent,
                                                         Path(databaseSchemas_path).name)

        self.df = productRecords_df.copy()

        self.filename_prefix = 'machine_layout_changes'

        self.output_dir = Path(output_dir)
        self.change_log_name = change_log_name

    def data_process(self,
                     record_date: pd.Timestamp):

        self.logger.info("Start processing...")
        new_record_date, has_change, layout_changes_dict = self.check_new_layout_change(record_date)

        if has_change:
            self.logger.info("New layout changes detected.")
            # Setup directories and timestamps
            timestamp_now = datetime.now()
            timestamp_str = timestamp_now.strftime("%Y-%m-%d %H:%M:%S")
            timestamp_file = timestamp_now.strftime("%Y%m%d_%H%M")

            newest_dir = self.output_dir / "newest"
            newest_dir.mkdir(parents=True, exist_ok=True)
            historical_dir = self.output_dir / "historical_db"
            historical_dir.mkdir(parents=True, exist_ok=True)

            log_entries = [f"[{timestamp_str}] Saving new version...\n"]

            # Move old files to historical_db
            for f in newest_dir.iterdir():
                if f.is_file():
                    try:
                        dest = historical_dir / f.name
                        shutil.move(str(f), dest)
                        log_entries.append(f"  ⤷ Moved old file: {f.name} → historical_db/{f.name}\n")
                        self.logger.info("Moved old file {} to historical_db as {}", f.name, dest.name)
                    except Exception as e:
                        self.logger.error("Failed to move file {}: {}", f.name, e)
                        raise OSError(f"Failed to move file {f.name}: {e}")

            # Save layout changes
            try:
                json_name = f"{timestamp_file}_{self.filename_prefix}_{new_record_date}.json"
                json_filepath = newest_dir / json_name
                with open(json_filepath, 'w', encoding='utf-8') as f:
                    json.dump(layout_changes_dict, f, ensure_ascii=False, indent=2, default=str)
                self.logger.info(f"Layout changes saved to {json_filepath}")
                log_entries.append(f"  ⤷ Saved new file: {json_filepath}\n")

            except Exception as e:
                self.logger.error("Failed to analyze layout changes: {}", e)
                raise OSError(f"Failed to analyze layout changes: {e}")

            # Save machine layout historical change
            try:
                excel_file_name = f"{timestamp_file}_{self.filename_prefix}_{new_record_date}.xlsx"
                excel_file_path = newest_dir / excel_file_name

                machine_layout_hist_change = self.record_machine_layout_hist_change()

                excel_data = {
                    "machineLayoutChange": machine_layout_hist_change
                }

                with pd.ExcelWriter(excel_file_path, engine="openpyxl") as writer:
                    for sheet_name, df in excel_data.items():
                        if not isinstance(df, pd.DataFrame):
                            df = pd.DataFrame([df])
                        df.to_excel(writer, sheet_name=sheet_name, index=False)
                log_entries.append(f"  ⤷ Saved data analysis results: {excel_file_path}\n")
                logger.info("✅ Saved data analysis results: {}", excel_file_path)
            except Exception as e:
                logger.error("❌ Failed to save file {}: {}", excel_file_name, e)
                raise OSError(f"Failed to save file {excel_file_name}: {e}")

            # Update change log
            try:
                log_path = self.output_dir / "change_log.txt"
                with open(log_path, "a", encoding="utf-8") as log_file:
                    log_file.writelines(log_entries)
                self.logger.info("Updated change log {}", log_path)
            except Exception as e:
                self.logger.error("Failed to update change log {}: {}", log_path, e)
                raise OSError(f"Failed to update change log {log_path}: {e}")

            return has_change, machine_layout_hist_change, log_entries

        self.logger.info("No new layout changes detected.")

        return has_change, None, None

    def load_layout_changes(self) -> Optional[Dict[str, Dict[str, str]]]:
        """Load layout changes from JSON file with error handling"""

        try:
            layout_changes_path = read_change_log(self.output_dir, self.change_log_name)
            if not os.path.exists(layout_changes_path):
                self.logger.warning(f"JSON file not found: {layout_changes_path}")
                return None

            with open(layout_changes_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self.logger.info(f"Loaded layout changes from {layout_changes_path}")
            return data

        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON format: {str(e)}")
            return None
        except Exception as e:
            self.logger.error(f"Error loading layout changes: {str(e)}")
            return None

    def check_new_layout_change(self,
                                new_record_date: pd.Timestamp) -> Tuple[str, bool, Dict[str, Dict[str, str]]]:
        """
        Check for new layout changes

        Args:
            new_record_date: Latest recordDate to check

        Returns:
            tuple: (has_change: bool, layout_changes_dict: dict)
        """
        # Load existing data
        layout_changes_dict = self.load_layout_changes()

        new_record_date_str = new_record_date.strftime("%Y-%m-%d")

        if layout_changes_dict is None:
            self.logger.info("No existing layout data found. Detecting all changes...")
            layout_changes_dict = self.detect_all_layout_changes()
            return new_record_date_str, True, layout_changes_dict

        if not layout_changes_dict:
            self.logger.info("Empty layout data found. Detecting all changes...")
            layout_changes_dict = self.detect_all_layout_changes()
            return new_record_date_str, True, layout_changes_dict

        # Get current layout at new_record_date
        current_layout = self._get_layout_at_date(new_record_date)

        # Get latest stored layout
        latest_date = max(layout_changes_dict.keys())
        latest_layout = layout_changes_dict[latest_date]

        # Compare layouts
        has_change = self._layouts_different(latest_layout, current_layout)

        if has_change:
            new_date_str = new_record_date.isoformat()
            if new_date_str not in layout_changes_dict:
                layout_changes_dict[new_date_str] = current_layout
                self.logger.info(f"New layout change detected at {new_date_str}")

        return new_record_date_str, has_change, layout_changes_dict

    def _prepare_data(self):
        """Prepare dataframe with machineInfo column"""
        if 'machineInfo' not in self.df.columns:
            self.df['machineInfo'] = self.df['machineNo'] + '-' + self.df['machineCode']

        # Ensure recordDate is datetime
        if not pd.api.types.is_datetime64_any_dtype(self.df['recordDate']):
            self.df['recordDate'] = pd.to_datetime(self.df['recordDate'])

    def detect_all_layout_changes(self) -> Dict[str, Dict[str, str]]:
        """Detect all layout changes from dataframe"""
        try:

            # Prepare data
            self._prepare_data()

            # Find dates with layout changes
            layout_change_dates = (
                self.df[['recordDate', 'machineNo', 'machineCode']]
                .sort_values('recordDate')
                .drop_duplicates(['machineNo', 'machineCode'], keep='first')
                ['recordDate']
                .unique()
            )

            layout_changes_dict = {}
            for date in sorted(layout_change_dates):
                machines_dict = self._get_layout_at_date(date)
                layout_changes_dict[date.isoformat()] = machines_dict

            self.logger.info(f"Detected {len(layout_changes_dict)} layout change dates")
            return layout_changes_dict

        except Exception as e:
            self.logger.error(f"Error detecting layout changes: {str(e)}")
            raise

    def _get_layout_at_date(self, target_date: pd.Timestamp) -> Dict[str, str]:
        """Get complete machine layout at a specific date"""
        active_machines = (
            self.df[self.df['recordDate'] <= target_date]
            .sort_values('recordDate')
            .drop_duplicates('machineNo', keep='last')
        )

        return dict(zip(active_machines['machineNo'], active_machines['machineCode']))

    def _layouts_different(self, layout1: Dict[str, str], layout2: Dict[str, str]) -> bool:
        """Compare two layouts for differences"""
        return layout1 != layout2

    def get_layout_summary(self, layout_changes_dict: Dict[str, Dict[str, str]]) -> pd.DataFrame:
        """Get a summary dataframe of layout changes"""
        summary_data = []
        for date_str, layout in layout_changes_dict.items():
            summary_data.append({
                'date': pd.to_datetime(date_str),
                'num_machines': len(layout),
                'machine_nos': sorted(layout.keys()),
                'layout_signature': hash(frozenset(layout.items()))
            })

        return pd.DataFrame(summary_data).sort_values('date')

    def detect_machine_changes(self, layout_changes_dict: Dict[str, Dict[str, str]]) -> pd.DataFrame:
        """Detect what specific machines changed between layout versions"""
        dates = sorted(layout_changes_dict.keys())
        changes_data = []

        for i in range(1, len(dates)):
            prev_date, curr_date = dates[i-1], dates[i]
            prev_layout = layout_changes_dict[prev_date]
            curr_layout = layout_changes_dict[curr_date]

            # Find changes
            added_machines = set(curr_layout.keys()) - set(prev_layout.keys())
            removed_machines = set(prev_layout.keys()) - set(curr_layout.keys())
            code_changes = {}

            for machine in set(prev_layout.keys()) & set(curr_layout.keys()):
                if prev_layout[machine] != curr_layout[machine]:
                    code_changes[machine] = {
                        'from': prev_layout[machine],
                        'to': curr_layout[machine]
                    }

            changes_data.append({
                'date': pd.to_datetime(curr_date),
                'added_machines': list(added_machines),
                'removed_machines': list(removed_machines),
                'code_changes': code_changes,
                'total_changes': len(added_machines) + len(removed_machines) + len(code_changes)
            })

        return pd.DataFrame(changes_data)

    def record_machine_layout_hist_change(self, **kwargs):
        machine_layout_hist_change = pd.DataFrame()

        # Get layout change infor
        layout_change_info = self._record_layout_change_info(self.df)

        # Iterate through each layout change and update historical layout record
        for hist_name, change_info in layout_change_info.items():
            layout_change_df = self._pivot_machine_layout_record(
                self.df,
                change_info['recordDate'],
                change_info['workingShift']
                )
            if machine_layout_hist_change.empty:
                machine_layout_hist_change = layout_change_df.copy()
                self.logger.debug("This is the first updated layout")
            else:
                self.logger.debug("Historical machine layouts updating...")
                machine_layout_hist_change = self._update_hist_machine_layout_record(
                    machine_layout_hist_change, layout_change_df
                )

        self.logger.debug("Hitorical Machine Layouts Updated: {} - {}",
                     machine_layout_hist_change.shape, machine_layout_hist_change.columns)

        return machine_layout_hist_change

    @staticmethod
    def _record_layout_change_info(df):

        # Convert dates and extract machineName from machineCode
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
                    'workingShift': shift_key.split("-S")[1]
                }
                change_index += 1
            prev_layout = current_layout

        return layout_changes

    @staticmethod
    def _pivot_machine_layout_record(df, recordDate, workingShift):
        # Filter data for given date and shift, remove duplicates
        df['workingShift'] = df['workingShift'].apply(lambda x: f'{x}')
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
            #merged[date] = merged[new_col].combine_first(merged[old_col])
            merged[date] = merged[new_col].fillna(merged[old_col])

        # Update machineName (prefer new name)
        merged['machineName'] = merged['machineName_new'].combine_first(merged['machineName_old'])

        # Return final table with updated layout info
        final = merged[date_cols + ['machineName', 'machineCode']].copy().reset_index(drop=True)

        return final