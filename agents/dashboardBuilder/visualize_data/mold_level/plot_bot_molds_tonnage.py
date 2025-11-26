from agents.decorators import validate_dataframe

def plot_bot_molds_tonnage(ax, df, colors, sizes, bot_n=20):
    """
    Plot the bottom N molds with the fewest machine tonnage types
    """

    subplot_title = f'Bottom {bot_n} Molds with Least Machine Tonnage Types Used'

    # Valid data frame
    required_columns = ['moldNo', 'usedMachineTonnage', 'usedTonnageCount']
    validate_dataframe(df, required_columns)

    bottom_molds = df.nsmallest(bot_n, 'usedTonnageCount')
    bar_colors = colors['general'][:len(bottom_molds)]
    
    bars = ax.barh(range(len(bottom_molds)),
                   bottom_molds['usedTonnageCount'],
                   color=bar_colors)
    
    # Add value labels on bars (for horizontal bars)
    for i, (bar, value) in enumerate(zip(bars, bottom_molds['usedTonnageCount'])):
        width = bar.get_width()
        ax.text(
            width,
            bar.get_y() + bar.get_height()/2.,
            f'{int(value)}',
            ha='left',
            va='center',
            fontsize=sizes['text']
        )

    # Optimize labels
    ax.set_yticks(range(len(bottom_molds)))
    ax.set_yticklabels(bottom_molds['moldNo'], 
                       fontsize=sizes['text'])
    
    ax.set_ylabel('Mold No', 
                  fontsize=sizes['ylabel'], 
                  fontweight='bold')

    ax.set_xlabel('Number of Used Tonnages', 
                  fontsize=sizes['xlabel'], 
                  fontweight='bold')
    
    ax.set_title(subplot_title,
                 fontsize=sizes['title'], 
                 fontweight='bold', 
                 color=colors['title'])
    
    ax.set_xticks([])
    
    ax.grid(True, alpha=0.3, axis='x')
    ax.invert_yaxis()