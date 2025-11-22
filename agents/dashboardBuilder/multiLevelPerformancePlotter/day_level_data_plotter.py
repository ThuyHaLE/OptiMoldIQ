from agents.dashboardBuilder.visualize_data.day_level.change_times_all_types_plotter import change_times_all_types_plotter
from agents.dashboardBuilder.visualize_data.day_level.item_based_overview_plotter import item_based_overview_plotter 
from agents.dashboardBuilder.visualize_data.day_level.machine_level_yield_efficiency_plotter import machine_level_yield_efficiency_plotter
from agents.dashboardBuilder.visualize_data.day_level.machine_level_mold_analysis_plotter import machine_level_mold_analysis_plotter
from agents.dashboardBuilder.visualize_data.day_level.shift_level_yield_efficiency_plotter import shift_level_yield_efficiency_plotter
from agents.dashboardBuilder.visualize_data.day_level.shift_level_detailed_yield_efficiency_plotter import shift_level_detailed_yield_efficiency_plotter
from agents.dashboardBuilder.visualize_data.day_level.mold_based_overview_plotter import mold_based_overview_plotter
from agents.dashboardBuilder.visualize_data.day_level.shift_level_mold_efficiency_plotter import shift_level_mold_efficiency_plotter

from agents.analyticsOrchestrator.analytics_orchestrator import AnalyticsOrchestratorConfig, AnalyticsOrchestrator

from agents.decorators import validate_init_dataframes
from agents.utils import load_annotation_path

from loguru import logger
from pathlib import Path
from datetime import datetime
import pandas as pd
import shutil
import os
import multiprocessing as mp
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
import psutil
import time
from typing import Tuple, Any, Callable
import traceback
import matplotlib.pyplot as plt

# Decorator to validate DataFrames are initialized with the correct schema
@validate_init_dataframes(lambda self: {"moldInfo_df": list(self.databaseSchemas_data['staticDB']['moldInfo']['dtypes'].keys())})

