from agents.decorators import validate_init_dataframes
from agents.dashboardBuilder.visualize_data.utils import generate_color_palette, save_plot
import pandas as pd
from loguru import logger
import matplotlib.pyplot as plt

@validate_init_dataframes({"df": ['machineNo', 'workingShift', 'itemName', 'itemTotalQuantity', 'itemGoodQuantity']})
def create_adapted_shift_level_yield_chart(df: pd.DataFrame,
                                file_path: str,
                                sns_style: str = 'seaborn-v0_8',
                                palette_name: str = 'muted',
                                figsize: tuple = None,
                                top_n: int = 15,
                                detailed_threshold: int = 25) -> None:

    """
    Automatically selects the appropriate chart type based on the number of machines

    Parameters:
        df (pd.DataFrame): Input data with columns ['machineNo', 'workingShift', 'itemName', 'itemTotalQuantity', 'itemGoodQuantity']
        file_path (str): Path to save the output chart
        sns_style (str): Seaborn style to use
        palette_name (str): Color palette name
        figsize (tuple): Optional figure size
        top_n (int): Top N machines by total output
        detailed_threshold (int): Optimize by adding overview chart when the number of machine > detailed_threshold
    """

    logger.info(
        "Called create_adapted_shift_level_yield_chart with \ndf.shape={}, \ncolumns={}, \nfile_path={}, \nsns_style={}, \npalette_name={}, \nfigsize={}, \ntop_n={}, \ndetailed_threshold={}",
        df.shape, list(df.columns), file_path, sns_style, palette_name, figsize, top_n, detailed_threshold)

    def create_summary_yield_chart(df: pd.DataFrame,
                                   file_path: str,
                                   top_n: int = 10) -> None:
        
        """
        Generate an overview chart for the top N machines with the highest output (for cases where there are too many machines)
        """

        logger.info(
        "Called create_summary_yield_chart with \ndf.shape={}, \ncolumns={}, \nfile_path={}, \ntop_n={}",
        df.shape, list(df.columns), file_path, top_n)

        logger.debug('Dataframe processing...')
        # Calculate total output by machine
        machine_totals = df.groupby('machineNo').agg({
            'itemTotalQuantity': 'sum',
            'itemGoodQuantity': 'sum'
        }).reset_index()

        # Calculate yield rate
        machine_totals['yield_rate'] = (
            machine_totals['itemGoodQuantity'] / machine_totals['itemTotalQuantity'] * 100
        ).round(2)
        
        logger.debug('Plotting...')
        # Get top N machines by total output
        top_machines = machine_totals.nlargest(top_n, 'itemTotalQuantity')

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

        # Yeild chart
        ax1.bar(top_machines['machineNo'], top_machines['itemTotalQuantity'],
              alpha=0.7, color='skyblue', label='Total Quantity')
        ax1.bar(top_machines['machineNo'], top_machines['itemGoodQuantity'],
              alpha=0.8, color='green', label='Good Quantity')
        ax1.set_title(f'Top {top_n} Machines by Production Volume', pad=20)
        ax1.set_xlabel('Machine No')
        ax1.set_ylabel('Quantity')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        plt.setp(ax1.get_xticklabels(), rotation=45)

        # Yield rate chart
        colors = ['red' if x < 90 else 'orange' if x < 95 else 'green' for x in top_machines['yield_rate']]
        ax2.bar(top_machines['machineNo'], top_machines['yield_rate'],
              color=colors, alpha=0.7)
        ax2.set_title(f'Yield Rate - Top {top_n} Machines', pad=20)
        ax2.set_xlabel('Machine No')
        ax2.set_ylabel('Yield Rate (%)')
        ax2.set_ylim(0, 100)
        ax2.grid(True, alpha=0.3)
        plt.setp(ax2.get_xticklabels(), rotation=45)

        # Add annotation
        for i, v in enumerate(top_machines['yield_rate']):
            ax2.text(i, v + 1, f'{v}%', ha='center', va='bottom', fontsize=8)

        plt.tight_layout()

        plt.show()

        logger.debug('Saving plot...')
        save_plot(fig, file_path, dpi=300)

    def create_detailed_yield_shift_chart(df: pd.DataFrame,
                                          file_path: str,
                                          sns_style: str = 'seaborn-v0_8',
                                          palette_name: str = 'muted',
                                          figsize: tuple = None) -> None:

        """
        Generate production analysis charts by machine and optimized work shifts for multiple machines (9-49 machines)
        """

        logger.info(
        "Called create_yield_shift_chart with \ndf.shape={}, \ncolumns={}, \nfile_path={}, \nsns_style={}, \npalette_name={}, \nfigsize={}",
        df.shape, list(df.columns), file_path, sns_style, palette_name, figsize)

        # # Group by machine and sort
        machines = sorted(df['machineNo'].unique())
        n_machines = len(machines)

        # Calculate optimal layout based on number of machines
        if n_machines <= 9:
            n_cols = 3
            base_figsize = (18, 12)
        elif n_machines <= 16:
            n_cols = 4
            base_figsize = (20, 16)
        elif n_machines <= 25:
            n_cols = 5
            base_figsize = (25, 20)
        elif n_machines <= 36:
            n_cols = 6
            base_figsize = (30, 24)
        else:  # > 36 machine
            n_cols = 7
            base_figsize = (35, 28)

        n_rows = (n_machines + n_cols - 1) // n_cols

        # Use passed figsize or automatic figsize
        final_figsize = figsize if figsize else base_figsize

        # Optimization: Preprocess data once for all machines
        logger.debug("Processing data for {} machines...", n_machines)

        # Group data by machine, shift and item at once
        grouped_data = df.groupby(['machineNo', 'workingShift', 'itemName']).agg({
            'itemTotalQuantity': 'sum',
            'itemGoodQuantity': 'sum'
        }).reset_index()

        # Create a dictionary to quickly access data by machine
        machine_data_dict = {}
        for machine in machines:
            machine_summary = grouped_data[grouped_data['machineNo'] == machine]

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

        logger.debug('Plotting...')
        # Optimize colormap - create once for all
        max_items = max([len(data['pivot_df'].columns) for data in machine_data_dict.values()] + [1])
        colors = generate_color_palette(max_items, palette_name=palette_name)

        # Create figures and axes
        plt.style.use(sns_style)
        logger.info('Used Seabon style: {}. \nAnother supported styles: {}', sns_style, plt.style.available)
        fig, axes = plt.subplots(n_rows, n_cols, figsize=final_figsize)

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
                          color='red', marker='o', linewidth=2, markersize=4,
                          label='Good Qty', zorder=5)

            # Optimize formatting
            ax.set_title(f'{machine}', fontsize=10, fontweight='bold', pad=10)
            ax.set_xlabel('Shift', fontsize=8)
            ax.set_ylabel('Quantity', fontsize=8)

            # Optimize legend - only show when needed
            if not pivot_df.empty and len(pivot_df.columns) <= 5:
                ax.legend(fontsize=6, loc='upper right')
            elif not good_by_shift.empty:
                ax.legend(['Good Qty'], fontsize=6, loc='upper right')

            # Optimize grid and tick labels
            ax.grid(True, alpha=0.2, linewidth=0.5)
            ax.tick_params(axis='both', which='major', labelsize=7)

            # Rotate labels if there are multiple shifts
            if not pivot_df.empty and len(pivot_df.index) > 3:
                plt.setp(ax.get_xticklabels(), rotation=45, ha='right')

        # Hide empty subplots
        total_subplots = n_rows * n_cols
        for idx in range(n_machines, total_subplots):
            row = idx // n_cols
            col = idx % n_cols
            ax_to_hide = axes[row, col] if n_rows > 1 else axes[col]
            ax_to_hide.set_visible(False)

        # Optimize title and layout
        title_fontsize = max(14, min(20, 20 - (n_machines - 9) * 0.2))
        plt.suptitle('Production Analysis by Machine and Shift',
                    fontsize=title_fontsize, fontweight='bold', y=0.01)

        # Optimize layout with appropriate padding
        plt.tight_layout(rect=[0, 0.02, 1, 0.96])

        plt.show()

        # Optimize DPI based on number of machines
        logger.debug('Saving plot...')
        dpi = 300 if n_machines <= 25 else 200  # Reduce DPI for smaller file size when multiple machines are involved
        save_plot(fig, file_path, dpi=dpi)


    # ---- Main Plot Logic ----
    n_machines = len(df['machineNo'].unique())
    if n_machines <= detailed_threshold:
        logger.debug("Create detailed plot for {} machines...", n_machines)
        # Plot detailed chart
        create_detailed_yield_shift_chart(df, f'{file_path}_detailed', sns_style, palette_name, figsize)
    else:
        logger.debug("Too many machines ({}). Create an overview chart...", n_machines)
        # Plot detailed and overview charts (with optimized layout) 
        create_detailed_yield_shift_chart(df, f'{file_path}_detailed', sns_style, palette_name, figsize)
        create_summary_yield_chart(df, f'{file_path}_summary', top_n=top_n)