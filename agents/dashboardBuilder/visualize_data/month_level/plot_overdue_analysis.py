from agents.decorators import validate_init_dataframes
from typing import Dict
import pandas as pd

@validate_init_dataframes({"df": ['poNo', 'poETA', 'itemQuantity', 'itemGoodQuantity', 'is_backlog',
                                  'itemCodeName', 'proStatus', 'poStatus', 'moldHistNum',
                                  'itemRemainQuantity', 'completionProgress', 'etaStatus',
                                  'overAvgCapacity', 'overTotalCapacity', 'is_overdue', 'capacityWarning',
                                  'capacitySeverity', 'capacityExplanation']})
    
def plot_overdue_analysis(ax, 
                          df: pd.DataFrame, 
                          colors: Dict, 
                          sizes: Dict):
    
    """
    Plot overdue vs on-time analysis
    """

    overdue_data = pd.crosstab(df['is_overdue'], df['poStatus'])
    overdue_data.plot(
        kind='bar',
        ax=ax,
        color=colors['general'][:3],
        stacked=True
    )
    ax.set_title(
        'Overdue Status by PO Status',
        fontsize=sizes['title'],
        color=colors['title'],
        fontweight='bold'
    )
    ax.set_xlabel('Is Overdue', fontsize=sizes['xlabel'])
    ax.set_ylabel('Number of POs', fontsize=sizes['ylabel'])
    ax.set_xticklabels(['On Time', 'Overdue'], rotation=0)
    ax.legend(title='PO Status', loc='upper right')