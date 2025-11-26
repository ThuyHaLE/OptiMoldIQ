import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from loguru import logger
from matplotlib.gridspec import GridSpec
from typing import Optional

from agents.decorators import validate_dataframe
from agents.dashboardBuilder.visualize_data.utils import generate_color_palette, load_visualization_config

from agents.dashboardBuilder.visualize_data.hardware_change_level.mold_level.plot_bot_molds_tonnage import plot_bot_molds_tonnage
from agents.dashboardBuilder.visualize_data.hardware_change_level.mold_level.plot_mold_based_tonnage_distribution import plot_mold_based_tonnage_distribution
from agents.dashboardBuilder.visualize_data.hardware_change_level.mold_level.plot_mold_based_tonnage_proportion_pie import plot_mold_based_tonnage_proportion_pie
from agents.dashboardBuilder.visualize_data.hardware_change_level.mold_level.plot_tonnage_usage_summary import plot_tonnage_usage_summary
from agents.dashboardBuilder.visualize_data.hardware_change_level.mold_level.plot_top_molds_tonnage import plot_top_molds_tonnage

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
        "hspace": 0.5,
        "wspace": 0.3,
        "top": 0.96,
        "bottom": 0.06,
        "left": 0.06,
        "right": 0.97
    },
    "row_nums": 10,
    "column_nums": 2,
    "palette_name": "muted",
    "color_nums": 30,
    "colors": {
        "title": "#2c3e50",
        "text": "#718096",
        "subtitle": "#3c4a5b",
        "bar_default": "#3498db",
        "highlight": "#e74c3c",
        "histogram": "#5dade2",
        "pie_explode": 0.05
    },
    "sizes": {
        "suptitle": 18,
        "title": 12,
        "ylabel": 9,
        "xlabel": 9,
        "legend": 8,
        "text": 7,
        "bar_label": 8,
        "pie_label": 9,
        "pie_percent": 10
    }
}

# Required columns for dataframe
REQUIRED_MOLD_MACHINE_COLUMNS = ['moldNo', 'usedMachineTonnage', 'usedTonnageCount']

def machine_ton_based_mold_utilization_plotter(
    used_mold_machine_df: pd.DataFrame,
    fig_title: str = 'Machine-tonage based Mold Utilization Dashboard',
    top_n: int = 20,
    bot_n: int = 20,
    visualization_config_path: Optional[str] = None
) -> plt.Figure:
    """
    Create comprehensive machine-based mold utilization dashboard.
    
    Parameters:
    -----------
    used_mold_machine_df : pd.DataFrame
        DataFrame containing mold-machine utilization data with required columns
    fig_title : str
        Main title for the dashboard
    bottom_n : int, default=20
        Number of bottom molds to show in least tonnage analysis
    visualization_config_path : Optional[str]
        Path to custom visualization config file
        
    Returns:
    --------
    plt.Figure
        Matplotlib figure object containing the complete dashboard
    """
    
    # Validate dataframe
    validate_dataframe(used_mold_machine_df, REQUIRED_MOLD_MACHINE_COLUMNS)
    
    if used_mold_machine_df.empty:
        logger.error("Cannot create dashboard with empty dataframe")
        raise ValueError("Input dataframe cannot be empty")
    
    logger.info("DataFrame status - Mold-Machine records: {} records", 
                len(used_mold_machine_df))
    
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
        plot_tonnage_usage_summary(
            fig.add_subplot(gs[0:1, :]),
            used_mold_machine_df,
            colors,
            sizes
        )
        
        plot_top_molds_tonnage(
            fig.add_subplot(gs[1:3, 0]),
            used_mold_machine_df,
            colors,
            sizes,
            top_n=top_n
        )
          
        plot_bot_molds_tonnage(
            fig.add_subplot(gs[1:3, 1]),
            used_mold_machine_df,
            colors,
            sizes,
            bot_n=bot_n
        )

        plot_mold_based_tonnage_distribution(
            fig.add_subplot(gs[3:5, 0]),
            used_mold_machine_df,
            colors,
            sizes
        )
        
        plot_mold_based_tonnage_proportion_pie(
            fig.add_subplot(gs[3:5, 1]),
            used_mold_machine_df,
            colors,
            sizes
        )
        
        # Add main title
        fig.suptitle(f'{fig_title}',
                     fontsize=sizes['suptitle'],
                     fontweight='bold',
                     y=0.995,
                     color=colors['title'])
        
        plt.tight_layout()
        return fig
    
    except Exception as e:
        logger.error("Dashboard generation failed: {}", e)
        raise