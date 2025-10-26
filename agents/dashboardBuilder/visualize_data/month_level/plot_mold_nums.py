from agents.decorators import validate_init_dataframes
from typing import Dict
import pandas as pd

@validate_init_dataframes({"df": ['poNo', 'itemCodeName', 'is_backlog', 'poStatus', 'itemQuantity',
                                  'itemGoodQuantity', 'etaStatus', 'proStatus', 'moldHistNum']})
    
def plot_mold_nums(ax, 
                   df: pd.DataFrame, 
                   colors: Dict, 
                   sizes: Dict):
    """
    Plot used mold nums for finished POs
    """

    subplot_title = 'Used Mold Nums (Finished POs)'

    if df.empty:
        ax.text(0.5, 0.5, 'No data available', 
                ha='center', va='center', 
                fontsize=sizes['title'],
                color=sizes['title'])
        ax.set_title(subplot_title,
                    fontsize=sizes['title'],
                    color=colors['title'],
                    fontweight='bold')
        ax.axis('off')
        return
    
    moldHistNum_counts = df[df['proStatus'] == 'finished']['moldHistNum'].astype(int).astype('str').value_counts()
    
    mold_nums = df[df['proStatus'] == 'finished']['moldHistNum'].astype(int).astype('str').unique().tolist()
    
    mold_nums_color_map = dict(zip(mold_nums, colors['general'][:len(mold_nums)]))
    
    bars = ax.bar(
        moldHistNum_counts.index,
        moldHistNum_counts.values,
        color=[mold_nums_color_map[x] for x in moldHistNum_counts.index]
    )
    ax.set_title(
        subplot_title,
        fontsize=sizes['title'],
        color=colors['title'],
        fontweight='bold',
        pad=15
    )
    ax.set_ylabel('Number of POs', fontsize=sizes['ylabel'])
    
    for bar in bars:
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width()/2.,
            height,
            f'{int(height)}',
            ha='center', va='bottom'
        )