import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from agents.dashboardBuilder.visualize_data.utils import generate_color_palette
from typing import Optional, Dict, Tuple
from loguru import logger
from agents.decorators import validate_init_dataframes
import matplotlib.ticker as mticker
import json

DEFAULT_CONFIG = {
    "colors": {
        "moldCount":  "#3498DB",
        "itemCount": "#9B59B6",
        "itemComponentCount": "#2ECC71",
        "dark": "#2C3E50",
        "secondary": "#95A5A6",
    },
    "sns_style": "seaborn-v0_8",
    "palette_name": "muted",
    "figsize": None,
    "gridspec_kw": {
        'hspace': 0.4,
        'wspace': 0.3,
        'top': 0.93,
        'bottom': 0.05,
        'left': 0.08,
        'right': 0.95
    },
    "text_colors": None,
    "main_title_y": 0.96,
    "subtitle_y": 0.945,
}

def deep_update(base: dict, updates: dict) -> Dict:
    for k, v in updates.items():
        if v is None:
            continue
        if isinstance(v, dict) and isinstance(base.get(k), Dict):
            base[k] = deep_update(base.get(k, {}), v)
        else:
            base[k] = v
    return base

def load_config(visualization_config_path: Optional[str] = None) -> Dict:
    """Load visualization configuration with fallback to defaults."""
    config = DEFAULT_CONFIG.copy()
    if visualization_config_path:
        try:
            with open(visualization_config_path, "r") as f:
                user_cfg = json.load(f)
            config = deep_update(config, user_cfg)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.warning(f"Could not load config from {visualization_config_path}: {e}")
    return config

def determine_plot_settings(num_machines: int, 
                            figsize_config: Optional[dict]) -> Tuple[int, int]:
    n_cols = 3 # Layout: 3 columns per machine (mold, item, item_component), machines in rows
    n_rows = num_machines
    if figsize_config is None:
        # Calculate height if not provided
        weight = 20
        height = 4 * n_rows
        return (n_cols, n_rows, weight, height)
    else:
        return (n_cols, n_rows, figsize_config[0], figsize_config[1] )  # Use provided figsize

@validate_init_dataframes({"df": ['machineInfo', 'moldCount', 'itemCount', 'itemComponentCount', 'workingShift', 'changeType']})
def change_times_all_types_plotter(record_df: pd.DataFrame,
                                   main_title = 'Manufacturing Performance Dashboard',
                                   subtitle = 'Change Analysis: All Types by Machine and Shift',
                                   visualization_config_path: Optional[str] = None) -> plt.Figure:
        """
        Plot all change types (mold, item, item_component) with 3 subplots per machine.
        Each machine gets 3 subplots in a row: mold, item, item_component.

        Args:
            df: DataFrame with manufacturing data
            main_title: Main chart title
            subtitle: Chart subtitle
            visualization_config_path: Path to JSON config file
            
        Returns:
            matplotlib Figure object
        """

        visualization_config = load_config(visualization_config_path)

        # Get all unique machines
        machines = sorted(record_df['machineInfo'].unique())
        n_machines = len(machines)
        n_cols, n_rows, weight, height = determine_plot_settings(n_machines, visualization_config['figsize'])

        # Set style
        plt.style.use(visualization_config['sns_style'])
        logger.info('Used Seaborn style: {}.\nAvailable styles: {}', visualization_config['sns_style'], plt.style.available)

        # Generate colors for changeType if not provided
        if visualization_config['text_colors'] is None:
            all_change_types = record_df['changeType'].unique()
            colors = generate_color_palette(len(all_change_types), palette_name=visualization_config['palette_name'])
            text_colors = dict(zip(all_change_types, colors))
        else:
            text_colors = visualization_config['text_ colors']
            
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(weight, height),
                                gridspec_kw = visualization_config['gridspec_kw'],
                                sharex=True)

        # Add main title
        fig.suptitle(f'{main_title}', fontsize=18, fontweight='bold', y=visualization_config['main_title_y'], color=visualization_config["colors"]["dark"])

        # Add subtitle
        fig.text(0.5, visualization_config['subtitle_y'], f'{subtitle}', ha='center', fontsize=11, style='italic', color=visualization_config["colors"]["secondary"])

        # Handle single machine case
        if n_machines == 1:
            axes = [axes] if n_cols > 1 else [[axes]]
        elif n_machines > 1:
            if not isinstance(axes[0], np.ndarray):
                axes = axes.reshape(n_rows, n_cols)

        # Get all unique shifts
        shifts = sorted(record_df['workingShift'].unique())

        # Plot configurations
        plot_configs = [
            {
                'count_column': 'moldCount',
                'ylabel': 'Mold Changes',
                'title_suffix': 'Mold Changes',
                'color': visualization_config['colors']['moldCount']
            },
            {
                'count_column': 'itemCount',
                'ylabel': 'Item Changes',
                'title_suffix': 'Item Changes',
                'color': visualization_config['colors']['itemCount']
            },
            {
                'count_column': 'itemComponentCount',
                'ylabel': 'Item Component Changes',
                'title_suffix': 'Item Component Changes',
                'color': visualization_config['colors']['itemComponentCount']
            }
        ]

        for row, machine in enumerate(machines):
            for col, config in enumerate(plot_configs):
                # Get the appropriate axis
                ax = axes[row][col] if n_machines > 1 else axes[col]

                # Filter data for this machine
                machine_data = record_df[record_df['machineInfo'] == machine].sort_values('workingShift')

                # Plot line
                ax.plot(machine_data['workingShift'], machine_data[config['count_column']],
                      marker='o', linestyle='-', color=config['color'],
                      linewidth=1, markersize=4)

                # Add text labels for change types
                max_val = machine_data[config['count_column']].max()
                if max_val > 0:
                    for x, y, label in zip(machine_data['workingShift'],
                                        machine_data[config['count_column']],
                                        machine_data['changeType']):
                        ax.text(x, y + max_val * 0.05, label,
                              ha='center', va='bottom', fontsize=8, rotation=30,
                              color=text_colors.get(label, 'black'), fontweight='bold')

                    ax.set_ylim(0, max_val * 2)
                else:
                    ax.set_ylim(0, 1)

                # Set y-axis to show integer ticks only
                ax.yaxis.set_major_locator(mticker.MultipleLocator(1))

                # Set title - machine name for first column
                if col == 0:
                    ax.set_title(f"\n\n{machine}\n\n{config['title_suffix']}",
                               fontsize=12, fontweight='bold')
                else:
                    ax.set_title(config['title_suffix'], fontsize=12, fontweight='bold')

                ax.set_ylabel(config['ylabel'], fontsize=12)
                ax.grid(True, alpha=0.3)

                # Set x-axis
                if shifts:
                    ax.set_xticks(shifts)
                    ax.set_xticklabels([f"Shift {s}" for s in shifts])

                # Only show x-label on bottom row
                if row == n_machines - 1:
                    ax.set_xlabel("Working Shift", fontsize=12)
                    ax.tick_params(labelbottom=True)
                else:
                    ax.tick_params(labelbottom=False)

        # Add legend for changeType colors
        if text_colors:
            handles = [plt.Line2D([0], [0], marker='o', color='w', markerfacecolor=color,
                                markersize=6, label=change_type)
                      for change_type, color in text_colors.items()]
            fig.legend(handles, text_colors.keys(), loc='lower right',
                      bbox_to_anchor=(0.98, 0.02), fontsize=10)
          
        return fig