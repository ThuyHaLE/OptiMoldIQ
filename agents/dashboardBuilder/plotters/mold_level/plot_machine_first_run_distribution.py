from agents.decorators import validate_dataframe

def plot_machine_first_run_distribution(ax, df, colors, sizes, threshold=10):
    """
    Plot number of molds first run on each machine
    """

    subplot_title = 'Number of Molds First Run on Each Machine'

    # Valid data frame
    required_columns = ['firstDate', 'machineCode', 'moldNo', 'acquisitionDate']
    validate_dataframe(df, required_columns)

    # Count molds per machine
    count_mold_per_machine = (
        df.groupby('machineCode')['moldNo']
        .nunique()
        .sort_values(ascending=False)
    )
    
    # Generate colors
    bar_colors = colors['general'][:len(count_mold_per_machine)]
    
    # Create bars
    bars = ax.bar(
        range(len(count_mold_per_machine)),
        count_mold_per_machine.values,
        color=bar_colors
    )
    
    # Add threshold line
    machines_at_threshold = len(count_mold_per_machine[count_mold_per_machine <= threshold])
    ax.axhline(
        threshold,
        color=colors['highlight'],
        linestyle='--',
        linewidth=2,
        label=f'Threshold: {threshold} molds ({machines_at_threshold} machines below)'
    )
    
    # Add value labels on bars
    for i, (bar, value) in enumerate(zip(bars, count_mold_per_machine.values)):
        ax.text(
            bar.get_x() + bar.get_width()/2.,
            value + max(count_mold_per_machine.values)*0.01,
            f'{int(value)}',
            ha='center',
            va='bottom',
            fontsize=sizes['bar_label']
        )
    
    # Set labels and title
    ax.set_xticks(range(len(count_mold_per_machine)))
    ax.set_xticklabels(
        count_mold_per_machine.index,
        rotation=0,
        ha='center',
        fontsize=sizes['text']
    )
    
    ax.set_title(
        subplot_title,
        fontsize=sizes['title'],
        fontweight='bold',
        color=colors['title']
    )
    
    ax.set_yticks([])
    
    ax.legend(fontsize=sizes['legend'], 
              loc='upper right')
    
    ax.grid(True, alpha=0.3, axis='y')
    
    # Add statistics text
    total_machines = len(count_mold_per_machine)
    total_molds = df['moldNo'].nunique()
    avg_molds = count_mold_per_machine.mean()
    
    stats_text = f'Total Machines: {total_machines} | Total Unique Molds: {total_molds} | Avg Molds/Machine: {avg_molds:.1f}'
    
    ax.text(
        0.5, 0.98,
        stats_text,
        transform=ax.transAxes,
        fontsize=sizes['text'],
        ha='center',
        va='top',
        bbox=dict(
            boxstyle='round',
            facecolor='white',
            edgecolor=colors['text'],
            alpha=0.8
        )
    )