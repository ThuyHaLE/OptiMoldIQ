from agents.decorators import validate_dataframe
from agents.dashboardBuilder.visualize_data.utils import generate_color_palette, load_visualization_config
import pandas as pd
import numpy as np
from loguru import logger
import matplotlib.pyplot as plt
from typing import Tuple, Optional, Dict

DEFAULT_CONFIG = {
    "colors": {
        "secondary": "#95A5A6",
        "dark": "#2C3E50"
    },
    "sns_style": "seaborn-v0_8",
    "palette_name": "muted",
    "figsize": None,
    "gridspec_kw": {
        'hspace': 0.4,
        'wspace': 0.3,
        'top': 0.92,
        'bottom': 0.1,
        'left': 0.08,
        'right': 0.95
        },
    "main_title_y": 0.99,
    "subtitle_y": 0.95,
    "summary_y": 0.01
}

def determine_plot_settings(num_machines: int, 
                            figsize_config: Optional[dict]) -> Tuple[int, int]:
    """Calculate optimal figure size based on number of machines."""
    if figsize_config is None:
        width = max(16, num_machines * 0.8)
        height = max(10, 8 + num_machines * 0.05)
        return (width, height)
    else:
        return tuple(figsize_config)  # Use provided figsize

def safe_division(numerator: pd.Series, denominator: pd.Series, fill_value: float = 0.0) -> pd.Series:
    """Safely divide two series, handling division by zero."""
    return np.where(denominator != 0, numerator / denominator * 100, fill_value)

