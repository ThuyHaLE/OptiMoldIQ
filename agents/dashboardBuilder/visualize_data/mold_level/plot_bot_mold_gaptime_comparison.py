from agents.decorators import validate_dataframe

def plot_bot_mold_gaptime_comparison(ax, df, colors, sizes, bot_n=20):

    """
    Bottom molds with shortest gap time analysis
    """
    
    subplot_title = f'Top {bot_n} Molds with Shortest Gap'

    # Valid data frame
    required_columns = ['moldNo', 'acquisitionDate', 'firstDate', 'daysDifference']
    validate_dataframe(df, required_columns)

    sorted_df = df.sort_values('daysDifference', ascending=True)
    bot_n_df = sorted_df.head(bot_n)
    
    ax.barh(range(len(bot_n_df)), 
            bot_n_df['daysDifference'], 
            color=colors['gap_shortest'], alpha=0.7)
    
    ax.set_yticks(range(len(bot_n_df)))

    ax.set_yticklabels(bot_n_df['moldNo'], 
                       fontsize=sizes['text'])
    
    ax.set_xlabel('Days between Acquisition and First Use', 
                  fontsize=sizes['xlabel'])
    
    ax.set_title(subplot_title, 
                 fontsize=sizes['title'], 
                 fontweight='bold', 
                 color=colors['title'])
    
    ax.grid(True, alpha=0.3, axis='x')
    
    ax.invert_yaxis()