from loguru import logger
from pathlib import Path
from datetime import datetime
import pandas as pd
import shutil
from typing import Dict, List

from agents.decorators import validate_init_dataframes
from agents.utils import validate_multi_level_analyzer_result

from configs.shared.config_report_format import ConfigReportMixin
from configs.shared.dict_based_report_generator import DictBasedReportGenerator
from agents.dashboardBuilder.visualizationPipelines.configs.visualization_pipeline_config import VisualizationPipelineResult

from agents.dashboardBuilder.plotters.utils import setup_parallel_config, plot_single_chart, execute_tasks, process_plot_results

from agents.dashboardBuilder.plotters.day_level.change_times_all_types_plotter import change_times_all_types_plotter
from agents.dashboardBuilder.plotters.day_level.item_based_overview_plotter import item_based_overview_plotter 
from agents.dashboardBuilder.plotters.day_level.machine_level_yield_efficiency_plotter import machine_level_yield_efficiency_plotter
from agents.dashboardBuilder.plotters.day_level.machine_level_mold_analysis_plotter import machine_level_mold_analysis_plotter
from agents.dashboardBuilder.plotters.day_level.shift_level_yield_efficiency_plotter import shift_level_yield_efficiency_plotter
from agents.dashboardBuilder.plotters.day_level.shift_level_detailed_yield_efficiency_plotter import shift_level_detailed_yield_efficiency_plotter
from agents.dashboardBuilder.plotters.day_level.mold_based_overview_plotter import mold_based_overview_plotter
from agents.dashboardBuilder.plotters.day_level.shift_level_mold_efficiency_plotter import shift_level_mold_efficiency_plotter

# Required columns for dataframes
REQUIRED_FILTER_COLUMNS = [
    'recordDate', 'workingShift', 'machineNo', 'machineCode', 'itemCode','itemName', 'colorChanged', 
    'moldChanged', 'machineChanged', 'poNo', 'moldNo', 'moldShot', 'moldCavity', 'itemTotalQuantity',
    'itemGoodQuantity', 'itemBlackSpot', 'itemOilDeposit', 'itemScratch', 'itemCrack', 'itemSinkMark', 
    'itemShort', 'itemBurst', 'itemBend', 'itemStain', 'otherNG', 'plasticResin', 'plasticResinCode',
    'plasticResinLot', 'colorMasterbatch', 'colorMasterbatchCode', 'additiveMasterbatch', 'additiveMasterbatchCode', 
    'itemQuantity', 'poETA', 'machineInfo', 'itemInfo', 'itemComponent', 'itemCount', 'moldCount', 
    'itemComponentCount', 'jobCount', 'lateStatus', 'changeType']

REQUIRED_MOLD_BASED_COLUMNS = [
    'machineInfo', 'workingShift', 'moldNo', 'moldShot', 'moldCavity', 'itemTotalQuantity', 
    'itemGoodQuantity', 'changeType', 'defectQuantity', 'defectRate']

REQUIRED_ITEM_BASED_COLUMNS = [
    'itemInfo', 'itemTotalQuantity', 'itemGoodQuantity', 'usedMachineNums', 'totalShifts', 
    'usedMoldNums', 'moldTotalShots', 'avgCavity', 'usedComponentNums', 'defectQuantity', 'defectRate']

# Decorator to validate DataFrames are initialized with the correct schema
@validate_init_dataframes({
    "moldInfo_df": ['moldNo', 'moldName', 'moldCavityStandard', 'moldSettingCycle',
                    'machineTonnage', 'acquisitionDate', 'itemsWeight', 'runnerWeight'],
    "filtered_df": REQUIRED_FILTER_COLUMNS,
    "mold_based_record_df": REQUIRED_MOLD_BASED_COLUMNS,
    "item_based_record_df": REQUIRED_ITEM_BASED_COLUMNS
    })

