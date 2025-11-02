import pandas as pd
import numpy as np
from matplotlib.patches import Rectangle
from matplotlib.colors import to_rgba, to_hex
from typing import Dict
from agents.decorators import validate_dataframe

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

def plot_ng_rate_distribution(ax,
                              df: pd.DataFrame,
                              colors: Dict,
                              sizes: Dict,
                              target_year: str = None) -> None:
    """
    Plot the distribution of NG Rate bins by month with background boxes and pattern overlays.

    Args:
        ax: Matplotlib axis object
        df: DataFrame containing columns 'poETA', 'poNo', 'itemNGQuantity', 'itemGoodQuantity'
        colors: Dictionary for color configurations
        sizes: Dictionary for font size configurations
        target_year: Target year (string). If None, the current year is used.
    """

    subplot_title = 'Distribution of NG Rate Bins (Number of POs)'

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

    # Prepare data
    df_work = df[['poETA', 'poNo', 'itemNGQuantity', 'itemGoodQuantity']].copy()

    # Determine the target year
    if target_year is None:
        target_year = str(df_work['poETA'].dt.year.mode()[0])

    df_work['poETA'] = pd.to_datetime(df_work['poETA'])
    df_work['poETA-mstr'] = df_work['poETA'].dt.strftime('%Y-%m')

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

    # ---- Create FIXED month list ----
    if len(df_work) > 0:
        df_work['year'] = df_work['poETA'].dt.year.astype(str)

        # Always generate 12 months for the target year
        start_date = pd.Timestamp(year=int(target_year), month=1, day=1)
        end_date = pd.Timestamp(year=int(target_year), month=12, day=1)

        # Extend if data exists outside the target year
        other_year_data = df_work[df_work['year'] != target_year]
        if len(other_year_data) > 0:
            data_min = other_year_data['poETA'].min()
            data_max = other_year_data['poETA'].max()

            if data_min < start_date:
                start_date = data_min.replace(day=1)
            if data_max > end_date:
                end_date = data_max.replace(day=1)
    else:
        start_date = pd.Timestamp(year=int(target_year), month=1, day=1)
        end_date = pd.Timestamp(year=int(target_year), month=12, day=1)

    # Generate the full month range
    months_full = pd.date_range(start=start_date, end=end_date, freq='MS')
    months_full_str = months_full.strftime('%Y-%m').tolist()

    # ---- Group by month and bin ----
    distribution = (
        df_work.groupby(['poETA-mstr', 'NG_bin'], observed=False)
        .agg(po_count=('poNo', 'count'))
        .reset_index()
    )

    # ---- Create a full DataFrame with ALL month × bin combinations ----
    full_index = pd.MultiIndex.from_product(
        [months_full_str, labels],
        names=['poETA-mstr', 'NG_bin']
    )

    distribution_full = (
        distribution.set_index(['poETA-mstr', 'NG_bin'])
        .reindex(full_index, fill_value=0)
        .reset_index()
    )

    # ---- Pivot table for plotting ----
    pivot_df = distribution_full.pivot(index='poETA-mstr', columns='NG_bin', values='po_count')
    pivot_df = pivot_df[labels]
    pivot_df = pivot_df.reindex(months_full_str, fill_value=0)

    # ---- Plot the chart ----
    n_months = len(months_full_str)
    n_bins = len(labels)

    bar_width = 0.15
    group_gap = 0.3

    x_pos = np.arange(n_months) * (n_bins * bar_width + group_gap)

    # Colors for each bin
    bin_colors = ['#84A59D', '#A8DADC', '#CDB4DB', '#F6BD60', '#F28482', '#E07A5F']

    ax.grid(False)

    # Find max value
    max_value = pivot_df.values.max()
    if max_value == 0:
        max_value = 10

    # ---- Draw background boxes (light colors) ----
    for i, (bin_label, color) in enumerate(zip(labels, bin_colors)):
        offset = i * bar_width
        light_color = lighten_color(color, 0.5)

        for j in range(n_months):
            rect = Rectangle(
                (x_pos[j] + offset - bar_width/2, 0),
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
        values = pivot_df[bin_label].values
        offset = i * bar_width

        bars = ax.bar(x_pos + offset, values, bar_width, label=bin_label,
                      color=color,
                      edgecolor='white',
                      linewidth=0.8,
                      hatch='///',
                      zorder=3)

        # Add text labels
        for j, (bar, value) in enumerate(zip(bars, values)):
            if value > 0:
                ax.text(bar.get_x() + bar.get_width()/2, value,
                       f'{int(value)}',
                       ha='center', va='bottom',
                       fontsize=8,
                       color='#333333',
                       zorder=4)

    # ---- Mark year boundaries ----
    for i in range(n_months - 1):
        current_year = int(months_full_str[i].split('-')[0])
        next_year = int(months_full_str[i + 1].split('-')[0])
        if current_year != next_year:
            end_of_current_group = x_pos[i] + n_bins * bar_width
            boundary_x = (end_of_current_group + x_pos[i+1]) / 2

            ax.axvline(boundary_x,
                      color='#e74c3c',
                      linestyle='--',
                      linewidth=1.5,
                      alpha=0.6,
                      zorder=2)
            ax.text(boundary_x,
                   max_value * 1.2,
                   f'▼ {next_year}',
                   ha='center',
                   fontsize=10,
                   fontweight='bold',
                   color='#e74c3c',
                   bbox=dict(boxstyle='round,pad=0.4',
                            facecolor='white',
                            edgecolor='#e74c3c',
                            linewidth=1),
                   zorder=5)

    # ---- Configure X-axis ----
    ax.set_xticks(x_pos + bar_width * (n_bins - 1) / 2)
    ax.set_xticklabels(months_full_str, rotation=0)

    # ---- Axis labels and title ----
    ax.set_xlabel('POs ETA (Month)', fontsize=sizes['xlabel'])
    ax.set_title(f'{subplot_title} - Year {target_year} ({len(months_full_str)} months)',
                 fontsize=sizes['title'],
                 fontweight='bold',
                 pad=10,
                 color=colors['title'])

    # Remove Y label
    ax.set_ylabel('')
    ax.set_yticklabels([])
    ax.set_ylim(0, max_value * 1.2)

    ax.legend(title='NG Rate (%)',
              bbox_to_anchor=(1.02, 1),
              loc='upper left',
              fontsize=sizes['legend'])

    # ---- Hide top & right spines ----
    for spine in ['top', 'right']:
        ax.spines[spine].set_visible(False)