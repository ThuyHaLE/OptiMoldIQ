from agents.decorators import validate_dataframe
import matplotlib.patches as mpatches
from typing import Dict
import pandas as pd

def plot_top_items_bar(ax, 
                       df: pd.DataFrame, 
                       colors: Dict, 
                       sizes: Dict):
    """
    Plot top 10 items by remaining quantity (horizontal bar)
    """

    subplot_title = 'Top 10 Items by Remaining Quantity'

    # Valid data frame
    required_columns = ['poNo', 'poETA', 'itemQuantity', 'itemGoodQuantity', 'itemNGQuantity',
                        'is_backlog', 'itemCodeName', 'proStatus', 'poStatus', 'moldHistNum',
                        'itemRemainQuantity', 'completionProgress', 'etaStatus',
                        'overAvgCapacity', 'overTotalCapacity', 'is_overdue', 'capacityWarning',
                        'capacitySeverity', 'capacityExplanation']
    validate_dataframe(df, required_columns)

    if df.empty:
        ax.text(0.5, 0.5, 'No data available', 
                ha='center', va='center', 
                fontsize=sizes['title'],
                color=sizes['title'])
        ax.set_title(subplot_title,
                    fontsize=sizes['title'],
                    color=colors['title'],
                    fontweight='bold')
        ax.axis('off')
        return
    
    top_items = df.nlargest(10, 'itemRemainQuantity')[
        ['poStatus', 'completionProgress', 'itemCodeName', 'itemRemainQuantity']
    ]

    top_items_statuses = top_items['poStatus'].unique().tolist()
    top_items_color_map = {
        status: colors['general'][i] 
        for i, status in enumerate(top_items_statuses)
    }
    top_items_colors_bar = [
        top_items_color_map[x] for x in top_items['poStatus']
    ]

    bars = ax.barh(
        range(len(top_items)),
        top_items['itemRemainQuantity'],
        color=top_items_colors_bar,
        edgecolor='white',
        linewidth=2.5,
        alpha=0.85
    )

    ax.set_yticks(range(len(top_items)))
    ax.set_yticklabels(
        [name[:50] + '...' if len(name) > 50 else name 
         for name in top_items['itemCodeName']],
        fontsize=9
    )
    ax.set_xlabel(
        'Remaining Quantity',
        fontsize=sizes['xlabel']
    )
    ax.set_title(
        subplot_title,
        fontsize=sizes['title'],
        fontweight='bold',
        pad=10,
        color=colors['title']
    )
    ax.invert_yaxis()
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(axis='x', alpha=0.3, linestyle='--')

    # Value labels
    for i, bar in enumerate(bars):
        width = bar.get_width()
        progress = top_items.iloc[i]['completionProgress']
        ax.text(
            width,
            bar.get_y() + bar.get_height()/2.,
            f'  {progress*100:.1f}% | {int(width):,}',
            ha='left', va='center',
            fontsize=sizes['text']
        )

    # Legend
    legend_handles = [
        mpatches.Patch(color=color, label=status.replace('_', ' ').title())
        for status, color in top_items_color_map.items()
    ]
    ax.legend(
        handles=legend_handles,
        bbox_to_anchor=(1.02, 1),
        loc='upper left',
        fontsize=sizes['legend'],
        framealpha=0.95
    )