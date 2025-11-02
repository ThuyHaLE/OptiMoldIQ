from agents.decorators import validate_dataframe
import matplotlib.patches as mpatches
from typing import Dict
import pandas as pd

def plot_top_ng_items_bar(ax, 
                       df: pd.DataFrame, 
                       colors: Dict, 
                       sizes: Dict):
    """
    Plot top 10 items by NG rate (horizontal bar)
    """

    subplot_title = 'Top 10 Items by NG Rate'

    # Valid data frame
    required_columns = ['poNo', 'itemCodeName', 'is_backlog', 'poStatus', 'poETA',
                        'itemNGQuantity', 'itemQuantity', 'itemGoodQuantity', 'etaStatus',
                        'proStatus', 'moldHistNum', 'itemNGRate']
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
    
    df['itemNGRate'] = df['itemNGQuantity'] / (df['itemGoodQuantity'] + df['itemNGQuantity']) * 100
    df['itemNGRate'] = df['itemNGRate'].fillna(0)

    # Lọc bỏ các dòng có itemNGRate là NaN hoặc inf
    df_filtered = df[df['itemNGRate']>0].copy()
    
    top_items = df_filtered.nlargest(10, 'itemNGRate')[
        ['poStatus', 'itemCodeName', 'itemNGRate', 'itemQuantity']
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
        top_items['itemNGRate'],
        color=top_items_colors_bar,
        edgecolor='white',
        linewidth=2.5,
        alpha=0.85
    )

    ax.set_xticklabels([])

    ax.set_yticks(range(len(top_items)))
    ax.set_yticklabels(
        [name[:50] + '...' if len(name) > 50 else name 
         for name in top_items['itemCodeName']],
        fontsize=9
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
        ng_qty = top_items.iloc[i]['itemQuantity']
        ax.text(
            width,
            bar.get_y() + bar.get_height()/2.,
            f'  {width*100:.2f}% | Total: {int(ng_qty):,}',
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
        loc='center left',
        fontsize=sizes['legend'],
        framealpha=0.95
    )