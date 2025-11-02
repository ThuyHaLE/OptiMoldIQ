from agents.decorators import validate_dataframe
from typing import Dict
import pandas as pd
import matplotlib.pyplot as plt

def plot_monthly_po_quantity(ax,
                             df: pd.DataFrame,
                             colors: Dict,
                             sizes: Dict,
                             target_year: str = None) -> None:
    """
    Plot a combined bar and line chart showing monthly PO counts and total item quantities.

    Parameters:
    -----------
    ax : matplotlib.axes.Axes
        The Axes object on which the chart is drawn.
    df : pd.DataFrame
        DataFrame containing the columns: 'poETA' (datetime), 'itemQuantity', 'poNo'.
    colors : Dict
        Dictionary containing chart colors.
    sizes : Dict
        Dictionary containing font sizes.
    target_year : str, optional
        The target year for analysis. If None, it will be inferred from the data.
    """

    subplot_title = 'Number of POs & Total Item Quantity'

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
    df_copy = df.copy()
    df_copy['poETA-mstr'] = df_copy['poETA'].dt.strftime('%Y-%m')

    # Aggregate by month
    monthly_sum = (
        df_copy
        .groupby('poETA-mstr')
        .agg(
            itemQuantity_sum=('itemQuantity', 'sum'),
            po_count=('poNo', 'count')
        )
        .reset_index()
        .sort_values('poETA-mstr')
    )

    # Determine the target year
    if target_year is None:
        target_year = str(df_copy['poETA'].dt.year.mode()[0])

    # Create the full month range
    if len(monthly_sum) > 0:
        # Step 1: Filter months belonging to the target year
        monthly_sum['year'] = monthly_sum['poETA-mstr'].str[:4]
        target_year_data = monthly_sum[monthly_sum['year'] == target_year]

        # Step 2: Always generate 12 months for the target year
        start_date = pd.Timestamp(year=int(target_year), month=1, day=1)
        end_date = pd.Timestamp(year=int(target_year), month=12, day=1)

        # Step 3: Extend the range if data exists outside the target year
        other_year_data = monthly_sum[monthly_sum['year'] != target_year]
        if len(other_year_data) > 0:
            data_min = pd.to_datetime(other_year_data['poETA-mstr'].min())
            data_max = pd.to_datetime(other_year_data['poETA-mstr'].max())

            # Extend backward if earlier months exist
            if data_min < start_date:
                start_date = data_min

            # Extend forward if later months exist
            if data_max > end_date:
                end_date = data_max

        # Drop the temporary column
        monthly_sum = monthly_sum.drop(columns=['year'])
    else:
        # No data → Create 12 months for the target year
        start_date = pd.Timestamp(year=int(target_year), month=1, day=1)
        end_date = pd.Timestamp(year=int(target_year), month=12, day=1)

    months_full = pd.date_range(start=start_date, end=end_date, freq='MS')
    months_full_str = months_full.strftime('%Y-%m')

    # Merge with actual data
    monthly_sum_full = (
        pd.DataFrame({'poETA-mstr': months_full_str})
        .merge(monthly_sum, on='poETA-mstr', how='left')
        .fillna(0)
    )

    # Disable grid
    ax.grid(False)

    # Draw bar chart – Number of POs
    bars = ax.bar(monthly_sum_full['poETA-mstr'],
                   monthly_sum_full['po_count'],
                   color='lightblue',
                   label='Number of POs',
                   alpha=0.7,
                   zorder=3)

    ax.set_xlabel('POs ETA (Month)', fontsize=sizes['xlabel'])
    ax.set_yticklabels([])

    # Add text labels above bars
    for i, (po_count, qty) in enumerate(zip(monthly_sum_full['po_count'],
                                            monthly_sum_full['itemQuantity_sum'])):
        if po_count > 0:
            label_text = f"{int(po_count):,} POs\n({int(qty):,})"
            ax.text(i, po_count, label_text,
                   ha='center', va='bottom', fontsize=sizes['text'],
                   color=colors.get('title', '#2c3e50'), zorder=10)

    # Create secondary y-axis for line chart
    ax2 = ax.twinx()
    ax2.grid(False)

    # Draw line chart – Total item quantity
    ax2.plot(monthly_sum_full['poETA-mstr'],
             monthly_sum_full['itemQuantity_sum'],
             marker='o',
             linewidth=1,
             markersize=4,
             label='Total Item Quantity',
             zorder=4)
    ax2.set_yticklabels([])

    # Align both y-axes starting from zero
    max_po = monthly_sum_full['po_count'].max()
    max_qty = monthly_sum_full['itemQuantity_sum'].max()

    ax.set_ylim(0, max_po * 1.2)  # Add 20% padding for text labels
    ax2.set_ylim(0, max_qty * 1.2)

    # Mark year boundaries
    months = monthly_sum_full['poETA-mstr'].tolist()
    n_months = len(months)

    for i in range(n_months - 1):
        current_year = int(months[i].split('-')[0])
        next_year = int(months[i + 1].split('-')[0])
        if current_year != next_year:
            boundary_x = i + 0.5
            ax.axvline(boundary_x,
                      color='#e74c3c',
                      linestyle='--',
                      linewidth=1.5,
                      alpha=0.6,
                      zorder=2)
            ax.text(boundary_x,
                   max_po * 1.2,
                   f'▼ {next_year}',
                   ha='center',
                   fontsize=sizes['text'],
                   fontweight='bold',
                   color='#e74c3c',
                   bbox=dict(boxstyle='round,pad=0.4',
                            facecolor='white',
                            edgecolor='#e74c3c',
                            linewidth=1),
                   zorder=5)

    # Format chart
    ax.set_title(f'{subplot_title} - Year {target_year} ({len(monthly_sum_full)} months)',
                 fontsize=sizes['title'],
                 fontweight='bold',
                 pad=25,
                 color=colors['title'])
    ax.tick_params(axis='x', rotation=0)
    plt.setp(ax.get_xticklabels(), rotation=0)

    # Combine legends
    lines, labels = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines + lines2, labels + labels2,
              bbox_to_anchor=(1.02, 1),
              loc='upper left',
              fontsize=sizes['legend'])