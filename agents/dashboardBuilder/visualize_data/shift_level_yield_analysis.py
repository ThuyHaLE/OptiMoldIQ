from agents.dashboardBuilder.visualize_data.decorators import validate_dataframe, validate_input
from agents.dashboardBuilder.visualize_data.utils import generate_color_palette, save_plot
import pandas as pd
import numpy as np
from loguru import logger
import matplotlib.pyplot as plt

@validate_input({"df": ['machineNo', 'itemName', 'itemTotalQuantity', 'itemGoodQuantity']})
def create_shift_level_yield_chart(df: pd.DataFrame,
                             file_path: str,
                             sns_style: str = 'seaborn-v0_8',
                             palette_name: str = 'muted',
                             figsize: tuple = None) -> None:

    """
    Generate yield analysis charts by machine and shift with optimization for large number of machines

    Parameters:
        df (pd.DataFrame): Input data with columns ['machineNo', 'workingShift', 'itemName', 'itemTotalQuantity', 'itemGoodQuantity']
        file_path (str): Path to save the output chart
        sns_style (str): Seaborn style to use
        palette_name (str): Color palette name
        figsize (tuple): Optional figure size
    """

    logger.info(
        "Called create_shift_level_yield_chart with \ndf.shape={}, \ncolumns={}, \nfile_path={}, \nsns_style={}, \npalette_name={}, \nfigsize={}",
        df.shape, list(df.columns), file_path, sns_style, palette_name, figsize)

    
    logger.debug("Dataframe processing...")
    # Data aggregation by machine, shift
    shift_summary = df.groupby(['machineNo', 'workingShift']).agg({
        'itemTotalQuantity': 'sum',
        'itemGoodQuantity': 'sum'
    }).reset_index()

    # Calculate efficiency for each machine-shift
    shift_summary['efficiency'] = (
        shift_summary['itemGoodQuantity'] / shift_summary['itemTotalQuantity'] * 100
    )

    logger.debug("Creating pivot tables...")
    # Create pivot tables
    pivot_total = shift_summary.pivot_table(
        index='machineNo', columns='workingShift',
        values='itemTotalQuantity', fill_value=0
    )
    pivot_good = shift_summary.pivot_table(
        index='machineNo', columns='workingShift',
        values='itemGoodQuantity', fill_value=0
    )
    pivot_efficiency = shift_summary.pivot_table(
        index='machineNo', columns='workingShift',
        values='efficiency', fill_value=0
    )

    logger.debug("Creating general statistics...")
    # General statistics
    total_production = shift_summary['itemTotalQuantity'].sum()
    total_good = shift_summary['itemGoodQuantity'].sum()
    overall_efficiency = (total_good / total_production * 100) if total_production > 0 else 0

    # Top/Bottom performers
    machine_summary = shift_summary.groupby('machineNo').agg({
        'itemTotalQuantity': 'sum',
        'itemGoodQuantity': 'sum'
    })
    machine_summary['efficiency'] = (
        machine_summary['itemGoodQuantity'] / machine_summary['itemTotalQuantity'] * 100
    )

    best_machine = machine_summary['efficiency'].idxmax()
    worst_machine = machine_summary['efficiency'].idxmin()
    best_eff = machine_summary.loc[best_machine, 'efficiency']
    worst_eff = machine_summary.loc[worst_machine, 'efficiency']

    logger.debug("Plotting...")
    # Number of machines and shifts
    machines = sorted(shift_summary['machineNo'].unique())
    shifts = sorted(shift_summary['workingShift'].unique(), key=lambda x: x if isinstance(x, int) else 99)
    n_machines = len(machines)
    n_shifts = len(shifts)

    # Color for each shift (expand palette)
    colors = generate_color_palette(n_shifts, palette_name=palette_name)

    # Automatically adjust figsize based on machine count
    if figsize is None:
        width = max(16, n_machines * 0.8)  # Minimum 16, increasing with number of machines
        height = max(10, 8 + n_machines * 0.05)  # Slight height increase
        figsize = (width, height)

    # Set style and figure
    plt.style.use(sns_style)
    logger.info('Used Seabon style: {}. \nAnother supported styles: {}', sns_style, plt.style.available)
    fig, ax = plt.subplots(figsize=figsize)

    # Adjust bar width based on machine and shift count
    base_width = 0.8 / n_shifts  # Total width = 0.8, divided equally among the shifts
    bar_width = min(base_width, 0.25)  # Not exceeding 0.25

    x_pos = np.arange(n_machines)

    # Draw bars
    bars_data = []

    for i, shift in enumerate(shifts):
        # x position for this shift
        offset = (i - (n_shifts - 1) / 2) * bar_width
        x_shift = x_pos + offset

        # Get data for this shift
        total_values = pivot_total[shift].reindex(machines, fill_value=0).values
        good_values = pivot_good[shift].reindex(machines, fill_value=0).values
        efficiency_values = pivot_efficiency[shift].reindex(machines, fill_value=0).values

        # Draw total quantity bars (background)
        bars_total = ax.bar(x_shift, total_values, bar_width,
                           color=colors[i], alpha=0.4,
                           label=f'Shift {shift} - Total')

        # Draw good quantity bars (overlay)
        bars_good = ax.bar(x_shift, good_values, bar_width,
                          color=colors[i], alpha=0.8,
                          edgecolor='white', linewidth=0.5,
                          label=f'Shift {shift} - Good')

        bars_data.append((bars_total, bars_good, shift, colors[i]))

        # Add efficiency annotations (only visible when space is available)
        if n_machines <= 25:  # Only show % when machine is less
            for j, (total, good, eff) in enumerate(zip(total_values, good_values, efficiency_values)):
                if total > 0:
                    ax.text(x_shift[j], good + total * 0.02, f'{eff:.0f}%',
                           ha='center', va='bottom', fontsize=max(6, 10-n_machines*0.1),
                           fontweight='bold', rotation=90 if n_machines > 15 else 0,
                           bbox=dict(boxstyle="round,pad=0.1", facecolor='yellow', alpha=0.6))

    # Optimize legend
    if n_shifts <= 5:  # Full legend when shift is less
        legend_elements = []
        for i, shift in enumerate(shifts):
            legend_elements.extend([
                plt.Rectangle((0,0),1,1, facecolor=colors[i], alpha=0.4, label=f'Shift {shift} - Total'),
                plt.Rectangle((0,0),1,1, facecolor=colors[i], alpha=0.8,
                             edgecolor='white', linewidth=0.5, label=f'Shift {shift} - Good')
            ])
        ax.legend(handles=legend_elements, bbox_to_anchor=(1.02, 1), loc='upper left',
                 frameon=True, fontsize=9)
    else:  # Legend shortens when shift is too much
        logger.warning("Too many shifts, optimizing legend...")
        legend_elements = [plt.Rectangle((0,0),1,1, facecolor=colors[i], alpha=0.8,
                                       label=f'Shift {shift}') for i, shift in enumerate(shifts)]
        ax.legend(handles=legend_elements, bbox_to_anchor=(1.02, 1), loc='upper left',
                 frameon=True, fontsize=9, title="Shifts (Good/Total)")

    # Set axes
    ax.set_title('Yield Analysis by Machine and Working Shift',
                fontsize=max(14, 18-n_machines*0.1), fontweight='bold', pad=20)
    ax.set_ylabel('Quantity', fontsize=12, fontweight='bold')
    ax.set_xlabel('Machine No', fontsize=12, fontweight='bold')

    # Optimize x-axis labels
    ax.set_xticks(x_pos)
    if n_machines <= 20:
        ax.set_xticklabels(machines, rotation=45, ha='right', fontsize=10)
    elif n_machines <= 35:
        ax.set_xticklabels(machines, rotation=90, ha='center', fontsize=8)
    else:
        logger.warning("Too many shifts, optimizing labels (show every 2nd machine)...")
        # Show every 2nd machine when too many
        labels = [machines[i] if i % 2 == 0 else '' for i in range(n_machines)]
        ax.set_xticklabels(labels, rotation=90, ha='center', fontsize=7)

    ax.tick_params(axis='y', labelsize=10)
    ax.grid(True, alpha=0.3, linestyle='--', axis='y')

    # Subtitle with detailed information
    subtitle = (f'Total: {int(total_production):,} | Good: {int(total_good):,} | '
                f'Overall: {overall_efficiency:.1f}% | '
                f'Best: M{best_machine}({best_eff:.1f}%) | Worst: M{worst_machine}({worst_eff:.1f}%)')

    fig.suptitle(subtitle, fontsize=max(10, 12-n_machines*0.05), y=0.01)

    # Layout adjustments
    plt.tight_layout()
    bottom_margin = 0.15 if n_machines <= 20 else 0.2
    right_margin = 0.82 if n_shifts <= 3 else 0.75
    plt.subplots_adjust(bottom=bottom_margin, right=right_margin)

    plt.show()

    # Lưu với DPI cao
    logger.debug("Saving plot...")
    save_plot(fig, file_path, dpi=300)