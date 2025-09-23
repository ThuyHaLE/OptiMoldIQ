from agents.decorators import validate_init_dataframes
from agents.dashboardBuilder.visualize_data.utils import generate_color_palette, load_visualization_config
import pandas as pd
import numpy as np
from loguru import logger
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from typing import Optional

DEFAULT_CONFIG = {
    "colors": {
        'secondary': '#95A5A6',    # Gray
        'dark': '#2C3E50'          # Dark blue
    },
    "sns_style": "seaborn-v0_8",
    "palette_name": "muted",
    "figsize": (16, 12),
    "gridspec_kw": {
        'hspace': 0.4,
        'wspace': 0.3,
        'top': 0.85,
        'bottom': 0.1,
        'left': 0.08,
        'right': 0.95
    },
    "main_title_y": 0.96,
    "subtitle_y": 0.92,
}

def get_metric_value(df, mold, shift_num, column):
    try:
        mask = (df['moldNo'] == mold) & (df['workingShift'] == shift_num)
        values = df.loc[mask, column]
        if values.empty:
            logger.warning(f"No data found for mold {mold} in shift {shift_num}")
            return np.nan
        return values.iloc[0]  # Use iloc[0] instead of values[0]
    except Exception as e:
        logger.error(f"Error getting metric value: {e}")
        return np.nan

def prepare_data(df, molds, unique_shifts, shifts, column):
    shift_data = {}
    for shift_num in unique_shifts:
        shift_key = f'Shift {shift_num}'
        shift_data[shift_key] = [get_metric_value(df, mold, shift_num, column) for mold in molds]

    logger.debug('shift_data keys={}', list(shift_data.keys()))
    logger.debug('shifts list={}', shifts)

    # Calculate average across all shifts dynamically
    avg_data = []
    for mold_idx in range(len(molds)):
        shift_values = []
        for shift in shifts:
            if shift in shift_data:
                value = shift_data[shift][mold_idx]
                # Safe check for valid numeric values
                if value is not None and not (isinstance(value, float) and np.isnan(value)):
                    shift_values.append(value)
        avg_data.append(np.nanmean(shift_values) if shift_values else np.nan)

    return shift_data, avg_data

def data_processing(df, moldInfo_df):

    merged = pd.merge(df[['workingShift', 'machineNo', 'itemName', 'itemTotalQuantity',
                          'itemGoodQuantity', 'moldNo', 'moldShot', 'moldCavity', 'moldCount']],
                      moldInfo_df[['moldNo', 'moldCavityStandard', 'moldSettingCycle']],
                      on='moldNo', how='left')

    new_df = merged[(merged['moldCount'] == 1) & (merged['moldShot'] > 0)].copy()

    new_df['moldCycle'] = (8 * 3600) / new_df['moldShot']
    new_df['moldCavityUtilizationRate'] = (new_df['moldCavity'] / new_df['moldCavityStandard']) * 100
    new_df['moldCavityGap'] = new_df['moldCavity'] - new_df['moldCavityStandard']
    new_df['moldCycleEfficiency'] = (new_df['moldSettingCycle'] / new_df['moldCycle']) * 100
    new_df['moldCycleDeviation'] = (new_df['moldSettingCycle'] - new_df['moldCycle'])
    new_df['overallProductionEfficiency'] = (new_df['moldCavityUtilizationRate'] + new_df['moldCycleEfficiency']) / 2
    new_df['expected_total_quantity'] = (((8 * 3600) / new_df['moldSettingCycle']) * new_df['moldCavityStandard'])
    new_df['expectedYieldEfficiency'] = (new_df['itemTotalQuantity'] / new_df['expected_total_quantity']) * 100

    return new_df


@validate_init_dataframes({"df": ['workingShift', 'machineNo', 'itemName', 'itemTotalQuantity',
                                  'itemGoodQuantity', 'moldNo', 'moldShot', 'moldCavity', 'moldCount',
                                  'moldCavityStandard', 'moldSettingCycle', 'moldCycle',
                                  'moldCavityUtilizationRate', 'moldCavityGap', 'moldCycleEfficiency',
                                  'moldCycleDeviation', 'overallProductionEfficiency',
                                  'expected_total_quantity', 'expectedYieldEfficiency']})

