import pandas as pd
import matplotlib.pyplot as plt
from loguru import logger
from pathlib import Path
import shutil
import multiprocessing as mp
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
import psutil
import traceback
import os
import re
import time
from datetime import datetime
from typing import Tuple, Dict, Any, Callable
from agents.decorators import validate_init_dataframes
from agents.utils import load_annotation_path
from agents.analyticsOrchestrator.multiLevelDataAnalytics.multi_level_data_processor import AnalyticflowConfig, MultiLevelDataAnalytics
from agents.dashboardBuilder.visualize_data.month_level.month_performance_plotter import month_performance_plotter 
from agents.dashboardBuilder.reportFormatters.generate_early_warning_report import generate_early_warning_report
from agents.dashboardBuilder.visualize_data.month_level.machine_based_dashboard_plotter import machine_based_dashboard_plotter
from agents.dashboardBuilder.visualize_data.month_level.mold_based_dashboard_plotter import mold_based_dashboard_plotter

# Required columns for dataframes
REQUIRED_FINISHED_COLUMNS = ['poReceivedDate', 'poNo', 'poETA', 'itemCode', 'itemName',
                             'itemQuantity', 'itemCodeName', 'firstRecord', 'lastRecord',
                             'itemGoodQuantity', 'moldHistNum', 'moldHist', 'proStatus',
                             'is_backlog', 'itemNGQuantity', 'itemRemainQuantity', 'poStatus',
                             'overproduction_quantity', 'etaStatus']

REQUIRED_UNFINISHED_COLUMNS = ['poReceivedDate', 'poNo', 'poETA', 'itemCode', 'itemName',
                               'itemQuantity', 'itemCodeName', 'firstRecord', 'lastRecord',
                               'itemGoodQuantity', 'moldHistNum', 'moldHist', 'proStatus',
                               'is_backlog', 'itemNGQuantity', 'itemRemainQuantity', 'poStatus',
                               'overproduction_quantity', 'moldNum', 'moldList', 'totalItemCapacity',
                               'avgItemCapacity', 'accumulatedQuantity', 'completionProgress',
                               'totalRemainByMold', 'accumulatedRate', 'totalEstimatedLeadtime',
                               'avgEstimatedLeadtime', 'poOTD', 'poRLT', 'avgCumsumLT',
                               'totalCumsumLT', 'overTotalCapacity', 'overAvgCapacity', 'is_overdue',
                               'etaStatus', 'capacityWarning', 'capacitySeverity',
                               'capacityExplanation']

REQUIRED_UNFINISHED_SHORT_COLUMNS = [
    'poNo', 'poETA', 'itemQuantity', 'itemGoodQuantity', 'itemNGQuantity',
    'is_backlog', 'itemCodeName', 'proStatus', 'poStatus', 'moldHistNum',
    'itemRemainQuantity', 'completionProgress', 'etaStatus',
    'overAvgCapacity', 'overTotalCapacity', 'is_overdue', 'capacityWarning',
    'capacitySeverity', 'capacityExplanation']

REQUIRED_PROGRESS_COLUMNS = [
    'poNo', 'itemCodeName', 'is_backlog', 'poStatus', 'poETA',
    'itemNGQuantity', 'itemQuantity', 'itemGoodQuantity', 'etaStatus',
    'proStatus', 'moldHistNum'
]