class DayLevelVisualizationPipeline(ConfigReportMixin):

    """
    Pipeline for day-level PO dashboard with visualization and reporting.
    
    Attributes:
        day_level_results: Results from day level analyzer
        default_dir: Directory for saving outputs
    """
    
    DAY_LEVEL_KEYS = ['selectedDateFilter', 'moldBasedRecords', 'itemBasedRecords']
    
    def __init__(self, 
                 day_level_results: Dict,
                 requested_timestamp: str,
                 moldInfo_df: pd.DataFrame,
                 default_dir: str = "agents/shared_db/DashboardBuilder/MultiLevelPerformanceVisualizationService/DayLevelVisualizationPipeline/newest/visualized_results",
                 visualization_config_path: str = None,
                 enable_parallel: bool = True,
                 max_workers: int = None):

        self._capture_init_args()
        self.logger = logger.bind(class_="DayLevelVisualizationPipeline")
        
        # Load visualization config
        self.visualization_config_path = (
            visualization_config_path 
            or "agents/dashboardBuilder/plotters/day_level/visualization_config.json"
        )

        self.requested_timestamp = pd.to_datetime(requested_timestamp).date().isoformat()

        # Load base dataframes
        self.moldInfo_df = moldInfo_df

        # Validate data
        self.day_level_results = day_level_results
        validate_multi_level_analyzer_result(self.day_level_results, self.DAY_LEVEL_KEYS)

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

        # Setup output directory
        self.output_dir = Path(default_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _prepare_data(self) -> None:
        "Extract and prepare data for visualizing"

        # Extract features
        self.filtered_df = self.day_level_results['selectedDateFilter']
        self.mold_based_record_df = self.day_level_results['moldBasedRecords']
        self.item_based_record_df = self.day_level_results['itemBasedRecords']
        
        # Create Dict for result return
        self.raw_data = {
            "base_df": self.moldInfo_df,
            "day_level_results": self.day_level_results
        }

        self.visualized_data = {
                "filtered_df": self.filtered_df,
                "mold_based_record_df": self.mold_based_record_df,
                "item_based_record_df": self.item_based_record_df
            }
        
    def _define_plots_args(self) -> List: 
        """Define all plotting tasks with their arguments."""

        plots_args = [
            (
                self.filtered_df, 
                self.visualization_config_path, 
                f"change_times_all_types_fig",
                change_times_all_types_plotter,
                {}  # No extra kwargs
            ),

            (
                self.item_based_record_df, 
                self.visualization_config_path, 
                f"item_based_overview_dashboard", 
                item_based_overview_plotter,
                {}  # No extra kwargs
            ),

            (
                self.filtered_df, 
                self.visualization_config_path, 
                f"machine_level_yield_efficiency_chart", 
                machine_level_yield_efficiency_plotter,
                {}  # No extra kwargs
            ),

            (
                self.filtered_df, 
                self.visualization_config_path, 
                f"machine_level_mold_analysis_chart", 
                machine_level_mold_analysis_plotter,
                {}  # No extra kwargs
            ),

            (
                self.filtered_df, 
                self.visualization_config_path, 
                f"shift_level_yield_efficiency_chart", 
                shift_level_yield_efficiency_plotter,
                {}  # No extra kwargs
            ),

            (
                self.filtered_df, 
                self.visualization_config_path, 
                f"shift_level_detailed_yield_efficiency_chart", 
                shift_level_detailed_yield_efficiency_plotter,
                {}  # No extra kwargs
            ),
            
            (
                self.mold_based_record_df, 
                self.visualization_config_path, 
                f"mold_based_overview_dashboard", 
                mold_based_overview_plotter,
                {}  # No extra kwargs
            ),

            (
                (self.filtered_df, self.moldInfo_df), 
                self.visualization_config_path, 
                f"shift_level_mold_efficiency_chart", 
                shift_level_mold_efficiency_plotter,
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

        # Execute plotting (parallel or sequential)
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