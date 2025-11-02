from agents.decorators import validate_dataframe
from agents.dashboardBuilder.visualize_data.utils import generate_color_palette, load_visualization_config
import pandas as pd
from loguru import logger
import matplotlib.pyplot as plt
from typing import Optional, Dict, Tuple

DEFAULT_CONFIG = {
    "colors": {
        'secondary': '#95A5A6',    # Gray
        'dark': '#2C3E50'          # Dark blue
    },
    "sns_style": "seaborn-v0_8",
    "palette_name": "muted",
    "figsize": None,
    "gridspec_kw": {
        'hspace': 0.3,
        'wspace': 0.3,
        'top': 0.92,
        'bottom': 0.05,
        'left': 0.08,
        'right': 0.95
    },
    "main_title_y": 0.96,    
    "subtitle_y": 0.945,     
}

def determine_plot_settings(n_machines: int, 
                            figsize_config: Optional[dict]) -> Tuple[int, int]:
        """Calculate optimal figure size based on number of machines."""
        n_cols = 2
        n_rows = (n_machines + n_cols - 1) // n_cols
        if figsize_config is None:
            # Calculate optimal layout based on number of machines
            if n_machines <= 9:
                base_figsize = (18, 32)
            elif n_machines <= 16:
                base_figsize = (20, 35)
            elif n_machines <= 25:
                base_figsize = (25, 40)
            elif n_machines <= 36:
                base_figsize = (30, 55)
            else:  # > 36 machine
                base_figsize = (35, 70)
        else:
            base_figsize = tuple(figsize_config)  # Use provided figsize
        return (n_cols, n_rows, base_figsize)

def preprocess_machine_data(df: pd.DataFrame, machines: list) -> Dict:
    """Preprocess data for all machines to optimize performance."""
    logger.debug(f"Preprocessing data for {len(machines)} machines...")
    
    # Group data by machine, shift and item at once
    grouped_data = df.groupby(['machineNo', 'workingShift', 'itemName']).agg({
        'itemTotalQuantity': 'sum',
        'itemGoodQuantity': 'sum'
    }).reset_index()
    
    machine_data_dict = {}
    for machine in machines:
        machine_summary = grouped_data[grouped_data['machineNo'] == machine]
        
        if machine_summary.empty:
            machine_data_dict[machine] = {
                'pivot_df': pd.DataFrame(),
                'good_by_shift': pd.Series(dtype=float)
            }
            continue
            
        # Create pivot table
        pivot_df = machine_summary.pivot_table(
            index='workingShift',
            columns='itemName',
            values='itemTotalQuantity',
            fill_value=0
        )
        
        # Calculate good quantity by shift
        good_by_shift = machine_summary.groupby('workingShift')['itemGoodQuantity'].sum()
        
        machine_data_dict[machine] = {
            'pivot_df': pivot_df,
            'good_by_shift': good_by_shift
        }
    
    return machine_data_dict

