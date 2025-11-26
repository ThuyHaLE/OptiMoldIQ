import numpy as np
from agents.decorators import validate_dataframe

def plot_mold_based_tonnage_distribution(ax, df, colors, sizes):
    """
    Plot a histogram of the distribution of tonnage types per mold
    """

    subplot_title = 'Distribution of Tonnage Variety per Mold'

    # Valid data frame
    required_columns = ['moldNo', 'usedMachineTonnage', 'usedTonnageCount']
    validate_dataframe(df, required_columns)

    max_count = df['usedTonnageCount'].max()
    bins = np.arange(0.5, max_count + 1.5, 1)
    
    n, bins_used, patches = ax.hist(df['usedTonnageCount'],
                                     bins=bins, 
                                     edgecolor='black', 
                                     alpha=0.7,
                                     color=colors.get('histogram', '#5dade2'))
    
    # Add values on bars
    for i, (patch, count) in enumerate(zip(patches, n)):
        if count > 0:
            ax.text(patch.get_x() + patch.get_width()/2., 
                    count + max(n)*0.01,
                    f'{int(count)}', 
                    ha='center', 
                    va='bottom', 
                    fontsize=sizes['bar_label'],
                    fontweight='bold')
    
    ax.set_xlabel('Number of Machine Tonnages Used', 
                  fontsize=sizes['xlabel'], 
                  fontweight='bold')
    
    ax.set_ylabel('Number of Molds', 
                  fontsize=sizes['ylabel'], 
                  fontweight='bold')
    
    ax.set_title(subplot_title,
                 fontsize=sizes['title'], 
                 fontweight='bold',
                 color=colors['title'])
    
    ax.set_xticks(range(1, max_count + 1))

    ax.grid(True, alpha=0.3, axis='y')