from agents.decorators import validate_dataframe
from agents.dashboardBuilder.visualize_data.utils import generate_color_palette, load_visualization_config
import pandas as pd
from loguru import logger
import matplotlib.pyplot as plt

DEFAULT_CONFIG = {
    "colors": {
        "secondary": "#95A5A6",
        "dark": "#2C3E50"
    },
    "sns_style": "seaborn-v0_8",
    "palette_name": "muted",
    "figsize": {
        "s": [14, 8],
        "m": [18, 10],
        "l": [22, 12],
        "xl": [26, 14]
        },
    "gridspec_kw": {
        'hspace': 0.4,
        'wspace': 0.3,
        'top': 0.85,
        'bottom': 0.15,
        'left': 0.08,
        'right': 0.95
        },
    "main_title_y": 0.96,
    "subtitle_y": 0.90,
    "summary_y": 0.04
}

def calculate_efficiency_metrics(df: pd.DataFrame) -> tuple:
    """Calculate efficiency metrics from the dataframe."""
    # Aggregate item quantities per machine and item
    df_agg = df.groupby(['machineNo', 'itemName'])[['itemTotalQuantity', 'itemGoodQuantity']].sum().reset_index()
    
    pivot_df = df_agg.pivot_table(
        index='machineNo',
        columns='itemName',
        values='itemTotalQuantity',
        aggfunc='sum',
        fill_value=0
    )

    # Compute total and good quantities per machine
    total_qty = df_agg.groupby('machineNo')['itemTotalQuantity'].sum()
    good_qty = df_agg.groupby('machineNo')['itemGoodQuantity'].sum()

    # Calculate efficiency rate (%) with zero division protection
    efficiency_rate = ((good_qty / total_qty.replace(0, 1)) * 100).round(1)
    efficiency_rate = efficiency_rate.where(total_qty > 0, 0)

    return pivot_df, total_qty, good_qty, efficiency_rate

def determine_plot_settings(num_machines: int, figsize_config: dict) -> tuple:
    """Determine appropriate plot settings based on data size."""
    # Figure size
    if num_machines <= 15:
        figsize = figsize_config["s"]
    elif num_machines <= 25:
        figsize = figsize_config["m"]
    elif num_machines <= 35:
        figsize = figsize_config["l"]
    else:
        figsize = figsize_config["xl"]
    
    # Other responsive settings
    bar_width = max(0.4, min(0.8, 12 / num_machines))
    marker_size = max(4, min(8, 80 / num_machines))
    font_size = max(8, min(12, 120 / num_machines))
    annotation_spacing = max(10, min(20, 200 / num_machines))
    
    return figsize, bar_width, marker_size, font_size, annotation_spacing

