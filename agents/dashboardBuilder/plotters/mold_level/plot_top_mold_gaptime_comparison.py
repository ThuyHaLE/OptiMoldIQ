from agents.decorators import validate_dataframe

def plot_top_mold_gaptime_comparison(ax, df, colors, sizes, top_n=20):
    """
    Top molds with longest gap time analysis
    """

    subplot_title = f'Top {top_n} Molds with Longest Gap'

    # Valid data frame
    required_columns = ['moldNo', 'acquisitionDate', 'firstDate', 'daysDifference']
    validate_dataframe(df, required_columns)


    sorted_df = df.sort_values('daysDifference', ascending=False)
    top_n_df = sorted_df.head(top_n)
    
    ax.barh(range(len(top_n_df)), 
            top_n_df['daysDifference'], 
            color=colors['gap_longest'], 
            alpha=0.7)
    
    ax.set_yticks(range(len(top_n_df)))

    ax.set_yticklabels(top_n_df['moldNo'], 
                       fontsize=sizes['text'])
    
    ax.set_xlabel('Days between Acquisition and First Use', 
                  fontsize=sizes['xlabel'])
    
    ax.set_title(subplot_title, 
                 fontsize=sizes['title'], 
                 fontweight='bold', 
                 color=colors['title'])
    
    ax.grid(True, alpha=0.3, axis='x')

    ax.invert_yaxis()