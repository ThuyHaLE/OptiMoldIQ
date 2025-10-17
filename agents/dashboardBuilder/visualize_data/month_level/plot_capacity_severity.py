from agents.decorators import validate_init_dataframes
from typing import Dict
import pandas as pd

@validate_init_dataframes({"df": ['poNo', 'poETA', 'itemQuantity', 'itemGoodQuantity', 'is_backlog',
                                  'itemCodeName', 'proStatus', 'poStatus', 'moldHistNum',
                                  'itemRemainQuantity', 'completionProgress', 'etaStatus',
                                  'overAvgCapacity', 'overTotalCapacity', 'is_overdue', 'capacityWarning',
                                  'capacitySeverity', 'capacityExplanation']})
    
def plot_capacity_severity(ax, 
                           df: pd.DataFrame, 
                           colors: Dict, 
                           sizes: Dict):
    """
    Plot capacity severity distribution
    """
    severity_counts = df['capacitySeverity'].value_counts()
    bars = ax.bar(
        severity_counts.index,
        severity_counts.values,
        color=[colors['colors_severity'].get(x, '#CCCCCC') 
               for x in severity_counts.index]
    )
    ax.set_title(
        'Capacity Severity',
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