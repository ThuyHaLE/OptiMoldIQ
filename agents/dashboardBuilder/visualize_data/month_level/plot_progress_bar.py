import matplotlib.patches as mpatches
from agents.decorators import validate_dataframe
from typing import Dict
import pandas as pd

def plot_progress_bar(ax, 
                      df: pd.DataFrame, 
                      colors: Dict, 
                      sizes: Dict):
    """
    Plot production progress bar with gradient effect
    """

    subplot_title = 'Progress Bar'

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
    
    ax.axis('off')
    ax.set_facecolor('#f8fafc')

    # Add gradient background panel with shadow effect
    panel = mpatches.FancyBboxPatch(
        (0, 0), 1, 1,
        boxstyle="round,pad=0.015",
        facecolor='white',
        edgecolor='none',
        linewidth=0,
        transform=ax.transAxes,
        zorder=0
    )
    ax.add_patch(panel)

    # Add subtle shadow
    shadow = mpatches.FancyBboxPatch(
        (-0.002, -0.003), 1.004, 1.003,
        boxstyle="round,pad=0.015",
        facecolor='#cbd5e0',
        edgecolor='none',
        transform=ax.transAxes,
        zorder=-1,
        alpha=0.3
    )
    ax.add_patch(shadow)

    # Calculate progress
    total_good_quantity = df['itemGoodQuantity'].sum()
    total_quantity = df['itemQuantity'].sum()
    progress_percentage = (total_good_quantity / total_quantity) * 100

    ax.set_xlim(0, 100)
    ax.set_ylim(0, 1)

    # Determine color scheme based on progress
    if progress_percentage < 25:
        bar_colors = ['#dc2626', '#ef4444', '#f87171']
        glow_color = '#fca5a5'
    elif progress_percentage < 50:
        bar_colors = ['#ea580c', '#f97316', '#fb923c']
        glow_color = '#fdba74'
    elif progress_percentage < 75:
        bar_colors = ['#d97706', '#f59e0b', '#fbbf24']
        glow_color = '#fcd34d'
    elif progress_percentage < 90:
        bar_colors = ['#0284c7', '#0ea5e9', '#38bdf8']
        glow_color = '#7dd3fc'
    else:
        bar_colors = ['#16a34a', '#22c55e', '#4ade80']
        glow_color = '#86efac'

    # Background bar with border and inner shadow
    bg_border = mpatches.FancyBboxPatch(
        (1, 0.2), 98, 0.5,
        boxstyle="round,pad=0.012",
        facecolor='none',
        edgecolor='#cbd5e0',
        linewidth=2,
        transform=ax.transData,
        zorder=1
    )
    ax.add_patch(bg_border)

    bg_bar = mpatches.FancyBboxPatch(
        (1.5, 0.23), 97, 0.44,
        boxstyle="round,pad=0.01",
        facecolor='#e2e8f0',
        edgecolor='none',
        transform=ax.transData,
        zorder=2
    )
    ax.add_patch(bg_bar)

    # Progress bar with layered gradient effect
    if progress_percentage > 0:
        # Glow effect
        glow = mpatches.FancyBboxPatch(
            (1.5, 0.23), max(0, progress_percentage-3), 0.44,
            boxstyle="round,pad=0.01",
            facecolor=glow_color,
            edgecolor='none',
            transform=ax.transData,
            zorder=3,
            alpha=0.4
        )
        ax.add_patch(glow)

        # Main gradient (3 layers)
        for i, color in enumerate(bar_colors):
            alpha = 0.5 - (i * 0.15)
            bar_height = 0.44 - (i * 0.08)
            bar_y = 0.23 + (i * 0.04)

            progress_bar = mpatches.FancyBboxPatch(
                (1.5, bar_y), max(0, progress_percentage-3), bar_height,
                boxstyle="round,pad=0.01",
                facecolor=color,
                edgecolor='none',
                transform=ax.transData,
                zorder=4+i,
                alpha=alpha+0.5
            )
            ax.add_patch(progress_bar)

        # Shine effect on top
        shine = mpatches.FancyBboxPatch(
            (1.5, 0.5), max(0, progress_percentage-3), 0.12,
            boxstyle="round,pad=0.008",
            facecolor='white',
            edgecolor='none',
            transform=ax.transData,
            zorder=7,
            alpha=0.3
        )
        ax.add_patch(shine)

    # Percentage text with modern styling
    if progress_percentage > 20:
        # Text shadow
        ax.text(
            progress_percentage/2 + 0.3, 0.43,
            f'{progress_percentage:.1f}%',
            ha='center', va='center',
            fontsize=sizes['progress_text']* 0.7,
            fontweight='bold',
            color='#1e293b',
            alpha=0.2,
            zorder=8
        )
        # Main text
        ax.text(
            progress_percentage/2, 0.45,
            f'{progress_percentage:.1f}%',
            ha='center', va='center',
            fontsize=sizes['progress_text']* 0.7,
            fontweight='bold',
            color='white',
            zorder=9
        )
    else:
        ax.text(
            progress_percentage + 6, 0.45,
            f'{progress_percentage:.1f}%',
            ha='left', va='center',
            fontsize=sizes['progress_text']* 0.7,
            fontweight='bold',
            color=bar_colors[1],
            zorder=9
        )

    # Bottom text
    ax.text(
        50, -0.15,
        f'Completed: {int(total_good_quantity):,} / {int(total_quantity):,} | Remaining: {int(total_quantity - total_good_quantity):,}',
        ha='center', va='bottom',
        fontsize=sizes['title'],
        color=colors['text']
    )

    # Title
    ax.text(
        50, 1.2, subplot_title,
        ha='center', va='top',
        fontsize=sizes['title'],
        fontweight='bold',
        color=colors['title'],
        transform=ax.transData
    )