from agents.dashboardBuilder.plotters.utils import lighten_color, format_value_short, load_visualization_config
from agents.dashboardBuilder.plotters.year_level.utils import process_mold_based_data

import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from typing import List, Optional
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

def mold_based_year_view_dashboard_plotter(df: pd.DataFrame,
                                           visualization_metric: List,
                                           fig_title: str,
                                           visualization_config_path: Optional[str] = None
                                           ) -> plt.Figure:
    """
    Plot a multi-metric production dashboard for each mold based on yearly data.

    Parameters
    ----------
    df : pd.DataFrame
        Input dataframe containing mold-based production data.
    fig_title : str
        Title of the dashboard figure.
    visualization_metric:
        List of metric to visualize.
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
    plt.rcParams['figure.figsize'] = (16, 16)

    sizes = visualization_config["sizes"]
    colors = visualization_config["colors"]
    
    # Create subplot grid (1 column × N metrics)
    n_cols = 1
    n_rows = len(visualization_metric)
    
    fig, axes = plt.subplots(n_rows, n_cols)
    axes = axes.flatten()

    # Set main title
    fig.suptitle(f'{fig_title}',
                 fontsize=sizes["title"],
                 fontweight='bold',
                 y=visualization_config["main_title_y"],
                 color=colors["title"])
    
    # Add subtitle
    metrics_str = ', '.join(visualization_metric)
    subtitle = f'Metrics: {metrics_str}'
    fig.text(0.5, 
            visualization_config['subtitle_y'], 
            f'{subtitle}', 
            ha='center', 
            fontsize=sizes["suptitle"], 
            style='italic', 
            color=colors["subtitle"])
    
    # Data processing
    # Aggregate and prepare data grouped by mold
    combined_summary = process_mold_based_data(df, group_by_month=False)
    molds = combined_summary['moldNo'].tolist()
    mold_index_map = {mold: idx + 1 for idx, mold in enumerate(molds)}

    # Valid metrics
    validate_dataframe(combined_summary, visualization_metric)

    # Define base color palette for molds
    base_colors = base_colors = sns.color_palette(visualization_config["sns_palette"], len(molds))
    mold_colors = [lighten_color(c, 0.1) for c in base_colors]

    # Iterate through each metric subplot
    for i, metric in enumerate(visualization_metric):
        ax = axes[i]
        ax.set_facecolor("#FAFAFA")

        # Extract metric values by mold
        vals = []
        for mold in molds:
            row = combined_summary[combined_summary['moldNo'] == mold]
            val = row[metric].iloc[0] if not row.empty else 0
            vals.append(val)

        # Define metric range and bar positions
        metric_max = max(vals) or 1
        metric_min = min(vals) or 0
        x_pos = np.arange(len(molds))

        # Draw bars
        bars = ax.bar(x_pos, vals,
                      width=0.9,
                      color=mold_colors,
                      edgecolor='white',
                      linewidth=1.0,
                      alpha=0.9,
                      zorder=3)

        # Highlight max/min reference lines
        if metric_max > 0:
            ax.hlines(metric_max, 
                      xmin=-0.5, 
                      xmax=len(molds)-0.5,
                      color="#DDD", 
                      linestyle='-.', 
                      linewidth=1, 
                      zorder=5)
        if metric_min > 0:
            ax.hlines(metric_min, 
                      xmin=-0.5, 
                      xmax=len(molds)-0.5,
                      color="#DDD", 
                      linestyle='--', 
                      linewidth=1, 
                      zorder=5)

        rotation = 30 if metric == 'totalShots' else 0
        ha = 'left' if metric == 'totalShots' else 'center'

        # Display value labels on top of bars
        for bar, val in zip(bars, vals):
            if val > metric_max * 0.01:
                label = format_value_short(val)
                color = '#C0392B' if val == metric_min else '#333'
                ax.text(bar.get_x() + bar.get_width()/2, val,
                        label, ha=ha, va='bottom',
                        fontsize=sizes["text"], 
                        color=color, 
                        zorder=4, 
                        rotation=rotation,
                        path_effects=[pe.withStroke(linewidth=2, 
                                                    foreground="white")])

        # Set axis labels and title
        ax.set_title(metric, 
                     fontweight='bold', 
                     fontsize=sizes["suptitle"],
                     pad=7, 
                     color="#222")
        ax.set_ylim(0, metric_max * 1.2)
        ax.set_xticks(x_pos)
        ax.set_xticklabels([mold_index_map[mold] for mold in molds], 
                           fontsize=sizes["xlabel"])
        ax.set_yticks([])

        # Grid and border styling
        ax.grid(axis='x', color='#eee', linewidth=0.8, zorder=0)
        ax.grid(axis='y', color='#eee', linewidth=0.8, zorder=0)
        for spine in ['top', 'right', 'left']:
            ax.spines[spine].set_visible(False)
        ax.spines['bottom'].set_color('#CCC')

    # Create legend mapping (index) → moldNo
    legend_elements = [
        plt.Rectangle((0, 0), 1, 1,
                      facecolor=color,
                      edgecolor='white',
                      linewidth=0.8,
                      label=f"({mold_index_map[mold]})-{mold}")
        for mold, color in zip(molds, mold_colors)
    ]
    fig.legend(handles=legend_elements,
               loc='lower center',
               bbox_to_anchor=(0.5, -0.12),
               ncol=min(len(molds), int(np.ceil(len(molds)/10))),
               fontsize=sizes["legend"],
               frameon=False,
               handlelength=1.2,
               handletextpad=0.4,
               columnspacing=0.8)

    # Final layout adjustment
    plt.tight_layout()

    return combined_summary, fig