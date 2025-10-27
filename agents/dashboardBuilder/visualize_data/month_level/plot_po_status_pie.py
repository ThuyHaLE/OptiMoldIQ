from agents.decorators import validate_init_dataframes
from typing import Dict
import pandas as pd

@validate_init_dataframes({"df": ['poNo', 'poETA', 'itemQuantity', 'itemGoodQuantity', 'itemNGQuantity',
                                  'is_backlog', 'itemCodeName', 'proStatus', 'poStatus', 'moldHistNum',
                                  'itemRemainQuantity', 'completionProgress', 'etaStatus',
                                  'overAvgCapacity', 'overTotalCapacity', 'is_overdue', 'capacityWarning',
                                  'capacitySeverity', 'capacityExplanation']})

def plot_po_status_pie(ax, 
                       df: pd.DataFrame, 
                       po_status: str, 
                       title: str, 
                       colors: Dict, 
                       sizes: Dict):
    """
    Plot PO status distribution as pie chart
    
    Args:
        po_status: 'in_progress', 'not_started', or 'finished'
    """

    if df.empty:
        ax.text(0.5, 0.5, 'No data available', 
                ha='center', va='center', 
                fontsize=sizes['title'],
                color=sizes['title'])
        ax.set_title(title,
                    fontsize=sizes['title'],
                    color=colors['title'],
                    fontweight='bold')
        ax.axis('off')
        return
    
    status_counts = df[df['poStatus'] == po_status]['etaStatus'].value_counts()
    ax.pie(
        status_counts.values,
        labels=status_counts.index,
        autopct='%1.1f%%',
        colors=colors['general'],
        startangle=90
    )
    ax.set_title(
        title,
        fontsize=sizes['title'],
        color=colors['title'],
        fontweight='bold',
        pad=10
    )
