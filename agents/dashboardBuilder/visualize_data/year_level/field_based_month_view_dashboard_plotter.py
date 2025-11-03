from agents.dashboardBuilder.visualize_data.utils import lighten_color, format_value_short
from agents.dashboardBuilder.visualize_data.year_level.utils import process_mold_based_data, process_machine_based_data
from agents.dashboardBuilder.visualize_data.utils import load_visualization_config

import seaborn as sns
import matplotlib.pyplot as plt
from typing import List, Optional
from matplotlib.patches import Rectangle
import numpy as np
import pandas as pd
from agents.decorators import validate_dataframe
from loguru import logger

# Default config for visualization
DEFAULT_CONFIG = {
    "sns_style": "seaborn-v0_8-darkgrid",
    "sns_palette": "Set2",
    "sns_set_style": "whitegrid",
    "plt_rcParams_update": {
        "figure.facecolor": "#f8f9fa",
        "axes.facecolor": "white",
        "axes.edgecolor": "#dee2e6",
        "axes.labelcolor": "#495057",
        "text.color": "#495057",
        "xtick.color": "#495057",
        "ytick.color": "#495057",
        "grid.color": "#e9ecef",
        "grid.linewidth": 0.8,
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "DejaVu Sans"],
        "font.size": 10
    },
    "layout_params": {
        "hspace": 0.75,
        "wspace": 0.3,
        "top": 0.96,
        "bottom": 0.06,
        "left": 0.06,
        "right": 0.97
    },
    "row_nums": 10,
    "column_nums": 3,
    "palette_name": "muted",
    "color_nums": 30,
    "colors": {
        "title": "#2c3e50",
        "text": "#718096",
        "subtitle": "#3c4a5b",
    },
    "sizes": {
        "title": 18,
        "suptitle": 12,
        "progress_text": 30,
        "ylabel": 9,
        "xlabel": 9,
        "legend": 8,
        "text": 7
        },
    "main_title_y": 1.02,
    "subtitle_y": 1.01
    }

AVAILABLE_METRICS = {
        'machineCode': [
            'poNums', 'itemNums', 'moldNums', 'itemComponentNums', 'avgNGRate',
            'workingDays', 'notProgressDays', 'workingShifts', 'notProgressShifts',
            'totalQuantity', 'goodQuantity', 'totalMoldShot'
            ], 
        'moldNo':[
            'totalShots', 'cavityNums', 'avgCavity', 'machineNums', 'totalNGRate',
            'totalQuantity', 'goodQuantity', 'totalNG'
        ]
    }

AVAILABLE_FIELDS = {'machineCode': 'Machine', 'moldNo': 'Mold'}

# Metrics that need to be scaled down
LARGE_METRICS = {
    'totalQuantity': 10000,
    'goodQuantity': 10000,
    'totalMoldShot': 10000,
    'totalNG': 1000,
    'totalShots': 1000
    }

