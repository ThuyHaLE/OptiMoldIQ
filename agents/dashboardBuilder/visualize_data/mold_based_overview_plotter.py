from agents.decorators import validate_init_dataframes
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from typing import Dict, Optional
import json
from loguru import logger
from agents.dashboardBuilder.visualize_data.utils import generate_color_palette

DEFAULT_CONFIG = {
    "colors": {
        'primary': '#3498DB',      # Blue
        'success': '#2ECC71',      # Green
        'warning': '#F39C12',      # Orange
        'danger': '#E74C3C',       # Red
        'secondary': '#95A5A6',    # Gray
        'dark': '#2C3E50'          # Dark blue
    },
    "sns_style": "seaborn-v0_8",
    "palette_name": "muted",
    "figsize": (25, 30),
    "gridspec_kw": {
        'hspace': 0.5,    
        'wspace': 0.5,    
        'top': 0.94,      
        'bottom': 0.04,   
        'left': 0.06,     
        'right': 0.96     
    },
    "main_title_y": 0.97,    
    "subtitle_y": 0.955,     
}

def deep_update(base: dict, updates: dict) -> Dict:
    for k, v in updates.items():
        if v is None:
            continue
        if isinstance(v, dict) and isinstance(base.get(k), Dict):
            base[k] = deep_update(base.get(k, {}), v)
        else:
            base[k] = v
    return base

def load_config(visualization_config_path: Optional[str] = None) -> Dict:
    """Load visualization configuration with fallback to defaults."""
    config = DEFAULT_CONFIG.copy()
    if visualization_config_path:
        try:
            with open(visualization_config_path, "r") as f:
                user_cfg = json.load(f)
            config = deep_update(config, user_cfg)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.warning(f"Could not load config from {visualization_config_path}: {e}")
    return config

def add_custom_colors(visualization_config: Dict, 
                      num_colors: int = 10):
    if 'color_list' not in visualization_config:
        colors = generate_color_palette(num_colors, 
                                        palette_name=visualization_config['palette_name'])
        visualization_config['color_list'] = colors
        return visualization_config
    
@validate_init_dataframes({"df": ['workingShift', 'moldNo', 'moldShot', 'moldCavity', 'itemTotalQuantity',
                                  'itemGoodQuantity', 'changeType', 'defectQuantity', 'defectRate']})

def mold_based_overview_plotter(df: pd.DataFrame,
                                main_title = 'Manufacturing Performance Dashboard',
                                subtitle = 'Comprehensive Analysis for Mold-based Records',
                                visualization_config_path: Optional[str] = None
                                ) -> plt.Figure:
    """
    Create comprehensive overview dashboard for mold-based analysis.

    Args:
        df: DataFrame containing item-based records
        main_title: Main chart title
        subtitle: Chart subtitle
        visualization_config_path: Path to JSON config file

    Returns:
        matplotlib.figure.Figure: The created figure
    """

    visualization_config = add_custom_colors(load_config(visualization_config_path))

    # Set style
    plt.style.use(visualization_config['sns_style'])
    logger.info('Used Seaborn style: {}.\nAvailable styles: {}', visualization_config['sns_style'], plt.style.available)

    # Create figure with subplots
    fig, ((ax1, ax2), (ax3, ax4), (ax5, ax6), (ax7, ax8), (ax9, ax10)) = plt.subplots(
        5, 2, figsize=visualization_config['figsize'],
        gridspec_kw=visualization_config['gridspec_kw']
    )

    # Enhanced main title
    fig.suptitle(f'{main_title}', fontsize=18, fontweight='bold', 
                 y=visualization_config['main_title_y'], 
                 color=visualization_config['colors']['dark'])
    fig.text(0.5, visualization_config['subtitle_y'], f'{subtitle}', 
             ha='center', fontsize=11, style='italic', 
             color=visualization_config['colors']['secondary'])

    # Create subplots
    plots_config = [
        (ax1, _plot_mold_based_bar_chart),
        (ax2, _plot_mold_based_shift_defect_rate),
        (ax3, _plot_mold_based_heatmap),
        (ax4, _plot_mold_based_shift_trend),
        (ax5, _plot_mold_based_cavities),
        (ax6, _plot_mold_based_defect_rate),
        (ax7, _plot_mold_based_production_distribution),
        (ax8, _plot_mold_based_shots_vs_defect_rate),
        (ax9, _plot_mold_based_shot_variation),
        (ax10, _plot_mold_based_good_vs_defect)
    ]

    for ax, plot_func in plots_config:
        try:
            plot_func(df, visualization_config, ax)
        except Exception as e:
            _plot_no_data(ax, visualization_config, f'Error: {str(e)}', 'Chart Error')
            logger.error(f"Error in {plot_func.__name__}: {e}")

    plt.tight_layout()
    return fig