def machine_level_yield_efficiency_plotter(df: pd.DataFrame,
                                           main_title: str = 'Manufacturing Performance Dashboard',
                                           subtitle: str = 'Yield Efficiency by Machine',
                                           visualization_config_path: str = None,
                                           ) -> plt.Figure:
    """
    Create a yield efficiency chart per machine, showing stacked item quantity and good item trend line.
    
    Args:
        df: DataFrame with columns ['machineNo', 'itemName', 'itemTotalQuantity', 'itemGoodQuantity']
        main_title: Main chart title
        subtitle: Chart subtitle
        visualization_config_path: Path to custom config JSON file
        
    Returns:
        matplotlib Figure object
    """
    
    # Valid data frame
    required_columns = ['recordDate', 'workingShift', 'machineNo', 'machineCode', 'itemCode',
                        'itemName', 'colorChanged', 'moldChanged', 'machineChanged', 'poNo',
                        'moldNo', 'moldShot', 'moldCavity', 'itemTotalQuantity',
                        'itemGoodQuantity', 'itemBlackSpot', 'itemOilDeposit', 'itemScratch',
                        'itemCrack', 'itemSinkMark', 'itemShort', 'itemBurst', 'itemBend',
                        'itemStain', 'otherNG', 'plasticResin', 'plasticResinCode',
                        'plasticResinLot', 'colorMasterbatch', 'colorMasterbatchCode',
                        'additiveMasterbatch', 'additiveMasterbatchCode', 'itemQuantity',
                        'poETA', 'machineInfo', 'itemInfo', 'itemComponent', 'itemCount',
                        'moldCount', 'itemComponentCount', 'jobCount', 'lateStatus',
                        'changeType']
    validate_dataframe(df, required_columns)

    # Load visualization config
    visualization_config = load_visualization_config(DEFAULT_CONFIG, visualization_config_path)
    
    logger.debug("Processing dataframe with shape: {}", df.shape)
    
    try:
        # Calculate efficiency metrics
        pivot_df, total_qty, good_qty, efficiency_rate = calculate_efficiency_metrics(df)
        
        num_machines = len(pivot_df)
        logger.debug("Number of machines: {}", num_machines)
        
        # Determine plot settings
        figsize, bar_width, marker_size, font_size, annotation_spacing = determine_plot_settings(
            num_machines, visualization_config["figsize"]
        )
        
        # Generate colors
        colors = generate_color_palette(num_machines, palette_name=visualization_config["palette_name"])
        
        logger.info(
            "Creating chart with: df.shape={}, machines={}, figsize={}",
            df.shape, num_machines, figsize
        )
        
        # Set style
        plt.style.use(visualization_config["sns_style"])
        fig, ax = plt.subplots(figsize=figsize,
                               gridspec_kw = {
                                  'hspace': 0.4,
                                  'wspace': 0.3,
                                  'top': 0.85,
                                  'bottom': 0.15,
                                  'left': 0.08,
                                  'right': 0.95
                                  })
                                
        # Calculate overall efficiency for title
        total_production = total_qty.sum()
        total_good = good_qty.sum()
        overall_efficiency = ((total_good / total_production) * 100).round(1) if total_production > 0 else 0
        
        # Add titles and summary
        fig.suptitle(main_title, fontsize=18, fontweight='bold', y=visualization_config['main_title_y'], 
                    color=visualization_config["colors"]["dark"])
        
        fig.text(0.5, visualization_config['subtitle_y'], subtitle, ha='center', fontsize=11, style='italic', 
                color=visualization_config["colors"]["secondary"])
        
        summary_info = f'Total Quantity: {int(total_production):,} | Good Quantity: {int(total_good):,} | Yield Efficiency: {overall_efficiency}%'
        fig.text(0.5, visualization_config['summary_y'], summary_info, ha='center', fontsize=11, style='italic', 
                color=visualization_config["colors"]["secondary"])
        
        # Plot stacked bar chart
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
        
        # Add efficiency rate annotations
        show_all_annotations = num_machines <= 25
        step = max(1, num_machines // 20) if not show_all_annotations else 1
        
        for i, (machine, rate) in enumerate(efficiency_rate.items()):
            if (show_all_annotations or i % step == 0) and not pd.isna(rate):
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
        max_legend_items = 15
        
        if len(handles) > max_legend_items:
            item_totals = pivot_df.sum().sort_values(ascending=False)
            top_items = item_totals.head(max_legend_items - 1).index.tolist()
            
            filtered_handles, filtered_labels = [], []
            for handle, label in zip(handles, labels):
                if label == 'itemGoodQuantity' or label in top_items:
                    filtered_handles.append(handle)
                    filtered_labels.append(label)
            handles, labels = filtered_handles, filtered_labels
        
        # Set legend
        legend_cols = min(3, max(1, len(labels) // 8))
        ax.legend(
            handles,
            labels,
            bbox_to_anchor=(1.02, 1),
            loc='upper left',
            frameon=True,
            fancybox=True,
            shadow=True,
            ncol=legend_cols,
            fontsize=max(8, font_size - 2)
        )
        
        # Set axis labels and formatting
        ax.set_ylabel('Item Quantity', fontsize=max(10, min(14, figsize[0] - 2)), fontweight='bold')
        ax.set_xlabel('Machine No', fontsize=max(10, min(14, figsize[0] - 2)), fontweight='bold')
        
        # X-axis formatting
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
        
        # Final layout
        plt.tight_layout()
        plt.subplots_adjust(bottom=0.15, top=0.88, right=0.85)
        
        logger.info("Chart created successfully")
        return fig
        
    except Exception as e:
        logger.error(f"Error creating chart: {e}")
        raise