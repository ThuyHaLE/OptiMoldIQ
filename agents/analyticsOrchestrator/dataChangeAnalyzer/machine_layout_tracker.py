import json
import os
from loguru import logger
from typing import Dict, Tuple, Optional
import pandas as pd
from pathlib import Path

class MachineLayoutTracker:
    """Class to track machine layout changes over time"""
    
    def __init__(self, 
                 productRecords_df: pd.DataFrame, 
                 output_dir: str = 'agents/shared_db/UpdateHistMachineLayout',
                 json_name: str = 'layout_changes.json'):
        
        self.logger = logger.bind(class_="MachineLayoutTracker")
        
        self.df = productRecords_df.copy()

        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.json_filepath = self.output_dir / json_name

        self._prepare_data()
    
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
    
    def save_layout_changes(self, layout_changes_dict: Dict[str, Dict[str, str]]) -> bool:
        """Save layout changes to JSON file with error handling"""
        try:
            with open(self.json_filepath, 'w', encoding='utf-8') as f:
                json.dump(layout_changes_dict, f, ensure_ascii=False, indent=2, default=str)
            
            self.logger.info(f"Layout changes saved to {self.json_filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving layout changes: {str(e)}")
            # Restore backup if exists
            backup_path = f"{self.json_filepath}.backup"
            if os.path.exists(backup_path):
                os.rename(backup_path, self.json_filepath)
                self.logger.info("Restored from backup")
            return False
    
    def load_layout_changes(self) -> Optional[Dict[str, Dict[str, str]]]:
        """Load layout changes from JSON file with error handling"""
        try:
            if not os.path.exists(self.json_filepath):
                self.logger.warning(f"JSON file not found: {self.json_filepath}")
                return None
                
            with open(self.json_filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.logger.info(f"Loaded layout changes from {self.json_filepath}")
            return data
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON format: {str(e)}")
            return None
        except Exception as e:
            self.logger.error(f"Error loading layout changes: {str(e)}")
            return None
    
    def check_new_layout_change(self, new_record_date: pd.Timestamp) -> Tuple[bool, Dict[str, Dict[str, str]]]:
        """
        Check for new layout changes
        
        Args:
            new_record_date: Latest recordDate to check
            
        Returns:
            tuple: (has_change: bool, layout_changes_dict: dict)
        """
        # Load existing data
        layout_changes_dict = self.load_layout_changes()
        
        if layout_changes_dict is None:
            self.logger.info("No existing layout data found. Detecting all changes...")
            layout_changes_dict = self.detect_all_layout_changes()
            self.save_layout_changes(layout_changes_dict)
            return True, layout_changes_dict
        
        if not layout_changes_dict:
            self.logger.info("Empty layout data found. Detecting all changes...")
            layout_changes_dict = self.detect_all_layout_changes()
            self.save_layout_changes(layout_changes_dict)
            return True, layout_changes_dict
        
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
                self.save_layout_changes(layout_changes_dict)
                self.logger.info(f"New layout change detected at {new_date_str}")
        
        return has_change, layout_changes_dict
    
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