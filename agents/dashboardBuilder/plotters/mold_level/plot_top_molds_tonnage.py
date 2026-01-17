from agents.decorators import validate_dataframe

def plot_top_molds_tonnage(ax, df, colors, sizes, top_n=20):
    """
    Plot the top N molds with the most machine tonnage types.
    """

    subplot_title = f'Top {top_n} Molds with Least Machine Tonnage Types Used'

    # Valid data frame
    required_columns = ['moldNo', 'usedMachineTonnage', 'usedTonnageCount']
    validate_dataframe(df, required_columns)

    top_molds = df.nlargest(top_n, 'usedTonnageCount')
    bar_colors = colors['general'][:len(top_molds)]
    
    bars = ax.barh(range(len(top_molds)),
                   top_molds['usedTonnageCount'],
                   color=bar_colors)
    
    # Add value labels on bars (for horizontal bars)
    for i, (bar, value) in enumerate(zip(bars, top_molds['usedTonnageCount'])):
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
    ax.set_yticks(range(len(top_molds)))
    ax.set_yticklabels(top_molds['moldNo'], 
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