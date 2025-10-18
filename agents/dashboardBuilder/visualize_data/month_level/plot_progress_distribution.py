from agents.decorators import validate_init_dataframes
from typing import Dict
import pandas as pd

@validate_init_dataframes({"df": ['poNo', 'poETA', 'itemQuantity', 'itemGoodQuantity', 'is_backlog',
                                  'itemCodeName', 'proStatus', 'poStatus', 'moldHistNum',
                                  'itemRemainQuantity', 'completionProgress', 'etaStatus',
                                  'overAvgCapacity', 'overTotalCapacity', 'is_overdue', 'capacityWarning',
                                  'capacitySeverity', 'capacityExplanation']})
    
def plot_progress_distribution(ax, 
                               df: pd.DataFrame, 
                               colors: Dict, 
                               sizes: Dict):
    """
    Plot progress distribution (bar chart)
    """

    subplot_title = 'Progress Distribution'

    if df.empty:
        ax.text(0.5, 0.5, 'No data available', 
                ha='center', va='center', 
                fontsize=sizes.get('title', 14),
                color=colors.get('title', 'black'))
        ax.set_title(subplot_title,
                    fontsize=sizes['title'],
                    color=colors['title'],
                    fontweight='bold')
        ax.axis('off')
        return
    
    progress_ranges = pd.cut(
        df['completionProgress'],
        bins=[0, 0.25, 0.5, 0.75, 1.0],
        labels=['0-25%', '25-50%', '50-75%', '75-100%']
    )
    progress_dist = progress_ranges.value_counts().sort_index()
    bars = ax.bar(
        range(len(progress_dist)),
        progress_dist.values,
        color=colors['general'][:len(progress_dist.values)],
        alpha=0.8
    )
    ax.set_xticks(range(len(progress_dist)))
    ax.set_xticklabels(progress_dist.index, rotation=0)
    ax.set_ylabel('Number of POs', fontsize=sizes['ylabel'])
    ax.set_title(
        subplot_title,
        fontsize=sizes['title'],
        fontweight='bold',
        color=colors['title'],
        pad=10
    )
    ax.grid(axis='y', alpha=0.3)

    # Add value labels on bars
    for bar in bars:
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width()/2.,
            height,
            f'{int(height)}',
            ha='center', va='bottom',
            fontsize=sizes['text'],
            fontweight='bold'
        )
