import pandas as pd
from loguru import logger
from pathlib import Path
import shutil
from datetime import datetime
from typing import Dict, List
from agents.decorators import validate_init_dataframes
from agents.utils import validate_multi_level_analyzer_result

from configs.shared.config_report_format import ConfigReportMixin
from configs.shared.dict_based_report_generator import DictBasedReportGenerator
from agents.dashboardBuilder.visualizationPipelines.configs.visualization_pipeline_config import VisualizationPipelineResult

from agents.dashboardBuilder.plotters.utils import setup_parallel_config, plot_single_chart, execute_tasks, process_plot_results

from agents.dashboardBuilder.plotters.year_level.monthly_performance_plotter import monthly_performance_plotter
from agents.dashboardBuilder.plotters.year_level.year_performance_plotter import year_performance_plotter
from agents.dashboardBuilder.plotters.year_level.machine_based_year_view_dashboard_plotter import machine_based_year_view_dashboard_plotter
from agents.dashboardBuilder.plotters.year_level.mold_based_year_view_dashboard_plotter import mold_based_year_view_dashboard_plotter
from agents.dashboardBuilder.plotters.year_level.field_based_month_view_dashboard_plotter import field_based_month_view_dashboard_plotter

# Required columns for dataframes
REQUIRED_FINISHED_COLUMNS = [
    'poReceivedDate', 'poNo', 'poETA', 'itemCode', 'itemName', 'itemQuantity', 'itemCodeName', 'firstRecord', 
    'lastRecord', 'itemGoodQuantity', 'itemNGQuantity', 'moldHistNum', 'moldHist', 'proStatus', 'is_backlog', 
    'itemRemainQuantity', 'poStatus', 'overproduction_quantity', 'etaStatus']

REQUIRED_UNFINISHED_COLUMNS = [
    'poReceivedDate', 'poNo', 'poETA', 'itemCode', 'itemName', 'itemQuantity', 'itemCodeName', 'firstRecord', 
    'lastRecord', 'itemGoodQuantity', 'itemNGQuantity', 'moldHistNum', 'moldHist', 'proStatus', 'is_backlog', 
    'itemRemainQuantity', 'poStatus', 'overproduction_quantity', 'moldNum', 'moldList', 'totalItemCapacity',
    'avgItemCapacity', 'accumulatedQuantity', 'completionProgress', 'totalRemainByMold', 'accumulatedRate', 
    'totalEstimatedLeadtime', 'avgEstimatedLeadtime', 'poOTD', 'poRLT', 'avgCumsumLT', 'totalCumsumLT', 
    'overTotalCapacity', 'overAvgCapacity', 'is_overdue', 'etaStatus', 'capacityWarning', 'capacitySeverity', 
    'capacityExplanation']

REQUIRED_UNFINISHED_SHORT_COLUMNS = [
    'poNo', 'poETA', 'itemQuantity', 'itemGoodQuantity', 'itemNGQuantity', 'is_backlog', 'itemCodeName', 'proStatus', 
    'poStatus', 'moldHistNum', 'itemRemainQuantity', 'completionProgress', 'etaStatus', 'overAvgCapacity', 
    'overTotalCapacity', 'is_overdue', 'capacityWarning', 'capacitySeverity', 'capacityExplanation']

REQUIRED_PROGRESS_COLUMNS = [
    'poNo', 'itemCodeName', 'is_backlog', 'poStatus', 'poETA', 'itemNGQuantity', 'itemQuantity', 
    'itemGoodQuantity', 'etaStatus', 'proStatus', 'moldHistNum']

