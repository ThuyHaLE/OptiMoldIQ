import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Optional
from loguru import logger
from agents.decorators import validate_init_dataframes
from matplotlib.gridspec import GridSpec

from agents.dashboardBuilder.visualize_data.utils import generate_color_palette, load_visualization_config

from agents.dashboardBuilder.visualize_data.year_level.plot_monthly_eta_status import plot_monthly_eta_status
from agents.dashboardBuilder.visualize_data.year_level.plot_monthly_po_quantity import plot_monthly_po_quantity
from agents.dashboardBuilder.visualize_data.year_level.plot_ng_rate_distribution import plot_ng_rate_distribution
from agents.dashboardBuilder.visualize_data.month_level.plot_progress_bar import plot_progress_bar
from agents.dashboardBuilder.visualize_data.month_level.plot_kpi_cards import plot_kpi_cards
from agents.dashboardBuilder.visualize_data.month_level.plot_late_items_bar import plot_late_items_bar

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
        "hspace": 0.75,
        "wspace": 0.3,
        "top": 0.96,
        "bottom": 0.06,
        "left": 0.06,
        "right": 0.97
    },
    "row_nums": 9,
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
        },
    "main_title_y": 1.02,
    "subtitle_y": 0.99
    }

@validate_init_dataframes({
    "unfinished_df": ['poNo', 'poETA', 'itemQuantity', 'itemGoodQuantity', 'itemNGQuantity',
                      'is_backlog', 'itemCodeName', 'proStatus', 'poStatus', 'moldHistNum',
                      'itemRemainQuantity', 'completionProgress', 'etaStatus',
                      'overAvgCapacity', 'overTotalCapacity', 'is_overdue', 'capacityWarning',
                      'capacitySeverity', 'capacityExplanation'],
    "all_progress_df": ['poNo', 'itemCodeName', 'is_backlog', 'poStatus', 'poETA',
                        'itemNGQuantity', 'itemQuantity', 'itemGoodQuantity', 'etaStatus',
                        'proStatus', 'moldHistNum']
                        })

def monthly_performance_plotter(unfinished_df: pd.DataFrame,
                                all_progress_df: pd.DataFrame,
                                record_year: str,
                                analysis_timestamp: str,
                                main_title = 'Manufacturing Performance Dashboard',
                                subtitle = 'Monthly POs Dashboard',
                                visualization_config_path: Optional[str] = None) -> plt.Figure:

        if unfinished_df.empty or all_progress_df.empty:
            logger.error("Cannot create dashboard with empty dataframes")
            raise ValueError("Input dataframes cannot be empty")

        logger.info("Start creating POs dashboard for {} | Analysis Date: {}",
                    record_year,
                    analysis_timestamp.strftime("%Y-%m-%d"))
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
            gs = GridSpec(row_nums,
                        column_nums,
                        fig,
                        **layout_params)

            # Plot all subplots
            plot_progress_bar(
                fig.add_subplot(gs[0, :]),
                all_progress_df,
                colors, sizes
                )

            plot_monthly_po_quantity(
                fig.add_subplot(gs[1:3, :]),
                all_progress_df,
                colors, sizes,
                record_year
                )

            plot_monthly_eta_status(
                fig.add_subplot(gs[3:5, :]),
                all_progress_df,
                colors, sizes,
                record_year
                )

            plot_ng_rate_distribution(
                fig.add_subplot(gs[5:7, :]),
                all_progress_df,
                colors, sizes,
                record_year
                )

            plot_late_items_bar(fig.add_subplot(gs[7, :]), unfinished_df, colors, sizes)
            plot_kpi_cards(fig.add_subplot(gs[8, :]), all_progress_df, colors, sizes)

            # Add main title
            fig.suptitle(f'{main_title}', 
                        fontsize=sizes['suptitle'], 
                        fontweight='bold', 
                        y=visualization_config['main_title_y'], 
                        color=colors['title'])

            # Add subtitle
            fig.text(0.5, 
                    visualization_config['subtitle_y'], 
                    f'{subtitle} for {record_year} | Analysis Date: {analysis_timestamp.strftime("%Y-%m-%d")}',
                    ha='center', 
                    fontsize=sizes['title'],
                    style='italic', 
                    color=colors['subtitle'])

            plt.tight_layout()
            return fig
        
        except Exception as e:
            logger.error("Dashboard generation failed: {}", e)
            raise