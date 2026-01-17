from agents.decorators import validate_dataframe

def plot_mold_first_run_distribution(ax, df, colors, sizes):
    """
    Plot number of machines first run for each mold (horizontal bars)
    Only show molds that have run on more than 1 machine
    """

    subplot_title = 'Number of Machines Each Mold Has Run On'

    # Valid data frame
    required_columns = ['firstDate', 'machineCode', 'moldNo', 'acquisitionDate']
    validate_dataframe(df, required_columns)

    # Count machines per mold
    count_machine_per_mold = (
        df.groupby('moldNo')['machineCode']
        .nunique()
        .sort_values(ascending=True)
    )
    
    # Filter molds with more than 1 machine
    count_machine_per_mold = count_machine_per_mold[count_machine_per_mold > 1]
    
    # Generate colors
    bar_colors = colors['general'][:len(count_machine_per_mold)]
    
    # Create horizontal bars
    bars = ax.barh(
        range(len(count_machine_per_mold)),
        count_machine_per_mold.values,
        color=bar_colors
    )
    
    # Add value labels on bars
    for i, (bar, value) in enumerate(zip(bars, count_machine_per_mold.values)):
        ax.text(
            value + max(count_machine_per_mold.values)*0.01,
            bar.get_y() + bar.get_height()/2.,
            f'{int(value)}',
            ha='left',
            va='center',
            fontsize=sizes['bar_label']
        )
    
    # Set labels and title
    ax.set_yticks(range(len(count_machine_per_mold)))
    ax.set_yticklabels(
        count_machine_per_mold.index,
        fontsize=sizes['text']
    )
    
    ax.set_title(
        subplot_title,
        fontsize=sizes['title'],
        fontweight='bold',
        color=colors['title']
    )
    
    ax.set_xticks([])
    ax.set_ylabel('Mold No', fontsize=sizes['ylabel'], fontweight='bold')
    
    ax.legend(fontsize=sizes['legend'], 
              loc='upper right')
    
    ax.grid(True, alpha=0.3, axis='x')
    
    # Add statistics text
    total_molds = len(count_machine_per_mold)
    total_machines = df['machineCode'].nunique()
    avg_machines = count_machine_per_mold.mean()
    
    # Calculate single-machine molds from original data
    all_counts = df.groupby('moldNo')['machineCode'].nunique()
    single_machine_molds = len(all_counts[all_counts == 1])
    
    stats_text = f'Multi-Machine Molds: {total_molds} | Total Unique Machines: {total_machines} | Avg Machines/Mold: {avg_machines:.1f} | Single-Machine Molds (excluded): {single_machine_molds}'
    
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