class DayLevelDataPlotter:
    def __init__(self, 
                 selected_date: str,
                 source_path: str = 'agents/shared_db/DataLoaderAgent/newest', 
                 annotation_name: str = "path_annotations.json",
                 databaseSchemas_path: str = 'database/databaseSchemas.json',
                 default_dir: str = "agents/shared_db/DashboardBuilder/MultiLevelPerformancePlotter",
                 visualization_config_path: str = None,
                 enable_parallel: bool = True,
                 max_workers: int = None):

        self.logger = logger.bind(class_="DayLevelDataPlotter")
        
        # Parallel processing configuration
        self.enable_parallel = enable_parallel
        self.max_workers = max_workers
        self._setup_parallel_config()

        self.visualization_config_path = (
            visualization_config_path 
            or "agents/dashboardBuilder/visualize_data/day_level/visualization_config.json"
        )
        
        self.day_level_data_processor = AnalyticsOrchestrator(
            AnalyticsOrchestratorConfig(
            enable_multi_level_analysis = True,
            source_path = source_path,
            annotation_name = annotation_name,
            databaseSchemas_path = databaseSchemas_path,
            record_date = selected_date
            )
        )

        # Process data
        try:
            all_results, _  = self.day_level_data_processor.run_analytics()
            day_level_results = all_results['multi_level_analytics']["results"]['day_level_results']

            self.processed_df = day_level_results["processed_records"]
            self.mold_based_record_df = day_level_results["mold_based_records"]
            self.item_based_record_df = day_level_results["item_based_records"]
            self.summary_stats = day_level_results["summary_stats"]
            self.analysis_summary = day_level_results["analysis_summary"]

        except Exception as e:
            self.logger.error("Failed to process data: {}", e)
            raise
        
        self.selected_date = selected_date
        self.path_annotation = load_annotation_path(source_path, annotation_name)
        self._load_base_dataframes()

        self.databaseSchemas_path = databaseSchemas_path
        self._setup_schemas()
      
        self.default_dir = Path(default_dir)
        self.output_dir = self.default_dir / "DayLevelDataPlotter"

    def _setup_parallel_config(self) -> None:
        """Setup parallel processing configuration based on system resources."""
        try:
            # Get system information
            cpu_count = mp.cpu_count()
            memory_gb = psutil.virtual_memory().total / (1024**3)
            
            self.logger.info("System specs: {} CPU cores, {:.1f}GB RAM", cpu_count, memory_gb)
            
            # Determine optimal worker count if not specified
            if self.max_workers is None:
                if cpu_count == 1:
                    # Single core - no parallel benefit
                    self.max_workers = 1
                    self.enable_parallel = False
                elif cpu_count == 2:
                    # Dual core (like Colab) - can still benefit from 2 workers if enough RAM
                    if memory_gb >= 8:
                        self.max_workers = 2  # Use both cores
                        self.logger.info("Colab-style environment detected. Using both cores.")
                    else:
                        self.max_workers = 1
                        self.logger.warning("Limited RAM with dual core. Using sequential processing.")
                else:
                    # Multi-core systems
                    if memory_gb < 4:
                        self.max_workers = max(1, min(2, cpu_count // 2))
                        self.logger.warning("Limited RAM detected. Limiting workers to {}", self.max_workers)
                    elif memory_gb < 8:
                        self.max_workers = max(2, min(3, cpu_count // 2))
                    else:
                        self.max_workers = max(2, int(cpu_count * 0.75))
                    
            # Final check - disable if explicitly disabled or only 1 worker needed
            if not self.enable_parallel or self.max_workers <= 1:
                self.enable_parallel = False
                self.max_workers = 1
                self.logger.info("Parallel processing disabled. Workers: {}", self.max_workers)
            else:
                # Double-check we have enough plots to benefit from parallel processing
                num_plots = 8  # We have 8 different plots
                if self.max_workers >= num_plots:
                    self.max_workers = num_plots  # No need for more workers than plots
                
                self.logger.info("Parallel processing enabled. Workers: {} (optimized for plotting)", self.max_workers)
                
        except Exception as e:
            self.logger.warning("Failed to detect system specs: {}. Using sequential processing.", e)
            self.enable_parallel = False
            self.max_workers = 1

    def _setup_schemas(self) -> None:
        """Load database schema configuration for column validation."""
        try:
            self.databaseSchemas_data = load_annotation_path(
                Path(self.databaseSchemas_path).parent,
                Path(self.databaseSchemas_path).name
            )
            self.logger.debug("Database schemas loaded successfully")
        except Exception as e:
            self.logger.error("Failed to load database schemas: {}", str(e))
            raise

    def _load_base_dataframes(self) -> None:
        """Load base DataFrames required for processing"""
        dataframes_to_load = [
            ('moldInfo', 'moldInfo_df')
        ]
        
        for path_key, attr_name in dataframes_to_load:
            self._load_single_dataframe(path_key, attr_name)

    def _load_single_dataframe(self, path_key: str, attr_name: str) -> None:
        """Load a single DataFrame with error handling"""
        path = self.path_annotation.get(path_key)
        
        if not path or not os.path.exists(path):
            raise FileNotFoundError(f"Path to '{path_key}' not found or does not exist: {path}")
        
        try:
            df = pd.read_parquet(path)
            setattr(self, attr_name, df)
            self.logger.debug("{}: {} - {}", path_key, df.shape, list(df.columns))
        except Exception as e:
            self.logger.error("Failed to load {}: {}", path_key, str(e))
            raise

    def plot_all(self, **kwargs):
        """Generate all plots with optional parallel processing."""
        self.logger.info("Start charting... (Parallel: {})", self.enable_parallel)
        
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

        # Save day level extracted records
        try:
            excel_file_name = f"{timestamp_file}_extracted_records_{self.selected_date}.xlsx"
            excel_file_path = newest_dir / excel_file_name
            excel_data = {
                "selectedDateFilter": self.processed_df,
                "moldBasedRecords": self.mold_based_record_df,
                "itemBasedRecords": self.item_based_record_df,
                "summaryStatics": self.summary_stats
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

        # Save analysis summary 
        try:
            analysis_summary_name = f"{timestamp_file}_summary_{self.selected_date}.txt"
            analysis_summary_path = newest_dir / analysis_summary_name
            with open(analysis_summary_path, "w", encoding="utf-8") as log_file:
                log_file.writelines(self.analysis_summary)
            log_entries.append(f"  ⤷ Saved analysis summary: {analysis_summary_path}\n")
            self.logger.info("✅ Saved analysis summary: {}", analysis_summary_path)
        except Exception as e:
            self.logger.warning("Failed to generate summary: {}", e)
         
        # Prepare plotting tasks
        tasks = self._prepare_plot_tasks(timestamp_file, newest_dir)

        # Execute plotting (parallel or sequential)
        try:
            if self.enable_parallel and len(tasks) > 1:
                successful_plots, failed_plots = self._execute_plots_parallel(tasks)
            else:
                successful_plots, failed_plots = self._execute_plots_sequential(tasks)
                
            # Add successful plots to log
            log_entries.extend([f"{plot}\n" for plot in successful_plots])
            
            # Handle failures
            if failed_plots:
                error_summary = f"Failed to create {len(failed_plots)} plots:\n" + "\n".join(failed_plots)
                self.logger.error(error_summary)
                raise OSError(error_summary)
                
        except Exception as e:
            self.logger.error("Plotting process failed: {}", str(e))
            raise

        # Update change log
        try:
            log_path = self.output_dir / "change_log.txt"
            with open(log_path, "a", encoding="utf-8") as log_file:
                log_file.writelines(log_entries)
            self.logger.info("Updated change log {}", log_path)
        except Exception as e:
            self.logger.error("Failed to update change log {}: {}", log_path, e)
            raise OSError(f"Failed to update change log {log_path}: {e}")
        
        return log_entries
    
    def _prepare_plot_tasks(self, timestamp_file: str, newest_dir: Path) -> list:
        """Prepare plotting tasks for parallel execution."""
        plots_args = [
            (self.processed_df, self.visualization_config_path, 
             f"change_times_all_types_fig", change_times_all_types_plotter),

            (self.item_based_record_df, self.visualization_config_path, 
             f"item_based_overview_dashboard", item_based_overview_plotter),

            (self.processed_df, self.visualization_config_path, 
             f"machine_level_yield_efficiency_chart", machine_level_yield_efficiency_plotter),

            (self.processed_df, self.visualization_config_path, 
             f"machine_level_mold_analysis_chart", machine_level_mold_analysis_plotter),

            (self.processed_df, self.visualization_config_path, 
             f"shift_level_yield_efficiency_chart", shift_level_yield_efficiency_plotter),

            (self.processed_df, self.visualization_config_path, 
             f"shift_level_detailed_yield_efficiency_chart", shift_level_detailed_yield_efficiency_plotter),
            
            (self.mold_based_record_df, self.visualization_config_path, 
             f"mold_based_overview_dashboard", mold_based_overview_plotter),

            ((self.processed_df, self.moldInfo_df), 
             self.visualization_config_path, 
             f"shift_level_mold_efficiency_chart", shift_level_mold_efficiency_plotter),
        ]

        tasks = []
        for data, config_path, name, func in plots_args:
            path = newest_dir / f'{timestamp_file}_{name}_{self.selected_date}.png'
            tasks.append((data, config_path, name, func, str(path), timestamp_file))
            
        return tasks

    def _execute_plots_parallel(self, tasks: list) -> Tuple[list, list]:
        """Execute plotting tasks in parallel."""
        successful_plots = []
        failed_plots = []
        
        self.logger.info("Starting parallel plotting with {} workers for {} tasks", 
                        self.max_workers, len(tasks))
        
        start_time = time.time()
        
        # Use ThreadPoolExecutor for I/O bound operations (matplotlib plotting)
        # ProcessPoolExecutor can be problematic with matplotlib and large dataframes
        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_task = {executor.submit(self._plot_single_chart, task): task for task in tasks}
            
            # Collect results as they complete
            for future in as_completed(future_to_task):
                task = future_to_task[future]
                try:
                    success, name, path_collection, error_msg, exec_time = future.result()
                    if success:
                        path_collection_str = '\n'.join(path_collection)
                        successful_plots.append(f"  ⤷ Saved new plots for {name} ({exec_time:.1f}s): {path_collection_str}")
                        self.logger.info("✅ Created plot: {} ({:.1f}s)", name, exec_time)
                    else:
                        failed_plots.append(error_msg)
                        self.logger.error("❌ {}", error_msg)
                except Exception as e:
                    error_msg = f"Task execution failed for {task[1]}: {str(e)}"
                    failed_plots.append(error_msg)
                    self.logger.error("❌ {}", error_msg)
        
        total_time = time.time() - start_time
        self.logger.info("Parallel plotting completed in {:.1f}s. Success: {}, Failed: {}", 
                        total_time, len(successful_plots), len(failed_plots))
        
        return successful_plots, failed_plots

    def _execute_plots_sequential(self, tasks: list) -> Tuple[list, list]:
        """Execute plotting tasks sequentially (fallback method)."""
        successful_plots = []
        failed_plots = []
        
        self.logger.info("Starting sequential plotting for {} tasks", len(tasks))
        start_time = time.time()
        
        for task in tasks:
            success, name, path_collection, error_msg, exec_time = self._plot_single_chart(task)
            if success:
                path_collection_str = '\n'.join(path_collection)
                successful_plots.append(f"  ⤷ Saved new plots for {name} ({exec_time:.1f}s): {path_collection_str}")
                self.logger.info("✅ Created plot: {} ({:.1f}s)", name, exec_time)
            else:
                failed_plots.append(error_msg)
                self.logger.error("❌ {}", error_msg)
        
        total_time = time.time() - start_time
        self.logger.info("Sequential plotting completed in {:.1f}s", total_time)
        
        return successful_plots, failed_plots

    @staticmethod
    def _plot_single_chart(args: Tuple[Any, str, Callable, str, str]) -> Tuple[bool, str, list, str, float]:
        """
        Worker function to create a single plot.
        Returns: (success, plot_name, error_message, execution_time)
        """
        data, config_path, name, func, path, timestamp_file = args
        start_time = time.time()
        
        path_collection = []

        try:
            # Create the plot
            if isinstance(data, tuple):
                fig = func(*data, visualization_config_path = config_path)
            else:
                fig = func(data, visualization_config_path = config_path)
                
            # Save the plot
            fig.savefig(path, dpi=300, bbox_inches="tight", pad_inches=0.5)
            path_collection.append(path)
            
            plt.close(fig)

            execution_time = time.time() - start_time
            return True, name, path_collection, "", execution_time
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Failed to create plot '{name}': {str(e)}\n{traceback.format_exc()}"
            return False, name, path_collection, error_msg, execution_time