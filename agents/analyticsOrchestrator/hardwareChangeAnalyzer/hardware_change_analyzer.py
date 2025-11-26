from agents.decorators import validate_init_dataframes
from agents.utils import load_annotation_path
from loguru import logger
import pandas as pd
from pathlib import Path
import os
import time
from dataclasses import dataclass
from typing import Dict, Any, Optional
from datetime import datetime

from agents.analyticsOrchestrator.hardwareChangeAnalyzer.machine_layout_tracker import MachineLayoutTracker
from agents.analyticsOrchestrator.hardwareChangeAnalyzer.machine_mold_pair_tracker import MachineMoldPairTracker

@dataclass
class ChangeAnalyticflowConfig:
    """Configuration class for analyticflow parameters"""
    
    enable_machine_layout_tracker: bool = False
    enable_machine_mold_pair_tracker: bool = False
    
    # Shared paths
    source_path: str = 'agents/shared_db/DataLoaderAgent/newest'
    annotation_name: str = "path_annotations.json"
    databaseSchemas_path: str = 'database/databaseSchemas.json'

    default_dir: str = "agents/shared_db/HardwareChangeAnalyzer"

    machine_layout_tracker_dir: str = "agents/shared_db/HardwareChangeAnalyzer/UpdateMachineLayout/tracker_results"
    machine_layout_tracker_change_log_name: str = "change_log.txt"

    machine_mold_pair_tracker_dir: str = "agents/shared_db/HardwareChangeAnalyzer/UpdateMoldOverview/tracker_results"
    machine_mold_pair_tracker_change_log_name: str = "change_log.txt"

@validate_init_dataframes(lambda self: {
    "productRecords_df": list(self.databaseSchemas_data['dynamicDB']['productRecords']['dtypes'].keys()),
    "moldInfo_df": list(self.databaseSchemas_data['staticDB']['moldInfo']['dtypes'].keys()),
    "machineInfo_df": list(self.databaseSchemas_data['staticDB']['machineInfo']['dtypes'].keys())
})

