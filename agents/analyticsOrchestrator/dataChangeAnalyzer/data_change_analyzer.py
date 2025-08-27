from agents.decorators import validate_init_dataframes
from agents.utils import load_annotation_path
from loguru import logger
import pandas as pd
from pathlib import Path
import os
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
import psutil
import time
from typing import Tuple, Dict, Any, Optional
from agents.analyticsOrchestrator.dataChangeAnalyzer.machine_layout_tracker import MachineLayoutTracker
from agents.analyticsOrchestrator.dataChangeAnalyzer.machine_mold_pair_tracker import MachineMoldPairTracker

@validate_init_dataframes(lambda self: {
    "productRecords_df": list(self.databaseSchemas_data['dynamicDB']['productRecords']['dtypes'].keys()),
    "moldInfo_df": list(self.databaseSchemas_data['staticDB']['moldInfo']['dtypes'].keys()),
    "machineInfo_df": list(self.databaseSchemas_data['staticDB']['machineInfo']['dtypes'].keys()),
})

class DataChangeAnalyzer:
    def __init__(self, 
                 source_path: str = 'agents/shared_db/DataLoaderAgent/newest', 
                 annotation_name: str = "path_annotations.json",
                 databaseSchemas_path: str = 'database/databaseSchemas.json',
                 machine_layout_output_dir: str = "agents/shared_db/UpdateHistMachineLayout",
                 mold_overview_output_dir: str = "agents/shared_db/UpdateHistMoldOverview",
                 min_workers: int = 2,
                 max_workers: Optional[int] = None,
                 parallel_mode: str = "process"):  # "process" or "thread"
        
        self.logger = logger.bind(class_="DataChangeAnalyzer")
        
        self.machine_layout_output_dir = Path(machine_layout_output_dir)
        self.mold_overview_output_dir = Path(mold_overview_output_dir)
        
        # Parallel configuration
        self.min_workers = min_workers
        self.max_workers = max_workers or min(mp.cpu_count(), 4)
        self.parallel_mode = parallel_mode
        
        # Ensure output directory exists
        self.machine_layout_output_dir.mkdir(parents=True, exist_ok=True)
        self.mold_overview_output_dir.mkdir(parents=True, exist_ok=True)

        # Load database schema and database paths annotation
        self.databaseSchemas_data = self._load_database_schemas(databaseSchemas_path)
        self.path_annotation = self._load_path_annotations(source_path, annotation_name)

        # Load DataFrames
        self.productRecords_df = self._load_dataframe('productRecords')
        self.moldInfo_df = self._load_dataframe('moldInfo')
        self.machineInfo_df = self._load_dataframe('machineInfo')

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

    def _check_system_resources(self) -> Tuple[bool, int]:
        """Check available system resources for parallel processing."""
        try:
            # Check CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            available_cpu = 100 - cpu_percent
            
            # Check memory usage
            memory = psutil.virtual_memory()
            available_memory_gb = memory.available / (1024**3)
            
            # Check logical CPU count
            logical_cpu_count = mp.cpu_count()
            
            # Determine optimal worker count
            if available_memory_gb < 2:  # Less than 2GB available
                optimal_workers = max(1, logical_cpu_count // 4)
            elif available_memory_gb < 4:  # 2-4GB available
                optimal_workers = max(1, logical_cpu_count // 2)
            else:  # 4GB+ available
                optimal_workers = min(self.max_workers, logical_cpu_count)
            
            # Apply CPU usage factor
            if cpu_percent > 80:
                optimal_workers = max(1, optimal_workers // 2)
            
            can_run_parallel = (
                optimal_workers >= self.min_workers and
                available_memory_gb >= 1.0 and  # At least 1GB available
                cpu_percent < 90  # CPU not overloaded
            )
            
            self.logger.info(
                "System resources - CPU: {:.1f}% used, Memory: {:.1f}GB available, "
                "Optimal workers: {}, Can run parallel: {}",
                cpu_percent, available_memory_gb, optimal_workers, can_run_parallel
            )
            
            return can_run_parallel, optimal_workers
            
        except Exception as e:
            self.logger.warning("Failed to check system resources: {}, falling back to sequential", e)
            return False, 1

    def _analyze_layout_changes_task(self) -> Tuple[str, bool, Dict]:
        """Task function for layout analysis."""
        try:
            self.logger.info("Worker analyzing layout changes...")
            
            machine_layout_tracker = MachineLayoutTracker(
                productRecords_df=self.productRecords_df,
                output_dir=self.machine_layout_output_dir,
                json_name='layout_changes.json'
            )
            
            has_new_layout_change, layout_changes_dict = machine_layout_tracker.check_new_layout_change(
                self.latest_record_date
            )
            
            return "layout", has_new_layout_change, layout_changes_dict
            
        except Exception as e:
            self.logger.error("❌ Layout analysis task failed: {}", e)
            return "layout", False, {}

    def _analyze_machine_mold_pair_changes_task(self) -> Tuple[str, bool, list, Dict]:
        """Task function for machine-mold pair analysis."""
        try:
            self.logger.info("Worker analyzing machine-mold pair changes...")
            
            machine_mold_pair_tracker = MachineMoldPairTracker(
                productRecords_df=self.productRecords_df, 
                output_dir=self.mold_overview_output_dir / 'machine_molds',
                json_name='machine_molds.json',
                change_log_name='change_log.txt'
            )
            
            has_new_pair_change, new_pairs, pair_data = machine_mold_pair_tracker.check_new_pairs(
                self.latest_record_date
            )
            
            return "machine_mold", has_new_pair_change, new_pairs, pair_data
            
        except Exception as e:
            self.logger.error("❌ Machine-mold pair analysis task failed: {}", e)
            return "machine_mold", False, [], {}

    def analyze_changes(self, force_parallel: bool = False):
        """Analyze both layout and machine-mold pair changes with optional parallel processing."""
        self.logger.info("Starting change analysis for date: {}", self.latest_record_date)
        
        # Check system resources
        can_run_parallel, optimal_workers = self._check_system_resources()
        
        if force_parallel or can_run_parallel:
            self._analyze_changes_parallel(optimal_workers)
        else:
            self.logger.info("Running sequential analysis due to insufficient resources")
            self._analyze_changes_sequential()

    def _analyze_changes_parallel(self, num_workers: int):
        """Run analysis tasks in parallel."""
        self.logger.info("Running parallel analysis with {} workers", num_workers)
        start_time = time.time()
        
        # Choose executor based on mode
        executor_class = ProcessPoolExecutor if self.parallel_mode == "process" else ThreadPoolExecutor
        
        try:
            with executor_class(max_workers=num_workers) as executor:
                # Submit tasks
                future_to_task = {
                    executor.submit(self._analyze_layout_changes_task): "layout",
                    executor.submit(self._analyze_machine_mold_pair_changes_task): "machine_mold"
                }
                
                # Process completed tasks
                for future in as_completed(future_to_task):
                    task_name = future_to_task[future]
                    
                    try:
                        result = future.result()
                        
                        if task_name == "layout":
                            _, self.has_new_layout_change, self.layout_changes_dict = result
                            self.logger.info("✅ Layout analysis completed: {}", self.has_new_layout_change)
                            
                            if self.has_new_layout_change:
                                self._update_layout_changes()
                                
                        elif task_name == "machine_mold":
                            _, self.has_new_pair_change, self.new_pairs, self.pair_data = result
                            self.logger.info("✅ Machine-mold analysis completed: {}", self.has_new_pair_change)
                            
                            if self.has_new_pair_change:
                                self._update_mold_overview()
                                
                    except Exception as e:
                        self.logger.error("❌ Task {} failed: {}", task_name, e)
                        # Set default values for failed tasks
                        if task_name == "layout":
                            self.has_new_layout_change = False
                            self.layout_changes_dict = {}
                        elif task_name == "machine_mold":
                            self.has_new_pair_change = False
                            self.new_pairs = []
                            self.pair_data = {}
        
        except Exception as e:
            self.logger.error("❌ Parallel execution failed, falling back to sequential: {}", e)
            self._analyze_changes_sequential()
        
        elapsed_time = time.time() - start_time
        self.logger.info("✅ Parallel analysis completed in {:.2f} seconds", elapsed_time)

    def _analyze_changes_sequential(self):
        """Run analysis tasks sequentially (original behavior)."""
        start_time = time.time()
        
        # Analyze layout changes
        self._analyze_layout_changes()
        
        # Analyze machine-mold pair changes
        self._analyze_machine_mold_pair_changes()
        
        elapsed_time = time.time() - start_time
        self.logger.info("✅ Sequential analysis completed in {:.2f} seconds", elapsed_time)

    def _analyze_layout_changes(self):
        """Analyze layout changes and update if necessary."""
        self.logger.info("Checking for layout changes...")
        
        # Initialize layout tracker
        machine_layout_tracker = MachineLayoutTracker(
            productRecords_df=self.productRecords_df,
            output_dir=self.machine_layout_output_dir,
            json_name='layout_changes.json'
        )
        
        # Check for new layout changes
        (self.has_new_layout_change, 
         self.layout_changes_dict) = machine_layout_tracker.check_new_layout_change(
             self.latest_record_date
         )

        self.logger.info("Has new layout changes: {}", self.has_new_layout_change)

        if self.has_new_layout_change:
            self.logger.info("Updating and plotting new layout changes...")
            self._update_layout_changes()
        else:
            self.logger.info("No new layout changes detected.")

    def _analyze_machine_mold_pair_changes(self):
        """Analyze machine-mold pair changes and update if necessary."""
        self.logger.info("Checking for machine-mold pair changes...")
        
        # Initialize machine-mold pair tracker
        machine_mold_pair_tracker = MachineMoldPairTracker(
            productRecords_df=self.productRecords_df, 
            output_dir=self.mold_overview_output_dir / 'machine_molds',
            json_name='machine_molds.json',
            change_log_name='change_log.txt'
        )
        
        # Check for new mold-machine pair changes
        (self.has_new_pair_change, 
         self.new_pairs, 
         self.pair_data) = machine_mold_pair_tracker.check_new_pairs(
             self.latest_record_date
         )
        
        self.logger.info("Has new mold-machine pair changes: {}", self.has_new_pair_change)

        if self.has_new_pair_change:
            self.logger.info("Updating and plotting new mold overview changes...")
            self._update_mold_overview()
        else: 
            self.logger.info("No new machine-mold pairs detected.")

    def _update_layout_changes(self):
        """Update layout changes by importing and running UpdateHistMachineLayout."""
        try:
            from agents.analyticsOrchestrator.dataChangeAnalyzer.update_hist_machine_layout import UpdateHistMachineLayout
            UpdateHistMachineLayout(
                productRecords_df=self.productRecords_df,
                output_dir = self.machine_layout_output_dir
            ).update_and_plot()
            self.logger.info("✅ Layout changes updated successfully")
        except Exception as e:
            self.logger.error("❌ Failed to update layout changes: {}", e)
            raise

    def _update_mold_overview(self):
        """Update mold overview by importing and running UpdateHistMoldOverview."""
        try:
            from agents.analyticsOrchestrator.dataChangeAnalyzer.update_hist_mold_overview import UpdateHistMoldOverview
            UpdateHistMoldOverview(
                productRecords_df=self.productRecords_df,
                moldInfo_df=self.moldInfo_df,
                machineInfo_df=self.machineInfo_df,
                output_dir = self.mold_overview_output_dir
            ).update_and_plot()
            self.logger.info("✅ Mold overview updated successfully")
        except Exception as e:
            self.logger.error("❌ Failed to update mold overview: {}", e)
            raise

    def get_analysis_summary(self) -> dict:
        """Return a summary of the analysis results."""
        return {
            'latest_record_date': self.latest_record_date,
            'has_new_layout_change': getattr(self, 'has_new_layout_change', False),
            'layout_changes': getattr(self, 'layout_changes_dict', {}),
            'machine_layout_output_dir': str(self.machine_layout_output_dir),
            'has_new_pair_change': getattr(self, 'has_new_pair_change', False),
            'new_pairs': getattr(self, 'new_pairs', []),
            'mold_overview_output_dir': str(self.mold_overview_output_dir),
            'parallel_config': {
                'min_workers': self.min_workers,
                'max_workers': self.max_workers,
                'parallel_mode': self.parallel_mode
            }
        }