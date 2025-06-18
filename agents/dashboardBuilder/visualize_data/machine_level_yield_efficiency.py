from agents.decorators import validate_init_dataframes
from agents.dashboardBuilder.visualize_data.utils import generate_color_palette, save_plot
import pandas as pd
from loguru import logger
import matplotlib.pyplot as plt


@validate_init_dataframes({"df": ['machineNo', 'itemName', 'itemTotalQuantity', 'itemGoodQuantity']})
def create_machine_level_yield_efficiency_chart(df: pd.DataFrame,
                                              file_path: str,
                                              sns_style: str = 'seaborn-v0_8',
                                              palette_name: str = "muted",
                                              figsize: tuple = None
                                              ) -> None:
    """
    Create a yield efficiency chart per machine, showing stacked item quantity and good item trend line.

    Parameters:
        df (pd.DataFrame): Input data with columns ['machineNo', 'itemName', 'itemTotalQuantity', 'itemGoodQuantity']
        file_path (str): Path to save the output chart
        sns_style (str): Seaborn style to use
        palette_name (str): Color palette name
        figsize (tuple): Optional figure size
    """

    logger.info(
        "Called create_machine_level_yield_efficiency_chart with \ndf.shape={}, \ncolumns={}, \nfile_path={}, \nsns_style={}, \npalette_name={}, \nfigsize={}",
        df.shape, list(df.columns), file_path, sns_style, palette_name, figsize)
    
    logger.debug("Dataframe processing...")
    # Aggregate item quantities per machine and item
    pivot_df = df.pivot_table(index='machineNo',
                              columns='itemName',
                              values='itemTotalQuantity',
                              aggfunc='sum',
                              fill_value=0
                              )

    # Compute total and good quantities per machine
    total_qty = df.groupby('machineNo')['itemTotalQuantity'].sum()
    good_qty = df.groupby('machineNo')['itemGoodQuantity'].sum()

    # Calculate efficiency rate (%)
    efficiency_rate = (good_qty / total_qty * 100).round(1)

    logger.debug("Plotting...")
    # Generate colors
    num_machines = len(pivot_df)
    colors = generate_color_palette(num_machines, palette_name=palette_name)

    # Determine figure size based on number of machines
    if figsize is None:
        if num_machines <= 15:
            figsize = (14, 8)
        elif num_machines <= 25:
            figsize = (18, 10)
        elif num_machines <= 35:
            figsize = (22, 12)
        else:
            figsize = (26, 14)

    # Set style
    plt.style.use(sns_style)
    logger.info('Used Seaborn style: {}.\nAvailable styles: {}', sns_style, plt.style.available)
    fig, ax = plt.subplots(figsize=figsize)

    # Plot stacked bar chart
    bar_width = max(0.4, min(0.8, 12 / num_machines))
    pivot_df.plot(
        kind='bar',
        stacked=True,
        ax=ax,
        color=colors,
        alpha=0.8,
        width=bar_width
    )

    # Plot good quantity trend line
    x_pos = range(len(good_qty))
    marker_size = max(4, min(8, 80 / num_machines))
    ax.plot(
        x_pos,
        good_qty.values,
        color='red',
        marker='o',
        linestyle='-',
        linewidth=2,
        markersize=marker_size,
        label='itemGoodQuantity',
        markerfacecolor='white',
        markeredgecolor='red',
        markeredgewidth=1.5
    )

    # Add annotations for efficiency rates
    font_size = max(8, min(12, 120 / num_machines))
    annotation_spacing = max(10, min(20, 200 / num_machines))
    show_all_annotations = num_machines <= 25
    step = max(1, num_machines // 20) if not show_all_annotations else 1

    for i, (machine, rate) in enumerate(efficiency_rate.items()):
        if show_all_annotations or i % step == 0:
            if not pd.isna(rate):
                ax.annotate(
                    f'{rate}%',
                    (i, good_qty.iloc[i]),
                    textcoords="offset points",
                    xytext=(0, annotation_spacing),
                    ha='center',
                    fontsize=font_size,
                    fontweight='bold',
                    bbox=dict(boxstyle="round,pad=0.2", facecolor='yellow', alpha=0.7)
                )

    # Handle legend for too many items
    handles, labels = ax.get_legend_handles_labels()
    short_labels = [
        label.replace('M', '') if label != 'itemGoodQuantity' else label
        for label in labels
    ]

    logger.debug("Original legend labels: {}", labels)
    logger.debug("Shortened legend labels: {}", short_labels)

    max_legend_items = 15
    if len(handles) > max_legend_items:
        item_totals = pivot_df.sum().sort_values(ascending=False)
        top_items = item_totals.head(max_legend_items - 1).index.tolist()

        logger.debug("Filtering legend to top {} items", max_legend_items)
        logger.debug("Top items: {}", top_items)

        filtered_handles, filtered_labels = [], []
        for handle, label in zip(handles, short_labels):
            if label == 'itemGoodQuantity' or label in top_items:
                filtered_handles.append(handle)
                filtered_labels.append(label)
        handles, short_labels = filtered_handles, filtered_labels

        if len(filtered_handles) < len(handles):
          logger.debug("Legend filtered from {} to {} items", len(handles), len(filtered_handles))

    # Set legend
    legend_cols = min(3, max(1, len(short_labels) // 8))
    ax.legend(
        handles,
        short_labels,
        bbox_to_anchor=(1.02, 1),
        loc='upper left',
        frameon=True,
        fancybox=True,
        shadow=True,
        ncol=legend_cols,
        fontsize=max(8, font_size - 2)
    )

    # Axis titles and labels
    ax.set_title(
        f'Yield Efficiency by Machine ({num_machines} machines)',
        fontsize=max(14, min(18, figsize[0])),
        fontweight='bold',
        pad=20
    )
    ax.set_ylabel('Item Quantity', fontsize=max(10, min(14, figsize[0] - 2)), fontweight='bold')
    ax.set_xlabel('Machine No', fontsize=max(10, min(14, figsize[0] - 2)), fontweight='bold')

    # X-axis label rotation and step control
    rotation_angle = 45 if num_machines <= 20 else 90
    label_step = max(1, num_machines // 30)

    ax.set_xticks(list(x_pos))
    if label_step > 1:
        tick_labels = [
            good_qty.index[i] if i % label_step == 0 else ''
            for i in range(len(good_qty.index))
        ]
        ax.set_xticklabels(tick_labels, rotation=rotation_angle, ha='right')
    else:
        ax.set_xticklabels(good_qty.index, rotation=rotation_angle, ha='right')

    ax.tick_params(axis='x', labelsize=max(8, font_size - 2))
    ax.tick_params(axis='y', labelsize=max(8, font_size - 2))
    ax.grid(True, alpha=0.3, linestyle='--')

    # Add overall efficiency summary
    total_production = total_qty.sum()
    total_good = good_qty.sum()
    overall_efficiency = (total_good / total_production * 100).round(1)

    fig.suptitle(
        f'Total Quantity: {int(total_production):,} | Good Quantity: {int(total_good):,} | '
        f'Yield Efficiency: {overall_efficiency}%',
        fontsize=max(10, min(14, figsize[0] - 4)),
        y=0.01
    )

    # Final layout tweaks
    plt.tight_layout()
    plt.subplots_adjust(bottom=0.12, right=0.85)
    plt.show()

    # Save figure with appropriate DPI
    logger.debug("Saving plot...")
    dpi = 300 if num_machines <= 25 else 400
    save_plot(fig, file_path, dpi=dpi)