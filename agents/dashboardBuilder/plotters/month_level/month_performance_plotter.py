import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from loguru import logger
from matplotlib.gridspec import GridSpec
from typing import Optional

from agents.decorators import validate_dataframe
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


# Default config for visualization
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
REQUIRED_UNFINISHED_COLUMNS = [
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

def month_performance_plotter(unfinished_df: pd.DataFrame,
                              all_progress_df: pd.DataFrame,
                              fig_title: str,
                              visualization_config_path: Optional[str] = None) -> plt.Figure:
        
        # Valid data frame
        validate_dataframe(unfinished_df, REQUIRED_UNFINISHED_COLUMNS)
        validate_dataframe(all_progress_df, REQUIRED_PROGRESS_COLUMNS)

        if unfinished_df.empty or all_progress_df.empty:
            logger.error("Cannot create dashboard with empty dataframes")
            raise ValueError("Input dataframes cannot be empty")

        logger.info("DataFrame status - Unfinished POs: {} records, All POs: {} records",
                         len(unfinished_df), len(all_progress_df))

        try:
              
            # Load visualization config
            visualization_config = load_visualization_config(
                DEFAULT_CONFIG,
                visualization_config_path
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
            plot_progress_bar(fig.add_subplot(gs[0, :]), 
                              all_progress_df, 
                              colors, sizes)
        
            plot_po_status_pie(
                fig.add_subplot(gs[1, 0]), 
                unfinished_df, 'in_progress',
                'In-progress PO Status Distribution', 
                colors, sizes
            )
            
            plot_po_status_pie(
                fig.add_subplot(gs[1, 1]), 
                unfinished_df, 'not_started',
                'Not-started PO Status Distribution', 
                colors, sizes
            )
            
            plot_po_status_pie(
                fig.add_subplot(gs[1, 2]), 
                all_progress_df, 'finished',
                'Finished PO Status Distribution', 
                colors, sizes
            )
            
            plot_backlog_analysis(fig.add_subplot(gs[2, 0]), 
                                  all_progress_df, colors, sizes)
            plot_overdue_analysis(fig.add_subplot(gs[2, 1]), 
                                  unfinished_df, colors, sizes)
            plot_capacity_warning_matrix(fig.add_subplot(gs[2, 2]),
                                         unfinished_df, colors, sizes)

            plot_top_items_bar(fig.add_subplot(gs[3:5, :]), 
                               unfinished_df, colors, sizes)

            plot_capacity_severity(fig.add_subplot(gs[5, 0]), 
                                   unfinished_df, colors, sizes)
            plot_progress_distribution(fig.add_subplot(gs[5, 1]), 
                                       unfinished_df, colors, sizes)
            plot_mold_nums(fig.add_subplot(gs[5, 2]), 
                           all_progress_df, colors, sizes)

            plot_late_items_bar(fig.add_subplot(gs[6, :]), 
                                unfinished_df, colors, sizes)

            plot_top_ng_items_bar(fig.add_subplot(gs[7:9, :2]), 
                                  all_progress_df, colors, sizes)
            plot_ng_rate(fig.add_subplot(gs[7:9, 2]), 
                         all_progress_df, colors, sizes)
            
            plot_kpi_cards(fig.add_subplot(gs[9, :]), 
                           all_progress_df, colors, sizes)
            
            # Add main title
            fig.suptitle(f'{fig_title}',
                        fontsize=sizes['title'], 
                        fontweight='bold', 
                        y=1.02, 
                        color=colors['title'])

            plt.tight_layout()
            return fig
        
        except Exception as e:
            logger.error("Dashboard generation failed: {}", e)
            raise