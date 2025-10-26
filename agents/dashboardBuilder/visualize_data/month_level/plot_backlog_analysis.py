from agents.decorators import validate_init_dataframes
from typing import Dict
import pandas as pd

@validate_init_dataframes({"df": ['poNo', 'poETA', 'itemQuantity', 'itemGoodQuantity', 'is_backlog',
                                  'itemCodeName', 'proStatus', 'poStatus', 'moldHistNum',
                                  'itemRemainQuantity', 'completionProgress', 'etaStatus',
                                  'overAvgCapacity', 'overTotalCapacity', 'is_overdue', 'capacityWarning',
                                  'capacitySeverity', 'capacityExplanation']})
    
def plot_backlog_analysis(ax, 
                          df: pd.DataFrame, 
                          colors: Dict, 
                          sizes: Dict):
    
    """
    Plot backlog analysis
    """
    
    subplot_title = 'Backlog Status'

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
    
    backlog_counts = df['is_backlog'].value_counts()
    colors_backlog = list(colors['backlog'].values())
    bars = ax.bar(
        list(colors['backlog'].keys()),
        [backlog_counts.get(False, 0), backlog_counts.get(True, 0)],
        color=colors_backlog
    )
    ax.set_title(
        subplot_title,
        fontsize=sizes['title'],
        color=colors['title'],
        fontweight='bold',
        pad=15
    )
    ax.set_ylabel('Number of POs', fontsize=sizes['ylabel'])
    
    for bar in bars:
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width()/2.,
            height,
            f'{int(height)}',
            ha='center', va='bottom'
        )