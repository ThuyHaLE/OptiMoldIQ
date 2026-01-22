from agents.dashboardBuilder.plotters.utils import add_value_labels
from agents.dashboardBuilder.plotters.year_level.utils import process_machine_based_data
from agents.dashboardBuilder.plotters.utils import load_visualization_config

import matplotlib.pyplot as plt
from typing import Optional
import numpy as np
import pandas as pd
from agents.decorators import validate_dataframe
from loguru import logger

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
    "subtitle_y": 0.99
    }

def machine_based_year_view_dashboard_plotter(df: pd.DataFrame,
                                              fig_title: str,
                                              visualization_config_path: Optional[str] = None
                                              ) -> plt.Figure:
    """
    Plot a multi-metric production dashboard for each machine based on yearly data.

    Parameters
    ----------
    df : pd.DataFrame
        Input dataframe containing machine-based production data.
    fig_title : str
        Title of the dashboard figure.
    """

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
    plt.rcParams['figure.figsize'] = (18, 14)

    sizes = visualization_config["sizes"]
    
    # Create 3x3 subplot grid
    fig, axes = plt.subplots(3, 3, 
                             sharey='row')

    # Set main title
    fig.suptitle(f'{fig_title}',
                 fontsize=sizes["title"],
                 fontweight='bold',
                 y=visualization_config["main_title_y"],
                 color=visualization_config["colors"]["title"])
    
    # Data processing
    # Aggregate and prepare data grouped by machine
    combined_summary = process_machine_based_data(df, 
                                                  group_by_month=False)

    # Define x-axis positions and bar width
    x = np.arange(len(combined_summary))
    width = 0.35

    # Row 1: Working Days, Working Shifts, PO Numbers
    # (1,1) Working Days chart
    ax1 = axes[0, 0]
    ax1.barh(x + width/2, 
             combined_summary['notProgressDays'], 
             width,
             label='Not-progress', 
             color='salmon', 
             alpha=0.8)
    ax1.barh(x - width/2, 
             combined_summary['workingDays'], 
             width,
             label='In-progress',
             color='lightgreen', 
             alpha=0.8)
    ax1.set_title('Working Days', 
                  size = sizes["title"],
                  fontweight='bold')
    ax1.tick_params(axis='x', 
                    which='both', 
                    bottom=False, 
                    labelbottom=False)
    ax1.legend(loc='upper left', 
               bbox_to_anchor=(0, -0.05),
               ncol=2, 
               fontsize=sizes["legend"], 
               frameon=True)
    add_value_labels(ax1)

    # (1,2) Working Shifts chart
    ax2 = axes[0, 1]
    ax2.barh(x + width/2, 
             combined_summary['notProgressShifts'], 
             width,
             label='Not-progress', 
             color='salmon', 
             alpha=0.8)
    ax2.barh(x - width/2, 
             combined_summary['workingShifts'], 
             width,
             label='In-progress', 
             color='lightgreen',
             alpha=0.8)
    ax2.set_title('Total Working Shifts', 
                  size = sizes["title"], 
                  fontweight='bold')
    ax2.tick_params(axis='x', 
                    which='both', 
                    bottom=False, 
                    labelbottom=False)
    ax2.legend(loc='upper left', 
               bbox_to_anchor=(0, -0.05),
               ncol=2, 
               fontsize=sizes["legend"], 
               frameon=True)
    add_value_labels(ax2)

    # (1,3) PO Numbers chart
    ax3 = axes[0, 2]
    combined_summary['poNums'].plot(kind='barh', 
                                    ax=ax3, 
                                    color='lightcoral')
    ax3.set_title('Number of POs', 
                  size = sizes["title"],
                  fontweight='bold')
    ax3.tick_params(axis='x', 
                    which='both', 
                    bottom=False, 
                    labelbottom=False)
    add_value_labels(ax3)

    # Row 2: Total Quantity, Average NG Rate, Good vs Total Quantity
    # (2,1) Total Quantity chart
    ax4 = axes[1, 0]
    combined_summary['totalQuantity'].plot(kind='barh', 
                                           ax=ax4, 
                                           color='coral')
    ax4.set_title('Total Quantity Produced', 
                  size = sizes["title"],
                  fontweight='bold')
    ax4.set_ylabel('Machine Code')
    ax4.tick_params(axis='x', 
                    which='both', 
                    bottom=False, 
                    labelbottom=False)
    add_value_labels(ax4, short_format=True)

    # (2,2) Average NG Rate chart
    ax5 = axes[1, 1]
    combined_summary['avgNGRate'].plot(kind='barh', 
                                       ax=ax5, 
                                       color='tomato')
    ax5.set_title('Average NG Rate (%)', 
                  size = sizes["title"], 
                  fontweight='bold')
    ax5.tick_params(axis='x', 
                    which='both', 
                    bottom=False, 
                    labelbottom=False)
    add_value_labels(ax5, float_type=True)

    # (2,3) Good vs Total Quantity chart
    ax6 = axes[1, 2]
    ax6.barh(x - width/2, 
             combined_summary['totalQuantity'], 
             width,
             label='Total', 
             alpha=0.8, 
             color='coral')
    ax6.barh(x + width/2, 
             combined_summary['goodQuantity'], 
             width,
             label='Good', 
             alpha=0.8, 
             color='lightgreen')
    ax6.set_title('Good vs Total Quantity', 
                  size = sizes["title"],
                  fontweight='bold')
    ax6.tick_params(axis='x', 
                    which='both', 
                    bottom=False, 
                    labelbottom=False)
    ax6.legend(loc='upper left', 
               bbox_to_anchor=(0, -0.05),
               ncol=2, 
               fontsize=sizes['legend'], 
               frameon=True)
    add_value_labels(ax6, short_format=True)

    # Row 3: Mold Numbers, Item Components, Total Mold Shots
    #(3,1) Mold Numbers chart
    ax7 = axes[2, 0]
    combined_summary['moldNums'].plot(kind='barh', 
                                      ax=ax7, 
                                      color='mediumpurple')
    ax7.set_title('Number of Different Molds', 
                  size = sizes["title"],
                  fontweight='bold')
    ax7.set_ylabel('Machine Code')
    ax7.tick_params(axis='x', 
                    which='both', 
                    bottom=False, 
                    labelbottom=False)
    add_value_labels(ax7)

    #(3,2) Item Components chart
    ax8 = axes[2, 1]
    combined_summary['itemComponentNums'].plot(kind='barh', 
                                               ax=ax8, 
                                               color='teal')
    ax8.set_title('Number of Item Components', 
                  size = sizes["title"],
                  fontweight='bold')
    ax8.tick_params(axis='x', 
                    which='both', 
                    bottom=False, 
                    labelbottom=False)
    add_value_labels(ax8)

    #(3,3) Total Mold Shots chart
    ax9 = axes[2, 2]
    combined_summary['totalMoldShot'].plot(kind='barh', 
                                           ax=ax9, 
                                           color='mediumseagreen')
    ax9.set_title('Total Mold Shots', 
                  size = sizes["title"],
                  fontweight='bold')
    ax9.tick_params(axis='x', 
                    which='both', 
                    bottom=False, 
                    labelbottom=False)
    add_value_labels(ax9, short_format=True)

    #Final layout adjustment
    plt.tight_layout()

    return combined_summary, fig