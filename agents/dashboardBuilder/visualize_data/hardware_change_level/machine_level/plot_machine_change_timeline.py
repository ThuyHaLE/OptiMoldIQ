import matplotlib.pyplot as plt
from agents.decorators import validate_dataframe

def plot_machine_change_timeline(ax, df, unique_machines, colors, sizes):

    """
    Plot timeline showing layout changes for all machines
    """
    subplot_title = 'Layout Change Timeline For All Machines'
    
    # Valid data frame
    required_columns = ['machineCode', 'machineName', 'changedDate', 'machineNo', 'machineNo_numeric']
    validate_dataframe(df, required_columns)

    # Generate colors for machines
    color_palette = colors['general']
    machine_colors = {machine: color_palette[i] for i, machine in enumerate(unique_machines)}
    
    # Plot timeline for each machine
    for machine_code in unique_machines:
        machine_data = df[df['machineCode'] == machine_code].sort_values('changedDate')
        color = machine_colors[machine_code]
        
        if len(machine_data) > 1:
            ax.plot(machine_data['changedDate'], 
                    machine_data['machineNo_numeric'],
                   color=color, 
                   linewidth=2, 
                   alpha=0.7, 
                   marker='o', 
                   markersize=6)
        else:
            ax.scatter(machine_data['changedDate'], 
                       machine_data['machineNo_numeric'],
                      color=color, 
                      s=80, 
                      alpha=0.8, 
                      edgecolors='white', 
                      linewidth=1)
    
    ax.set_title(subplot_title, 
                 fontsize=sizes['title'], 
                 fontweight='bold', 
                 color=colors['title'])

    # Show all machineNo values on Y axis
    all_machine_numbers = sorted(df['machineNo_numeric'].unique())
    ax.set_yticks(all_machine_numbers)
    ax.set_yticklabels([f'NO.{num:02d}' for num in all_machine_numbers])

    ax.set_xticks(machine_data['changedDate'].unique())
    
    ax.grid(True, 
            alpha=0.3, 
            linestyle='--')
    
    ax.tick_params(axis='x', 
                   rotation=0, 
                   labelsize=sizes['tick'])
    
    ax.tick_params(axis='y', 
                   labelsize=sizes['text'])
    
    # Legend optimization based on number of machines
    n_unique = len(unique_machines)
    legend_elements = [plt.Line2D([0], [0], color=color, lw=3, label=code)
                      for code, color in machine_colors.items()]
    
    if n_unique <= 20:
        ax.legend(handles=legend_elements, 
                  title='Machine Code',
                  bbox_to_anchor=(1.05, 1), 
                  loc='upper left',
                  fontsize=sizes['legend'], 
                  title_fontsize=sizes['legend']+2)
    else:
        ncol = min(3, (n_unique + 15) // 16)
        ax.legend(handles=legend_elements, 
                  title='Machine Code',
                  bbox_to_anchor=(1.05, 1), 
                  loc='upper left',
                  fontsize=sizes['legend']-1, 
                  title_fontsize=sizes['legend']+1, 
                  ncol=ncol)