def create_pivot_tables(shift_summary: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Create all pivot tables in one efficient operation."""
    
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
    
    return pivot_total, pivot_good, pivot_efficiency

def calculate_performance_metrics(shift_summary)-> dict:

      logger.debug("Creating general statistics...")

      # General statistics with safe division
      total_production = shift_summary['itemTotalQuantity'].sum()
      total_good = shift_summary['itemGoodQuantity'].sum()
      overall_efficiency = (total_good / total_production * 100) if total_production > 0 else 0

      # Top/Bottom performers
      machine_summary = shift_summary.groupby('machineNo').agg({
          'itemTotalQuantity': 'sum',
          'itemGoodQuantity': 'sum'
      })
      machine_summary['efficiency'] = safe_division(
          machine_summary['itemGoodQuantity'], 
          machine_summary['itemTotalQuantity']
      )

      # Handle case where no machines have data
      if machine_summary.empty or machine_summary['efficiency'].isna().all():
          logger.warning("No valid efficiency data found")
          best_machine = worst_machine = "N/A"
          best_eff = worst_eff = 0
      else:
          best_machine = machine_summary['efficiency'].idxmax()
          worst_machine = machine_summary['efficiency'].idxmin()
          best_eff = machine_summary.loc[best_machine, 'efficiency']
          worst_eff = machine_summary.loc[worst_machine, 'efficiency']

      return {
          "total_production": total_production,
          "total_good": total_good,
          "overall_efficiency": overall_efficiency,
          "best_machine": best_machine,
          "worst_machine": worst_machine, 
          "best_eff": best_eff,
          "worst_eff": worst_eff
      }

def shift_level_yield_efficiency_plotter(df: pd.DataFrame,
                                         main_title: str = 'Manufacturing Performance Dashboard',
                                         subtitle: str = 'Yield Efficiency by Machine & Shift',
                                         visualization_config_path: Optional[str] = None) -> plt.Figure:
    """
    Generate yield analysis charts by machine and shift with optimization for large number of machines.
    
    Args:
        df: DataFrame with manufacturing data
        main_title: Main chart title
        subtitle: Chart subtitle
        visualization_config_path: Path to JSON config file
        
    Returns:
        matplotlib Figure object
    """
    # Valid data frame
    required_columns = ['machineNo', 'itemName', 'itemTotalQuantity', 'itemGoodQuantity']
    validate_dataframe(df, required_columns)

    # Input validation
    if df.empty:
        logger.warning("Empty dataframe provided")
        return plt.figure()
    
    # Check for required shift column
    if 'workingShift' not in df.columns:
        logger.error("Required column 'workingShift' not found in dataframe")
        raise ValueError("Missing required column 'workingShift'")

    # Load visualization config
    visualization_config = load_visualization_config(DEFAULT_CONFIG, visualization_config_path)

    logger.debug("Processing dataframe with shape: {}", df.shape)
    
    # Data aggregation by machine, shift
    shift_summary = df.groupby(['machineNo', 'workingShift']).agg({
        'itemTotalQuantity': 'sum',
        'itemGoodQuantity': 'sum'
    }).reset_index()

    # Calculate efficiency using safe division
    shift_summary['efficiency'] = safe_division(
        shift_summary['itemGoodQuantity'], 
        shift_summary['itemTotalQuantity']
    )

    # Create pivot tables efficiently
    pivot_total, pivot_good, pivot_efficiency = create_pivot_tables(shift_summary)
    
    # Calculate performance metrics
    metrics = calculate_performance_metrics(shift_summary)

    logger.debug("Plotting...")
    # Number of machines and shifts
    machines = sorted(shift_summary['machineNo'].unique())
    shifts = sorted(shift_summary['workingShift'].unique(), 
                   key=lambda x: x if isinstance(x, (int, float)) else 99)
    n_machines = len(machines)
    n_shifts = len(shifts)

    # Validate we have data to plot
    if n_machines == 0 or n_shifts == 0:
        logger.warning("No machines or shifts to plot")
        return plt.figure()

    # Color for each shift (expand palette)
    colors = generate_color_palette(n_shifts, palette_name=visualization_config['palette_name'])
    
    figsize = determine_plot_settings(n_machines, visualization_config["figsize"])
    
    logger.info(
        "Creating chart with: df.shape={}, machines={}, shifts={}, figsize={}",
        df.shape, n_machines, n_shifts, figsize
    )
    
    # Set style and figure
    plt.style.use(visualization_config['sns_style'])
    logger.info('Used Seaborn style: {}. Available styles: {}', 
                visualization_config['sns_style'], plt.style.available[:5])  # Limit log output
    
    fig, ax = plt.subplots(figsize=figsize,
                           gridspec_kw=visualization_config["gridspec_kw"])

    # Add main title
    fig.suptitle(f'{main_title}',
                fontsize=18, fontweight='bold', y=visualization_config['main_title_y'], 
                color=visualization_config["colors"]["dark"])

    # Add subtitle
    fig.text(0.5, visualization_config['subtitle_y'], f'{subtitle}',
            ha='center', fontsize=11, style='italic', 
            color=visualization_config["colors"]["secondary"])

    # Add summary information at the bottom
    summary_info = (f"Total: {int(metrics['total_production']):,} | Good: {int(metrics['total_good']):,} | "
                    f"Overall: {metrics['overall_efficiency']:.1f}% | "
                    f"Best: M{metrics['best_machine']}({metrics['best_eff']:.1f}%) | Worst: M{metrics['worst_machine']}({metrics['worst_eff']:.1f}%)")
    fig.text(0.5, visualization_config['summary_y'], summary_info,
            ha='center', fontsize=11, style='italic', 
            color=visualization_config["colors"]["secondary"])

    # Adjust bar width based on machine and shift count
    base_width = 0.8 / n_shifts  # Total width = 0.8, divided equally among shifts
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

        # Add efficiency annotations (only when space is available)
        if n_machines <= 25:  # Only show % when machines <= 25
            for j, (total, good, eff) in enumerate(zip(total_values, good_values, efficiency_values)):
                if total > 0:  # Only annotate bars with data
                    font_size = max(6, 10 - n_machines * 0.1)
                    rotation = 90 if n_machines > 15 else 0
                    
                    ax.text(x_shift[j], good + total * 0.02, f'{eff:.0f}%',
                           ha='center', va='bottom', fontsize=font_size,
                           fontweight='bold', rotation=rotation,
                           bbox=dict(boxstyle="round,pad=0.1", facecolor='yellow', alpha=0.6))

    # Optimize legend
    if n_shifts <= 5:  # Full legend when shifts <= 5
        legend_elements = []
        for i, shift in enumerate(shifts):
            legend_elements.extend([
                plt.Rectangle((0,0),1,1, facecolor=colors[i], alpha=0.4, 
                             label=f'Shift {shift} - Total'),
                plt.Rectangle((0,0),1,1, facecolor=colors[i], alpha=0.8,
                             edgecolor='white', linewidth=0.5, 
                             label=f'Shift {shift} - Good')
            ])
        ax.legend(handles=legend_elements, bbox_to_anchor=(1.02, 1), loc='upper left',
                 frameon=True, fontsize=9)
    else:  # Simplified legend when too many shifts
        logger.warning("Too many shifts ({}), using simplified legend", n_shifts)
        legend_elements = [plt.Rectangle((0,0),1,1, facecolor=colors[i], alpha=0.8,
                                       label=f'Shift {shift}') 
                          for i, shift in enumerate(shifts)]
        ax.legend(handles=legend_elements, bbox_to_anchor=(1.02, 1), loc='upper left',
                 frameon=True, fontsize=9, title="Shifts (Good/Total)")

    # Set axes labels
    ax.set_ylabel('Quantity', fontsize=12, fontweight='bold')
    ax.set_xlabel('Machine No', fontsize=12, fontweight='bold')

    # Optimize x-axis labels based on number of machines
    ax.set_xticks(x_pos)
    if n_machines <= 20:
        ax.set_xticklabels(machines, rotation=45, ha='right', fontsize=10)
    elif n_machines <= 35:
        ax.set_xticklabels(machines, rotation=90, ha='center', fontsize=8)
    else:
        logger.warning("Too many machines ({}), showing every 2nd label", n_machines)
        # Show every 2nd machine when too many
        labels = [machines[i] if i % 2 == 0 else '' for i in range(n_machines)]
        ax.set_xticklabels(labels, rotation=90, ha='center', fontsize=7)

    ax.tick_params(axis='y', labelsize=10)
    ax.set_axisbelow(True)
    ax.grid(True, alpha=0.5, linestyle='--', axis='y', color='gray', linewidth=0.5)
    

    # Layout adjustments
    plt.tight_layout()
    bottom_margin = 0.15 if n_machines <= 20 else 0.2
    right_margin = 0.82 if n_shifts <= 3 else 0.75
    plt.subplots_adjust(bottom=bottom_margin, right=right_margin)

    return fig