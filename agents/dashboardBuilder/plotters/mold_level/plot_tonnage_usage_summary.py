from agents.decorators import validate_dataframe

def plot_tonnage_usage_summary(ax, df, colors, sizes):
    """
    Plot summary statistics of tonnage usage
    """
    
    # Valid data frame
    required_columns = ['moldNo', 'usedMachineTonnage', 'usedTonnageCount']
    validate_dataframe(df, required_columns)
    
    ax.axis('off')

    # Calculate statistics
    total_molds = len(df)
    avg_tonnages = df['usedTonnageCount'].mean()
    median_tonnages = df['usedTonnageCount'].median()
    max_tonnages = df['usedTonnageCount'].max()
    min_tonnages = df['usedTonnageCount'].min()
    single_tonnage_count = len(df[df['usedTonnageCount'] == 1])
    
    # Create summary text
    summary_text = f"""
    Machine Tonnage Utilization Summary
    
    Total Molds Analyzed: {total_molds:,}
    
    Average Tonnage Types Used: {avg_tonnages:.2f}
    Median Tonnage Types Used: {median_tonnages:.0f}
    
    Range: {min_tonnages} - {max_tonnages} tonnage types
    
    Molds Using Only 1 Tonnage: {single_tonnage_count} ({single_tonnage_count/total_molds*100:.1f}%)
    Molds Using Multiple Tonnages: {total_molds - single_tonnage_count} ({(total_molds - single_tonnage_count)/total_molds*100:.1f}%)
    """
    
    ax.text(0.5, 0.5, summary_text,
            transform=ax.transAxes,
            fontsize=sizes['title'],
            verticalalignment='center',
            horizontalalignment='center',
            bbox=dict(boxstyle='round', 
                     facecolor='white', 
                     edgecolor=colors['title'],
                     linewidth=2,
                     alpha=0.9),
            family='monospace')