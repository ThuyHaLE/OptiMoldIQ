from agents.decorators import validate_dataframe

def plot_acquisition_firstuse_comparison(ax, df, colors, sizes):
    """
    Comparison of Acquisition Date and First Use Date
    """

    subplot_title = 'Comparison of Acquisition Date and First Use Date'
    
    # Valid data frame
    required_columns = ['moldNo', 'acquisitionDate', 'firstDate', 'daysDifference']
    validate_dataframe(df, required_columns)

    df['moldIndex'] = range(len(df))
    
    ax.scatter(df['moldIndex'], 
               df['acquisitionDate'],
               label='Acquisition Date', 
               alpha=0.6, 
               s=20,
               color=colors['acquisition'])
    
    ax.scatter(df['moldIndex'], 
               df['firstDate'],
               label='First Use Date', 
               alpha=0.6, 
               s=20,
               color=colors['first_use'])
    
    ax.set_xticks([])
    ax.set_ylabel('Date', 
                  fontsize=sizes['ylabel'])
    
    ax.set_title(subplot_title, 
                 fontsize=sizes['title'], 
                 fontweight='bold', 
                 color=colors['title'])
    
    ax.legend(
        bbox_to_anchor=(1.02, 1),
        loc='center left',
        fontsize=sizes['legend'],
        framealpha=0.95)
    
    ax.grid(True, alpha=0.3)