# Decorator to validate DataFrames are initialized with the correct schema
@validate_init_dataframes(lambda self: {
    "productRecords_df": [
        'recordDate', 'workingShift', 'machineNo', 'machineCode', 'itemCode', 'itemName', 'colorChanged', 
        'moldChanged', 'machineChanged', 'poNote', 'moldNo', 'moldShot', 'moldCavity', 'itemTotalQuantity',
        'itemGoodQuantity', 'itemBlackSpot', 'itemOilDeposit', 'itemScratch', 'itemCrack', 'itemSinkMark', 
        'itemShort', 'itemBurst', 'itemBend', 'itemStain', 'otherNG', 'plasticResin', 'plasticResinCode',
        'plasticResinLot', 'colorMasterbatch', 'colorMasterbatchCode', 'additiveMasterbatch', 'additiveMasterbatchCode'],
    "finished_df": REQUIRED_FINISHED_COLUMNS,
    "unfinished_df": REQUIRED_UNFINISHED_COLUMNS,
    "short_unfinished_df": REQUIRED_UNFINISHED_SHORT_COLUMNS,
    "all_progress_df": REQUIRED_PROGRESS_COLUMNS
})

class YearLevelVisualizationPipeline(ConfigReportMixin):
    """
    Plotter for year-level PO dashboard with visualization and reporting.

    Attributes:
        year_level_results: Results from year level analyzer
       default_dir: Directory for saving outputs
    """

    YEAR_LEVEL_KEYS = ['finishedRecords', 'unfinishedRecords']

    def __init__(self,
                 year_level_results: Dict,
                 requested_timestamp: str,
                 analysis_date: str,
                 productRecords_df: pd.DataFrame, 
                 default_dir: str = "agents/shared_db/DashboardBuilder/MultiLevelPerformanceVisualizationService/YearLevelVisualizationPipeline/newest/visualized_results",
                 visualization_config_path: str = None,
                 enable_parallel: bool = True,
                 max_workers: int = None):

        self._capture_init_args()
        self.logger = logger.bind(class_="YearLevelVisualizationPipeline")

        # Setup config path
        self.visualization_config_path = (
            visualization_config_path
            or "agents/dashboardBuilder/plotters/year_level/visualization_config.json"
        )

        self.requested_timestamp = requested_timestamp
        self.analysis_date = pd.to_datetime(analysis_date)

        # Load base dataframes
        self.productRecords_df = productRecords_df
        
        # Validate data
        self.year_level_results = year_level_results
        validate_multi_level_analyzer_result(self.year_level_results, self.YEAR_LEVEL_KEYS)

        # Extract features
        self._prepare_data()

        # Define plots arguments
        self.plots_args = self._define_plots_args()

        # Setup parallel configuration using the reusable function
        self.enable_parallel, self.max_workers = setup_parallel_config(
            enable_parallel=enable_parallel,
            max_workers=max_workers,
            num_tasks=len(self.plots_args),
            min_memory_gb=4.0
        )

        # Setup directories
        self.output_dir = Path(default_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _prepare_data(self) -> None:
        "Extract and prepare data for visualizing"

        # Extract features
        self.finished_df = self.year_level_results['finishedRecords'].copy()
        self.unfinished_df = self.year_level_results['unfinishedRecords'].copy()
        
        # Filter production data by date and year
        self.filtered_df = self.productRecords_df[
            (self.productRecords_df['recordDate'].dt.date < self.analysis_date.date()) &
            (self.productRecords_df['recordDate'].dt.year == int(self.requested_timestamp))
        ].copy()
        self.filtered_df['recordMonth'] = self.filtered_df['recordDate'].dt.strftime('%Y-%m')

        # Prepare unfinished POs and Total POs data
        self.short_unfinished_df = self.unfinished_df[REQUIRED_UNFINISHED_SHORT_COLUMNS].copy()
        self.all_progress_df = pd.concat(
            [
                self.finished_df[REQUIRED_PROGRESS_COLUMNS].copy(),
                self.unfinished_df[REQUIRED_PROGRESS_COLUMNS].copy()
            ],
            ignore_index=True
        )

        self.logger.info("Data prepared: {} unfinished records, {} total records", 
                         len(self.short_unfinished_df), len(self.all_progress_df))
        
        # Create Dict for result return
        self.raw_data = {
            "base_df": self.productRecords_df,
            "year_level_results": self.year_level_results
        }

        self.visualized_data = {
                "short_unfinished_df": self.short_unfinished_df,
                "all_progress_df": self.all_progress_df,
                "filtered_records": self.filtered_df
            }
        
    def _define_plots_args(self) -> List: 
        """Define all plotting tasks with their arguments."""

        fig_title_date = f'{self.requested_timestamp} - Analysis date: {self.analysis_date.date().isoformat()}'

        plots_args = [
            # 1. Monthly performance plotter
            # Signature: (short_unfinished_df, all_progress_df, record_year, analysis_date, visualization_config_path)
            (
                (self.short_unfinished_df, self.all_progress_df, 
                self.requested_timestamp, self.analysis_date),
                self.visualization_config_path,
                "monthly_performance_dashboard",
                monthly_performance_plotter,
                {}  # No extra kwargs
            ),
            
            # 2. Year performance plotter
            # Signature: (short_unfinished_df, all_progress_df, record_year, analysis_date, visualization_config_path)
            (
                (self.short_unfinished_df, self.all_progress_df, 
                self.requested_timestamp, self.analysis_date),
                self.visualization_config_path,
                "year_performance_dashboard",
                year_performance_plotter,
                {}  # No extra kwargs
            ),
            
            # 3. Machine based year view
            # Signature: (filtered_df, fig_title, visualization_config_path)
            (
                (self.filtered_df, f'Production Dashboard by Machine for {fig_title_date}'),
                self.visualization_config_path,
                "machine_based_year_view_dashboard",
                machine_based_year_view_dashboard_plotter,
                {}  # No extra kwargs
            ),
            
            # 4. Mold based year view
            # Signature: (filtered_df, metrics, fig_title, visualization_config_path)
            (
                (self.filtered_df, 
                ['totalShots', 'cavityNums', 'avgCavity', 'machineNums', 'totalNGRate'],
                f'Production Dashboard by Mold for {fig_title_date}'),
                self.visualization_config_path,
                "mold_based_year_view_dashboard",
                mold_based_year_view_dashboard_plotter,
                {}  # No extra kwargs
            ),
            
            # 5. Machine - Working days metrics
            # Signature: (filtered_df, metrics, fig_title, field, subfig_per_page, visualization_config_path)
            (
                (self.filtered_df,
                ['workingDays', 'notProgressDays', 'workingShifts', 'notProgressShifts'],
                f"Production Dashboard by Machine for {fig_title_date}",
                'machineCode',
                10),
                self.visualization_config_path,
                "machine_working_days_dashboard",
                field_based_month_view_dashboard_plotter,
                {}  # No extra kwargs
            ),
            
            # 6. Machine - PO/Item metrics
            # Signature: (filtered_df, metrics, fig_title, field, subfig_per_page, visualization_config_path)
            (
                (self.filtered_df,
                ['poNums', 'itemNums', 'moldNums', 'itemComponentNums', 'avgNGRate'],
                f"Production Dashboard by Machine for {fig_title_date}",
                'machineCode',
                10),
                self.visualization_config_path,
                "machine_po_item_dashboard",
                field_based_month_view_dashboard_plotter,
                {}  # No extra kwargs
            ),
            
            # 7. Machine - Quantity metrics
            # Signature: (filtered_df, metrics, fig_title, field, subfig_per_page, visualization_config_path)
            (
                (self.filtered_df,
                ['totalQuantity', 'goodQuantity', 'totalMoldShot'],
                f"Production Dashboard by Machine for {fig_title_date}",
                'machineCode',
                10),
                self.visualization_config_path,
                "machine_quantity_dashboard",
                field_based_month_view_dashboard_plotter,
                {}  # No extra kwargs
            ),
            
            # 8. Mold - Shots metrics
            # Signature: (filtered_df, metrics, fig_title, field, subfig_per_page, visualization_config_path)
            (
                (self.filtered_df,
                ['totalShots', 'cavityNums', 'avgCavity', 'machineNums', 'totalNGRate'],
                f"Production Dashboard by Mold for {fig_title_date}",
                'moldNo',
                10),
                self.visualization_config_path,
                "mold_shots_dashboard",
                field_based_month_view_dashboard_plotter,
                {}  # No extra kwargs
            ),
            
            # 9. Mold - Quantity metrics
            # Signature: (filtered_df, metrics, fig_title, field, subfig_per_page, visualization_config_path)
            (
                (self.filtered_df,
                ['totalQuantity', 'goodQuantity', 'totalNG'],
                f"Production Dashboard by Mold for {fig_title_date}",
                'moldNo',
                10),
                self.visualization_config_path,
                "mold_quantity_dashboard",
                field_based_month_view_dashboard_plotter,
                {}  # No extra kwargs
            ),
        ]

        return plots_args

    def _prepare_plot_tasks(self, 
                            plots_args: List, 
                            timestamp_file: str, 
                            output_dir: Path) -> list:
        
        """Prepare plotting tasks for parallel execution."""

        tasks = []
        for data, config_path, name, func, kwargs in plots_args:
            path = output_dir / f'{timestamp_file}_{name}_{self.requested_timestamp}.png'
            tasks.append((data, config_path, name, func, str(path), timestamp_file, kwargs))

        return tasks

    def run_pipeline(self, **kwargs) -> VisualizationPipelineResult:
        """Generate all plots with optional parallel processing."""

        pipeline_name = self.__class__.__name__

        self.logger.info("Starting {}... (Parallel: {})", pipeline_name, self.enable_parallel)
        
        # Generate config header
        start_time = datetime.now()
        timestamp_str = start_time.strftime("%Y-%m-%d %H:%M:%S")
        config_header = self._generate_config_report(timestamp_str)
        
        log_entries = [
            config_header,
            "--Processing Summary--",
            f"⤷ {pipeline_name} results:",
            f"[{timestamp_str}] Saving new version..."
        ]

        # Generate summary report
        reporter = DictBasedReportGenerator(use_colors=False)
        pipeline_summary = "\n".join(reporter.export_report(
            {
               "raw_data": self.raw_data, 
               "visualized_data": self.visualized_data
            }
            ))
        
        # Prepare plotting tasks
        timestamp_file = start_time.strftime("%Y%m%d_%H%M")
        tasks = self._prepare_plot_tasks(self.plots_args, timestamp_file, self.output_dir)

        # Execute plotting using the reusable utility
        try:
            raw_results, failed_tasks = execute_tasks(
                tasks=tasks,
                worker_function=plot_single_chart,
                enable_parallel=self.enable_parallel,
                max_workers=self.max_workers,
                executor_type="process",  # CPU-bound plotting operations
                task_name_extractor=lambda task: task[2]  # Extract name from task
            )

            # Process results
            successful_plots, failed_plots = process_plot_results(raw_results)

            # Add successful plots to log
            log_entries.append(f"Successed to create {len(successful_plots)} plots:\n")
            log_entries.extend([f"{plot}\n" for plot in successful_plots])

            # Handle failures
            if failed_plots:
                error_summary = f"Failed to create {len(failed_plots)} plots:\n" + "\n".join(failed_plots)
                log_entries.append(error_summary)
                self.logger.error(error_summary)

            return VisualizationPipelineResult(
                raw_data = self.raw_data,
                visualized_data = self.visualized_data,
                pipeline_name = pipeline_name,
                pipeline_summary = pipeline_summary,
                log = '\n'.join(log_entries)
                )

        except Exception as e:
            self.logger.error("Plotting process failed: {}", str(e))
            raise