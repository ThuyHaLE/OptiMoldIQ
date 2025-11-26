import pandas as pd
import matplotlib.pyplot as plt
from loguru import logger
from pathlib import Path
import shutil
import multiprocessing as mp
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
import psutil
import traceback
import time
from datetime import datetime
from typing import Tuple, Dict, Any, Callable
from agents.decorators import validate_init_dataframes

from agents.dashboardBuilder.visualize_data.mold_level.machine_ton_based_mold_utilization_plotter import machine_ton_based_mold_utilization_plotter
from agents.dashboardBuilder.visualize_data.mold_level.mold_machine_first_pairing_plotter import mold_machine_first_pairing_plotter
from agents.dashboardBuilder.visualize_data.mold_level.mold_utilization_plotter import mold_utilization_plotter

# Required columns for dataframes
FIRST_USED_MOLD_REQUIRED_COLUMNS = ['moldNo', 'acquisitionDate', 'firstDate', 'daysDifference']
FIRST_PAIRED_MOLD_MACHINE_REQUIRED_COLUMNS = ['firstDate', 'machineCode', 'moldNo', 'acquisitionDate']
USED_MOLD_MACHINE_REQUIRED_COLUMNS = ['moldNo', 'usedMachineTonnage', 'usedTonnageCount']

# Decorator to validate DataFrames are initialized with the correct schema
@validate_init_dataframes({
    "first_mold_usage": FIRST_USED_MOLD_REQUIRED_COLUMNS, 
    "first_paired_mold_machine": FIRST_PAIRED_MOLD_MACHINE_REQUIRED_COLUMNS, 
    "mold_tonnage_summary": USED_MOLD_MACHINE_REQUIRED_COLUMNS
})

class MachineMoldPairPlotter:
    """
    Plotter for mold-level dashboard with visualization and reporting.
    """
    
    def __init__(self, 
                 first_mold_usage: pd.DataFrame, 
                 first_paired_mold_machine: pd.DataFrame,
                 mold_tonnage_summary: pd.DataFrame,
                 default_dir: str = "agents/shared_db/DashboardBuilder/HardwareChangePlotter/MachineMoldPairPlotter",
                 visualization_config_path: str = None,
                 enable_parallel: bool = True,
                 max_workers: int = None):
        
        self.logger = logger.bind(class_="MachineMoldPairPlotter")
        
        # Parallel processing configuration
        self.enable_parallel = enable_parallel
        self.max_workers = max_workers
        self._setup_parallel_config()
        
        # Setup config path
        self.visualization_config_path = (
            visualization_config_path 
            or "agents/dashboardBuilder/visualize_data/mold_level/visualization_config.json"
        )
        
        self.first_mold_usage = first_mold_usage
        self.first_paired_mold_machine = first_paired_mold_machine
        self.mold_tonnage_summary = mold_tonnage_summary

        # Setup directories
        self.output_dir = Path(default_dir)

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
                # Estimate number of plots for month level (3 different plot types)
                num_plots = 3
                if self.max_workers >= num_plots:
                    self.max_workers = num_plots  # No need for more workers than plots

                self.logger.info("Parallel processing enabled. Workers: {} (optimized for plotting)", self.max_workers)

        except Exception as e:
            self.logger.warning("Failed to detect system specs: {}. Using sequential processing.", e)
            self.enable_parallel = False
            self.max_workers = 1
    
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

        log_path = self.output_dir / "change_log.txt"
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
            with open(log_path, "a", encoding="utf-8") as log_file:
                log_file.writelines(log_entries)
            self.logger.info("Updated change log {}", log_path)
        except Exception as e:
            self.logger.error("Failed to update change log {}: {}", log_path, e)
            raise OSError(f"Failed to update change log {log_path}: {e}")
        
        return log_entries
    
    def _prepare_plot_tasks(self, timestamp_file: str, newest_dir: Path) -> list:
        """Prepare plotting tasks for parallel execution."""

        plots_args = plots_args = [
            (self.first_mold_usage,
             'Mold_utilization_dashboard', 
             self.visualization_config_path,
             mold_utilization_plotter),

            (self.first_paired_mold_machine,
            'Mold_machine_first_pairing_dashboard', 
            self.visualization_config_path,
            mold_machine_first_pairing_plotter),

            (self.mold_tonnage_summary,
             'Machine_tonage_based_mold_utilization_dashboard', 
             self.visualization_config_path,
             machine_ton_based_mold_utilization_plotter)
        ]

        tasks = []
        for data, name, config_path, func in plots_args:
            path = newest_dir / f'{timestamp_file}_{name}.png'
            tasks.append((data, name, config_path, func, str(path), timestamp_file))

        return tasks

    def _execute_plots_parallel(self, tasks: list) -> Tuple[list, list]:
        """Execute plotting tasks in parallel."""
        successful_plots = []
        failed_plots = []

        self.logger.info("Starting parallel plotting with {} workers for {} tasks",
                        self.max_workers, len(tasks))

        start_time = time.time()

        # Use ProcessPoolExecutor for CPU-bound plotting operations
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
                    error_msg = f"Task execution failed for {task[2]}: {str(e)}"
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
    def _plot_single_chart(args: Tuple[Any, str, Callable, str, str, Dict]) -> Tuple[bool, str, list, str, float]:
        """
        Worker function to create a single plot.
        Returns: (success, plot_name, error_message, execution_time)
        """
        data, name, config_path, func, path, timestamp_file = args
        start_time = time.time()

        path_collection = []

        try:
            # Create the plot - pass visualization_config_path as keyword argument
            if isinstance(data, tuple):
                result = func(*data, visualization_config_path=config_path)
            else:
                result = func(data, visualization_config_path=config_path)

            # Handle different return types
            if isinstance(result, tuple):

                if isinstance(result, list):
                    # Multiple figures - save each one
                    for idx, fig in enumerate(result):
                        fig_path = path.replace('.png', f'_page{idx+1}.png')
                        fig.savefig(fig_path, dpi=300, bbox_inches="tight", pad_inches=0.5)
                        path_collection.append(fig_path)
                        plt.close(fig)

                else:
                    # Single figure
                    result.savefig(path, dpi=300, bbox_inches="tight", pad_inches=0.5)
                    path_collection.append(path)
                    plt.close(result)

            else:
                # Result is just a figure
                result.savefig(path, dpi=300, bbox_inches="tight", pad_inches=0.5)
                path_collection.append(path)
                plt.close(result)
                
            execution_time = time.time() - start_time
            return True, name, path_collection, "", execution_time

        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Failed to create plot '{name}': {str(e)}\n{traceback.format_exc()}"
            return False, name, path_collection, error_msg, execution_time