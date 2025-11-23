from agents.decorators import validate_dataframe

def plot_mold_based_tonnage_proportion_pie(ax, df, colors, sizes):
    """
    Plot a pie chart of mold proportions according to the number of tonnage types
    """

    subplot_title = 'Proportion of Molds by Number of Tonnage Types Used'

    # Valid data frame
    required_columns = ['moldNo', 'usedMachineTonnage', 'usedTonnageCount']
    validate_dataframe(df, required_columns)

    count_dist = df['usedTonnageCount'].value_counts().sort_index()
    pie_colors = colors['general'][:len(count_dist)]
    
    wedges, texts, autotexts = ax.pie(
        count_dist.values,
        labels=[f'{k} types\n({v} molds)' for k, v in count_dist.items()],
        autopct='%1.1f%%',
        startangle=140,
        colors=pie_colors,
        explode=[colors.get('pie_explode', 0.05)] * len(count_dist)
    )
    
    # Improve appearance
    for autotext in autotexts:
        autotext.set_color('black')
        autotext.set_fontweight('bold')
        autotext.set_fontsize(sizes['pie_percent'])
    
    for text in texts:
        text.set_fontsize(sizes['pie_label'])
        text.set_fontweight('bold')
    
    ax.set_title(subplot_title,
                 fontsize=sizes['title'], 
                 fontweight='bold',
                 color=colors['title'],
                 pad=20)