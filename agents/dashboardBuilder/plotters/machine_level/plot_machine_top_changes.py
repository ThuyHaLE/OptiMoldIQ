from agents.decorators import validate_dataframe
import pandas as pd

def plot_machine_top_changes(ax, df, colors, sizes, top_n=15):
    """
    Plot bar chart showing top N machines with most layout changes
    """

    subplot_title = f'Top {top_n} Machines with Most Layout Change Times'
    
    # Valid data frame
    required_columns = ['machineCode', 'machineName', 'changedDate', 'machineNo', 'machineNo_numeric']
    validate_dataframe(df, required_columns)

    ax.set_title(subplot_title,
                fontsize=sizes['title'], 
                fontweight='bold', 
                color=colors['title'])
    
    #Calculate change statistics
    change_stats = (
        df.groupby('machineCode')['machineNo'].nunique() - 1
    ).to_dict()
    
    # Filter out machine with change count > 0
    filtered_stats = {k: v for k, v in change_stats.items() if v > 0}
    
    if not filtered_stats:
        # Detect machines added (no position changes) if any
        df_temp = df.copy()
        df_temp['machineInfo'] = df_temp['machineNo'] + ' & ' + df_temp['machineCode']
        
        # Get machines by timeline
        sorted_timelines = sorted(df_temp['changedDate'].unique())
        
        if len(sorted_timelines) > 1:
            first_timeline = sorted_timelines[0]
            first_machines = set(df_temp[df_temp['changedDate'] == first_timeline]['machineCode'])
            
            all_machines = set(df_temp['machineCode'])
            new_machines = all_machines - first_machines
            
            if new_machines:
                # Get layout change timeline
                new_machine_info = df_temp[
                    df_temp['machineCode'].isin(new_machines)
                ][['machineCode', 'machineNo', 'changedDate']].drop_duplicates()
                
                # Group by changedDate to display by timeline
                new_machine_list = []
                for date in sorted(new_machine_info['changedDate'].unique()):
                    machines_on_date = new_machine_info[new_machine_info['changedDate'] == date]
                    date_str = date.strftime('%Y-%m-%d')
                    
                    for _, row in machines_on_date.iterrows():
                        new_machine_list.append(f"{date_str}: {row['machineNo']} is {row['machineCode']}")
                
                message = f"No layout changes detected\n\nBut added {len(new_machines)} new machine(s):\n" + "\n".join(new_machine_list)
            else:
                message = 'No layout changes detected'
        else:
            message = 'No layout changes detected'
        
        ax.text(0.5, 0.5, message,
                transform=ax.transAxes,
                fontsize=sizes['text'],
                ha='center', va='center',
                bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.5))
        ax.axis('off')
        return change_stats
    
    machine_change_df = pd.DataFrame(
        list(filtered_stats.items()),
        columns=['machineCode', 'n_changes']).sort_values(
            'n_changes', ascending=False).head(top_n)
    
    color_list = colors['general'][:len(machine_change_df)]

    bars = ax.bar(range(len(machine_change_df)), 
                  machine_change_df['n_changes'],
                  color=color_list, 
                  alpha=0.8, 
                  edgecolor='darkred', 
                  linewidth=1)

    # Add value labels on bars
    for i, (bar, value) in enumerate(zip(bars, machine_change_df['n_changes'])):
        ax.text(
            bar.get_x() + bar.get_width()/2.,
            value + max(machine_change_df['n_changes'])*0.01,
            f'{int(value)}',
            ha='center',
            va='bottom',
            fontsize=sizes['bar_label']
        )
    
    ax.set_xticks(range(len(machine_change_df)))
    ax.set_xticklabels(machine_change_df['machineCode'], 
                       rotation=0, ha='center')
    ax.set_yticks([])
    
    ax.grid(True, alpha=0.3, axis='y', linestyle='--')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.tick_params(labelsize=sizes['tick'])