@validate_init_dataframes(lambda self: {
    "productRecords_df": list(self.databaseSchemas_data['dynamicDB']['productRecords']['dtypes'].keys())
})
@validate_init_dataframes({
    "finished_df": REQUIRED_FINISHED_COLUMNS, 
    "unfinished_df": REQUIRED_UNFINISHED_COLUMNS,
    "short_unfinished_df": REQUIRED_UNFINISHED_SHORT_COLUMNS,
    "all_progress_df": REQUIRED_PROGRESS_COLUMNS
})
class MonthLevelDataPlotter:
    """
    Plotter for month-level PO dashboard with visualization and reporting.
    
    Attributes:
        record_month: Target month in YYYY-MM format
        analysis_date: Date of analysis (defaults to current date)
        output_dir: Directory for saving outputs
    """
    
    def __init__(self, 
                 record_month: str,
                 analysis_date: str = None,
                 source_path: str = 'agents/shared_db/DataLoaderAgent/newest', 
                 annotation_name: str = "path_annotations.json",
                 databaseSchemas_path: str = 'database/databaseSchemas.json',
                 default_dir: str = "agents/shared_db",
                 visualization_config_path: str = None,
                 enable_parallel: bool = True,
                 max_workers: int = None):
        
        self.logger = logger.bind(class_="MonthLevelDataPlotter")
        
        # Parallel processing configuration
        self.enable_parallel = enable_parallel
        self.max_workers = max_workers
        self._setup_parallel_config()
        
        # Validate record_month format
        self._validate_record_month(record_month)
        analysis_date = analysis_date or datetime.now().strftime("%Y-%m-%d")
        
        # Setup config path
        self.visualization_config_path = (
            visualization_config_path 
            or "agents/dashboardBuilder/visualize_data/month_level/visualization_config.json"
        )

        # Load path annotations and base dataframes
        self.path_annotation = load_annotation_path(source_path, annotation_name)
        self._load_base_dataframes()

        # Load database schemas
        self.databaseSchemas_path = databaseSchemas_path
        self._setup_schemas()
        
        # Initialize data processor    
        self.month_level_data_processor = MultiLevelDataAnalytics(
            config = AnalyticflowConfig(
                record_month = record_month,
                month_analysis_date = analysis_date,
                source_path = source_path,
                annotation_name = annotation_name,
                databaseSchemas_path = databaseSchemas_path,
                default_dir = default_dir)
                )
        
        # Process data
        try:

            month_level_results = self.month_level_data_processor.data_process()["month_level_results"]

            self.analysis_timestamp = month_level_results["month_analysis_date"]
            self.adjusted_record_month = month_level_results["record_month"]
            self.finished_df = month_level_results["finished_records"]
            self.unfinished_df = month_level_results["unfinished_records"]
            self.final_summary = month_level_results["summary_stats"]
            
            self.early_warning_report = generate_early_warning_report(
                self.unfinished_df, 
                self.adjusted_record_month,
                self.analysis_timestamp,
                colored=False
            )
            
            # Filter data by date and month
            self.filtered_df = self.productRecords_df[
                (self.productRecords_df['recordDate'].dt.date < self.analysis_timestamp.date()) &
                (self.productRecords_df['recordDate'].dt.strftime('%Y-%m') == self.adjusted_record_month)
            ].copy()
            self.filtered_df['recordMonth'] = self.filtered_df['recordDate'].dt.strftime('%Y-%m')
            
            # Prepare unfinished POs and Total POs data
            self.short_unfinished_df, self.all_progress_df = self._prepare_data()

            self.logger.info(
                "Data prepared: {} unfinished records, {} total records",
                len(self.short_unfinished_df), len(self.all_progress_df)
            )
            
        except Exception as e:
            self.logger.error("Failed to process data: {}", e)
            raise
        
        # Setup directories
        self.default_dir = Path(default_dir)
        self.output_dir = self.default_dir / "MonthLevelDataPlotter"

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
            ('productRecords', 'productRecords_df')
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
    
    def _validate_record_month(self, record_month: str) -> None:
        """Validate record_month format (YYYY-MM)."""
        if not re.match(r'^\d{4}-\d{2}$', record_month):
            raise ValueError(
                f"Invalid record_month format: '{record_month}'. Expected format: YYYY-MM"
            )
    
    def _prepare_data(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Prepare dataframes for visualization.
        
        Returns:
            Tuple of (short_unfinished_df, all_progress_df) containing processed data
        """
        # Prepare main dataframe
        short_unfinished_df = self.unfinished_df[REQUIRED_UNFINISHED_SHORT_COLUMNS].copy()
        
        # Prepare progress dataframe
        all_progress_df = pd.concat(
            [
                self.finished_df[REQUIRED_PROGRESS_COLUMNS], 
                self.unfinished_df[REQUIRED_PROGRESS_COLUMNS]
            ], 
            ignore_index=True
        )
        
        return short_unfinished_df, all_progress_df

    @staticmethod
    def _plot_single_chart(args: Tuple[Any, str, Callable, str, str, Dict]) -> Tuple[bool, str, list, str, float]:
        """
        Worker function to create a single plot.
        Returns: (success, plot_name, error_message, execution_time)
        """
        data, config_path, name, func, path, timestamp_file, kwargs = args
        start_time = time.time()

        path_collection = []

        try:
            # Create the plot - pass visualization_config_path as keyword argument
            if isinstance(data, tuple):
                result = func(*data, visualization_config_path=config_path, **kwargs)
            else:
                result = func(data, visualization_config_path=config_path, **kwargs)

            # Handle different return types
            if isinstance(result, tuple):
                # Result is (summary, fig) or (summary, figs)
                summary, fig_or_figs = result
                
                if isinstance(fig_or_figs, list):
                    # Multiple figures - save each one
                    for idx, fig in enumerate(fig_or_figs):
                        fig_path = path.replace('.png', f'_page{idx+1}.png')
                        fig.savefig(fig_path, dpi=300, bbox_inches="tight", pad_inches=0.5)
                        path_collection.append(fig_path)
                        plt.close(fig)

                else:
                    # Single figure
                    fig_or_figs.savefig(path, dpi=300, bbox_inches="tight", pad_inches=0.5)
                    path_collection.append(path)
                    plt.close(fig_or_figs)

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

    def _prepare_plot_tasks(self, timestamp_file: str, newest_dir: Path) -> list:
        """Prepare plotting tasks for parallel execution."""
        
        fig_title_date = f'{self.adjusted_record_month} - Analysis date: {self.analysis_timestamp.date()}'
        
        plots_args = [
            # 1. Month performance plotter
            # Signature: (short_unfinished_df, all_progress_df, fig_title, visualization_config_path)
            (
                (self.short_unfinished_df, self.all_progress_df,
                f'Month Performance Dashboard for {fig_title_date}'),
                self.visualization_config_path,
                "month_performance_dashboard",
                month_performance_plotter,
                {}  # No extra kwargs
            ),
            
            # 2. Machine based dashboard
            # Signature: (filtered_df, metrics, fig_title, visualization_config_path)
            (
                (self.filtered_df,
                ['totalQuantity', 'goodQuantity', 'totalMoldShot', 'avgNGRate',
                 'workingDays', 'notProgressDays', 'workingShifts', 'notProgressShifts',
                 'poNums', 'itemNums', 'itemComponentNums'],
                f'Production Dashboard by Machine for {fig_title_date}'),
                self.visualization_config_path,
                "machine_based_dashboard",
                machine_based_dashboard_plotter,
                {}  # No extra kwargs
            ),
            
            # 3. Mold based dashboard
            # Signature: (filtered_df, metrics, fig_title, visualization_config_path)
            (
                (self.filtered_df,
                ['totalShots', 'cavityNums', 'avgCavity', 'machineNums',
                 'totalQuantity', 'goodQuantity', 'totalNG', 'totalNGRate'],
                f'Production Dashboard by Mold for {fig_title_date}'),
                self.visualization_config_path,
                "mold_based_dashboard",
                mold_based_dashboard_plotter,
                {}  # No extra kwargs
            ),
        ]

        tasks = []
        for data, config_path, name, func, kwargs in plots_args:
            path = newest_dir / f'{timestamp_file}_{name}_{self.adjusted_record_month}.png'
            tasks.append((data, config_path, name, func, str(path), timestamp_file, kwargs))

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

        # Save month level extracted records
        excel_file_name = f"{timestamp_file}_extracted_records_{self.adjusted_record_month}.xlsx"
        excel_file_path = newest_dir / excel_file_name

        excel_data = {
            "finished_df": self.finished_df,
            "unfinished_df": self.unfinished_df,
            "short_unfinished_df": self.short_unfinished_df,
            "all_progress_df": self.all_progress_df,
            "filtered_records": self.filtered_df
        }

        try:
            with pd.ExcelWriter(excel_file_path, engine="openpyxl") as writer:
                for sheet_name, df in excel_data.items():
                    if not isinstance(df, pd.DataFrame):
                        df = pd.DataFrame([df])
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
            log_entries.append(f"  ⤷ Saved data analysis results: {excel_file_path}\n")
            self.logger.info("✅ Saved data analysis results: {}", excel_file_path)
        except Exception as e:
            self.logger.error("❌ Failed to save file {}: {}", excel_file_name, e)
            raise OSError(f"Failed to save file {excel_file_name}: {e}")
        
        # Save final summary
        report_name = f"{timestamp_file}_final_summary_{self.adjusted_record_month}.txt"
        report_path = newest_dir / report_name
        try:
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(self.final_summary)
            log_entries.append(f"  ⤷ Saved final summary: {report_name}\n")
            self.logger.info("✅ Saved final summary: {}", report_name)
        except Exception as e:
            self.logger.warning("Failed to generate summary: {}", e)

        # Save early warning report
        warning_report_name = f"{timestamp_file}_early_warning_report_{self.adjusted_record_month}.txt"
        warning_report_path = newest_dir / warning_report_name
        try:
            with open(warning_report_path, "w", encoding="utf-8") as f:
                f.write(self.early_warning_report)
            log_entries.append(f"  ⤷ Saved early warning report: {warning_report_name}\n")
            self.logger.info("✅ Saved early warning report: {}", warning_report_name)
        except Exception as e:
            self.logger.warning("Failed to generate early warning report: {}", e)

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