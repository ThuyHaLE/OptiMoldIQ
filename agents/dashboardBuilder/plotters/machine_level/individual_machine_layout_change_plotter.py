import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from loguru import logger
from matplotlib.gridspec import GridSpec
from typing import Optional
import math

from agents.decorators import validate_dataframe
from agents.dashboardBuilder.visualize_data.utils import generate_color_palette, load_visualization_config

from agents.dashboardBuilder.visualize_data.machine_level.plot_individual_machine_change_timeline import plot_individual_machine_change_timeline

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
        "hspace": 0.4,
        "wspace": 0.3,
        "top": 0.96,
        "bottom": 0.04,
        "left": 0.04,
        "right": 0.98
    },
    "row_nums": 12,
    "column_nums": 2,
    "palette_name": "husl",
    "color_nums": 50,
    "colors": {
        "title": "#2c3e50",
        "text": "#718096",
        "subtitle": "#3c4a5b",
        "highlight": "red",
        "highlight_bg": "yellow",
        "stats_bg": "lightblue",
        "border_normal": "#dee2e6"
    },
    "sizes": {
        "suptitle": 18,
        "title": 14,
        "ylabel": 12,
        "xlabel": 12,
        "legend": 10,
        "text": 11,
        "tick": 11
    },
    "max_change_threshold": 5,
    "ncols": 2
}

# Required columns for dataframe
REQUIRED_MACHINE_COLUMNS = ['machineCode', 'machineName', 'changedDate', 'machineNo', 'machineNo_numeric']

def individual_machine_layout_change_plotter(machine_layout_df: pd.DataFrame,
                                             fig_title: str = 'Individual machine layout change times dashboard',
                                             visualization_config_path: Optional[str] = None) -> plt.Figure:
    """
    Create comprehensive machine layout change dashboard.
    
    Parameters:
    -----------
    machine_layout_df : pd.DataFrame
        DataFrame containing machine layout change information
    fig_title : str
        Main title for the dashboard
    visualization_config_path : Optional[str]
        Path to custom visualization config file
        
    Returns:
    --------
    plt.Figure
        Matplotlib figure object containing the complete dashboard
    """
    
    # Validate dataframe
    validate_dataframe(machine_layout_df, REQUIRED_MACHINE_COLUMNS)
    
    if machine_layout_df.empty:
        logger.error("Cannot create dashboard with empty dataframe")
        raise ValueError("Input dataframe cannot be empty")
    
    # Get unique machines
    unique_machines = sorted(machine_layout_df['machineCode'].unique())
    n_unique = len(unique_machines)
    
    logger.info("DataFrame status - Machine layout records: {} records, {} unique machines",
                len(machine_layout_df), n_unique)
    
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
        
        # Generate colors for machines
        color_palette = generate_color_palette(
            max(visualization_config["color_nums"], n_unique),
            palette_name=visualization_config['palette_name']
        )
        
        # Load colors and sizes
        colors = visualization_config['colors']
        colors['general'] = color_palette
        sizes = visualization_config['sizes']
        
        # Calculate figure size based on number of machines
        n_cols = min(2, n_unique) if n_unique > 4 else min(1, n_unique)
        n_rows_individual = math.ceil(n_unique / n_cols)
        
        # Dynamic figure height
        base_height = 28
        individual_section_height = n_rows_individual * 4
        total_height = max(base_height, individual_section_height + 16)
        
        plt.rcParams['figure.figsize'] = (18, total_height)
        
        # Load fig params
        layout_params = visualization_config['layout_params']
        row_nums = max(12, n_rows_individual * 2 + 6)
        column_nums = visualization_config['column_nums']
        
        # Create figure with GridSpec
        fig = plt.figure()
        gs = GridSpec(row_nums, column_nums, fig, **layout_params)
        
        # Individual machine plots
        subfig = fig.add_subfigure(gs[1:, :])
        plot_individual_machine_change_timeline(
            subfig,
            machine_layout_df,
            unique_machines,
            colors,
            sizes,
            max_change_threshold=visualization_config['max_change_threshold'],
            ncols=visualization_config['ncols']
        )
        
        # Add main title
        fig.suptitle(f'{fig_title}',
                     fontsize=sizes['suptitle'],
                     fontweight='bold',
                     y=0.96,
                     color=colors['title'])
        
        plt.tight_layout()

        return fig
    
    except Exception as e:
        logger.error("Dashboard generation failed: {}", e)
        raise