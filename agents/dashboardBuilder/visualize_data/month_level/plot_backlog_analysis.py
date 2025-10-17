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
    
    backlog_counts = df['is_backlog'].value_counts()
    colors_backlog = list(colors['backlog'].values())
    bars = ax.bar(
        list(colors['backlog'].keys()),
        [backlog_counts.get(False, 0), backlog_counts.get(True, 0)],
        color=colors_backlog
    )
    ax.set_title(
        'Backlog Status',
        fontsize=sizes['title'],
        color=colors['title'],
        fontweight='bold'
    )
    ax.set_ylabel('Number of POs', fontsize=sizes['ylabel'])
    
    for bar in bars:
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width()/2.,
            height,
            f'{int(height)}',
            ha='center', va='bottom',
            fontweight='bold'
        )