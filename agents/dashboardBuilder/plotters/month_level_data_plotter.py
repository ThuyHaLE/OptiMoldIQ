import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from loguru import logger
from pathlib import Path
import shutil
import re
from datetime import datetime
from matplotlib.gridspec import GridSpec
from typing import Tuple

from agents.decorators import validate_init_dataframes
from agents.dashboardBuilder.visualize_data.utils import generate_color_palette, load_visualization_config
from agents.dashboardBuilder.visualize_data.month_level.plot_backlog_analysis import plot_backlog_analysis
from agents.dashboardBuilder.visualize_data.month_level.plot_capacity_severity import plot_capacity_severity
from agents.dashboardBuilder.visualize_data.month_level.plot_capacity_warning_matrix import plot_capacity_warning_matrix
from agents.dashboardBuilder.visualize_data.month_level.plot_kpi_cards import plot_kpi_cards
from agents.dashboardBuilder.visualize_data.month_level.plot_late_items_bar import plot_late_items_bar
from agents.dashboardBuilder.visualize_data.month_level.plot_mold_nums import plot_mold_nums
from agents.dashboardBuilder.visualize_data.month_level.plot_overdue_analysis import plot_overdue_analysis
from agents.dashboardBuilder.visualize_data.month_level.plot_po_status_pie import plot_po_status_pie
from agents.dashboardBuilder.visualize_data.month_level.plot_progress_bar import plot_progress_bar
from agents.dashboardBuilder.visualize_data.month_level.plot_progress_distribution import plot_progress_distribution
from agents.dashboardBuilder.visualize_data.month_level.plot_top_items_bar import plot_top_items_bar
from agents.dashboardBuilder.visualize_data.month_level.plot_top_ng_items_bar import plot_top_ng_items_bar
from agents.dashboardBuilder.visualize_data.month_level.plot_ng_rate import plot_ng_rate
from agents.analyticsOrchestrator.multiLevelDataAnalytics.month_level_data_processor import MonthLevelDataProcessor
from agents.dashboardBuilder.reportFormatters.generate_early_warning_report import generate_early_warning_report

DEFAULT_CONFIG = {
    "sns_style": "seaborn-v0_8-darkgrid",
    "sns_palette": "husl",
    "sns_set_style": "whitegrid",
    "plt_rcParams_update": {
        "figure.facecolor": "#f8f9fa",
        "axes.facecolor": "white",
        "axes.edgecolor": "#dee2e6",
        "axes.labelcolor": "#495057",
        "text.color": "#495057",
        "xtick.color": "#495057",
        "ytick.color": "#495057",
        "grid.color": "#e9ecef",
        "grid.linewidth": 0.8,
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "DejaVu Sans"],
        "font.size": 10
    },
    "layout_params": {
        "hspace": 0.95,
        "wspace": 0.3,
        "top": 0.96,
        "bottom": 0.06,
        "left": 0.06,
        "right": 0.97
    },
    "row_nums": 10,
    "column_nums": 3,
    "palette_name": "muted",
    "color_nums": 30,
    "colors": {
        "title": "#2c3e50",
        "text": "#718096",
        "subtitle": "#3c4a5b",
        "colors_severity": {
            "normal": "#95E1D3", 
            "critical": "#F38181"
        },
        "backlog": {
            "Active": "#95E1D3", 
            "Backlog": "#F38181"
        },
        "kpi": {
            "Total POs": "#667eea",
            "Backlog": "#feca57",
            "In-progress POs": "#fc5c65",
            "Not-started POs": "#fd79a8",
            "Finished POs": "#4caf50",
            "Late POs": "#e17055",
            "Avg progress": "#00b894",
            "Total progress": "#ffc107"
        }
    },
    "sizes": {
        "suptitle": 18,
        "progress_text": 30,
        "title": 12,
        "ylabel": 9,
        "xlabel": 9,
        "legend": 8,
        "text": 7
    }
}

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

