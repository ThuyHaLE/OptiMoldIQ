from loguru import logger
import pandas as pd
from datetime import datetime
from typing import Dict, Optional
from agents.decorators import validate_init_dataframes
from configs.shared.config_report_format import ConfigReportMixin
from configs.shared.dict_based_report_generator import DictBasedReportGenerator
from agents.analyticsOrchestrator.trackers.configs.tracker_config import TrackerResult

@validate_init_dataframes(lambda self: {
    "record_df": list(self.databaseSchemas_data['dynamicDB']['productRecords']['dtypes'].keys())
})
class MachineLayoutTracker(ConfigReportMixin):
    """Class to track machine layout changes over time"""

    def __init__(self,
                 productRecords_df: pd.DataFrame,
                 databaseSchemas_data: Dict,
                 layout_changes_dict: Optional[Dict[str, Dict[str, str]]] = None):
        
        self._capture_init_args()
        self.logger = logger.bind(class_="MachineLayoutTracker")
        
        self.record_df = productRecords_df.copy()
        self.databaseSchemas_data = databaseSchemas_data
        self.layout_changes_dict = layout_changes_dict

    def check_new_layout_change(self, new_record_date: pd.Timestamp) -> TrackerResult:

        """Check for new layout changes"""
        
        self.logger.info("Starting MachineLayoutTracker ...")
        
        # Generate config header
        start_time = datetime.now()
        timestamp_str = start_time.strftime("%Y-%m-%d %H:%M:%S")
        config_header = self._generate_config_report(timestamp_str)
        
        tracking_log_entries = [
            config_header,
            "--Processing Summary--\n",
            f"⤷ {self.__class__.__name__} results:\n"
        ]
        
        new_record_date_str = new_record_date.strftime("%Y-%m-%d")
        
        if new_record_date not in self.record_df['recordDate'].values:
            self.logger.error("Date {} not found in records", new_record_date)
            raise ValueError(f"Date {new_record_date} not found in records")
        
        try:
            # Prepare data
            self._prepare_data()

            # Case 1 & 2: No layout data or empty - detect all and mark as change
            if not self.layout_changes_dict:
                self.logger.info("No existing layout data. Detecting all changes...")
                self.layout_changes_dict = self.detect_all_layout_changes()
                
                tracking_log_entries.append(f"Initial layout detection at {new_record_date.isoformat()}")
                
                changes_data = {
                    'machine_layout_hist_change': self.update_machine_layout_hist_change(),
                    'machine_changes': self.detect_machine_changes(self.layout_changes_dict),
                    'machine_layout_summary': self.get_layout_summary(self.layout_changes_dict)
                }
                
                reporter = DictBasedReportGenerator(use_colors=False)
                tracking_summary = "\n".join(reporter.export_report(changes_data))
                tracking_log_entries.append(tracking_summary)
                
                return TrackerResult(
                    record_date=new_record_date_str,
                    has_change=True,  # Always change at first time
                    changes_dict=self.layout_changes_dict,
                    changes_data=changes_data,
                    tracker_summary=tracking_summary,
                    log='\n'.join(tracking_log_entries)
                )
            
            # Case 3: Compare with existing layout
            current_layout = self._get_layout_at_date(new_record_date)
            latest_date = max(self.layout_changes_dict.keys())
            latest_layout = self.layout_changes_dict[latest_date]
            
            has_change = current_layout != latest_layout
            changes_data = {}
            tracking_summary = ""
            
            if not has_change:
                self.logger.info("No layout change detected!")
                tracking_log_entries.append("No layout change detected!")
                
            else:
                new_date_str = new_record_date.isoformat()
                
                # Only adding if it is not available
                if new_date_str not in self.layout_changes_dict:
                    self.layout_changes_dict[new_date_str] = current_layout
                    self.logger.info("New layout change detected at {}", new_date_str)
                    tracking_log_entries.append(f"New layout change detected at {new_date_str}")
                    
                    changes_data = {
                        'machine_layout_hist_change': self.update_machine_layout_hist_change(),
                        'machine_changes': self.detect_machine_changes(self.layout_changes_dict),
                        'machine_layout_summary': self.get_layout_summary(self.layout_changes_dict)
                    }
                    
                    reporter = DictBasedReportGenerator(use_colors=False)
                    tracking_summary = "\n".join(reporter.export_report(changes_data))
                    tracking_log_entries.append(tracking_summary)
            
            return TrackerResult(
                record_date=new_record_date_str,
                has_change=has_change,
                changes_dict=self.layout_changes_dict,
                changes_data=changes_data,
                tracker_summary=tracking_summary,
                log='\n'.join(tracking_log_entries)
            )
        
        except Exception as e:
            self.logger.error("❌ Tracker failed: {}", str(e))
            raise

    def detect_all_layout_changes(self) -> Dict[str, Dict[str, str]]:
        """Detect all layout changes from dataframe"""
        try:
            layout_change_dates = (
                self.record_df[['recordDate', 'machineNo', 'machineCode']]
                .sort_values('recordDate')
                .drop_duplicates(['machineNo', 'machineCode'], keep='first')
                ['recordDate']
                .unique()
            )
            
            layout_changes_dict = {
                date.isoformat(): self._get_layout_at_date(date)
                for date in sorted(layout_change_dates)
            }
            
            self.logger.info(f"Detected {len(layout_changes_dict)} layout change dates")
            return layout_changes_dict
        
        except Exception as e:
            self.logger.error(f"Error detecting layout changes: {str(e)}")
            raise

    def _prepare_data(self) -> None:
        if 'machineInfo' not in self.record_df.columns:
            self.record_df['machineInfo'] = (
                self.record_df['machineNo'].astype(str) + '-' + 
                self.record_df['machineCode'].astype(str)
            )
        
        if not pd.api.types.is_datetime64_any_dtype(self.record_df['recordDate']):
            self.record_df['recordDate'] = pd.to_datetime(self.record_df['recordDate'])
        
        self.record_df = self.record_df.sort_values('recordDate')

    def _get_layout_at_date(self, target_date: pd.Timestamp) -> Dict[str, str]:
        """Get complete machine layout at a specific date - Optimized"""
        mask = self.record_df['recordDate'] <= target_date
        active_machines = (
            self.record_df[mask]
            .drop_duplicates('machineNo', keep='last')
        )
        
        return dict(zip(active_machines['machineNo'], active_machines['machineCode']))

    def update_machine_layout_hist_change(self) -> pd.DataFrame:
        """Update machine layout historical change - Optimized"""
        
        layout_change_info = self._record_layout_change_info(self.record_df)
        
        layout_dfs = [
            self._pivot_machine_layout_record(
                self.record_df,
                info['recordDate'],
                info['workingShift']
            )
            for info in layout_change_info.values()
        ]
        
        if not layout_dfs:
            return pd.DataFrame()
        
        # Merge all layouts efficiently
        machine_layout_hist_change = layout_dfs[0]
        for layout_df in layout_dfs[1:]:
            machine_layout_hist_change = self._update_hist_machine_layout_record(
                machine_layout_hist_change, layout_df
            )
        
        self.logger.debug("Historical Machine Layouts Updated: {} - {}",
                         machine_layout_hist_change.shape, 
                         machine_layout_hist_change.columns.tolist())
        
        return machine_layout_hist_change

    @staticmethod
    def _record_layout_change_info(record_df: pd.DataFrame) -> Dict[str, Dict[str, str]]:
        """Record layout change info - Optimized"""
        
        df = record_df[['recordDate', 'workingShift', 'machineNo', 'machineCode']].copy()
        
        # Vectorized operations
        df['machineName'] = df['machineCode'].str.extract(r'([A-Z]+[0-9]*)', expand=False)
        df = df.drop_duplicates()
        
        df['shift_key'] = (
            df['recordDate'].dt.strftime('%Y-%m-%d') + 
            '-S' + df['workingShift'].astype(str)
        )
        
        # Group by shift and create layout strings
        # intentional for readability, optimize later if scale
        layout_dict = {}
        for shift_key, group in df.groupby('shift_key', sort=True):
            layout_string = '|'.join(
                group.sort_values('machineCode')
                .apply(lambda r: f"{r['machineCode']}-{r['machineNo']}-{r['machineName']}", 
                      axis=1)
                .tolist()
            )
            layout_dict[shift_key] = layout_string
        
        # Detect changes
        layout_changes = {}
        prev_layout = None
        change_index = 1
        
        for shift_key, current_layout in layout_dict.items():
            if current_layout != prev_layout:
                date_part, shift_part = shift_key.split("-S")
                layout_changes[f'layout_change_{change_index}'] = {
                    'recordDate': date_part,
                    'workingShift': shift_part
                }
                change_index += 1
            prev_layout = current_layout
        
        return layout_changes

    @staticmethod
    def _pivot_machine_layout_record(record_df: pd.DataFrame,
                                     recordDate: str,
                                     workingShift: str) -> pd.DataFrame:
        """Pivot machine layout record - Optimized"""
        
        # Filter và prepare data
        mask = (
            (record_df['recordDate'] == recordDate) & 
            (record_df['workingShift'].astype(str) == workingShift)
        )
        df = record_df[mask].drop_duplicates().copy()
        
        if df.empty:
            return pd.DataFrame()
        
        # Take first record per machineCode
        df_first = df.groupby('machineCode', as_index=False).first()
        
        # Extract machineName
        df_first['machineName'] = df_first['machineCode'].str.extract(r'([A-Z]+[0-9]*)', expand=False)
        df_first['date_str'] = pd.to_datetime(df_first['recordDate']).dt.strftime('%Y-%m-%d')
        
        # Pivot
        pivot = df_first.pivot(
            index='machineCode',
            columns='date_str',
            values='machineNo'
        ).reset_index()
        
        # Add machineName
        machine_names = df_first.set_index('machineCode')['machineName']
        pivot['machineName'] = pivot['machineCode'].map(machine_names)
        
        # Reorder columns
        date_cols = [col for col in pivot.columns if col not in ['machineCode', 'machineName']]
        return pivot[date_cols + ['machineName', 'machineCode']].reset_index(drop=True)

    @staticmethod
    def _update_hist_machine_layout_record(df_old: pd.DataFrame,
                                           df_new: pd.DataFrame) -> pd.DataFrame:
        """Update historical machine layout record - Optimized"""
        
        date_cols = sorted(
            set(df_old.columns).union(df_new.columns) - {'machineName', 'machineCode'}
        )
        
        # Merge
        merged = pd.merge(
            df_old, df_new,
            on='machineCode',
            how='outer',
            suffixes=('_old', '_new')
        )
        
        # Update each date column
        for date in date_cols:
            old_col = f"{date}_old"
            new_col = f"{date}_new"
            
            # Fillna efficiently
            if new_col in merged.columns:
                merged[date] = merged[new_col].fillna(
                    merged[old_col] if old_col in merged.columns else None
                )
            elif old_col in merged.columns:
                merged[date] = merged[old_col]
        
        # Update machineName
        if 'machineName_new' in merged.columns:
            merged['machineName'] = merged['machineName_new'].fillna(
                merged.get('machineName_old')
            )
        elif 'machineName_old' in merged.columns:
            merged['machineName'] = merged['machineName_old']
        
        return merged[date_cols + ['machineName', 'machineCode']].reset_index(drop=True)

    def get_layout_summary(self, 
                          layout_changes_dict: Dict[str, Dict[str, str]]) -> pd.DataFrame:
        """Get a summary dataframe of layout changes - Optimized"""
        
        summary_data = [
            {
                'date': pd.to_datetime(date_str),
                'num_machines': len(layout),
                'machine_nos': sorted(layout.keys()),
                'layout_signature': hash(frozenset(layout.items()))
            }
            for date_str, layout in layout_changes_dict.items()
        ]
        
        return pd.DataFrame(summary_data).sort_values('date').reset_index(drop=True)

    def detect_machine_changes(self,
                               layout_changes_dict: Dict[str, Dict[str, str]]) -> pd.DataFrame:
        """Detect specific machine changes between layouts - Optimized"""
        
        dates = sorted(layout_changes_dict.keys())
        
        if len(dates) < 2:
            return pd.DataFrame()
        
        changes_data = []
        
        for i in range(1, len(dates)):
            prev_layout = layout_changes_dict[dates[i-1]]
            curr_layout = layout_changes_dict[dates[i]]
            
            prev_keys = set(prev_layout.keys())
            curr_keys = set(curr_layout.keys())
            
            added = curr_keys - prev_keys
            removed = prev_keys - curr_keys
            
            # Detect code changes efficiently
            code_changes = {
                machine: {'from': prev_layout[machine], 'to': curr_layout[machine]}
                for machine in prev_keys & curr_keys
                if prev_layout[machine] != curr_layout[machine]
            }
            
            changes_data.append({
                'date': pd.to_datetime(dates[i]),
                'added_machines': list(added),
                'removed_machines': list(removed),
                'code_changes': code_changes,
                'total_changes': len(added) + len(removed) + len(code_changes)
            })
        
        return pd.DataFrame(changes_data)