import seaborn as sns
from agents.decorators import validate_dataframe
from typing import Dict
import pandas as pd

def plot_capacity_warning_matrix(ax, 
                                 df: pd.DataFrame, 
                                 colors: Dict, 
                                 sizes: Dict):
    """
    Plot capacity warning matrix heatmap
    """
    
    subplot_title = 'Capacity Warning Matrix'

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
                fontsize=sizes.get('title', 14),
                color=colors.get('title', 'black'))
        ax.set_title(subplot_title,
                    fontsize=sizes['title'],
                    color=colors['title'],
                    fontweight='bold')
        ax.axis('off')
        return
    
    warning_data = df.copy()
    warning_matrix = warning_data.groupby(
        ['capacityWarning', 'capacitySeverity']
    ).size().unstack(fill_value=0)
    
    sns.heatmap(
        warning_matrix,
        annot=True,
        fmt='d',
        cmap='icefire',
        ax=ax,
        cbar_kws={'label': 'Number of POs'},
        linewidths=1,
        linecolor='white'
    )
    ax.set_title(
        subplot_title,
        fontsize=sizes['title'],
        color=colors['title'],
        fontweight='bold',
        pad=10
    )
    ax.set_xlabel('Capacity Severity', fontsize=sizes['xlabel'])
    ax.set_ylabel('Capacity Warning', fontsize=sizes['ylabel'])