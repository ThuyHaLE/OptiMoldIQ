from agents.decorators import validate_dataframe
from typing import Dict
import pandas as pd

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

    # Valid data frame
    required_columns = ['poNo', 'itemCodeName', 'is_backlog', 'poStatus', 'poETA',
                        'itemNGQuantity', 'itemQuantity', 'itemGoodQuantity', 'etaStatus',
                        'proStatus', 'moldHistNum']
    
    validate_dataframe(df, required_columns)

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