def _plot_no_data(ax: plt.Axes, visualization_config:Dict, message: str, title: str) -> None:
        """
        Helper function to display no data message.

        Args:
            ax: Matplotlib axes object
            message: Message to display
            title: Chart title
        """
        ax.text(0.5, 0.5, message, ha='center', va='center',
               transform=ax.transAxes, fontsize=11,
               color=visualization_config['colors']['secondary'], style='italic')
        ax.set_title(title, fontweight='bold', fontsize=12, pad=15)
        ax.set_xticks([])
        ax.set_yticks([])

def _plot_mold_based_bar_chart(df: pd.DataFrame, visualization_config:Dict, ax: plt.Axes) -> None:
    """Plot total production by mold and shift."""
    try:
        pivot_total = df.pivot_table(
            values='itemTotalQuantity',
            index='moldNo',
            columns='workingShift',
            aggfunc='sum',
            fill_value=0
        )

        if pivot_total.empty:
            _plot_no_data(ax, visualization_config, 'No data to display', 'Production by Mold and Shift')
            return

        pivot_total.plot(kind='bar', ax=ax, width=0.8,
                        color=[visualization_config['colors']['danger'], 
                               visualization_config['colors']['primary'], 
                               visualization_config['colors']['success']])
        ax.set_title('Total Production by Mold and Shift', fontsize=14, fontweight='bold')
        ax.set_xlabel('Mold Code', fontsize=12)
        ax.set_ylabel('Product Quantity', fontsize=12)
        ax.legend(title='Shift', title_fontsize=10)
        ax.tick_params(axis='x', rotation=45)
        ax.grid(True, alpha=0.3)
    except Exception as e:
        _plot_no_data(ax, visualization_config, f'Error: {str(e)}', 'Production by Mold and Shift')

def _plot_mold_based_shift_defect_rate(df: pd.DataFrame, visualization_config:Dict, ax: plt.Axes) -> None:
    """Plot defect rate by mold and shift."""
    try:
        pivot_defect = df.pivot_table(
            values='defectRate',
            index='moldNo',
            columns='workingShift',
            aggfunc='mean',
            fill_value=0
        )

        if pivot_defect.empty:
            _plot_no_data(ax, visualization_config, 'No data to display', 'Defect Rate Analysis')
            return

        pivot_defect.plot(kind='bar', ax=ax, width=0.8,
                        color=[visualization_config['colors']['danger'], 
                               visualization_config['colors']['primary'], 
                               visualization_config['colors']['success']])
        ax.set_title('Average Defect Rate by Mold and Shift', fontsize=14, fontweight='bold')
        ax.set_xlabel('Mold Code', fontsize=12)
        ax.set_ylabel('Defect Rate (%)', fontsize=12)
        ax.legend(title='Shift', title_fontsize=10)
        ax.tick_params(axis='x', rotation=45)
        ax.grid(True, alpha=0.3)
    except Exception as e:
        _plot_no_data(ax, visualization_config, f'Error: {str(e)}', 'Defect Rate Analysis')

def _plot_mold_based_heatmap(df: pd.DataFrame, visualization_config:Dict, ax: plt.Axes) -> None:
    """Plot production heatmap."""
    try:
        pivot_total = df.pivot_table(
            values='itemTotalQuantity',
            index='moldNo',
            columns='workingShift',
            aggfunc='sum',
            fill_value=0
        )

        if pivot_total.empty:
            _plot_no_data(ax, visualization_config, 'No data to display', 'Production Heatmap')
            return

        sns.heatmap(pivot_total.astype(float), annot=True, fmt='g', cmap='YlOrRd', ax=ax)
        ax.set_title('Production Heat Map by Mold and Shift', fontsize=14, fontweight='bold')
        ax.set_xlabel('Shift', fontsize=12)
        ax.set_ylabel('Mold Code', fontsize=12)
    except Exception as e:
        _plot_no_data(ax, visualization_config, f'Error: {str(e)}', 'Production Heatmap')

