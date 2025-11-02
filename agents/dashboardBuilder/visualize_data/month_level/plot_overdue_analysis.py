from agents.decorators import validate_dataframe
from typing import Dict
import pandas as pd

def plot_overdue_analysis(ax, 
                          df: pd.DataFrame, 
                          colors: Dict, 
                          sizes: Dict):
    
    """
    Plot overdue vs on-time analysis
    """

    subplot_title = 'Overdue Status by PO Status'

    # Valid data frame
    required_columns = ['poNo', 'poETA', 'itemQuantity', 'itemGoodQuantity', 'itemNGQuantity',
                        'is_backlog', 'itemCodeName', 'proStatus', 'poStatus', 'moldHistNum',
                        'itemRemainQuantity', 'completionProgress', 'etaStatus',
                        'overAvgCapacity', 'overTotalCapacity', 'is_overdue', 'capacityWarning',
                        'capacitySeverity', 'capacityExplanation']
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

    # Auto detect xtick lables
    bool_to_status = dict(zip([True, False], ['On Time', 'Overdue']))
    overdue_values = df['is_overdue'].unique().tolist()
    xtick_lables = [bool_to_status[x] for x in overdue_values]

    overdue_data = pd.crosstab(df['is_overdue'], df['poStatus'])
    overdue_data.plot(
        kind='bar',
        ax=ax,
        color=colors['general'],
        stacked=True
    )

    ax.set_title(
        subplot_title,
        fontsize=sizes['title'],
        color=colors['title'],
        fontweight='bold',
        pad=10,
    )

    ax.set_xlabel('Is Overdue', fontsize=sizes['xlabel'])
    ax.set_ylabel('Number of POs', fontsize=sizes['ylabel'])
    ax.set_xticklabels(xtick_lables, rotation=0)
    ax.legend(loc='upper right')