def shift_level_mold_efficiency_plotter(df: pd.DataFrame,
                                        moldInfo_df: pd.DataFrame,
                                        main_title: str = 'Manufacturing Performance Dashboard',
                                        subtitle: str = 'Mold Efficiency Analysis by Shift',
                                        visualization_config_path: Optional[str] = None,
                                        show_stats: bool = True,
                                        legend_position: str = 'top') -> plt.Figure:

    """
    Create a mold efficiency chart per machine, showing stacked item quantity and good item trend line.

    Parameters:
        df (pd.DataFrame): DataFrame with manufacturing data
        main_title: Main chart title
        subtitle: Chart subtitle
        visualization_config_path: Path to JSON config file
        show_stats (bool): Show statistics
        legend_position (str): Legend position
    """

    visualization_config = load_visualization_config(DEFAULT_CONFIG, visualization_config_path)

    df = data_processing(df, moldInfo_df)

    logger.debug("Configs setting...")
    metrics_config = [
        {'column': 'moldCavityUtilizationRate', 
         'title': 'Cavity Utilization Rate (%)', 
         'ylabel': 'Cavity Utilization Rate (%)'},
        {'column': 'moldCycleEfficiency', 
         'title': 'Cycle Time Efficiency (%)', 
         'ylabel': 'Cycle Time Efficiency (%)'},
        {'column': 'overallProductionEfficiency', 
         'title': 'Overall Production Efficiency (%)', 
         'ylabel': 'Production Efficiency (%)'},
        {'column': 'expectedYieldEfficiency', 
         'title': 'Expected Yield Efficiency (%)', 
         'ylabel': 'Yield Efficiency (%)'}
    ]
    ylim = max(df['moldCycleEfficiency'].max(), df['moldCavityUtilizationRate'].max(),
              df['overallProductionEfficiency'].max(), df['expectedYieldEfficiency'].max())

    # Dynamic shift handling
    unique_shifts = sorted(df['workingShift'].unique(), key=lambda x: x if isinstance(x, int) else 99)
    shifts = [f'Shift {shift}' for shift in unique_shifts]
    n_shifts = len(shifts)

    color_list = generate_color_palette(n_shifts+1, palette_name=visualization_config['palette_name'])
    shift_colors = {shifts[i]: color_list[i] for i in range(n_shifts)}
    shift_colors['avg'] = color_list[-1]

    # Dynamic width calculation based on number of shifts
    # Total space per mold group = 4 * base_width
    # Each bar gets: total_space / (n_shifts + 1) where +1 is for average
    base_width = 0.18
    total_width = 4 * base_width
    width = total_width / (n_shifts + 1)

    logger.debug("Data processing...")
    molds = sorted(df['moldNo'].unique())

    logger.debug("Plotting...")
    x_positions = np.arange(len(molds))

    # Set style
    plt.style.use(visualization_config['sns_style'])
    logger.info('Used Seaborn style: {}.\nAvailable styles: {}', visualization_config['sns_style'], plt.style.available)

    fig, axes = plt.subplots(len(metrics_config), 1, 
                             figsize=visualization_config['figsize'], 
                             sharex=True, facecolor='white',
                             gridspec_kw=visualization_config['gridspec_kw'])

    # Add main title with all information
    # Combine title and subtitle
    fig.suptitle(f'{main_title}',
                fontsize=18, fontweight='bold', y=visualization_config['main_title_y'], 
                color=visualization_config['colors']['dark'])

    # Add subtitle
    fig.text(0.5, visualization_config['subtitle_y'], f'{subtitle}',
            ha='center', fontsize=11, style='italic', color=visualization_config['colors']['secondary'])

    for i, (ax, config) in enumerate(zip(axes, metrics_config)):
        shift_data, avg_data = prepare_data(df, molds, unique_shifts, shifts, config['column'])
        plot_bars(ax, n_shifts, shift_colors, width, x_positions, shift_data, avg_data)
        add_bounding_boxes(ax, n_shifts, width, x_positions, ylim)
        add_legend = (legend_position == 'first_subplot' and i == 0) or (legend_position == 'all')
        style_subplot(ax, ylim, config['title'], config['ylabel'], add_legend=add_legend)
        if show_stats:
            add_statistics_text(ax, shift_data)

    if legend_position == 'top':
        handles, labels = axes[0].get_legend_handles_labels()
        # Dynamic ncol based on number of shifts + 1 (for average)
        ncol = min(n_shifts + 1, 6)  # Max 6 columns to avoid overcrowding
        fig.legend(handles, labels, loc='upper center', bbox_to_anchor=(0.5, -0.01),
                  ncol=ncol, frameon=True, fancybox=True, shadow=True, fontsize=10)
        plt.subplots_adjust(top=0.90)

    plt.xticks(x_positions, molds, rotation=45, ha='right')
    plt.xlabel('Mold Number', fontsize=12, fontweight='bold')

    if legend_position != 'top':
        plt.tight_layout(pad=2.0)

    return fig

