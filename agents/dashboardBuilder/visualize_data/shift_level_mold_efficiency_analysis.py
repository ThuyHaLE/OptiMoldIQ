from agents.decorators import validate_init_dataframes
from agents.dashboardBuilder.visualize_data.utils import generate_color_palette, save_plot
import pandas as pd
import numpy as np
from loguru import logger
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from typing import Tuple

@validate_init_dataframes({"df": ['workingShift', 'machineNo', 'itemName', 'itemTotalQuantity',
                        'itemGoodQuantity', 'moldNo', 'moldShot', 'moldCavity',
                        'moldCavityStandard', 'moldSettingCycle', 'moldCount', 'moldCycle',
                        'moldCavityUtilizationRate', 'moldCavityGap', 'moldCycleEfficiency',
                        'moldCycleDeviation', 'overallProductionEfficiency',
                        'expected_total_quantity', 'expectedYieldEfficiency']})

def create_shift_level_mold_efficiency_chart(df: pd.DataFrame,
                                file_path: str,
                                sns_style: str = 'seaborn-v0_8',
                                palette_name: str = 'muted',
                                figsize: Tuple[int, int] = (16, 12),
                                show_stats: bool = True,
                                legend_position: str = 'top') -> plt.Figure:

    """
    Create a mold efficiency chart per machine, showing stacked item quantity and good item trend line.

    Parameters:
        df (pd.DataFrame): Input data with columns ['machineNo', 'itemName', 'itemTotalQuantity', 'itemGoodQuantity']
        file_path (str): Path to save the output chart
        sns_style (str): Seaborn style to use
        palette_name (str): Color palette name
        figsize (tuple): Optional figure size
        show_stats (bool): Show statistics
        legend_position (str): Legend position
    """

    logger.info(
        "Called create_mold_efficiency_chart with \ndf.shape={}, \ncolumns={}, \nfile_path={}, \nsns_style={}, \npalette_name={}, \nfigsize={}, \nshow_stats={}, \nlegend_position={}",
        df.shape, list(df.columns), file_path, sns_style, palette_name, figsize, show_stats, legend_position)
    
    def get_metric_value(mold, shift_num, column):
        mask = (df['moldNo'] == mold) & (df['workingShift'] == shift_num)
        values = df.loc[mask, column]
        return values.values[0] if not values.empty else np.nan

    def prepare_data(column):
        # Dynamic shift data preparation
        shift_data = {}
        for i, shift_num in enumerate(unique_shifts):
            shift_key = f'Shift {shift_num}'
            shift_data[shift_key] = [get_metric_value(mold, shift_num, column) for mold in molds]

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

    def plot_bars(ax, x_positions, shift_data, avg_data):

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

    def add_bounding_boxes(ax, x_positions, y_max=120):

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

    def add_statistics_text(ax, shift_data, avg_data):

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

    # ---- Main Plot Logic ----
    logger.debug("Configs setting...")

    metrics_config = [
        {'column': 'moldCavityUtilizationRate', 'title': 'Cavity Utilization Rate (%)', 'ylabel': 'Cavity Utilization Rate (%)'},
        {'column': 'moldCycleEfficiency', 'title': 'Cycle Time Efficiency (%)', 'ylabel': 'Cycle Time Efficiency (%)'},
        {'column': 'overallProductionEfficiency', 'title': 'Overall Production Efficiency (%)', 'ylabel': 'Production Efficiency (%)'},
        {'column': 'expectedYieldEfficiency', 'title': 'Expected Yield Efficiency (%)', 'ylabel': 'Yield Efficiency (%)'}
    ]
    ylim = max(df['moldCycleEfficiency'].max(), df['moldCavityUtilizationRate'].max(),
              df['overallProductionEfficiency'].max(), df['expectedYieldEfficiency'].max())
    
    # Dynamic shift handling
    unique_shifts = sorted(df['workingShift'].unique(), key=lambda x: x if isinstance(x, int) else 99)
    shifts = [f'Shift {shift}' for shift in unique_shifts]
    n_shifts = len(shifts)

    color_list = generate_color_palette(n_shifts, palette_name=palette_name)
    shift_colors = {shifts[i]: color_list[i] for i in range(n_shifts)}
    shift_colors['avg'] = '#9B9B9B'

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

    plt.style.use(sns_style)
    logger.info("Used Seabon style: {}. \nAnother supported styles: {}", sns_style, plt.style.available)

    fig, axes = plt.subplots(len(metrics_config), 1, figsize=figsize, sharex=True, facecolor='white')

    for i, (ax, config) in enumerate(zip(axes, metrics_config)):
        shift_data, avg_data = prepare_data(config['column'])
        plot_bars(ax, x_positions, shift_data, avg_data)
        add_bounding_boxes(ax, x_positions, ylim)
        add_legend = (legend_position == 'first_subplot' and i == 0) or (legend_position == 'all')
        style_subplot(ax, ylim, config['title'], config['ylabel'], add_legend=add_legend)
        if show_stats:
            add_statistics_text(ax, shift_data, avg_data)

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

    plt.show()

    logger.debug("Saving plot...")
    save_plot(fig, file_path, dpi=300)