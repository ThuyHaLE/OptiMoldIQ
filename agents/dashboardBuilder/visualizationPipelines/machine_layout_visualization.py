import pandas as pd
from loguru import logger
from pathlib import Path
import shutil
from datetime import datetime
from typing import List, Dict
from agents.decorators import validate_init_dataframes

from configs.shared.config_report_format import ConfigReportMixin
from configs.shared.dict_based_report_generator import DictBasedReportGenerator
from agents.dashboardBuilder.visualizationPipelines.configs.visualization_pipeline_config import VisualizationPipelineResult

from agents.dashboardBuilder.plotters.utils import setup_parallel_config, plot_single_chart, execute_tasks, process_plot_results

from agents.dashboardBuilder.plotters.machine_level.individual_machine_layout_change_plotter import individual_machine_layout_change_plotter
from agents.dashboardBuilder.plotters.machine_level.machine_layout_change_plotter import machine_layout_change_plotter

# Decorator to validate DataFrames are initialized with the correct schema
@validate_init_dataframes({
    "machine_layout_hist_change_df": ['machineCode', 'machineName'],
    "melted_layout_change_df": ['machineCode', 'machineName', 'changedDate', 'machineNo', 'machineNo_numeric']
    })

class MachineLayoutVisualizationPipeline(ConfigReportMixin):
    """
    Pipeline for machine-level dashboard with visualization and reporting.
    """
    
    def __init__(self, 
                 machine_level_results: Dict,
                 default_dir: str = "agents/shared_db/DashboardBuilder/HardwareChangeVisualizationService/MachineLayoutVisualizationPipeline/newest/visualized_results",
                 visualization_config_path: str = None,
                 enable_parallel: bool = True,
                 max_workers: int = None):
        
        self._capture_init_args()
        self.logger = logger.bind(class_="MachineLayoutVisualizationPipeline")
        
        # Setup config path
        self.visualization_config_path = (
            visualization_config_path 
            or "agents/dashboardBuilder/plotters/machine_level/visualization_config.json"
        )
        
        # Extract features
        self.machine_level_results = machine_level_results
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
        """
        Prepare dataframes for visualization.
        """

        self.machine_layout_hist_change_df = self.machine_level_results['machine_layout_hist_change']

        # Convert into long format
        self.melted_layout_change_df = self._melt_machine_layout_change()

        self.melted_layout_change_df = self.melted_layout_change_df.dropna(subset=['machineNo'])
        self.melted_layout_change_df['changedDate'] = pd.to_datetime(self.melted_layout_change_df['changedDate'])
        self.melted_layout_change_df['machineNo_numeric'] = self.melted_layout_change_df['machineNo'].str.replace('NO.', '').astype(int)

        # Create Dict for result return
        self.visualized_data = {
            "melted_layout_change_df": self.melted_layout_change_df
            }
        
    def _melt_machine_layout_change(self) -> pd.DataFrame:
        """
        Transform machine layout history from wide → long format.
        """
        base_df = self.machine_layout_hist_change_df

        id_cols = ['machineCode', 'machineName']
        value_cols = [c for c in base_df.columns if c not in id_cols]

        return (
            base_df
            .copy()
            .melt(
                id_vars=id_cols,
                value_vars=value_cols,
                var_name='changedDate',
                value_name='machineNo'
            )
        )

    def _define_plots_args(self) -> List: 
        """Define all plotting tasks with their arguments."""

        plots_args = plots_args = [
            (
                self.melted_layout_change_df,
                self.visualization_config_path,
                'Individual_machine_layout_change_times_dashboard', 
                individual_machine_layout_change_plotter,
                {}  # No extra kwargs
            ),

            (
                self.melted_layout_change_df,
                self.visualization_config_path,
                'Machine_layout_change_dashboard',              
                machine_layout_change_plotter,
                {}  # No extra kwargs
            )
        ]

        return plots_args
    
    def _prepare_plot_tasks(self, 
                            plots_args: List, 
                            timestamp_file: str, 
                            output_dir: Path) -> list:
        
        """Prepare plotting tasks for parallel execution."""

        tasks = []
        for data, config_path, name, func, kwargs in plots_args:
            path = output_dir / f'{timestamp_file}_{name}.png'
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
               "raw_data": self.machine_level_results, 
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
                self.logger.warning(error_summary)

            return VisualizationPipelineResult(
                raw_data = self.machine_level_results,
                visualized_data = self.visualized_data,
                pipeline_name = pipeline_name,
                pipeline_summary= pipeline_summary,
                log = '\n'.join(log_entries)
                )

        except Exception as e:
            self.logger.error("Plotting process failed: {}", str(e))
            raise