def _plot_mold_based_shift_trend(df: pd.DataFrame, visualization_config:Dict, ax: plt.Axes) -> None:
    """Plot production trends by shift."""
    try:
        production_by_shift = df.groupby('workingShift').agg({
            'itemTotalQuantity': 'sum',
            'itemGoodQuantity': 'sum',
            'defectRate': 'mean'
        })

        if production_by_shift.empty:
            _plot_no_data(ax, visualization_config, 'No data to display', 'Shift Trends')
            return

        ax_twin = ax.twinx()

        # Bar charts for production
        x_pos = range(len(production_by_shift))
        bars1 = ax.bar([x - 0.2 for x in x_pos], production_by_shift['itemTotalQuantity'],
                        width=0.4, label='Total Production', alpha=0.7, color=visualization_config['colors']['primary'])
        bars2 = ax.bar([x + 0.2 for x in x_pos], production_by_shift['itemGoodQuantity'],
                        width=0.4, label='Good Products', alpha=0.7, color=visualization_config['colors']['success'])

        # Line for defect rate
        ax_twin.plot(x_pos, production_by_shift['defectRate'],
                    color=visualization_config['colors']['danger'], marker='o', linewidth=2, label='Defect Rate (%)')

        ax.set_title('Production Overview and Trends by Shift', fontsize=14, fontweight='bold')
        ax.set_xlabel('Shift', fontsize=12)
        ax.set_ylabel('Product Quantity', fontsize=12)
        ax_twin.set_ylabel('Defect Rate (%)', fontsize=12, color=visualization_config['colors']['danger'])

        # Add value labels on bars
        for bar in bars1:
            height = bar.get_height()
            if height > 0:
                ax.text(bar.get_x() + bar.get_width()/2., height + height * 0.01,
                        f'{int(height)}', ha='center', va='bottom', fontsize=9)

        for bar in bars2:
            height = bar.get_height()
            if height > 0:
                ax.text(bar.get_x() + bar.get_width()/2., height + height * 0.01,
                        f'{int(height)}', ha='center', va='bottom', fontsize=9)

        ax.set_xticks(x_pos)
        ax.set_xticklabels([f'Shift {int(shift)}' for shift in production_by_shift.index])
        ax.legend(loc='lower left')
        ax_twin.legend(loc='lower right')
        ax.grid(True, alpha=0.3)
    except Exception as e:
        _plot_no_data(ax, f'Error: {str(e)}', 'Shift Trends')

def _plot_mold_based_cavities(df: pd.DataFrame, visualization_config:Dict, ax: plt.Axes) -> None:
    """Plot cavities by mold and shift."""
    try:
        pivot_cavities = df.pivot_table(
            values='moldCavity',
            index='moldNo',
            columns='workingShift',
            aggfunc='sum',
            fill_value=0
        )

        if pivot_cavities.empty:
            _plot_no_data(ax, visualization_config, 'No data to display', 'Cavities Analysis')
            return

        pivot_cavities.plot(kind='bar', ax=ax, width=0.8,
                            color=[visualization_config['colors']['danger'], 
                                   visualization_config['colors']['primary'], 
                                   visualization_config['colors']['success']])
        ax.set_title('Total Cavities by Mold and Shift', fontsize=14, fontweight='bold')
        ax.set_xlabel('Mold Code', fontsize=12)
        ax.set_ylabel('Number of Cavities', fontsize=12)
        ax.legend(title='Shift', title_fontsize=10)
        ax.tick_params(axis='x', rotation=45)
        ax.grid(True, alpha=0.3)
    except Exception as e:
        _plot_no_data(ax, visualization_config, f'Error: {str(e)}', 'Cavities Analysis')

def _plot_mold_based_defect_rate(df: pd.DataFrame, visualization_config:Dict, ax: plt.Axes) -> None:
    """Plot defect rate by mold."""
    try:
        mold_stats = df.groupby('moldNo').agg({
            'itemTotalQuantity': 'sum',
            'itemGoodQuantity': 'sum',
            'defectRate': 'mean'
        }).sort_values('itemTotalQuantity', ascending=False)

        if mold_stats.empty:
            _plot_no_data(ax, visualization_config, 'No data to display', 'Defect Rate by Mold')
            return

        colors = visualization_config['color_list'][:len(mold_stats)]
        bars = ax.bar(range(len(mold_stats)), mold_stats['defectRate'],
                        color=colors, alpha=0.8)

        ax.set_title('Defect Rate by Mold', fontsize=14, fontweight='bold')
        ax.set_xlabel('Mold Code', fontsize=12)
        ax.set_ylabel('Defect Rate (%)', fontsize=12)
        ax.set_xticks(range(len(mold_stats)))
        ax.set_xticklabels(mold_stats.index, rotation=45)
        ax.grid(True, alpha=0.3)

        # Add labels for defect rate
        for i, bar in enumerate(bars):
            height = bar.get_height()
            if height > 0:
                ax.text(bar.get_x() + bar.get_width()/2., height + height * 0.01,
                        f'{mold_stats["defectRate"].iloc[i]:.1f}%',
                        ha='center', va='bottom', fontsize=10)
    except Exception as e:
        _plot_no_data(ax, visualization_config, f'Error: {str(e)}', 'Defect Rate by Mold')

