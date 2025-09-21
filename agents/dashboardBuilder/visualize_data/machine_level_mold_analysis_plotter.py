from agents.decorators import validate_init_dataframes
from agents.dashboardBuilder.visualize_data.utils import generate_color_palette
import pandas as pd
import numpy as np
from loguru import logger
import seaborn as sns
import matplotlib.pyplot as plt
from collections import defaultdict
from typing import Dict, Tuple, List, Optional
import json
import warnings
warnings.filterwarnings('ignore', category=FutureWarning)

DEFAULT_CONFIG = {
    "colors": {
        'secondary': '#95A5A6',    # Gray
        'dark': '#2C3E50'          # Dark blue
    },
    "sns_style": "seaborn-v0_8",
    "palette_name": "muted",
    "figsize": None,
    "gridspec_kw": {
        'hspace': 0.4,
        'wspace': 0.3,
        'top': 0.85,
        'bottom': 0.05,
        'left': 0.08,
        'right': 0.95
    },
    "main_title_y": 0.96,
    "subtitle_y": 0.90,
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

@validate_init_dataframes({"df": ['workingShift', 'machineNo', 'moldNo', 'moldShot', 'moldCount']})
def machine_level_mold_analysis_plotter(df: pd.DataFrame,
                                        main_title: str = 'Manufacturing Performance Dashboard',
                                        subtitle: str = 'Mold Analysis by Machine & Shift',
                                        visualization_config_path: Optional[str] = None,
                                        max_machines_display: int = 50,
                                        enable_scatter: bool = True,
                                        enable_trends: bool = True) -> Tuple:
    """
    Generate optimized mold analysis charts by machine with enhanced performance

    Parameters:
        df (pd.DataFrame): Input data with required columns
        main_title: Main chart title
        subtitle: Chart subtitle
        visualization_config_path: Path to JSON config file
        max_machines_display (int): Maximum number of machines to display
        enable_scatter (bool): Whether to show scatter points
        enable_trends (bool): Whether to show trend lines
    """

    visualization_config = load_config(visualization_config_path)

    logger.info("Creating machine level mold analysis chart with {} rows", len(df))

    # Early data validation and preprocessing
    if df.empty:
        raise ValueError("Input DataFrame is empty")

    # Remove any null values that might cause issues
    df_clean = df.dropna(subset=['workingShift', 'machineNo', 'moldShot', 'moldCount'])

    if df_clean.empty:
        raise ValueError("No valid data after removing nulls")

    # Pre-compute sorted unique values once
    machines = sorted(df_clean['machineNo'].unique())[:max_machines_display]
    shifts = sorted(df_clean['workingShift'].unique(),
                    key=lambda x: x if isinstance(x, (int, float)) else 99)

    n_machines = len(machines)
    n_shifts = len(shifts)

    # Validate data
    if n_machines == 0 or n_shifts == 0:
        raise ValueError(f"No valid machines ({n_machines}) or shifts ({n_shifts})")
    
    # Performance optimization for large datasets
    if n_machines > 40:
        max_machines_display = 30
        enable_scatter = False  # Disable scatter for performance

    # Filter dataframe to only include selected machines for performance
    df_filtered = df_clean[df_clean['machineNo'].isin(machines)].copy()

    # Get layout configuration
    config = get_layout_config(n_machines, n_shifts)

    # Setup colors
    colors = generate_color_palette(n_shifts, palette_name=visualization_config['palette_name'])

    # Set style
    plt.style.use(visualization_config['sns_style'])
    logger.info('Used Seaborn style: {}.\nAvailable styles: {}', visualization_config['sns_style'], plt.style.available)
    fig, ax = plt.subplots(figsize=config['figsize'], gridspec_kw=visualization_config['gridspec_kw'])
    ax2 = ax.twinx()

    # Add main title with all information
    fig.suptitle(f'{main_title}',
                fontsize=18, fontweight='bold', y=visualization_config['main_title_y'], 
                color=visualization_config['colors']['dark'])

    # Add subtitle
    fig.text(0.5, visualization_config['subtitle_y'], f'{subtitle}',
            ha='center', fontsize=11, style='italic', color=visualization_config['colors']['secondary'])

    
    logger.debug('Plotting...')
    # 1. Bar plot (most efficient with seaborn)
    sns.barplot(
        data=df_filtered,
        x='machineNo',
        y='moldCount',
        hue='workingShift',
        palette=visualization_config['palette_name'],
        ax=ax,
        edgecolor=visualization_config['colors']['dark'],
        linewidth=0.3 if n_machines > 25 else 0.5,
        order=machines,
        hue_order=shifts
    )

    # 2. Scatter and trends (only if enabled and reasonable number of machines)
    if (enable_scatter or enable_trends) and n_machines <= 40:
        _, shot_agg_df = precompute_aggregated_data(df_filtered)
        scatter_data = create_optimized_scatter_data(shot_agg_df, machines, shifts, config['bar_width'])

        # Plot scatter points
        if enable_scatter and n_machines <= 30:
            plot_scatter_points(ax2, scatter_data, shifts, colors, config['scatter_size'])

        # Plot trend lines
        if enable_trends:
            plot_trend_lines(ax2, scatter_data, machines, shifts)

    # Configure axes and styling
    configure_axes(ax, ax2, machines, config['fontsize'], config['rotation'], config['grid_alpha'])

    # Create legends
    create_legends(ax, ax2, n_machines)

    # Final layout optimization
    plt.tight_layout()

    logger.info("Successfully created optimized chart for {} machines and {} shifts",
                n_machines, n_shifts)

    return fig

def get_layout_config(n_machines: int, 
                      n_shifts) -> Dict:
    """Get optimized layout configuration based on machine count"""
    configs = [
        (15, (14, 8), 45, 12, 0.8, 30, 0.6),
        (25, (18, 8), 60, 10, 0.6, 20, 0.5),
        (35, (22, 9), 75, 9, 0.5, 15, 0.4),
        (float('inf'), (28, 10), 90, 8, 0.4, 10, 0.3)
    ]

    for max_machines, figsize, rotation, fontsize, bar_width, scatter_size, grid_alpha in configs:
        if n_machines <= max_machines:
            return {
                'figsize': figsize,
                'rotation': rotation,
                'fontsize': fontsize,
                'bar_width': bar_width / n_shifts if n_shifts > 1 else bar_width,
                'scatter_size': scatter_size,
                'grid_alpha': grid_alpha
            }

def precompute_aggregated_data(df_filtered: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Pre-compute aggregated data for better performance"""
    # Group by relevant columns once
    mold_count_agg = (df_filtered
                    .groupby(['workingShift', 'machineNo'])['moldCount']
                    .sum()
                    .reset_index())

    mold_shot_agg = (df_filtered
                    .groupby(['workingShift', 'machineNo'])['moldShot']
                    .agg(['sum', 'mean', 'count'])
                    .reset_index())
    mold_shot_agg.columns = ['workingShift', 'machineNo', 'moldShot_sum', 'moldShot_mean', 'moldShot_count']

    return mold_count_agg, mold_shot_agg

def create_optimized_scatter_data(shot_agg_df: pd.DataFrame, 
                                  machines: List, 
                                  shifts: List, 
                                  bar_width: float) -> Dict:
    """Create optimized scatter plot data structure"""
    scatter_data = defaultdict(lambda: {'x': [], 'y': [], 'machine': []})

    # Use vectorized operations where possible
    machine_positions = {machine: idx for idx, machine in enumerate(machines)}
    n_shifts = len(shifts)

    for _, row in shot_agg_df.iterrows():
        shift = row['workingShift']
        machine = row['machineNo']

        if machine in machine_positions and shift in shifts:
            shift_idx = shifts.index(shift)
            machine_idx = machine_positions[machine]

            # Calculate position with offset
            offset = (shift_idx - (n_shifts - 1) / 2) * bar_width
            x_pos = machine_idx + offset

            scatter_data[shift]['x'].append(x_pos)
            scatter_data[shift]['y'].append(row['moldShot_mean'])
            scatter_data[shift]['machine'].append(machine)

    return scatter_data

def plot_scatter_points(ax2, 
                        scatter_data: Dict, 
                        shifts: List, 
                        colors: List, 
                        scatter_size: int):
    """Plot optimized scatter points"""
    reversed_colors = colors[::-1]
    for shift_idx, shift in enumerate(shifts):
        if shift in scatter_data and scatter_data[shift]['x']:
            ax2.scatter(
                scatter_data[shift]['x'],
                scatter_data[shift]['y'],
                color=reversed_colors[shift_idx % len(reversed_colors)],
                s=scatter_size,
                alpha=0.6,
                edgecolor='white',
                linewidth=0.1,
                label=f'Shot S{shift}',
                zorder=5
            )

def plot_trend_lines(ax2, 
                     scatter_data: Dict, 
                     machines: List, 
                     shifts: List):
    """Plot optimized trend lines by machine"""
    # Group data by machine for trend lines
    machine_trends = defaultdict(lambda: {'x': [], 'y': []})

    for shift in shifts:
        if shift in scatter_data:
            for i, machine in enumerate(scatter_data[shift]['machine']):
                machine_trends[machine]['x'].append(scatter_data[shift]['x'][i])
                machine_trends[machine]['y'].append(scatter_data[shift]['y'][i])

    # Plot trend lines
    legend_shown = False
    line_alpha = 0.6 if len(machines) > 20 else 0.8
    line_width = 0.6 if len(machines) > 20 else 0.8

    for machine in machines:
        if machine in machine_trends and len(machine_trends[machine]['x']) >= 2:
            label = 'Machine Trends' if not legend_shown else ""
            legend_shown = True

            ax2.plot(
                machine_trends[machine]['x'],
                machine_trends[machine]['y'],
                color='Black',
                linewidth=line_width,
                alpha=line_alpha,
                linestyle='-',
                label=label,
                zorder=3
            )

def optimize_x_axis(ax, machines: List, fontsize: int, rotation: int):
    """Optimize x-axis labels for readability"""
    n_machines = len(machines)
    
    if n_machines > 30:
        # Show every nth label to avoid overlap
        step = max(2, n_machines // 20)
        labels = [machines[i] if i % step == 0 else ''
                    for i in range(len(machines))]
        ax.set_xticklabels(labels, rotation=rotation,
                            ha='right', fontsize=fontsize - 2)
    else:
        ax.tick_params(axis='x', rotation=rotation)

def sync_y_axes(ax, ax2):
    """Efficiently sync Y axes"""
    y1_min, y1_max = ax.get_ylim()
    y2_min, y2_max = ax2.get_ylim()

    # Simple case: all positive values
    if y1_min >= 0 and y2_min >= 0:
        ax.set_ylim(0, y1_max * 1.2)
        ax2.set_ylim(0, y2_max * 1.2)
        return

    # Handle mixed positive/negative values
    if y1_min < 0 or y2_min < 0:
        # Compute zero ratios
        zero_ratio_1 = abs(y1_min) / (y1_max - y1_min) if y1_max != y1_min else 0
        zero_ratio_2 = abs(y2_min) / (y2_max - y2_min) if y2_max != y2_min else 0
        target_ratio = max(zero_ratio_1, zero_ratio_2)

        if target_ratio > 0:
            new_range_1 = y1_max / (1 - target_ratio)
            new_range_2 = y2_max / (1 - target_ratio)

            ax.set_ylim(-new_range_1 * target_ratio, y1_max * 1.2)
            ax2.set_ylim(-new_range_2 * target_ratio, y2_max * 1.2)

def configure_axes(ax, ax2, 
                   machines: List, 
                   fontsize: int, 
                   rotation: int, 
                   grid_alpha: float):
    """Configure axes with optimized settings"""

    # Labels
    ax.set_xlabel('Machine No', fontsize=fontsize, fontweight='bold')
    ax.set_ylabel('Mold Count', fontsize=fontsize, fontweight='bold', color='steelblue')
    ax2.set_ylabel('Mold Shot', fontsize=fontsize, fontweight='bold', color='OrangeRed')

    # X-axis optimization for many machines
    optimize_x_axis(ax, machines, fontsize, rotation)

    # Tick parameters
    ax.tick_params(axis='y', labelcolor='steelblue', labelsize=fontsize - 1)
    ax2.tick_params(axis='y', labelcolor='OrangeRed', labelsize=fontsize - 1)
    ax.tick_params(axis='x', labelsize=fontsize - 2)

    # Grid
    ymax = int(ax.get_ylim()[1])
    ax.set_yticks(np.arange(0, ymax+1, 1))
    ax.grid(True, alpha=grid_alpha, axis='y', linestyle='--', color="skyblue")
    ax2.grid(True, alpha=grid_alpha, axis='y', linestyle='-.')

    # Sync Y axes
    sync_y_axes(ax, ax2)

def create_legends(ax, ax2, n_machines: int):
    """Create optimized legends"""
    handles1, labels1 = ax.get_legend_handles_labels()
    handles2, labels2 = ax2.get_legend_handles_labels()

    fontsize = 'small' if n_machines > 25 else 'medium'

    # Mold count legend
    if handles1:
        legend1 = ax.legend(
            handles1, [f'Count S{label}' for label in labels1],
            loc='upper left', title='Mold Count',
            framealpha=0.9, fontsize=fontsize,
            title_fontsize='small'
        )
        legend1.get_title().set_fontweight('bold')

    # Shot legend
    if handles2:
        shot_handles = [(h, l) for h, l in zip(handles2, labels2)
                        if 'Shot' in l or 'Trends' in l]
        if shot_handles:
            handles, labels = zip(*shot_handles)
            legend2 = ax2.legend(
                handles, labels,
                loc='upper right', title='Mold Shot',
                framealpha=0.9, fontsize=fontsize,
                title_fontsize='small'
            )
            legend2.get_title().set_fontweight('bold')