@validate_init_dataframes({
    "finished_df": REQUIRED_FINISHED_COLUMNS, 
    "unfinished_df": REQUIRED_UNFINISHED_COLUMNS,
    "df": REQUIRED_UNFINISHED_SHORT_COLUMNS,
    "all_progress_df": REQUIRED_PROGRESS_COLUMNS})

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
                 visualization_config_path: str = None):
        
        self.logger = logger.bind(class_="MonthLevelDataPlotter")
        
        # Validate record_month format
        self._validate_record_month(record_month)
        analysis_date = analysis_date or datetime.now().strftime("%Y-%m-%d")
        
        # Setup config path
        self.visualization_config_path = (
            visualization_config_path 
            or "agents/dashboardBuilder/visualize_data/month_level/visualization_config.json"
        )
        
        # Initialize data processor
        self.month_level_data_processor = MonthLevelDataProcessor(
            record_month,
            analysis_date, 
            source_path,
            annotation_name,
            databaseSchemas_path,
            default_dir
        )
        
        # Process data
        try:
            (self.analysis_timestamp, self.adjusted_record_month, 
             self.finished_df, self.unfinished_df) = self.month_level_data_processor.product_record_processing()
            
            # Unfinished POs and Total POs
            self.df, self.all_progress_df = self.prepare_data()

            self.logger.info(
                "Data prepared: {} unfinished records, {} total records",
                len(self.df), len(self.all_progress_df)
                )
            
        except Exception as e:
            self.logger.error("Failed to process data: {}", e)
            raise
        
        # Setup directories
        self.default_dir = Path(default_dir)
        self.output_dir = self.default_dir / "MonthLevelDataPlotter"
    
    def _validate_record_month(self, record_month: str) -> None:
        """Validate record_month format (YYYY-MM)."""
        if not re.match(r'^\d{4}-\d{2}$', record_month):
            raise ValueError(
                f"Invalid record_month format: '{record_month}'. Expected format: YYYY-MM"
            )
    
    def prepare_data(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Prepare dataframes for visualization.
        
        Returns:
            Tuple of (df, progress_df) containing processed data
        """
        # Prepare main dataframe
        df = self.unfinished_df[REQUIRED_UNFINISHED_COLUMNS].copy()
        
        # Prepare progress dataframe
        progress_df = pd.concat(
            [
                self.finished_df[REQUIRED_PROGRESS_COLUMNS], 
                self.unfinished_df[REQUIRED_PROGRESS_COLUMNS]
            ], 
            ignore_index=True
        )
        
        return df, progress_df
    
    def plot_and_save_results(self) -> None:
        """
        Generate dashboard, save results and update change log.
        
        Raises:
            OSError: If file operations fail
            ValueError: If data is empty or invalid
        """
        # Check for empty data
        if self.df.empty or self.all_progress_df.empty:
            self.logger.warning("No data to plot for month: {}", self.adjusted_record_month)
            return
        
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
        self._archive_old_files(newest_dir, historical_dir, timestamp_file, log_entries)
        
        # Save extracted records
        self._save_excel_data(newest_dir, timestamp_file, log_entries)
        
        # Plot and save dashboard
        self._save_dashboard(newest_dir, timestamp_file, log_entries)
        
        # Save early warning report
        self._save_early_warning_report(newest_dir, timestamp_file, log_entries)
        
        # Update change log
        self._update_change_log(log_path, log_entries)
    
    def _archive_old_files(self, 
                          newest_dir: Path, 
                          historical_dir: Path, 
                          timestamp_file: str,
                          log_entries: list) -> None:
        """Move old files from newest to historical_db."""
        for f in newest_dir.iterdir():
            if f.is_file():
                try:
                    # Add timestamp to avoid overwriting
                    dest = historical_dir / f"{timestamp_file}_{f.name}"
                    shutil.move(str(f), dest)
                    log_entries.append(f"  ⤷ Moved old file: {f.name} → {dest.name}\n")
                    self.logger.info("Archived old file {} as {}", f.name, dest.name)
                except Exception as e:
                    self.logger.error("Failed to archive file {}: {}", f.name, e)
                    raise OSError(f"Failed to archive file {f.name}: {e}")
    
    def _save_excel_data(self, 
                        newest_dir: Path, 
                        timestamp_file: str, 
                        log_entries: list) -> None:
        """Save extracted records to Excel file."""
        excel_file_name = f"{timestamp_file}_extracted_records_{self.adjusted_record_month}.xlsx"
        excel_file_path = newest_dir / excel_file_name
        
        excel_data = {
            "finishedRecords": self.finished_df,
            "unfinishedRecords": self.unfinished_df,
            "allRecords": self.all_progress_df,
        }
        
        try:
            with pd.ExcelWriter(excel_file_path, engine="openpyxl") as writer:
                for sheet_name, df in excel_data.items():
                    if not isinstance(df, pd.DataFrame):
                        df = pd.DataFrame([df])
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            log_entries.append(f"  ⤷ Saved Excel: {excel_file_name}\n")
            self.logger.info("✅ Saved Excel file: {}", excel_file_name)
        except Exception as e:
            self.logger.error("❌ Failed to save Excel file {}: {}", excel_file_name, e)
            raise OSError(f"Failed to save Excel file {excel_file_name}: {e}")
    
    def _save_dashboard(self, 
                        newest_dir: Path, 
                        timestamp_file: str, 
                        log_entries: list) -> None:
        """Generate and save dashboard figure."""
        self.logger.info("Generating dashboard...")
        fig = None
        
        try:
            fig = self.create_po_dashboard()
            fig_name = f"{timestamp_file}_pos_dashboard_{self.adjusted_record_month}.png"
            fig_path = newest_dir / fig_name
            plt.savefig(fig_path, dpi=300, bbox_inches='tight')
            
            log_entries.append(f"  ⤷ Saved dashboard: {fig_name}\n")
            self.logger.info("✅ Saved dashboard: {}", fig_name)
        except Exception as e:
            self.logger.error("❌ Failed to generate dashboard: {}", e)
            raise
        finally:
            if fig is not None:
                plt.close(fig)
    
    def _save_early_warning_report(self, 
                                   newest_dir: Path, 
                                   timestamp_file: str, 
                                   log_entries: list) -> None:
        """Generate and save early warning report if applicable."""
        try:
            early_warning_report = generate_early_warning_report(
                self.unfinished_df, 
                self.adjusted_record_month,
                self.analysis_timestamp,
                colored=False
            )
            
            if early_warning_report and early_warning_report.strip():
                report_name = f"{timestamp_file}_early_warning_report_{self.adjusted_record_month}.txt"
                report_path = newest_dir / report_name
                
                with open(report_path, "w", encoding="utf-8") as f:
                    f.write(early_warning_report)
                
                log_entries.append(f"  ⤷ Saved warning report: {report_name}\n")
                self.logger.info("✅ Saved early warning report: {}", report_name)
            else:
                self.logger.info("No early warnings to report")
        except Exception as e:
            self.logger.warning("Failed to generate early warning report: {}", e)
    
    def _update_change_log(self, 
                           log_path: Path, 
                           log_entries: list) -> None:
        """Append entries to change log."""
        try:
            with open(log_path, "a", encoding="utf-8") as log_file:
                log_file.writelines(log_entries)
            self.logger.info("Updated change log: {}", log_path)
        except Exception as e:
            self.logger.error("Failed to update change log {}: {}", log_path, e)
            raise OSError(f"Failed to update change log {log_path}: {e}")
    
    def create_po_dashboard(self) -> plt.Figure:
        """
        Create comprehensive PO dashboard with all visualizations.
        
        Returns:
            Matplotlib figure object
        """
        
        if self.df.empty:
            self.logger.warning("⚠️ Warning: Main DataFrame is empty")
        if self.all_progress_df.empty:
            self.logger.warning("⚠️ Warning: Progress DataFrame is empty")

        self.logger.info("Start creating POs dashboard for {} | Analysis Date: {}",
                         self.adjusted_record_month,
                         self.analysis_timestamp.strftime("%Y-%m-%d"))
        self.logger.info("DataFrame status - Unfinished POs: {} records, All POs: {} records",
                         len(self.df), len(self.all_progress_df))

        # Load visualization config
        visualization_config = load_visualization_config(
            DEFAULT_CONFIG, 
            self.visualization_config_path
        )
        
        # Set style
        plt.style.use(visualization_config['sns_style']) 
        sns.set_palette(visualization_config['sns_palette']) 
        plt.rcParams.update(visualization_config['plt_rcParams_update']) 
        sns.set_style(visualization_config['sns_set_style']) 
        plt.rcParams['figure.figsize'] = (16, 28)
        
        # Load colors and sizes
        colors = visualization_config['colors']
        colors['general'] = generate_color_palette(
            visualization_config["color_nums"], 
            palette_name=visualization_config['palette_name']
        )
        sizes = visualization_config['sizes']
        
        # Load fig params
        layout_params = visualization_config['layout_params']
        row_nums = visualization_config['row_nums']
        column_nums = visualization_config['column_nums']
        
        # Create figure with GridSpec
        fig = plt.figure()
        gs = GridSpec(row_nums, column_nums, fig, **layout_params)
        
        # Plot all subplots
        plot_progress_bar(fig.add_subplot(gs[0, :]), self.all_progress_df, colors, sizes)
        
        plot_po_status_pie(
            fig.add_subplot(gs[1, 0]), self.df, 'in_progress',
            'In-progress PO Status Distribution', colors, sizes
        )
        
        plot_po_status_pie(
            fig.add_subplot(gs[1, 1]), self.df, 'not_started',
            'Not-started PO Status Distribution', colors, sizes
        )
        
        plot_po_status_pie(
            fig.add_subplot(gs[1, 2]), self.all_progress_df, 'finished',
            'Finished PO Status Distribution', colors, sizes
        )
        
        plot_backlog_analysis(fig.add_subplot(gs[2, 0]), self.all_progress_df, colors, sizes)

        plot_overdue_analysis(fig.add_subplot(gs[2, 1]), self.df, colors, sizes)
        plot_capacity_warning_matrix(fig.add_subplot(gs[2, 2]), self.df, colors, sizes)

        plot_top_items_bar(fig.add_subplot(gs[3:5, :]), self.df, colors, sizes)

        plot_capacity_severity(fig.add_subplot(gs[5, 0]), self.df, colors, sizes)
        plot_progress_distribution(fig.add_subplot(gs[5, 1]), self.df, colors, sizes)
        plot_mold_nums(fig.add_subplot(gs[5, 2]), self.all_progress_df, colors, sizes)

        plot_late_items_bar(fig.add_subplot(gs[6, :]), self.df, colors, sizes)

        plot_ng_rate(fig.add_subplot(gs[7:9, 2]), self.all_progress_df, colors, sizes)
        plot_top_ng_items_bar(fig.add_subplot(gs[7:9, :2]), self.all_progress_df, colors, sizes)

        plot_kpi_cards(fig.add_subplot(gs[9, :]), self.all_progress_df, colors, sizes)
        
        # Add main title
        fig.suptitle(
            f'Purchase Orders (POs) Dashboard for {self.adjusted_record_month} | Analysis Date: {self.analysis_timestamp.strftime("%Y-%m-%d")}',
            fontsize=sizes['suptitle'],
            fontweight='bold',
            color=colors['subtitle'],
            y=1.02
        )
        
        plt.tight_layout()
        return fig