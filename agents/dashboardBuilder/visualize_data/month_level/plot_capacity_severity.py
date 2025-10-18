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
    
    subplot_title = 'Capacity Severity'

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
    
    severity_counts = df['capacitySeverity'].value_counts()
    bars = ax.bar(
        severity_counts.index,
        severity_counts.values,
        color=[colors['colors_severity'].get(x, '#CCCCCC') 
               for x in severity_counts.index]
    )
    ax.set_title(
        subplot_title,
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