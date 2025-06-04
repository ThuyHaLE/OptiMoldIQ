from agents.dashboardBuilder.visualize_data.decorators import validate_dataframe, validate_input
from agents.dashboardBuilder.visualize_data.utils import generate_color_palette, save_plot
import pandas as pd
import numpy as np
from loguru import logger
import seaborn as sns
import matplotlib.pyplot as plt
from collections import defaultdict
from typing import Dict, Tuple, List

@validate_input({
    "moldInfo_moldCount_merged_productRecords_df": ['workingShift', 'machineNo', 'itemName', 'itemTotalQuantity',
                                                    'itemGoodQuantity', 'moldNo', 'moldShot', 'moldCavity',
                                                    'moldCavityStandard', 'moldSettingCycle', 'moldCount'],
    "moldShot_df": ['workingShift', 'machineNo', 'moldShot']
    })
def create_machine_level_mold_analysis_chart(moldInfo_moldCount_merged_productRecords_df: pd.DataFrame,
                                        moldShot_df: pd.DataFrame,
                                        file_path: str,
                                        sns_style: str = 'seaborn-v0_8',
                                        palette_name: str = 'muted') -> Tuple:

    """
    Generate mold analysis charts by machine with optimization for large number of machines

    Parameters:
        moldInfo_moldCount_merged_productRecords_df (pd.DataFrame): Input data with columns 
                                                    ['workingShift', 'machineNo', 'itemName', 'itemTotalQuantity',
                                                    'itemGoodQuantity', 'moldNo', 'moldShot', 'moldCavity',
                                                    'moldCavityStandard', 'moldSettingCycle', 'moldCount']
        moldShot_df (pd.DataFrame): ['workingShift', 'machineNo', 'moldShot']
        file_path (str): Path to save the output chart
        sns_style (str): Seaborn style to use
        palette_name (str): Color palette name
    """

    logger.info(
        "Called create_machine_level_mold_analysis_chart with \nmain_df.shape={}, \nmain_columns={}, \nlookup_df.shape={}, \nlookup_columns={}, \nfile_path={}, \nsns_style={}, \npalette_name={}",
        moldInfo_moldCount_merged_productRecords_df.shape, list(moldInfo_moldCount_merged_productRecords_df.columns),
        moldShot_df.shape, list(moldShot_df.columns), file_path, sns_style, palette_name)

    def prepare_plot_data(moldInfo_moldCount_merged_productRecords_df: pd.DataFrame,
                          moldShot_df: pd.DataFrame) -> dict:

        """
        Prepare and validate data for plot - Optimized version
        """

        logger.info(
        "Called prepare_plot_data with \nmain_df.shape={}, \nmain_columns={}, \nlookup_df.shape={}, \nlookup_columns={}",
        moldInfo_moldCount_merged_productRecords_df.shape, list(moldInfo_moldCount_merged_productRecords_df.columns),
        moldShot_df.shape, list(moldShot_df.columns))


        # Get unique values efficiently
        machines = sorted(moldInfo_moldCount_merged_productRecords_df['machineNo'].unique())
        shifts = sorted(moldInfo_moldCount_merged_productRecords_df['workingShift'].unique(), key=lambda x: x if isinstance(x, int) else 99)

        if not machines or not shifts:
            logger.error("❌ No data found for machines or shifts")
            raise ValueError(f"No data found for machines or shifts: {machines}|{shifts}")

        return {
            'machines': machines,
            'shifts': shifts,
            'n_machines': len(machines),
            'n_shifts': len(shifts)
        }

    def calculate_bar_positions(n_machines: int,
                                n_shifts: int) -> dict:

        """
        Calculating the position of bars - Optimized for large machine counts
        """

        logger.info(
        "Called prepare_plot_data with \nn_machines={}, \nn_shifts={}", n_machines, n_shifts)

        # Adjust bar width based on number of machines for better visualization
        base_width = 0.8
        if n_machines > 20:
            base_width = 0.6
        elif n_machines > 30:
            base_width = 0.4

        bar_width = base_width / n_shifts if n_shifts > 1 else base_width
        group_centers = np.arange(n_machines)

        return {
            'group_centers': group_centers,
            'bar_width': bar_width,
            'base_width': base_width
        }

    def precompute_shot_data(moldShot_df: pd.DataFrame,
                             machines: List,
                             shifts: List) -> Dict:

        """
        Pre-compute shot data for faster plotting - Major optimization
        """

        logger.info(
        "Called precompute_shot_data with \ndf.shape={}, \ncolumns={}, \nmachines={}, \nshifts={}",
        moldShot_df.shape, list(moldShot_df.columns), machines, shifts)

        shot_data = defaultdict(lambda: defaultdict(list))
        trend_data = defaultdict(lambda: {'x': [], 'y': []})

        # Group data once instead of filtering multiple times
        grouped = moldShot_df.groupby(['workingShift', 'machineNo'])['moldShot']

        for (shift, machine), group in grouped:
            if shift in shifts and machine in machines:
                shot_data[shift][machine] = group.tolist()

        return shot_data

    def plot_scatter_and_trends_optimized(ax2,
                                          shot_data: Dict,
                                          machines: List,
                                          shifts: List,
                                          colors: List,
                                          bar_width: float) -> None:

        """
        Drawing scatter plot and trend lines - Optimized version
        """

        logger.info(
        "Called plot_scatter_and_trends_optimized with \nax2={}, \ndata.dict length={} | Keys={}, \nmachines={}, \nshifts={}, \ncolors={}, \nbar_width={}",
        ax2, len(shot_data), list(shot_data.keys()), machines, shifts, colors, bar_width)

        n_shifts = len(shifts)
        n_machines = len(machines)

        # Skip scatter points if too many machines to avoid clutter
        show_scatter = (n_machines <= 25) or (n_shifts == 1)

        # Pre-compute machine positions
        machine_positions = {machine: idx for idx, machine in enumerate(machines)}

        trend_data = defaultdict(lambda: {'x': [], 'y': []})

        for shift_idx, shift in enumerate(shifts):
            if shift not in shot_data:
                continue

            x_positions = []
            y_values = []

            # Calculate offset once
            offset = (shift_idx - (n_shifts - 1) / 2) * bar_width

            for machine in machines:
                if machine not in shot_data[shift]:
                    continue

                machine_idx = machine_positions[machine]
                x_pos = machine_idx + offset
                machine_shots = shot_data[shift][machine]

                if not machine_shots:
                    continue

                avg_shot = np.mean(machine_shots)

                # Collect scatter data only if showing scatter
                if show_scatter:
                    x_positions.extend([x_pos] * len(machine_shots))
                    y_values.extend(machine_shots)

                # Store trend data
                trend_data[machine]['x'].append(x_pos)
                trend_data[machine]['y'].append(avg_shot)

            # Plot scatter points only for smaller datasets
            if show_scatter and x_positions:
                # Use smaller points for large datasets
                point_size = max(10, 30 - n_machines)
                ax2.scatter(
                    x_positions, y_values,
                    color=colors[shift_idx],
                    s=point_size,
                    alpha=0.6,
                    edgecolor='black',
                    linewidth=0.1,
                    label=f'Shot Shift {shift}',
                    zorder=5
                )

        # Plot trend lines with optimization
        plot_trend_lines_optimized(ax2, trend_data, machines, n_machines)

    def plot_trend_lines_optimized(ax2,
                                   trend_data: Dict,
                                   machines: List,
                                   n_machines: int) -> None:

        """
        Plot optimized trend lines
        """

        logger.info(
        "Called plot_trend_lines_optimized with \nax2={}, \ndata.dict length={} | Keys={}, \nmachines={}, \nn_machines={}",
        ax2, len(trend_data), list(trend_data.keys()), machines, n_machines)

        trend_color = 'red'
        line_width = 2 if n_machines <= 20 else 1.5
        alpha = 0.8 if n_machines <= 20 else 0.6

        # Only show legend for first machine to avoid clutter
        legend_shown = False

        for machine in machines:
            if machine not in trend_data or len(trend_data[machine]['x']) < 2:
                continue

            label = 'Machine Trends' if not legend_shown else ""
            legend_shown = True

            ax2.plot(
                trend_data[machine]['x'],
                trend_data[machine]['y'],
                color=trend_color,
                linewidth=line_width,
                alpha=alpha,
                linestyle='-',
                label=label,
                zorder=3
            )

    def setup_figure_layout(n_machines: int) -> Tuple[Tuple[int, int], int, str]:

        """
        Determine optimal figure layout based on number of machines
        """

        logger.info(
        "Called setup_figure_layout \nn_machines={}", n_machines)

        if n_machines <= 15:
            figsize = (14, 8)
            rotation = 45
            fontsize = 12
        elif n_machines <= 25:
            figsize = (18, 8)
            rotation = 60
            fontsize = 10
        elif n_machines <= 35:
            figsize = (22, 8)
            rotation = 75
            fontsize = 9
        else:  # > 35 machines
            figsize = (26, 10)
            rotation = 90
            fontsize = 8

        return figsize, rotation, fontsize

    def optimize_x_axis_labels(ax,
                               machines: List,
                               rotation: int,
                               fontsize: int) -> None:

        """
        Optimize x-axis labels for readability with many machines
        """

        logger.info(
        "Called optimize_x_axis_labels with \nax={}, \nmachines={}, \nrotation={}, \nfontsize={}", ax, machines, rotation, fontsize)

        n_machines = len(machines)

        # Show every nth label to avoid overlap
        if n_machines > 30:
            step = 2
        elif n_machines > 40:
            step = 3
        else:
            step = 1

        # Set ticks and labels
        tick_positions = range(len(machines))
        ax.set_xticks(tick_positions)

        if step > 1:
            labels = [machines[i] if i % step == 0 else '' for i in range(len(machines))]
            ax.set_xticklabels(labels, rotation=rotation, ha='right', fontsize=fontsize)
        else:
            ax.set_xticklabels(machines, rotation=rotation, ha='right', fontsize=fontsize)

    def sync_y_axes_optimized(ax, ax2) -> None:

        """
        Y Axis Synchronization - Optimized version
        """

        logger.info(
        "Called sync_y_axes_optimized with \nax={}, \nax2={}", ax, ax2)

        y1_min, y1_max = ax.get_ylim()
        y2_min, y2_max = ax2.get_ylim()

        # Simple alignment for positive values
        if y1_min >= 0 and y2_min >= 0:
            ax.set_ylim(0, y1_max * 1.05)
            ax2.set_ylim(0, y2_max * 1.05)
            return

        # Handle negative values efficiently
        if y1_min < 0 or y2_min < 0:
            zero_ratio_1 = abs(y1_min) / (y1_max - y1_min) if y1_min < 0 else 0
            zero_ratio_2 = abs(y2_min) / (y2_max - y2_min) if y2_min < 0 else 0
            target_zero_ratio = max(zero_ratio_1, zero_ratio_2)

            if target_zero_ratio > 0:
                # Vectorized calculation
                ranges = np.array([y1_max, y2_max]) / (1 - target_zero_ratio)
                new_mins = -ranges * target_zero_ratio

                ax.set_ylim(new_mins[0], y1_max * 1.05)
                ax2.set_ylim(new_mins[1], y2_max * 1.05)

    def create_legends_optimized(ax, ax2,
                                 n_machines: int) -> None:
      
        """
        Create optimized legends based on machine count
        """

        logger.info(
        "Called create_legends_optimized with \nax={}, \nax2={}, \nn_machines={}", ax, ax2, n_machines)
    
        handles1, labels1 = ax.get_legend_handles_labels()
        handles2, labels2 = ax2.get_legend_handles_labels()

        # Filter shot handles
        shot_handles = [(h, l) for h, l in zip(handles2, labels2) if 'Shot Shift' in l]

        # Adjust legend properties based on machine count
        if n_machines > 25:
            fontsize = 'small'
            framealpha = 0.8
        else:
            fontsize = 'medium'
            framealpha = 0.9

        legends = []

        # Mold count legend
        if handles1:
            legend1 = ax.legend(
                handles1,
                [f'Count S{label}' for label in labels1],  # Shortened labels
                loc='upper left',
                title='Mold Count',
                framealpha=framealpha,
                fontsize=fontsize
            )
            legends.append(legend1)

        # Shot legend
        if shot_handles:
            handles, labels = zip(*shot_handles)
            legend2 = ax2.legend(
                handles,
                [l.replace('Shot Shift', 'S') for l in labels],  # Shortened labels
                loc='upper right',
                title='Mold Shot',
                framealpha=framealpha,
                fontsize=fontsize
            )
            legends.append(legend2)

        # Add legends back
        for i, legend in enumerate(legends[:-1]):
            if i == 0:
                ax.add_artist(legend)

    # ---- Main Plot Logic ----

    # Prepare and validate data
    logger.debug("Prepare and validate data...")
    plot_data = prepare_plot_data(moldInfo_moldCount_merged_productRecords_df, moldShot_df)
    machines = plot_data['machines']
    shifts = plot_data['shifts']
    n_machines = plot_data['n_machines']
    n_shifts = plot_data['n_shifts']

    logger.debug("Plotting...")
    # Setup optimal layout based on machine count
    figsize, rotation, fontsize = setup_figure_layout(n_machines)

    # Calculate bar positions
    bar_info = calculate_bar_positions(n_machines, n_shifts)

    # Pre-compute shot data for performance
    shot_data = precompute_shot_data(moldShot_df, machines, shifts)

    # Create color palette
    if n_shifts == 1:
      colors = ['red']
    else:
      colors = generate_color_palette(n_shifts, palette_name=palette_name)

    # Setup figure and axes
    plt.style.use(sns_style)
    logger.info("Used Seabon style: {}. \nAnother supported styles: {}", sns_style, plt.style.available)
    fig, ax = plt.subplots(figsize=figsize)
    ax2 = ax.twinx()

    # Plot barplot with optimization
    sns.barplot(
        data=moldInfo_moldCount_merged_productRecords_df,
        x='machineNo',
        y='moldCount',
        hue='workingShift',
        palette=palette_name,
        ax=ax,
        edgecolor='black',
        linewidth=0.5 if n_machines <= 25 else 0.3
    )

    # Plot optimized scatter and trends
    plot_scatter_and_trends_optimized(
        ax2, shot_data, machines, shifts, colors, bar_info['bar_width']
    )

    # Configure axes with optimization
    ax.set_xlabel('Machine No', fontsize=fontsize, fontweight='bold')
    ax.set_ylabel('Mold Count', fontsize=fontsize, fontweight='bold', color='steelblue')
    ax2.set_ylabel('Mold Shot', fontsize=fontsize, fontweight='bold', color='red')

    # Optimize x-axis labels
    optimize_x_axis_labels(ax, machines, rotation, fontsize - 1)

    # Configure ticks
    ax.tick_params(axis='y', labelcolor='steelblue', labelsize=fontsize - 1)
    ax2.tick_params(axis='y', labelcolor='red', labelsize=fontsize - 1)

    # Grid optimization
    ax.grid(True, alpha=0.2 if n_machines > 25 else 0.3, axis='y')
    ax2.grid(False)

    # Sync Y axes
    sync_y_axes_optimized(ax, ax2)

    # Create optimized legends
    create_legends_optimized(ax, ax2, n_machines)

    # Title and layout
    title_fontsize = min(16, max(12, 20 - n_machines // 5))
    ax.set_title(
        f'Mold Analysis by Machine ({n_machines} machines)',
        fontsize=title_fontsize,
        fontweight='bold',
        pad=20
    )

    plt.tight_layout()
    plt.show()

    # Save with appropriate DPI based on size
    logger.debug("Saving plot...")
    dpi = 300 if n_machines <= 25 else 200
    save_plot(fig, file_path, dpi=dpi)