def field_based_month_view_dashboard_plotter(df: pd.DataFrame,
                                             visualization_metric: List,
                                             fig_title: str,
                                             field: str = 'machineCode',
                                             subfig_per_page: int = 10,
                                             visualization_config_path: Optional[str] = None
                                             ) -> plt.Figure:
    """
    Create a paginated dashboard with multiple metrics per field value.

    Args:
        df: Input DataFrame
        fig_title: Title for the figure
        metric: List of metrics to plot
        field: Field to group by - supports 'machineCode' or 'moldNo'
        subfig_per_page: Number of subfigures per page

    Returns:
        Last generated figure object
    """

    # Validate field parameter
    if field not in ['machineCode', 'moldNo']:
        raise ValueError(f"Field must be 'machineCode' or 'moldNo', got '{field}'")
    
    # Valid data frame
    required_columns = ['recordDate', 'workingShift', 'machineNo', 'machineCode', 'itemCode',
                        'itemName', 'colorChanged', 'moldChanged', 'machineChanged', 'poNote',
                        'moldNo', 'moldShot', 'moldCavity', 'itemTotalQuantity',
                        'itemGoodQuantity', 'itemBlackSpot', 'itemOilDeposit', 'itemScratch',
                        'itemCrack', 'itemSinkMark', 'itemShort', 'itemBurst', 'itemBend',
                        'itemStain', 'otherNG', 'plasticResin', 'plasticResinCode',
                        'plasticResinLot', 'colorMasterbatch', 'colorMasterbatchCode',
                        'additiveMasterbatch', 'additiveMasterbatchCode', 'recordMonth']
    validate_dataframe(df, required_columns)

    # Load visualization config
    visualization_config = load_visualization_config(DEFAULT_CONFIG, visualization_config_path)

    # Visualization style settings
    plt.style.use(visualization_config["sns_style"])
    logger.info('Used Seaborn style: {}.\nAvailable styles: {}', visualization_config['sns_style'], plt.style.available)

    plt.rcParams['font.size'] = visualization_config["plt_rcParams_update"]["font.size"]

    sizes = visualization_config["sizes"]
    colors = visualization_config["colors"]

    # Determine label for the field
    field_label = AVAILABLE_FIELDS[field]

    # Use the parameter name consistently
    ITEMS_PER_PAGE = subfig_per_page

    # Data processing
    if field == 'machineCode':
        combined_summary = process_machine_based_data(df, group_by_month=True).reset_index()
    else:
        combined_summary = process_mold_based_data(df, group_by_month=True)

    field_values = combined_summary[field].drop_duplicates().tolist()

    # Metrics processing
    metrics = [metric for metric in visualization_metric if metric in AVAILABLE_METRICS[field]]
    if len(metrics) < len(visualization_metric):
        not_available_metrics = [metric for metric in visualization_metric if metric not in AVAILABLE_METRICS[field]]
        logger.warning("There is {} not-available metrics: {}", len(not_available_metrics), not_available_metrics)

    # Validate metrics
    validate_dataframe(combined_summary, metrics)

    # Colors for each metric
    metric_colors = sns.color_palette(visualization_config["sns_palette"], len(metrics))

    # ---- Create month list ----
    if len(combined_summary) > 0:
        # Extract year from recordMonth (assuming format 'YYYY-MM')
        combined_summary['year'] = combined_summary['recordMonth'].str[:4]

        # Determine target year (most common year or latest year)
        target_year = combined_summary['year'].mode()[0] if len(
            combined_summary['year'].mode()) > 0 else combined_summary['year'].max()

        # Always generate 12 months for the target year
        start_date = pd.Timestamp(year=int(target_year), month=1, day=1)
        end_date = pd.Timestamp(year=int(target_year), month=12, day=1)

        # Extend if data exists outside the target year
        other_year_data = combined_summary[combined_summary['year'] != target_year]
        if len(other_year_data) > 0:
            data_min = pd.to_datetime(other_year_data['recordMonth'].min() + '-01')
            data_max = pd.to_datetime(other_year_data['recordMonth'].max() + '-01')

            if data_min < start_date:
                start_date = data_min.replace(day=1)
            if data_max > end_date:
                end_date = data_max.replace(day=1)
    else:
        # Default to current year if no data
        target_year = str(pd.Timestamp.now().year)
        start_date = pd.Timestamp(year=int(target_year), month=1, day=1)
        end_date = pd.Timestamp(year=int(target_year), month=12, day=1)

    # Generate the full month range
    months_full = pd.date_range(start=start_date,
                                end=end_date,
                                freq='MS')
    months = months_full.strftime('%Y-%m').tolist()

    # ===== PAGINATION LOOP =====
    total_items = len(field_values)
    total_pages = (total_items + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
    figs = []

    for page_num in range(total_pages):
        # Calculate item range for this page
        start_idx = page_num * ITEMS_PER_PAGE
        end_idx = min((page_num + 1) * ITEMS_PER_PAGE, total_items)
        item_group = field_values[start_idx:end_idx]
        n_items_in_group = len(item_group)

        # Print progress
        logger.info(f"Generating Page {page_num + 1}/{total_pages}")
        logger.info(f"{field_label}s: {', '.join(map(str, item_group))}")
        logger.info(f"Range: {start_idx + 1} to {end_idx} of {total_items}")

        # Calculate figure size for this page
        # Use ITEMS_PER_PAGE for consistent height, add extra space for title/legend
        subplot_height = 2.5
        fig_height = ITEMS_PER_PAGE * subplot_height
        fig_width = len(months) * 0.8 if len(months) > 15 else 15

        # Create figure for this page
        fig, axes = plt.subplots(ITEMS_PER_PAGE, 1,  # Always create ITEMS_PER_PAGE subplots
                                figsize=(fig_width, fig_height),
                                sharex=True,
                                squeeze=False)

        for idx in range(n_items_in_group, ITEMS_PER_PAGE):
            axes[idx, 0].set_visible(False)

        # Title with page info
        metrics_str = ', '.join(metrics)
        fig.suptitle(f'{fig_title}',
                    fontsize=sizes["title"],
                    fontweight='bold',
                    y=visualization_config["main_title_y"],
                    color=colors["title"])
        fig.text(0.5, 
                 visualization_config['subtitle_y'],
                 f'Metrics: {metrics_str}\nPage {page_num + 1}/{total_pages} | {field_label}s {start_idx + 1}-{end_idx}',
                 fontsize=sizes["suptitle"],
                 color=colors["subtitle"],
                 style='italic', 
                 ha='center',
                 va='top')

        # Calculate bar width and spacing
        n_metrics = len(metrics)
        bar_width = 0.25
        metric_group_width = n_metrics * bar_width
        month_gap = 0.3

        # Position for each month group
        x_pos_months = np.arange(len(months)) * (metric_group_width + month_gap)

        # Plot each item in this page
        for local_idx, item_value in enumerate(item_group):
            ax = axes[local_idx, 0]

            # Filter data for this item
            item_data = combined_summary[combined_summary[field] == item_value]

            # Calculate max values for each metric FOR THIS ITEM across all months
            item_metric_max = {}
            for metric in metrics:
                item_values = []
                for month in months:
                    month_data = item_data[item_data['recordMonth'] == month]
                    if len(month_data) > 0:
                        item_values.append(month_data[metric].values[0])

                if len(item_values) > 0:
                    max_val = max(item_values)
                    # Apply scaling to large metrics
                    if metric in LARGE_METRICS:
                        item_metric_max[metric] = max_val / LARGE_METRICS[metric]
                    else:
                        item_metric_max[metric] = max_val
                else:
                    item_metric_max[metric] = 0

            # Get scaled values for visualization
            scaled_data = {}
            actual_data = {}
            max_scaled_value = 0

            for metric in metrics:
                values = []
                actual_values = []
                for month in months:
                    month_data = item_data[item_data['recordMonth'] == month]
                    if len(month_data) > 0:
                        actual_val = month_data[metric].values[0]
                        actual_values.append(actual_val)
                        # Scale down large metrics
                        if metric in LARGE_METRICS:
                            values.append(actual_val / LARGE_METRICS[metric])
                        else:
                            values.append(actual_val)
                    else:
                        # No data for this month
                        values.append(0)
                        actual_values.append(0)

                scaled_data[metric] = values
                actual_data[metric] = actual_values
                if len(values) > 0:
                    max_scaled_value = max(max_scaled_value, max(values))

            # Draw background boxes (light colors) - using SAME height across all months
            for metric_idx, (metric, color) in enumerate(zip(metrics, metric_colors)):
                offset = metric_idx * bar_width
                light_color = lighten_color(color, 0.6)
                bg_height = item_metric_max[metric]  # Same height for all months!

                # Only draw background if there's data for this metric
                if bg_height > 0:
                    for month_idx, month in enumerate(months):
                        rect = Rectangle(
                            (x_pos_months[month_idx] + offset - bar_width/2, 0),
                            bar_width,
                            bg_height,  # Same height across all months
                            facecolor=light_color,
                            edgecolor='white',
                            linewidth=0.5,
                            alpha=0.8,
                            zorder=1
                        )
                        ax.add_patch(rect)

            # Set y-axis limit with some padding (use max from all metrics)
            y_max = max(item_metric_max.values()) if item_metric_max.values() else 1

            # Draw dashed horizontal lines at max value for each metric
            for metric_idx, (metric, color) in enumerate(zip(metrics, metric_colors)):
                max_val = item_metric_max[metric]
                if max_val > 0:
                    ax.hlines(
                        y=max_val,
                        xmin=x_pos_months[0] - month_gap/2,
                        xmax=x_pos_months[-1] + metric_group_width + month_gap/2,
                        colors=color,
                        linestyles='--',
                        linewidth=0.8,
                        alpha=0.7,
                        zorder=2
                    )

            # Draw actual bars with values
            for metric_idx, (metric, color) in enumerate(zip(metrics, metric_colors)):
                offset = metric_idx * bar_width
                values = scaled_data[metric]
                actual_values = actual_data[metric]

                bars = ax.bar(x_pos_months + offset,
                              values,
                              bar_width,
                              color=color,
                              edgecolor='white',
                              linewidth=0.8,
                              hatch='///',
                              zorder=3)

                # Add value labels
                for bar, actual_val, scaled_val in zip(bars, actual_values, values):
                    # Use metric-specific max instead of overall max
                    metric_max = item_metric_max[metric]
                    threshold = metric_max * 0.05 if metric_max > 0 else 0
                    # Only show label if bar is visible enough   
                    if scaled_val > threshold and scaled_val > 0:       
                        # Format number
                        label = format_value_short(actual_val, decimal=1)
                        ro = 30 if metric in LARGE_METRICS else 0  
                        ax.text(bar.get_x() + bar.get_width()/2,
                                scaled_val,
                                label,
                                ha='center', va='bottom',
                                fontsize=sizes["text"],
                                rotation=ro,
                                color='#333333',
                                zorder=4)

            # Draw vertical separators between month groups
            for month_idx in range(1, len(months)):
                separator_x = x_pos_months[month_idx] - month_gap/2
                ax.axvline(x=separator_x,
                          color='#CCCCCC',
                          linestyle='-.',
                          linewidth=1.1,
                          alpha=0.6,
                          zorder=2)

            # Configure axis
            ax.set_ylabel(f'{item_value}',
                          fontsize=sizes["ylabel"],
                          fontweight='bold',
                          rotation=0,
                          ha='right',
                          va='center')
            ax.set_ylim(0, y_max * 1.2)
            ax.set_xlim(x_pos_months[0] - month_gap/2,
                        x_pos_months[-1] + metric_group_width + month_gap/2)

            # Remove y-ticks since we're showing actual values on bars
            ax.set_yticks([])
            ax.grid(False)

            # Hide spines
            for spine in ['top', 'right', 'left']:
                ax.spines[spine].set_visible(False)
            ax.spines['bottom'].set_color('#CCCCCC')

            # Only show x-axis labels on bottom plot
            if local_idx == n_items_in_group - 1:
                ax.set_xticks(x_pos_months + metric_group_width/2 - bar_width/2)
                ax.set_xticklabels(months, rotation=0)
            else:
                ax.set_xticks([])

        # Create legend
        legend_elements = [plt.Rectangle((0,0),1,1,
                                         facecolor=color,
                                         edgecolor='white',
                                         linewidth=0.8,
                                         hatch='///',
                                         label=metric)
                          for metric, color in zip(metrics, metric_colors)]

        fig.legend(handles=legend_elements,
                  loc='upper center',
                  bbox_to_anchor=(0.5, 0.985),
                  ncol=len(metrics),
                  fontsize=sizes["legend"],
                  frameon=False)

        plt.tight_layout()
        plt.subplots_adjust(top=0.96)

        logger.info(f"Page {page_num + 1} completed")

        figs.append(fig)

    logger.info(f"All {total_pages} pages generated successfully!")

    return combined_summary, figs