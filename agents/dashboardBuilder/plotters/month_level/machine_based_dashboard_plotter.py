from agents.dashboardBuilder.plotters.year_level.utils import process_machine_based_data
from agents.dashboardBuilder.plotters.utils import load_visualization_config, lighten_color, format_value_short
from agents.dashboardBuilder.plotters.year_level.utils import find_best_ncols, generate_coords

import matplotlib.pyplot as plt
from typing import Optional, List
import numpy as np
import seaborn as sns
import pandas as pd
import matplotlib.patheffects as pe
from agents.decorators import validate_dataframe
from loguru import logger

# Default config for visualization
DEFAULT_CONFIG = {
    "sns_style": "seaborn-v0_8-darkgrid",
    "sns_palette": "husl",
    "sns_set_style": "whitegrid",
    "plt_rcParams_update": {
        "figure.facecolor": "#f8f9fa",
        "axes.facecolor": "white",
        "axes.edgecolor": "#dee2e6",
        "axes.labelcolor": "#495057",
        "text.color": "#495057",
        "xtick.color": "#495057",
        "ytick.color": "#495057",
        "grid.color": "#e9ecef",
        "grid.linewidth": 0.8,
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "DejaVu Sans"],
        "font.size": 10
    },
    "layout_params": {
        "hspace": 0.95,
        "wspace": 0.3,
        "top": 0.96,
        "bottom": 0.06,
        "left": 0.06,
        "right": 0.97
    },
    "row_nums": 10,
    "column_nums": 3,
    "palette_name": "muted",
    "color_nums": 30,
    "colors": {
        "title": "#2c3e50",
        "text": "#718096",
        "subtitle": "#3c4a5b",
        "colors_severity": {
            "normal": "#95E1D3", 
            "critical": "#F38181"
        },
        "backlog": {
            "Active": "#95E1D3", 
            "Backlog": "#F38181"
        },
        "kpi": {
            "Total POs": "#667eea",
            "Backlog": "#feca57",
            "In-progress POs": "#fc5c65",
            "Not-started POs": "#fd79a8",
            "Finished POs": "#4caf50",
            "Late POs": "#e17055",
            "Avg progress": "#00b894",
            "Total progress": "#ffc107"
        }
    },
    "sizes": {
        "suptitle": 18,
        "progress_text": 30,
        "title": 12,
        "ylabel": 9,
        "xlabel": 9,
        "legend": 8,
        "text": 7
    }
}

