from agents.decorators import validate_dataframe

def plot_acquisition_firstuse_timegap(ax, df, colors, sizes):

    """
    Distribution of Time Gap between Acquisition and First Use
    """
    
    subplot_title = 'Distribution of Time Gap between Acquisition and First Use'
    
    # Valid data frame
    required_columns = ['moldNo', 'acquisitionDate', 'firstDate', 'daysDifference']
    validate_dataframe(df, required_columns)

    ax.hist(df['daysDifference'], 
            bins=30, 
            alpha=0.7, 
            edgecolor='black')
    
    ax.set_xlabel('Days between Acquisition and First Use', 
                  fontsize=sizes['xlabel'])
    
    ax.set_ylabel('Number of Molds', 
                  fontsize=sizes['ylabel'])
    
    ax.set_title(subplot_title, 
                 fontsize=sizes['title'], 
                 fontweight='bold', 
                 color=colors['title'])
    
    ax.grid(True, alpha=0.3)
    
    # Add statistics
    mean_days = df['daysDifference'].mean()
    median_days = df['daysDifference'].median()

    ax.axvline(mean_days, 
               color='red', 
               linestyle='--', 
               label=f'Mean: {mean_days:.1f} days', 
               linewidth=2)
    
    ax.axvline(median_days, 
               color='orange', 
               linestyle='--', 
               label=f'Median: {median_days:.1f} days', 
               linewidth=2)
    
    ax.legend(
        bbox_to_anchor=(1.02, 1),
        loc='center left',
        fontsize=sizes['legend'],
        framealpha=0.95)