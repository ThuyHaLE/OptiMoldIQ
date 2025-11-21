import json
import os
from loguru import logger
from typing import Dict, Set, Tuple, Optional, List
import pandas as pd
from pathlib import Path
from datetime import datetime
from agents.decorators import validate_init_dataframes
from agents.utils import read_change_log, load_annotation_path
import shutil

# Decorator to validate DataFrames are initialized with the correct schema
@validate_init_dataframes(lambda self: {
    "df": list(self.databaseSchemas_data['dynamicDB']['productRecords']['dtypes'].keys())
})

class MachineMoldPairTracker:
    """Class to track machine-mold pair changes over time"""
    
    def __init__(self, 
                 productRecords_df: pd.DataFrame, 
                 databaseSchemas_path: str = 'database/databaseSchemas.json',
                 output_dir: str = 'agents/shared_db/DataChangeAnalyzer/UpdateMoldOverview/tracker_results',
                 change_log_name: str = 'change_log.txt'):
        
        self.logger = logger.bind(class_="MachineMoldPairTracker")

        # Load database schema and database paths annotation
        self.databaseSchemas_data = load_annotation_path(Path(databaseSchemas_path).parent,
                                                         Path(databaseSchemas_path).name)
        
        self.df = productRecords_df[productRecords_df['moldNo'].notna()].copy()
        
        self.filename_prefix = 'machine_mold_pair'

        self.output_dir = Path(output_dir)
        self.change_log_name = change_log_name
        
    def data_process(self, 
                     record_date: pd.Timestamp):
        
        self.logger.info("Start processing...")
        new_record_date, has_change, new_changes, machine_molds_dict = self.check_new_pairs(record_date)

        if has_change:
            self.logger.info("New machine-mold pair changes detected.")
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
                for time_str in machine_molds_dict.keys():
                    timestamp = datetime.fromisoformat(time_str).strftime("%Y-%m-%d") 
                    json_filepath = newest_dir / f"{timestamp}_{self.filename_prefix}_{new_record_date}.json"

                    with open(json_filepath, 'w', encoding='utf-8') as f:
                        json.dump(machine_molds_dict[time_str], f, ensure_ascii=False, indent=2)
                        
                    self.logger.info(f"Machine-mold pair changes saved to {json_filepath}")
                    log_entries.append(f"  ⤷ Saved new file: {json_filepath}\n")

            except Exception as e:
                self.logger.error("Failed to analyze machine-mold pair changes: {}", e)
                raise OSError(f"Failed to analyze machine-mold pair changes: {e}")

            # Update change log
            try:
                log_path = self.output_dir / "change_log.txt"
                with open(log_path, "a", encoding="utf-8") as log_file:
                    log_file.writelines(log_entries)
                self.logger.info("Updated change log {}", log_path)
            except Exception as e:
                self.logger.error("Failed to update change log {}: {}", log_path, e)
                raise OSError(f"Failed to update change log {log_path}: {e}")
            
            return has_change, new_changes, machine_molds_dict, log_entries
        
        self.logger.info("No new machine-mold pair changes detected.")
        return has_change, new_changes, machine_molds_dict, None
    
    def check_new_pairs(self, 
                        new_record_date: pd.Timestamp) -> Tuple[str, bool, Set[Tuple[str, str]], Dict[str, Dict[str, List[str]]]]:
        """
        Check for new machine-mold pairs
        
        Returns:
            tuple: (has_new_pairs, new_pairs_set, all_data)
        """
        # Load existing data
        machine_molds_dict = self.load_machine_molds()
        
        if not machine_molds_dict:
            self.logger.info("No existing data. Detecting all...")
            machine_molds_dict = self.detect_all_machine_molds()
            # Return all pairs as "new"
            all_pairs = self._extract_all_pairs(machine_molds_dict)
            return new_record_date, True, all_pairs, machine_molds_dict
        
        # Get current machine-molds mapping
        current_mapping = self._get_machine_molds_at_date(new_record_date)
        
        # Get historical pairs
        historical_pairs = self._extract_latest_pairs(machine_molds_dict)
        
        # Get current pairs
        current_pairs = set()
        for machine, molds in current_mapping.items():
            for mold in molds:
                current_pairs.add((machine, mold))
        
        # Find new pairs
        new_pairs = current_pairs - historical_pairs
        
        if new_pairs:
            new_date_str = new_record_date.isoformat()
            machine_molds_dict[new_date_str] = current_mapping
            
            self.logger.info(f"Found {len(new_pairs)} new pairs at {new_date_str}:")
            for machine, mold in new_pairs:
                self.logger.info(f"  - {machine} -> {mold}")
        
        return new_record_date, len(new_pairs) > 0, new_pairs, machine_molds_dict
    
    def _prepare_data(self):
        """Prepare dataframe"""
        if not pd.api.types.is_datetime64_any_dtype(self.df['recordDate']):
            self.df['recordDate'] = pd.to_datetime(self.df['recordDate'])

    def detect_all_machine_molds(self) -> Dict[str, Dict[str, List[str]]]:
        """Detect all machine-mold mappings from dataframe"""
        try:
            # Prepare data
            self._prepare_data()
            
            # Get dates when new machine-mold combinations appear
            change_dates = (
                self.df[['recordDate', 'machineCode', 'moldNo']]
                .sort_values('recordDate')
                .drop_duplicates(['machineCode', 'moldNo'], keep='first')
                ['recordDate']
                .unique()
            )

            machine_molds_dict = {}
            for date in sorted(change_dates):
                mapping = self._get_machine_molds_at_date(date)
                machine_molds_dict[date.isoformat()] = mapping

            self.logger.info(f"Detected {len(machine_molds_dict)} change dates")
            return machine_molds_dict
            
        except Exception as e:
            self.logger.error(f"Error detecting machine-molds: {str(e)}")
            raise
    
    def _get_machine_molds_at_date(self, target_date: pd.Timestamp) -> Dict[str, List[str]]:
        """Get machine->molds mapping at specific date"""
        df_filtered = self.df[self.df['recordDate'] <= target_date]
        mapping = df_filtered.groupby('moldNo')['machineCode'].apply(
            lambda x: sorted(list(x.unique()))
        ).to_dict()
        
        # Convert to string keys and values
        return {str(k): [str(v) for v in vals] for k, vals in mapping.items()}
    
    def load_machine_molds(self) -> Optional[Dict[str, Dict[str, List[str]]]]:
        """Load from JSON file"""

        try:
            stored_path = read_change_log(self.output_dir, self.change_log_name)

            latest_path = max(
                (Path(p) for p in stored_path),
                key=lambda p: datetime.strptime(p.name.split("_")[0], "%Y-%m-%d")
            )

            if not os.path.exists(latest_path):
                self.logger.warning(f"File not found: {latest_path}")
                return None
                
            with open(latest_path, 'r', encoding='utf-8') as f:
                return json.load(f)
            
        except Exception as e:
            self.logger.error(f"Error loading: {str(e)}")
            return None
    
    def _extract_all_pairs(self, machine_molds_dict: Dict[str, Dict[str, List[str]]]) -> Set[Tuple[str, str]]:
        """Extract all machine-mold pairs from dict"""
        all_pairs = set()
        for date_mapping in machine_molds_dict.values():
            for mold, machines in date_mapping.items():
                for machine in machines:
                    all_pairs.add((mold, machine))
        return all_pairs
    
    def _extract_latest_pairs(self, machine_molds_dict: Dict[str, List[str]]) -> Set[Tuple[str, str]]:
        """Extract all machine-mold pairs from dict"""
        all_pairs = set()
        for mold, machines in machine_molds_dict.items():
            for machine in machines:
                all_pairs.add((mold, machine))
        return all_pairs
    
    def get_latest_mapping(self, machine_molds_dict: Dict[str, Dict[str, List[str]]]) -> Dict[str, List[str]]:
        """Get latest machine->molds mapping"""
        if not machine_molds_dict:
            return {}
        
        latest_date = max(machine_molds_dict.keys())
        return machine_molds_dict[latest_date]
    
    def get_summary(self, machine_molds_dict: Dict[str, Dict[str, List[str]]]) -> pd.DataFrame:
        """Get summary statistics"""
        summary_data = []
        for date_str, mapping in machine_molds_dict.items():
            total_pairs = sum(len(machines) for machines in mapping.values())
            summary_data.append({
                'date': pd.to_datetime(date_str),
                'num_machines': len(mapping),
                'total_pairs': total_pairs,
                'avg_molds_per_machine': total_pairs / len(mapping) if mapping else 0
            })
        
        return pd.DataFrame(summary_data).sort_values('date')