def _plot_mold_based_production_distribution(df: pd.DataFrame, visualization_config:Dict, ax: plt.Axes) -> None:
    """Plot production distribution by mold."""
    try:
        mold_stats = df.groupby('moldNo').agg({
            'moldShot': 'sum'
        }).sort_values('moldShot', ascending=True)

        if mold_stats.empty:
            _plot_no_data(ax, visualization_config, 'No data to display', 'Shot Distribution')
            return

        y_pos = np.arange(len(mold_stats.index))
        bars = ax.barh(y_pos, mold_stats['moldShot'], alpha=0.8, color=visualization_config['colors']['primary'])
        ax.set_yticks(y_pos)
        ax.set_yticklabels(mold_stats.index)
        ax.set_xlabel('Total Shots', fontsize=12)
        ax.set_title('Total Shot Distribution by Mold', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3, axis='x')

        # Add value labels
        for i, bar in enumerate(bars):
            width = bar.get_width()
            if width > 0:
                ax.text(width + width * 0.01, bar.get_y() + bar.get_height()/2,
                        f'{int(width)}', ha='left', va='center', fontsize=9)
    except Exception as e:
        _plot_no_data(ax, visualization_config, f'Error: {str(e)}', 'Shot Distribution')

def _plot_mold_based_shots_vs_defect_rate(df: pd.DataFrame, visualization_config:Dict, ax: plt.Axes) -> None:
    """Plot scatter: shots vs defect rate."""
    try:
        scatter_data = df.groupby('moldNo').agg({
            'moldShot': 'sum',
            'defectRate': 'mean'
        })

        if scatter_data.empty:
            _plot_no_data(ax, visualization_config, 'No data to display', 'Shots vs Defect Rate')
            return

        scatter = ax.scatter(scatter_data['moldShot'], scatter_data['defectRate'],
                            s=100, alpha=0.6, c=range(len(scatter_data)), cmap='viridis')
        ax.set_xlabel('Total Shots', fontsize=12)
        ax.set_ylabel('Average Defect Rate (%)', fontsize=12)
        ax.set_title('Shot Count vs Defect Rate Correlation', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)

        # Add labels for points
        for idx, (mold, row) in enumerate(scatter_data.iterrows()):
            ax.annotate(mold, (row['moldShot'], row['defectRate']),
                        xytext=(5, 5), textcoords='offset points', fontsize=8)
    except Exception as e:
        _plot_no_data(ax, visualization_config, f'Error: {str(e)}', 'Shots vs Defect Rate')

def _plot_mold_based_shot_variation(df: pd.DataFrame, visualization_config:Dict, ax: plt.Axes) -> None:
    """Plot shot variation by shift."""
    try:
        shift_data = []
        shift_labels = []
        for shift in sorted(df['workingShift'].unique()):
            shift_shots = df[df['workingShift'] == shift]['moldShot'].dropna()
            if len(shift_shots) > 0:
                shift_data.append(shift_shots)
                shift_labels.append(f'Shift {int(shift)}')

        if not shift_data:
            _plot_no_data(ax, visualization_config, 'No shot data available', 'Shot Variation')
            return

        ax.boxplot(shift_data, labels=shift_labels)
        ax.set_title('Shot Count Distribution by Shift', fontsize=14, fontweight='bold')
        ax.set_ylabel('Number of Shots', fontsize=12)
        ax.grid(True, alpha=0.3)
    except Exception as e:
        _plot_no_data(ax, visualization_config, f'Error: {str(e)}', 'Shot Variation')

def _plot_mold_based_good_vs_defect(df: pd.DataFrame, visualization_config:Dict, ax: plt.Axes) -> None:
    """Plot stacked bar for good vs defective products."""
    try:
        mold_quality = df.groupby('moldNo').agg({
            'itemGoodQuantity': 'sum',
            'defectQuantity': 'sum'
        }).sort_values('itemGoodQuantity', ascending=True)

        if mold_quality.empty:
            _plot_no_data(ax, visualization_config, 'No data to display', 'Quality Distribution')
            return

        y_pos = np.arange(len(mold_quality.index))
        bars1 = ax.barh(y_pos, mold_quality['itemGoodQuantity'],
                        label='Good Products', alpha=0.8, color=visualization_config['colors']['success'])
        bars2 = ax.barh(y_pos, mold_quality['defectQuantity'],
                        left=mold_quality['itemGoodQuantity'],
                        label='Defective Products', alpha=0.8, color=visualization_config['colors']['danger'])

        ax.set_yticks(y_pos)
        ax.set_yticklabels(mold_quality.index)
        ax.set_xlabel('Product Quantity', fontsize=12)
        ax.set_title('Quality Distribution by Mold Performance', fontsize=14, fontweight='bold')
        ax.legend(loc='lower right')
        ax.grid(True, alpha=0.3, axis='x')
    except Exception as e:
        _plot_no_data(ax, visualization_config, f'Error: {str(e)}', 'Quality Distribution')