def plot_bars(ax, n_shifts, shift_colors, width, x_positions, shift_data, avg_data):

    bars = []

    # Dynamic positioning calculation
    total_bars = n_shifts + 1  # +1 for average
    start_offset = -(total_bars - 1) / 2

    # Plot shift bars
    for i, (shift_name, values) in enumerate(shift_data.items()):
        position = start_offset + i
        bar_kwargs = {
            'width': width,
            'label': shift_name,
            'color': shift_colors[shift_name],
            'alpha': 0.8,
            'edgecolor': 'white',
            'linewidth': 0.5
        }
        bars.append(ax.bar(x_positions + position * width, values, **bar_kwargs))

    # Plot average bar
    avg_position = start_offset + n_shifts
    bar_kwargs = {
        'width': width,
        'label': 'Average',
        'color': shift_colors['avg'],
        'alpha': 0.7,
        'hatch': '///',
        'edgecolor': 'white',
        'linewidth': 0.5
    }
    bars.append(ax.bar(x_positions + avg_position * width, avg_data, **bar_kwargs))

    return bars

def add_bounding_boxes(ax, n_shifts, width, x_positions, y_max=120):

    # Dynamic bounding box width based on number of shifts
    total_bars = n_shifts + 1
    box_width = total_bars * width

    for x_pos in x_positions:
        left = x_pos - box_width / 2
        rect = Rectangle(
            (left, 0), box_width, y_max,
            linewidth=1, edgecolor='gray',
            facecolor='none', linestyle=':', alpha=0.4
        )
        ax.add_patch(rect)

def style_subplot(ax, y_lim, title, ylabel,
                    target_line=100, add_legend=False):

    ax.set_ylim(0, int(y_lim) + 10)
    ax.set_title(title, fontsize=14, fontweight='bold', pad=15)
    ax.set_ylabel(ylabel, fontsize=11)
    ax.axhline(y=target_line, color='red', linestyle='--', alpha=0.7, linewidth=2, label=f'Target {target_line}%')
    ax.grid(axis='y', alpha=0.3, linestyle='-', linewidth=0.5)
    ax.set_axisbelow(True)
    if add_legend:
        ax.legend(loc='upper right', frameon=True, fancybox=True, shadow=True, fontsize=9)
    for spine in ax.spines.values():
        spine.set_linewidth(0.5)
        spine.set_color('gray')

def add_statistics_text(ax, shift_data):

    # Collect all values from all shifts dynamically
    all_values = []
    for shift_values in shift_data.values():
        for v in shift_values:
            # Safe check for valid numeric values
            if v is not None and not (isinstance(v, float) and np.isnan(v)):
                all_values.append(v)

    if all_values:
        mean_val = np.mean(all_values)
        max_val = np.max(all_values)
        min_val = np.min(all_values)
        stats_text = f'Mean: {mean_val:.1f}% | Range: {min_val:.1f}%-{max_val:.1f}%'
        ax.text(0.02, 0.98, stats_text, transform=ax.transAxes,
                verticalalignment='top', fontsize=8,
                bbox=dict(boxstyle='round,pad=0.3', facecolor='lightgray', alpha=0.5))