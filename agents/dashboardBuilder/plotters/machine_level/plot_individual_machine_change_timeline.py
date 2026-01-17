import numpy as np
import math
from agents.decorators import validate_dataframe

def plot_individual_machine_change_timeline(subfig, 
                                            df, 
                                            unique_machines, 
                                            colors, 
                                            sizes, 
                                            max_change_threshold=5, 
                                            ncols=2):
    """
    Plot individual timeline for each machine in subplots within a subfigure
    
    Parameters:
    -----------
    subfig : matplotlib.figure.SubFigure
        SubFigure object to plot on
    df : DataFrame
        Data containing machine layout changes
    unique_machines : list
        List of unique machine codes
    colors : dict
        Color configuration
    sizes : dict
        Font size configuration
    max_change_threshold : int
        Threshold for highlighting machines with most changes
    ncols : int
        Number of columns in subplot grid (default: 2)
    """
    
    # Validate dataframe
    required_columns = ['machineCode', 'machineName', 'changedDate', 'machineNo', 'machineNo_numeric']
    validate_dataframe(df, required_columns)
    
    # Calculate number of rows needed
    n_machines = len(unique_machines)
    nrows = math.ceil(n_machines / ncols)
    
    # Create subplots within the subfigure
    axes = subfig.subplots(nrows, ncols)
    
    # Flatten axes array for easier iteration
    if n_machines == 1:
        axes = [axes]
    else:
        axes = axes.flatten() if isinstance(axes, np.ndarray) else [axes]
    
    # Generate colors for machines
    color_palette = colors['general']
    machine_colors = {machine: color_palette[i] for i, machine in enumerate(unique_machines)}
    
    # Count changes per machine for highlighting
    change_counts = df.groupby('machineCode').size()
    
    # Plot each machine in its own subplot
    for idx, machine_code in enumerate(unique_machines):
        ax = axes[idx]
        machine_data = df[df['machineCode'] == machine_code].sort_values('changedDate')
        color = machine_colors[machine_code]
        
        # Get machine name and change count
        machine_name = machine_data['machineName'].iloc[0] if not machine_data.empty else ''
        change_count = change_counts.get(machine_code, 0)
        
        # Determine if this machine should be highlighted
        is_high_change = change_count >= max_change_threshold
        title_color = colors['highlight'] if is_high_change else color
        
        # Plot data
        if len(machine_data) > 1:
            ax.plot(machine_data['changedDate'], 
                    machine_data['machineNo_numeric'],
                    color=color, 
                    linewidth=2.5, 
                    alpha=0.8, 
                    marker='o', 
                    markersize=8)
        else:
            ax.scatter(machine_data['changedDate'], 
                       machine_data['machineNo_numeric'],
                       color=color, 
                       s=100, 
                       alpha=0.9, 
                       edgecolors='white', 
                       linewidth=2)

        # Set title with machine code, name and change count
        title_text = f'{machine_code}({change_count} changes)'
        ax.set_title(title_text, 
                     fontsize=sizes['text'], 
                     color=title_color,
                     bbox=dict(boxstyle='round,pad=0.5', 
                              facecolor=colors['highlight_bg'] if is_high_change else 'white',
                              edgecolor=title_color,
                              linewidth=2 if is_high_change else 1,
                              alpha=0.3 if is_high_change else 0))
        
        ax.set_yticks([])
        
        # Set x-axis with dates
        ax.set_xticks(machine_data['changedDate'].unique())
        ax.tick_params(axis='x', rotation=0, labelsize=sizes['tick']-1)
        
        # Add grid
        ax.grid(True, alpha=0.3, linestyle='--')
        
        # Add value labels on points
        for _, row in machine_data.iterrows():
            ax.annotate(f"NO.{int(row['machineNo_numeric']):02d}", 
                        (row['changedDate'], row['machineNo_numeric']),
                        textcoords="offset points", 
                        xytext=(0, 10), 
                        ha='center',
                        fontsize=sizes['text']-2,
                        bbox=dict(boxstyle='round,pad=0.3', 
                                  facecolor='white', 
                                  edgecolor=color, 
                                  alpha=0.7))
    
    # Hide empty subplots if any
    for idx in range(n_machines, len(axes)):
        axes[idx].set_visible(False)