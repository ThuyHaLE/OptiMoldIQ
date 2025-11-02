from agents.decorators import validate_dataframe
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle
from typing import Dict, Optional

def plot_monthly_eta_status(ax: plt.Axes,
                            df: pd.DataFrame,
                            colors: Dict,
                            sizes: Dict,
                            target_year: Optional[str] = None) -> None:
    """
    Plot monthly PO quantity analysis showing finished/unfinished and late/ontime status.

    Parameters:
    -----------
    ax : plt.Axes
        Matplotlib axes object to plot on
    df : pd.DataFrame
        DataFrame with columns: ['etaStatus', 'proStatus', 'poETA']
        where poETA is datetime format
    colors : Dict
        Dictionary containing color configurations
    sizes : Dict
        Dictionary containing font size configurations
    target_year : str, optional
        Year to analyze (e.g., '2019'). If None, uses current year
    """

    subplot_title = 'ETA Status'

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

    # Determine the target year
    if target_year is None:
        target_year = str(df_copy['poETA'].dt.year.mode()[0])

    # Prepare data
    df_copy = df[['etaStatus', 'proStatus', 'poETA']].copy()
    df_copy['poETA-mstr'] = pd.to_datetime(df_copy['poETA']).dt.strftime('%Y-%m')

    # Count and pivot data
    summary = df_copy.groupby(['poETA-mstr', 'proStatus', 'etaStatus']).size().reset_index(name='count')

    # Create monthly bins
    if len(summary) > 0:
        summary['year'] = summary['poETA-mstr'].str[:4]
        target_year_data = summary[summary['year'] == target_year]

        # Always create 12 months for target_year
        start_date = pd.Timestamp(year=int(target_year), month=1, day=1)
        end_date = pd.Timestamp(year=int(target_year), month=12, day=1)

        # Extend range if data exists outside target_year
        other_year_data = summary[summary['year'] != target_year]
        if len(other_year_data) > 0:
            data_min = pd.to_datetime(other_year_data['poETA-mstr'].min())
            data_max = pd.to_datetime(other_year_data['poETA-mstr'].max())

            if data_min < start_date:
                start_date = data_min
            if data_max > end_date:
                end_date = data_max

        summary = summary.drop(columns=['year'])
    else:
        start_date = pd.Timestamp(year=int(target_year), month=1, day=1)
        end_date = pd.Timestamp(year=int(target_year), month=12, day=1)

    months_full = pd.date_range(start=start_date, end=end_date, freq='MS')
    months_full_str = months_full.strftime('%Y-%m')
    n_months = len(months_full_str)

    # Reindex to include all combinations
    all_combos = pd.MultiIndex.from_product(
        [months_full_str, ['finished', 'unfinished'], ['late', 'ontime', 'expected_ontime']],
        names=['poETA-mstr', 'proStatus', 'etaStatus']
        )
    summary = summary.set_index(['poETA-mstr', 'proStatus', 'etaStatus']).reindex(all_combos, fill_value=0).reset_index()
    months = list(months_full_str)

    # Prepare plotting data
    data_dict = {
        'finished': {'late': [],
                     'ontime': [],
                     'expected_ontime': []},
        'unfinished': {'late': [],
                       'ontime': [],
                       'expected_ontime':[]}
    }
    for month in months:
        month_data = summary[summary['poETA-mstr'] == month]
        for pro_status in ['finished', 'unfinished']:
            for eta_status in ['late', 'ontime', 'expected_ontime']:
                val = month_data[
                    (month_data['proStatus'] == pro_status) &
                    (month_data['etaStatus'] == eta_status)
                ]['count'].values
                data_dict[pro_status][eta_status].append(val[0] if len(val) > 0 else 0)

    # Plotting configuration
    status_colors = {
        'late': '#ff6b6b',
        'ontime': '#51cf66',
        'expected_ontime': '#d52456'
        }
    patterns = {
        'finished': '',
        'unfinished': '...'
        }

    x = np.arange(n_months)
    bar_width = 0.35
    group_gap = 0.15

    ax.grid(False)

    # Draw month separators
    for i in range(n_months - 1):
      boundary_x = (x[i] + x[i + 1]) / 2
      ax.axvline(boundary_x,
                color='#ced4da',
                linestyle='-.',
                linewidth=1,
                alpha=0.8,
                zorder=1)

    # Plot bars
    bars_info = []
    for idx, (pro_status, pattern) in enumerate([('finished', patterns['finished']),
                                                   ('unfinished', patterns['unfinished'])]):
        offset = -bar_width/2 - group_gap/2 if pro_status == 'finished' else bar_width/2 + group_gap/2

        late_vals = data_dict[pro_status]['late']
        ontime_vals = data_dict[pro_status]['ontime']
        expected_ontime_vals = data_dict[pro_status]['expected_ontime']

        ax.bar(x + offset, late_vals, bar_width,
               color=status_colors['late'], alpha=0.85,
               edgecolor='white', linewidth=1.5,
               hatch=pattern, zorder=3)

        ax.bar(x + offset, ontime_vals, bar_width,
               bottom=late_vals,
               color=status_colors['ontime'], alpha=0.85,
               edgecolor='white', linewidth=1.5,
               hatch=pattern, zorder=3)

        ax.bar(x + offset, expected_ontime_vals, bar_width,
              bottom=np.array(late_vals) + np.array(ontime_vals),
              color=status_colors['expected_ontime'], alpha=0.85,
              edgecolor='white', linewidth=1.5,
              hatch=pattern, zorder=3)

        bars_info.append({
            'pro_status': pro_status,
            'offset': offset,
            'late': late_vals,
            'ontime': ontime_vals,
            'expected_ontime': expected_ontime_vals
        })

    # Mark year boundaries
    y_max_bars = max(max(np.array(data_dict['finished']['late']) +
                         np.array(data_dict['finished']['ontime']) +
                         np.array(data_dict['finished']['expected_ontime'])),
                      max(np.array(data_dict['unfinished']['late']) +
                          np.array(data_dict['unfinished']['ontime']) +
                          np.array(data_dict['finished']['expected_ontime']))
                      )

    for i in range(n_months - 1):
        current_year = int(months[i].split('-')[0])
        next_year = int(months[i + 1].split('-')[0])
        if current_year != next_year:
            boundary_x = (x[i] + x[i + 1]) / 2
            ax.axvline(boundary_x,
                       color='#e74c3c',
                       linestyle='--',
                       linewidth=1.5,
                       alpha=0.5,
                       zorder=2)
            ax.text(boundary_x,
                    y_max_bars * 1.20,
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

    # Add labels
    for bar_info in bars_info:
        offset = bar_info['offset']
        late_vals = bar_info['late']
        ontime_vals = bar_info['ontime']
        expected_ontime_vals = bar_info['expected_ontime']

        for i in range(n_months):
            total = late_vals[i] + ontime_vals[i] + expected_ontime_vals[i]
            if total == 0:
                continue
            x_pos = x[i] + offset

            if late_vals[i] > 0:
                ax.text(x_pos, late_vals[i]/2, f'{int(late_vals[i])}',
                       ha='center', va='center', fontsize=sizes['text'], color=colors['text'])
            if ontime_vals[i] > 0:
                ax.text(x_pos, late_vals[i] + ontime_vals[i]/2, f'{int(ontime_vals[i])}',
                       ha='center', va='center', fontsize=sizes['text'], color=colors['text'])
            if expected_ontime_vals[i] > 0:
                ax.text(x_pos, late_vals[i] + ontime_vals[i] + expected_ontime_vals[i]/2,
                      f'{int(expected_ontime_vals[i])}',
                      ha='center', va='center', fontsize=sizes['text'], color=colors['text'])

            late_pct = (late_vals[i] / total * 100) if total > 0 else 0
            ax.text(x_pos, total + max(late_vals + ontime_vals + expected_ontime_vals) * 0.03,
                   f'Total: {int(total)} POs\n({late_pct:.0f}% late)',
                   ha='center', va='bottom', fontsize=sizes['text'],
                   style='italic', color=colors['text'])

    # Configure axes
    ax.set_xlabel('POs ETA (Month)', fontsize=sizes['xlabel'])
    ax.set_xticks(x)
    ax.set_xticklabels(months, rotation=0)

    y_max = max(max(np.array(data_dict['finished']['late']) +
                    np.array(data_dict['finished']['ontime']) +
                    np.array(data_dict['finished']['expected_ontime'])),
                max(np.array(data_dict['unfinished']['late']) +
                    np.array(data_dict['unfinished']['ontime']) +
                    np.array(data_dict['finished']['expected_ontime'])
                    ))
    ax.set_ylim(0, y_max * 1.2)
    ax.set_yticklabels([])

    # Legend
    legend_elements = [
        Rectangle((0, 0), 1, 1,
                  facecolor=status_colors['late'],
                  alpha=0.85,
                  edgecolor='white',
                  linewidth=1,
                  label='Late'),
        Rectangle((0, 0), 1, 1,
                  facecolor=status_colors['ontime'],
                  alpha=0.85,
                  edgecolor='white',
                  linewidth=1,
                  label='Ontime'),
        Rectangle((0, 0), 1, 1,
                  facecolor=status_colors['expected_ontime'],
                  alpha=0.85,
                  edgecolor='white',
                  linewidth=1,
                  label='Expected Ontime'),
        Rectangle((0, 0), 1, 1,
                  facecolor='black',
                  alpha=0.3,
                  hatch=patterns['finished'],
                  label='Finished'),
        Rectangle((0, 0), 1, 1,
                  facecolor='black',
                  alpha=0.3,
                  hatch=patterns['unfinished'],
                  label='Unfinished')
    ]

    ax.set_title(f'{subplot_title} - Year {target_year} ({n_months} months)',
                 fontsize=sizes['title'],
                 fontweight='bold',
                 pad=10,
                 color=colors['title'])

    ax.legend(handles=legend_elements,
              bbox_to_anchor=(1.02, 1),
              loc='upper left',
              frameon=True,
              fancybox=True,
              shadow=True,
              fontsize=sizes['legend'])