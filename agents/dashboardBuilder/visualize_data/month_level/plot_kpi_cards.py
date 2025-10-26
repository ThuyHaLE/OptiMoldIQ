from agents.decorators import validate_init_dataframes
import matplotlib.patches as mpatches
from typing import Dict
import pandas as pd

@validate_init_dataframes({"df": ['poNo', 'itemCodeName', 'is_backlog', 'poStatus', 'itemQuantity',
                                  'itemGoodQuantity', 'etaStatus', 'proStatus', 'moldHistNum']})
    
def plot_kpi_cards(ax, 
                   df: pd.DataFrame, 
                   colors: Dict, 
                   sizes: Dict):
    """
    Plot KPI summary cards
    """

    subplot_title = 'KPI summary cards'

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
    
    ax.axis('off')

    # Calculate KPIs
    total_pos = len(df)
    backlog_pos = df['is_backlog'].sum()
    in_progress_pos = (df['poStatus'] == 'in_progress').sum()
    not_started_pos = (df['poStatus'] == 'not_started').sum()
    finished_pos = (df['poStatus'] == 'finished').sum()
    late_pos = (df['etaStatus'] == 'late').sum()
    avg_completion = (df['itemGoodQuantity'] / df['itemQuantity']).mean() * 100
    total_completion = (df['itemGoodQuantity'].sum() / df['itemQuantity'].sum()) * 100

    kpi_data = [
        ('Total POs', total_pos, colors['kpi']['Total POs']),
        ('Backlog', backlog_pos, colors['kpi']['Backlog']),
        ('Finished POs', finished_pos, colors['kpi']['Finished POs']),
        ('In-progress POs', in_progress_pos, colors['kpi']['In-progress POs']),
        ('Not-started POs', not_started_pos, colors['kpi']['Not-started POs']),
        ('Total progress', f'{total_completion:.1f}%', colors['kpi']['Total progress']),
        ('Avg progress', f'{avg_completion:.1f}%', colors['kpi']['Avg progress']),
        ('Late POs', late_pos, colors['kpi']['Late POs'])
    ]

    # Create KPI cards
    card_width = 0.1
    card_height = 0.8
    spacing = 0.02

    total_width = len(kpi_data) * card_width + (len(kpi_data) - 1) * spacing
    start_x = 0.5 - total_width / 2

    for i, (label, value, color) in enumerate(kpi_data):
        x = start_x + i * (card_width + spacing)

        # Card background
        rect = mpatches.FancyBboxPatch(
            (x, 0.1),
            card_width,
            card_height,
            boxstyle="round,pad=0.01",
            facecolor=color,
            edgecolor='white',
            linewidth=2,
            alpha=0.9,
            transform=ax.transAxes
        )
        ax.add_patch(rect)

        # Value text
        ax.text(
            x + card_width/2,
            0.55,
            str(value) if not isinstance(value, str) else value,
            ha='center', va='center',
            fontsize=24,
            fontweight='bold',
            color='white',
            transform=ax.transAxes
        )

        # Label text
        ax.text(
            x + card_width/2,
            0.25,
            label,
            ha='center', va='center',
            fontsize=11,
            fontweight='bold',
            color='white',
            transform=ax.transAxes
        )

    ax.set_title(
        subplot_title,
        fontsize=sizes['title'],
        fontweight='bold',
        color=colors['title'],
        pad=10
    )
