from agents.decorators import validate_init_dataframes
from agents.utils import load_annotation_path
from loguru import logger
import pandas as pd
from pathlib import Path
import os
import time
from typing import Dict, Any, Optional

from agents.analyticsOrchestrator.hardwareChangeAnalyzer.machine_layout_tracker import MachineLayoutTracker
from agents.analyticsOrchestrator.hardwareChangeAnalyzer.machine_mold_pair_tracker import MachineMoldPairTracker

from agents.analyticsOrchestrator.analyticsConfigs.change_analyticflow_config import ChangeAnalyticflowConfig
from agents.analyticsOrchestrator.logStrFormatters.hardware_change_analyzer_formatter import build_hardware_change_analyzer_log

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

    def analyze_changes(self):
        
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

        log_entries_str = build_hardware_change_analyzer_log(self.config, results)

        # Save log
        if self.config.save_hardware_change_analyzer_log:
            try:
                output_dir = Path(self.config.hardware_change_analyzer_dir)
                output_dir.mkdir(parents=True, exist_ok=True)
                log_path = output_dir / "change_log.txt"
                with open(log_path, "a", encoding="utf-8") as log_file:
                    log_file.write(log_entries_str)
                self.logger.info("✓ Updated and saved change log: {}", log_path)
            except Exception as e:
                self.logger.error("✗ Failed to save change log {}: {}", log_path, e)

        return results, log_entries_str
    
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