def machine_based_dashboard_plotter(df: pd.DataFrame,
                                    visualization_metric: List,
                                    fig_title: str,
                                    visualization_config_path: Optional[str] = None
                                    ) -> plt.Figure:
        
        """
        Plot a multi-metric production dashboard for each machine based on monthly data.

        Parameters
        ----------
        df : pd.DataFrame
            Input dataframe containing machine-based production data.
        visualization_metric: List of metrics to plot
        fig_title : str
            Title of the dashboard figure.
        """

        # Valid data frame
        required_columns = ['recordDate', 'workingShift', 'machineNo', 'machineCode', 'itemCode',
                            'itemName', 'colorChanged', 'moldChanged', 'machineChanged', 'poNote',
                            'moldNo', 'moldShot', 'moldCavity', 'itemTotalQuantity',
                            'itemGoodQuantity', 'itemBlackSpot', 'itemOilDeposit', 'itemScratch',
                            'itemCrack', 'itemSinkMark', 'itemShort', 'itemBurst', 'itemBend',
                            'itemStain', 'otherNG', 'plasticResin', 'plasticResinCode',
                            'plasticResinLot', 'colorMasterbatch', 'colorMasterbatchCode',
                            'additiveMasterbatch', 'additiveMasterbatchCode', 'recordMonth']
        validate_dataframe(df, required_columns)

        # Data processing
        combined_summary = process_machine_based_data(df, 
                                                      group_by_month = False).reset_index()

        # Create machine index mapping
        machines = combined_summary['machineCode'].tolist()
        machine_index_map = {machine: idx + 1 for idx, machine in enumerate(machines)}

        # Load visualization config
        visualization_config = load_visualization_config(DEFAULT_CONFIG, 
                                                         visualization_config_path)

        # Visualization style settings
        plt.style.use(visualization_config["sns_style"])
        logger.info('Used Seaborn style: {}.\nAvailable styles: {}', 
                    visualization_config['sns_style'], plt.style.available)

        plt.rcParams['font.size'] = visualization_config["plt_rcParams_update"]["font.size"]
        plt.rcParams['figure.figsize'] = (18, 14)

        sizes = visualization_config["sizes"]

        # Generate colors
        base_colors = sns.color_palette(visualization_config["sns_palette"],
                                        len(machines))
        machine_colors = [lighten_color(c, 0.1) for c in base_colors]

        # Auto-determine fig size
        n_cols = find_best_ncols(len(visualization_metric))
        n_rows = int(np.ceil(len(visualization_metric) / n_cols))
        
        # Create subplot grid
        fig, axes = plt.subplots(n_rows, n_cols, 
                                 figsize=(n_cols * 6, n_rows * 4))
        

        coords = generate_coords(n_rows, n_cols)
        if n_rows == 1:
            axes = np.array([axes])
        if n_cols == 1:
            axes = axes[:, np.newaxis] if axes.ndim == 1 else axes

        # Plot
        for i, metric in enumerate(visualization_metric):
            r, c = coords[i]
            ax = axes[r, c]
            ax.set_facecolor("#FAFAFA")

            bar_width = 0.9

            vals = []
            for machine in machines:
                row = combined_summary[combined_summary['machineCode'] == machine]
                val = row[metric].iloc[0] if not row.empty else 0
                vals.append(val)

            metric_max = max(vals) or 1
            metric_min = min(vals) or 0

            x_pos = np.arange(len(machines))
            bars = ax.bar(
                x_pos, vals,
                width=bar_width,
                color=machine_colors,
                edgecolor='white',
                linewidth=1.0,
                alpha=0.9,
                zorder=3
            )

            if metric_max > 0:
                ax.hlines(metric_max, xmin=-0.5,
                          xmax=len(machines)-0.5,
                          color="#DDD",
                          linestyle='-.',
                          linewidth=1,
                          zorder=5)

            if metric_min > 0:
                ax.hlines(metric_min, xmin=-0.5,
                          xmax=len(machines)-0.5,
                          color="#DDD",
                          linestyle='--',
                          linewidth=1,
                          zorder=5)

            for bar, val in zip(bars, vals):
                if val > metric_max * 0.01:
                    label = format_value_short(val, decimal=1)
                    color = '#C0392B' if val == metric_min else '#333'
                    ax.text(
                        bar.get_x() + bar.get_width()/2, val,
                        label, ha='center', 
                        va='bottom',
                        fontsize=sizes['text'], 
                        color=color, 
                        zorder=4,
                        path_effects=[pe.withStroke(linewidth=2, 
                                                    foreground="white")]
                    )

            ax.set_title(metric, 
                         fontsize=sizes['title'], 
                         fontweight='semibold',
                         pad=7, 
                         color="#222")
            ax.set_ylim(0, metric_max * 1.2)

            # Set x-axis with mold indices
            ax.set_xticks(x_pos)
            ax.set_xticklabels([machine_index_map[machine] for machine in machines], 
                               fontsize=sizes["xlabel"])

            ax.set_yticks([])

            ax.grid(axis='x', color='#eee', linewidth=0.8, zorder=0)
            ax.grid(axis='y', color='#eee', linewidth=0.8, zorder=0)

            for spine in ['top', 'right', 'left']:
                ax.spines[spine].set_visible(False)

            ax.spines['bottom'].set_color('#CCC')

        for j in range(len(visualization_metric), len(coords)):
            r, c = coords[j]
            axes[r, c].set_visible(False)

        # Draw vertical separators between metrics
        for c in range(1, n_cols):
            fig.add_artist(plt.Line2D(
                [c / n_cols, c / n_cols], [0.03, 0.9],
                transform=fig.transFigure,
                color="#DDD", linestyle='-.', linewidth=1
            ))

        #Create title
        fig.suptitle(f'{fig_title}',
                     fontsize=sizes["suptitle"],
                     fontweight='bold',
                     color=visualization_config["colors"]["title"],
                     y=1.08)

        # Create legend
        legend_elements = [plt.Rectangle((0,0),1,1, 
                                         facecolor=color, 
                                         edgecolor='white',
                                         linewidth=0.8, 
                                         label=f"({machine_index_map[machine]})-{machine}")
                            for machine, color in zip(machines, machine_colors)]

        fig.legend(
            handles=legend_elements,
            loc='upper center',
            bbox_to_anchor=(0.5, 1.05),
            ncol=min(len(machines), int(np.ceil(len(machines)/2))),
            fontsize=sizes["legend"],
            frameon=False,
            handlelength=1.2,
            handletextpad=0.4,
            columnspacing=0.8
        )

        plt.tight_layout()
        
        return fig