import matplotlib.patches as mpatches
from agents.decorators import validate_init_dataframes
from typing import Dict
import pandas as pd

@validate_init_dataframes({"df": ['poNo', 'poETA', 'itemQuantity', 'itemGoodQuantity', 'itemNGQuantity',
                                  'is_backlog', 'itemCodeName', 'proStatus', 'poStatus', 'moldHistNum',
                                  'itemRemainQuantity', 'completionProgress', 'etaStatus',
                                  'overAvgCapacity', 'overTotalCapacity', 'is_overdue', 'capacityWarning',
                                  'capacitySeverity', 'capacityExplanation']})

def plot_late_items_bar(ax, 
                        df: pd.DataFrame, 
                        colors: Dict, 
                        sizes: Dict):
    
    """
    Plot late status items by remaining quantity (horizontal bar)
    """

    subplot_title = 'Late Status Items by Remaining Quantity'

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
    
    late_items = df[df['etaStatus'] == 'late'].sort_values(
        ['completionProgress', 'itemRemainQuantity']
    ).copy()

    if len(late_items) > 0:
        late_items_statuses = late_items['poStatus'].unique().tolist()
        late_items_color_map = {
            status: colors['general'][i] 
            for i, status in enumerate(late_items_statuses)
        }
        late_items_colors_bar = [
            late_items_color_map[x] for x in late_items['poStatus']
        ]

        bars = ax.barh(
            range(len(late_items)),
            late_items['itemRemainQuantity'],
            color=late_items_colors_bar,
            edgecolor='white',
            linewidth=2.5,
            alpha=0.85
        )

        ax.set_yticks(range(len(late_items)))
        ax.set_yticklabels(
            [name[:50] + '...' if len(name) > 50 else name 
             for name in late_items['itemCodeName']],
            fontsize=9
        )
        ax.set_xlabel(
            'Remaining Quantity',
            fontsize=sizes['xlabel'],
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

        # Add value labels
        for i, bar in enumerate(bars):
            width = bar.get_width()
            progress = late_items.iloc[i]['completionProgress']
            ax.text(
                width,
                bar.get_y() + bar.get_height()/2.,
                f'  {progress*100:.1f}% | {int(width):,}',
                ha='left', va='center',
                fontsize=sizes['text']
            )

        # Modern legend
        legend_handles = [
            mpatches.Patch(color=color, label=status.replace('_', ' ').title())
            for status, color in late_items_color_map.items()
        ]
        ax.legend(
            handles=legend_handles,
            bbox_to_anchor=(1.02, 1),
            loc='upper left',
            fontsize=sizes['legend'],
            framealpha=0.95
        )