def shift_level_detailed_yield_efficiency_plotter(df: pd.DataFrame,
                                                  main_title: str = 'Manufacturing Performance Dashboard',
                                                  subtitle: str = 'Detailed Yield Efficiency by Machine & Shift',
                                                  visualization_config_path: Optional[str] = None
                                                  ) -> None:

    """
    Automatically selects the appropriate chart type based on the number of machines

    Args:
        df: DataFrame containing item-based records
        main_title: Main chart title
        subtitle: Chart subtitle
        visualization_config_path: Path to JSON config file

    Returns:
        matplotlib.figure.Figure: The created figure
    """

    # Valid data frame
    required_columns = ['machineNo', 'workingShift', 'itemName', 'itemTotalQuantity', 'itemGoodQuantity']
    validate_dataframe(df, required_columns)

    # Load visualization config
    visualization_config = load_visualization_config(DEFAULT_CONFIG, visualization_config_path)

    # Set style
    plt.style.use(visualization_config['sns_style'])
    logger.info('Used Seaborn style: {}.\nAvailable styles: {}', visualization_config['sns_style'], plt.style.available)

    # # Group by machine and sort
    machines = sorted(df['machineNo'].unique())
    n_machines = len(machines)
    
    # Use passed figsize or automatic figsize
    n_cols, n_rows, final_figsize = determine_plot_settings(n_machines, visualization_config["figsize"])

    # Optimization: Preprocess data once for all machines
    logger.debug("Processing data for {} machines...", n_machines)

    # Group data by machine, shift and item at once
    grouped_data = df.groupby(['machineNo', 'workingShift', 'itemName']).agg({
        'itemTotalQuantity': 'sum',
        'itemGoodQuantity': 'sum'
    }).reset_index()

    # Create a dictionary to quickly access data by machine
    machine_data_dict = preprocess_machine_data(grouped_data, machines)

    logger.debug('Plotting...')
    # Optimize colormap - create once for all
    max_items = max([len(data['pivot_df'].columns) for data in machine_data_dict.values()] + [1])
    colors = generate_color_palette(max_items, palette_name=visualization_config['palette_name'])

    # Create figures and axes
    plt.style.use(visualization_config['sns_style'])
    logger.info('Used Seabon style: {}. \nAnother supported styles: {}', visualization_config['sns_style'], plt.style.available)
    fig, axes = plt.subplots(n_rows, n_cols, figsize=final_figsize,
                            gridspec_kw=visualization_config['gridspec_kw'])

    # Add main title with all information
    # Combine title and subtitle
    fig.suptitle(f'{main_title}',
                fontsize=18, fontweight='bold', y=visualization_config['main_title_y'], 
                color=visualization_config['colors']['dark'])

    # Add subtitle
    fig.text(0.5, visualization_config['subtitle_y'], f'{subtitle}',
            ha='center', fontsize=11, style='italic', 
            color=visualization_config['colors']['secondary'])

    # Handling case with only 1 row
    if n_rows == 1:
        axes = axes.reshape(1, -1)
    elif n_cols == 1:
        axes = axes.reshape(-1, 1)

    # Draw a graph for each machine
    for idx, machine in enumerate(machines):
        row = idx // n_cols
        col = idx % n_cols
        ax = axes[row, col] if n_rows > 1 else axes[col]

        data = machine_data_dict[machine]
        pivot_df = data['pivot_df']
        good_by_shift = data['good_by_shift']

        # Draw stacked bars if there is data
        if not pivot_df.empty:
            # Use pre-created colormap
            current_colors = colors[:len(pivot_df.columns)]
            pivot_df.plot(kind='bar', stacked=True, ax=ax,
                        color=current_colors, alpha=0.8, legend=False)

            # Draw good quantity line
            if not good_by_shift.empty:
                x_positions = range(len(good_by_shift))
                ax.plot(x_positions, good_by_shift.values,
                    color='green', marker='o', linewidth=1, markersize=4,
                    label='Good Qty', zorder=5)

        # Optimize formatting
        ax.set_title(f'{machine}', fontsize=14, fontweight='bold', pad=10)
        ax.set_xlabel('Shift', fontsize=10)
        ax.set_ylabel('Quantity', fontsize=10)

        # Optimize legend - only show when needed
        if not pivot_df.empty and len(pivot_df.columns) <= 5:
            ax.legend(fontsize=11, loc='lower right')
        elif not good_by_shift.empty:
            ax.legend(['Good Qty'], fontsize=11, loc='lower right')

        # Optimize grid and tick labels
        ax.grid(True, alpha=0.2, linestyle='--', axis='y', color='gray', linewidth=0.5)
        ax.tick_params(axis='both', which='major', labelsize=11)

        # Keep labels horizontal (0 degree rotation)
        if not pivot_df.empty:
            plt.setp(ax.get_xticklabels(), rotation=0, ha='center')

    # Hide empty subplots
    total_subplots = n_rows * n_cols
    for idx in range(n_machines, total_subplots):
        row = idx // n_cols
        col = idx % n_cols
        ax_to_hide = axes[row, col] if n_rows > 1 else axes[col]
        ax_to_hide.set_visible(False)

    # Optimize layout with appropriate padding
    plt.tight_layout(rect=[0, 0.02, 1, 0.96])

    return fig