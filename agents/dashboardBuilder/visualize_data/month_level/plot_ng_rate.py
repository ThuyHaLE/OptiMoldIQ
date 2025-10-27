import pandas as pd
import numpy as np
from matplotlib.patches import Rectangle
from matplotlib.colors import to_rgba, to_hex
from typing import Dict
from agents.decorators import validate_init_dataframes

@validate_init_dataframes({"df": ['poNo', 'itemCodeName', 'is_backlog', 'poStatus', 'poETA',
                                  'itemNGQuantity', 'itemQuantity', 'itemGoodQuantity', 'etaStatus',
                                  'proStatus', 'moldHistNum', 'itemNGRate']})

def lighten_color(color, amount=0.5):
    """
    Lighten the given color by mixing it with white.

    Args:
        color (str or tuple): Original color (hex or RGBA)
        amount (float): 0 = original color, 1 = white

    Returns:
        str: Lightened hex color
    """
    c = to_rgba(color)
    white = (1, 1, 1, 1)
    new_color = tuple((1 - amount) * x + amount * y for x, y in zip(c, white))
    return to_hex(new_color)

def plot_ng_rate(ax,
                 df: pd.DataFrame,
                 colors: Dict,
                 sizes: Dict) -> None:
    """
    Plot the distribution of NG Rate bins by year with background boxes and pattern overlays.

    Args:
        ax: Matplotlib axis object
        df: DataFrame containing columns 'poETA', 'poNo', 'itemNGQuantity', 'itemGoodQuantity'
        colors: Dictionary for color configurations
        sizes: Dictionary for font size configurations
    """

    subplot_title = 'Distribution of NG Rate (Number of POs)'

    if df.empty:
        ax.text(0.5, 0.5, 'No data available',
                ha='center', va='center',
                fontsize=sizes['title'],
                color=colors['title'])
        ax.set_title(subplot_title,
                    fontsize=sizes['title'],
                    color=colors['title'],
                    fontweight='bold')
        ax.axis('off')
        return

    # Prepare data
    df_work = df[['poETA', 'poNo', 'itemNGQuantity', 'itemGoodQuantity']].copy()
    df_work['poETA'] = pd.to_datetime(df_work['poETA'])

    # ---- Calculate NG rate (%) ----
    df_work['NG_rate'] = df_work['itemNGQuantity'] / (df_work['itemGoodQuantity'] + df_work['itemNGQuantity']) * 100

    # ---- Define 6 bins ----
    bins = [0, 20, 40, 60, 80, 100]
    labels = ['Not Progress', '0–20%', '20–40%', '40–60%', '60–80%', '80–100%']

    # Assign NG rate into bins
    df_work['NG_bin'] = pd.cut(df_work['NG_rate'], bins=bins, labels=labels[1:], 
                               include_lowest=True, right=False).astype(str)

    # Mark "Not Progress" cases
    df_work.loc[(
        (df_work['itemGoodQuantity'] == 0) & (df_work['itemNGQuantity'] == 0) |
        (df_work['itemGoodQuantity'].isna()) & (df_work['itemNGQuantity'].isna())), 'NG_bin'] = 'Not Progress'

    # Convert to categorical
    df_work['NG_bin'] = pd.Categorical(df_work['NG_bin'], categories=labels, ordered=True)

    # ---- Group by bin only (single year) ----
    distribution = (
        df_work.groupby('NG_bin', observed=False)
        .agg(po_count=('poNo', 'count'))
        .reindex(labels, fill_value=0)
    )

    # ---- Plot the chart ----
    n_bins = len(labels)
    bar_width = 0.6  # Tăng từ 0.15 lên 0.6 để bars rộng hơn và gần nhau hơn
    x_pos = np.arange(n_bins)

    # Colors for each bin
    bin_colors = ['#84A59D', '#A8DADC', '#CDB4DB', '#F6BD60', '#F28482', '#E07A5F']

    ax.grid(False)

    # Find max value
    max_value = distribution.values.max()
    if max_value == 0:
        max_value = 10

    # ---- Draw background boxes (light colors) ----
    for i, (bin_label, color) in enumerate(zip(labels, bin_colors)):
        light_color = lighten_color(color, 0.5)

        rect = Rectangle(
            (x_pos[i] - bar_width/2, 0),
            bar_width,
            max_value,
            facecolor=light_color,
            edgecolor='white',
            linewidth=0.5,
            alpha=1,
            zorder=1
        )
        ax.add_patch(rect)

    # ---- Draw actual bars with pattern ----
    for i, (bin_label, color) in enumerate(zip(labels, bin_colors)):
        value = distribution.loc[bin_label, 'po_count']  # Extract the scalar value
        
        bar = ax.bar(x_pos[i], value, bar_width, label=bin_label,
                    color=color,
                    edgecolor='white',
                    linewidth=0.8,
                    hatch='///',
                    zorder=3)
        
        # Add text label
        if value > 0:
            ax.text(x_pos[i], value,
                  f'{int(value)}',
                  ha='center', va='bottom',
                  fontsize=9,
                  color='#333333',
                  fontweight='bold',
                  zorder=4)

    # ---- Configure X-axis ----
    ax.set_xticks(x_pos)
    ax.set_xticklabels(labels, 
                       rotation=30, 
                       ha='right', 
                       fontsize=sizes['xlabel'])
    
    # Thu hẹp xlim để các bins gần nhau hơn
    ax.set_xlim(-0.5, n_bins - 0.5)

    # ---- Axis labels and title ----
    ax.set_title(f'{subplot_title}',
                 fontsize=sizes['title'],
                 fontweight='bold',
                 pad=10,
                 color=colors['title'])

    # Remove Y label
    ax.set_ylabel('')
    ax.set_yticklabels([])
    ax.set_ylim(0, max_value * 1.25)

    # ---- Hide top & right spines ----
    for spine in ['top', 'right']:
        ax.spines[spine].set_visible(False)