class HardwareChangeAnalyzer:
    def __init__(self, 
                 config: ChangeAnalyticflowConfig):
        
        self.logger = logger.bind(class_="HardwareChangeAnalyzer")
        self.config = config
        
        # Load database schema and database paths annotation
        self.databaseSchemas_data = self._load_database_schemas(self.config.databaseSchemas_path)
        self.path_annotation = self._load_path_annotations(self.config.source_path, self.config.annotation_name)

        # Load DataFrames
        self.productRecords_df = self._load_dataframe('productRecords')
        self.machineInfo_df = self._load_dataframe('machineInfo')
        self.moldInfo_df = self._load_dataframe('moldInfo')

        # Get latest record date
        self.latest_record_date = self.productRecords_df['recordDate'].max()
        self.logger.info("Latest record date: {}", self.latest_record_date)

    def _load_database_schemas(self, databaseSchemas_path: str) -> dict:
        """Load database schemas with error handling."""
        try:
            return load_annotation_path(Path(databaseSchemas_path).parent, 
                                        Path(databaseSchemas_path).name)
        except Exception as e:
            self.logger.error("❌ Failed to load database schemas: {}", e)
            raise

    def _load_path_annotations(self, source_path: str, annotation_name: str) -> dict:
        """Load path annotations with error handling."""
        try:
            return load_annotation_path(source_path, annotation_name)
        except Exception as e:
            self.logger.error("❌ Failed to load path annotations: {}", e)
            raise

    def _load_dataframe(self, df_name: str) -> pd.DataFrame:
        """Load a specific DataFrame with error handling."""
        df_path = self.path_annotation.get(df_name)
        
        if not df_path:
            error_msg = f"Path to '{df_name}' not found in annotations."
            self.logger.error("❌ {}", error_msg)
            raise KeyError(error_msg)
        
        if not os.path.exists(df_path):
            error_msg = f"Path to '{df_name}' does not exist: {df_path}"
            self.logger.error("❌ {}", error_msg)
            raise FileNotFoundError(error_msg)
        
        try:
            df = pd.read_parquet(df_path)
            self.logger.info("✅ Successfully loaded {}: {} records", df_name, len(df))
            return df
        except Exception as e:
            error_msg = f"Failed to read parquet file for '{df_name}': {e}"
            self.logger.error("❌ {}", error_msg)
            raise

    def analyze_changes(self, save_log = False):
        
        results =  {
            "machine_layout_tracker": None, 
            "machine_mold_pair_tracker": None
            }

        # Nothing enabled
        if not self.config.enable_machine_layout_tracker and not self.config.enable_machine_mold_pair_tracker:
            self.logger.info("No analytics enabled. Nothing to run.")
        
        """Run analysis tasks sequentially"""

        start_time = time.time()

        # Analyze layout changes
        if self.config.enable_machine_layout_tracker:
            results["machine_layout_tracker"] = self._safe_process(
                self.analyze_layout_changes,
                "layout change analyzer")

        # Analyze machine-mold pair changes
        if self.config.enable_machine_mold_pair_tracker:
            results["machine_mold_pair_tracker"] = self._safe_process(
                self.analyze_machine_mold_pair_changes,
                "machine-mold pair change analyzer")
            
        elapsed_time = time.time() - start_time

        self.logger.info("✅ Analysis completed in {:.2f} seconds", elapsed_time)

        log_entries_str = self.update_change_logs(results)

        # Save log
        if save_log:
            try:
                output_dir = Path(self.config.default_dir)
                output_dir.mkdir(parents=True, exist_ok=True)
                log_path = output_dir / "change_log.txt"
                with open(log_path, "a", encoding="utf-8") as log_file:
                    log_file.write(log_entries_str)
                self.logger.info("✓ Updated and saved change log: {}", log_path)
            except Exception as e:
                self.logger.error("✗ Failed to save change log {}: {}", log_path, e)

        return results, log_entries_str

    def update_change_logs(self, results: Dict[str, Optional[Dict]]):
        """
        Update change log file with processing results and configuration.
        
        Args:
            results: Dictionary containing processing results for each level
        """
        timestamp_now = datetime.now()
        timestamp_str = timestamp_now.strftime("%Y-%m-%d %H:%M:%S")
        
        log_entries = []

        # Prepare log entries
        log_entries.append(f"[{timestamp_str}] hardwareChangeAnalyzer Run")
        log_entries.append("")

        # Configuration section
        log_entries.append("--Configuration--")

        # Database sources
        log_entries.append(f"⤷ Database Annotation: {self.config.source_path}/{self.config.annotation_name}")
        log_entries.append(f"⤷ Database Schemas: {self.config.databaseSchemas_path}")
        log_entries.append(f"⤷ Output Directory: {self.config.default_dir}")

        log_entries.append("")

        # Machine layout tracker
        if self.config.enable_machine_layout_tracker:
            log_entries.append("⤷ Machine layout tracker: Enable")
            log_entries.append("--MachineLayoutTracker Configuration--")
            log_entries.append(f"   ⤷ Machine Layout Output Directory: {self.config.machine_layout_tracker_dir}")
            log_entries.append(f"   ⤷ Machine Layout Change Log Name: {self.config.machine_layout_tracker_change_log_name}")
        else:
            log_entries.append("⤷ Machine layout tracker: Disable")

        # Machine mold pair tracker
        if self.config.enable_machine_mold_pair_tracker:
            log_entries.append("⤷ Machine mold pair tracker: Enable")
            log_entries.append("--MachineMoldPairTrackerr Configuration--")
            log_entries.append(f"   ⤷ Mold Overview Output Directory: {self.config.machine_mold_pair_tracker_dir}")
            log_entries.append(f"   ⤷ Mold Overview Change Log Name: {self.config.machine_mold_pair_tracker_change_log_name}")
        else:
            log_entries.append("⤷ Machine mold pair tracker: Disable")

        # Processing summary
        log_entries_dict = self._log_processing_summary(results)
        
        log_entries.append("--Processing Summary--")
        
        # Skipped levels
        if 'Skipped' in log_entries_dict['Processing Summary']:
            log_entries.append(f"⤷ Skipped: {log_entries_dict['Processing Summary']['Skipped']}")
        
        # Completed levels
        if 'Completed' in log_entries_dict['Processing Summary']:
            completed_str = log_entries_dict['Processing Summary']['Completed']
            log_entries.append(f"⤷ Completed: {completed_str}")
        log_entries.append("")
        
        # Detailed results
        if log_entries_dict.get('Details'):
            log_entries.append("--Details--")
            for level_name, level_result in log_entries_dict['Details'].items():
                log_entries.append(f"⤷ {level_name}:")
                log_entries.append(''.join(level_result))
            log_entries.append("")

        return "\n".join(log_entries)

    def _log_processing_summary(self, results: Dict[str, Optional[Dict]]):
        """Log summary of processing results."""

        log_entries = {
            'Processing Summary': {},
            'Details': {}
        }

        self.logger.info("Processing Summary:")
        
        skipped = [k for k, v in results.items() if v is None]

        if skipped:
            skipped_info = ", ".join(skipped)
            self.logger.info("  ⊘ Skipped: {}", skipped_info)
            log_entries['Processing Summary']['Skipped'] = skipped_info

        completed = [k for k, v in results.items() if v is not None]
        completed_info = ", ".join(completed) if completed else "None"
    
        self.logger.info("  ✓ Completed: {}", completed_info)
        log_entries['Processing Summary']['Completed'] = completed_info
        
        for lv in completed:
            if results[lv]["log_entries"] is not None:
                log_entries['Details'][lv] = results[lv]["log_entries"]
            else: 
                log_entries['Details'][lv] = "No new changes detected."

        return log_entries
    
    def analyze_layout_changes(self, save_output = False):
        """Analyze layout changes and update if necessary."""
        self.logger.info("Checking for layout changes...")
        
        # Initialize layout tracker
        tracker = MachineLayoutTracker( 
            productRecords_df=self.productRecords_df, 
            databaseSchemas_path = self.config.databaseSchemas_path,
            output_dir = self.config.machine_layout_tracker_dir,
            change_log_name = self.config.machine_layout_tracker_change_log_name)
        
        # Check for new layout changes
        (has_new_layout_change, machine_layout_hist_change, log_entries) = tracker.data_process(self.latest_record_date)

        if has_new_layout_change:
            self.logger.info("New layout changes detected.")
        else:
            self.logger.info("No new layout changes detected.")

        return {
            "has_new_layout_change": has_new_layout_change,
            "machine_layout_hist_change": machine_layout_hist_change,
            "log_entries": log_entries
        }

    def analyze_machine_mold_pair_changes(self):
        """Analyze machine-mold pair changes and update if necessary."""
        self.logger.info("Checking for machine-mold pair changes...")

        # Initialize machine-mold pair tracker
        tracker = MachineMoldPairTracker(
                 productRecords_df = self.productRecords_df, 
                 moldInfo_df = self.moldInfo_df,
                 machineInfo_df = self.machineInfo_df,
                 databaseSchemas_path = self.config.databaseSchemas_path,
                 output_dir = self.config.machine_mold_pair_tracker_dir,
                 change_log_name = self.config.machine_mold_pair_tracker_change_log_name)
        
        # Check for new mold-machine pair changes
        (has_new_pair_change, 
         mold_tonnage_summary_df,
         first_mold_usage_df, 
         first_paired_mold_machine_df,
         log_entries) = tracker.data_process(self.latest_record_date)

        if has_new_pair_change:
            self.logger.info("New machine-mold pair changes detected.")
        else: 
            self.logger.info("No new machine-mold pairs detected.")

        return {
            "has_new_pair_change": has_new_pair_change,
            "mold_tonnage_summary": mold_tonnage_summary_df,
            "first_mold_usage": first_mold_usage_df,
            "first_paired_mold_machine": first_paired_mold_machine_df,
            "log_entries": log_entries
        }
    
    def _safe_process(
        self,
        process_func,
        component_name: str) -> Optional[Dict[str, Any]]:
        """
        Execute processing function with error isolation.
        
        Args:
            process_func: Processing function to execute
            component_name: Name of component (for logging)
            
        Returns:
            Processing results or None if failed
        """
        try:
            result = process_func()
            self.logger.success("✓ {} completed", component_name)
            return result
        except Exception as e:
            self.logger.error("✗ {} failed: {}", component_name, e)
            return None