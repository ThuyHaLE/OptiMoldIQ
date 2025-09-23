import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import warnings
from typing import Optional, Dict
import matplotlib.patches as mpatches
from agents.decorators import validate_init_dataframes
from loguru import logger
from agents.dashboardBuilder.visualize_data.utils import generate_color_palette, load_visualization_config

# Optional import for text adjustment - gracefully handle if not available
try:
    from adjusttext import adjust_text
    ADJUSTTEXT_AVAILABLE = True
except ImportError:
    ADJUSTTEXT_AVAILABLE = False
    warnings.warn("adjustText not available. Labels in scatter plots may overlap.", UserWarning)

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')

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
    "figsize": (20, 24),
    "gridspec_kw": {
        'hspace': 0.4,
        'wspace': 0.2,
        'top': 0.92,
        'bottom': 0.05,
        'left': 0.08,
        'right': 0.95
        },
    "main_title_y": 0.96,
    "subtitle_y": 0.94,
}

def add_custom_colors(visualization_config: Dict, 
                      num_colors: int = 10):
    if 'color_list' not in visualization_config:
        colors = generate_color_palette(num_colors, 
                                        palette_name=visualization_config['palette_name'])
        visualization_config['color_list'] = colors
        return visualization_config
    
@validate_init_dataframes({"df": ['itemInfo', 'itemTotalQuantity', 'itemGoodQuantity', 'defectRate',
                                  'usedMachineNums', 'usedComponentNums', 'usedMoldNums',
                                  'moldTotalShots', 'avgCavity', 'itemNameShort']})

def item_based_overview_plotter(df: pd.DataFrame,
                                main_title = 'Manufacturing Performance Dashboard',
                                subtitle = 'Comprehensive Analysis for Item-based Records',
                                visualization_config_path: Optional[str] = None) -> plt.Figure:
    """
    Create comprehensive overview dashboard for item-based analysis.

    Args:
        df: DataFrame containing item-based records
        main_title: Main chart title
        subtitle: Chart subtitle
        visualization_config_path: Path to JSON config file

    Returns:
        matplotlib.figure.Figure: The created figure
    """

    df = _preprocess_data(df)

    visualization_config = add_custom_colors(
        load_visualization_config(DEFAULT_CONFIG, visualization_config_path)
        )

    # Set style
    plt.style.use(visualization_config['sns_style'])
    logger.info('Used Seaborn style: {}.\nAvailable styles: {}', visualization_config['sns_style'], plt.style.available)

    # Create figure with subplots
    fig, ((ax1, ax2), 
          (ax3, ax4), 
          (ax5, ax6), 
          (ax7, ax8)) = plt.subplots(
              4, 2, figsize=visualization_config['figsize'],
              gridspec_kw=visualization_config['gridspec_kw'])

    # Enhanced main title
    fig.suptitle(f'{main_title}', fontsize=18, fontweight='bold', y=visualization_config['main_title_y'], color=visualization_config['colors']['dark'])
    fig.text(0.5, visualization_config['subtitle_y'], f'{subtitle}', ha='center', fontsize=11, style='italic', color=visualization_config['colors']['secondary'])

    # Create subplots
    plots_config = [
        (ax1, _plot_item_based_defect_rate),
        (ax2, _plot_item_based_efficiency),
        (ax3, _plot_item_based_production_volume),
        (ax4, _plot_item_based_total_shots),
        (ax5, _plot_item_based_machine_usage),
        (ax6, _plot_item_based_cavity_vs_shots),
        (ax7, _plot_item_based_shots_share),
        (ax8, _plot_item_based_production_share)
    ]

    for ax, plot_func in plots_config:
        try:
            plot_func(df, visualization_config, ax)
        except Exception as e:
            _plot_no_data(ax, visualization_config, f'Error: {str(e)}', 'Chart Error')
            logger.error(f"Error in {plot_func.__name__}: {e}")

    plt.tight_layout()

    return fig

def _preprocess_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Preprocess data for visualization.

    Args:
        df: Input DataFrame

    Returns:
        pd.DataFrame: Preprocessed DataFrame
    """
    df = df.copy()

    # Calculate efficiency if not exists
    if 'efficiency' not in df.columns and 'itemTotalQuantity' in df.columns and 'itemGoodQuantity' in df.columns:
        df['efficiency'] = np.where(
            df['itemTotalQuantity'] > 0,
            (df['itemGoodQuantity'] / df['itemTotalQuantity'] * 100),
            0
        )

    # Clean item names for better display if itemInfo exists
    if 'itemInfo' in df.columns:
        df['itemName'] = df['itemInfo'].str.split('(').str[0].str.strip()
        df['itemNameShort'] = df['itemName'].apply(
            lambda x: x[:15] + '...' if len(str(x)) > 15 else str(x)
        )

    # Fill NaN values in numeric columns
    numeric_columns = df.select_dtypes(include=[np.number]).columns
    df[numeric_columns] = df[numeric_columns].fillna(0)

    return df

def _plot_no_data(ax: plt.Axes,
                  visualization_config: Dict,
                  message: str,
                  title: str) -> None:
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

def _plot_item_based_defect_rate(df: pd.DataFrame, visualization_config: Dict, ax: plt.Axes) -> None:
    """Plot defect rate analysis."""
    try:
        defect_data = df[df['defectRate'] > 0].sort_values('defectRate', ascending=True)

        if len(defect_data) == 0:
            _plot_no_data(ax, visualization_config, 'No defect data available', 'Defect Rate Analysis')
            return

        # Create gradient colors based on defect rate
        colors = []
        for rate in defect_data['defectRate']:
            if rate <= 2:
                colors.append(visualization_config['colors']['success'])
            elif rate <= 5:
                colors.append(visualization_config['colors']['warning'])
            else:
                colors.append(visualization_config['colors']['danger'])

        # Create horizontal bar chart
        bars = ax.barh(range(len(defect_data)), defect_data['defectRate'],
                        color=colors, alpha=0.8, edgecolor='white', linewidth=1)

        ax.set_yticks(range(len(defect_data)))
        ax.set_yticklabels(defect_data['itemNameShort'], fontsize=9)
        ax.set_xlabel('Defect Rate (%)', fontweight='bold', fontsize=10)
        ax.set_title('Defect Rate Analysis', fontweight='bold', fontsize=12, pad=15)

        # Add value labels
        max_rate = defect_data['defectRate'].max()
        for i, (bar, rate) in enumerate(zip(bars, defect_data['defectRate'])):
            width = bar.get_width()
            ax.text(width + max_rate * 0.01, bar.get_y() + bar.get_height()/2,
                    f'{rate:.1f}%', ha='left', va='center',
                    fontsize=8, fontweight='bold')

        # Add reference lines
        ax.axvline(x=2, color=visualization_config['colors']['success'], linestyle='--', alpha=0.6, linewidth=2)
        ax.axvline(x=5, color=visualization_config['colors']['warning'], linestyle='--', alpha=0.6, linewidth=2)

        # Enhanced legend
        legend_elements = [
            mpatches.Patch(color=visualization_config['colors']['success'], label='Excellent (≤2%)'),
            mpatches.Patch(color=visualization_config['colors']['warning'], label='Good (2-5%)'),
            mpatches.Patch(color=visualization_config['colors']['danger'], label='Needs Attention (>5%)')
        ]
        ax.legend(handles=legend_elements, loc='lower right', fontsize=7, framealpha=0.9)
        ax.grid(axis='x', alpha=0.3)
    except Exception as e:
        _plot_no_data(ax, visualization_config, f'Error: {str(e)}', 'Shot Distribution')

def _plot_item_based_efficiency(df: pd.DataFrame, visualization_config: Dict, ax: plt.Axes) -> None:
    """Plot efficiency analysis."""
    try:
        efficiency_data = df.sort_values('efficiency', ascending=True)

        colors = []
        for eff in efficiency_data['efficiency']:
            if eff >= 95:
                colors.append(visualization_config['colors']['success'])
            elif eff >= 90:
                colors.append(visualization_config['colors']['warning'])
            else:
                colors.append(visualization_config['colors']['danger'])

        bars = ax.barh(range(len(efficiency_data)), efficiency_data['efficiency'],
                        color=colors, alpha=0.8, edgecolor='white', linewidth=1)

        ax.set_yticks(range(len(efficiency_data)))
        ax.set_yticklabels(efficiency_data['itemNameShort'], fontsize=9)
        ax.set_xlabel('Efficiency (%)', fontweight='bold', fontsize=10)
        ax.set_title('Production Efficiency', fontweight='bold', fontsize=12, pad=15)
        ax.set_xlim(0, 100)

        # Add value labels
        for i, (bar, eff) in enumerate(zip(bars, efficiency_data['efficiency'])):
            width = bar.get_width()
            label_color = 'white' if width > 50 else visualization_config['colors']['dark']
            ax.text(width - 2 if width > 10 else width + 2,
                    bar.get_y() + bar.get_height()/2,
                    f'{eff:.1f}%', ha='right' if width > 10 else 'left',
                    va='center', fontsize=8, fontweight='bold', color=label_color)

        # Reference lines
        ax.axvline(x=90, color=visualization_config['colors']['danger'], linestyle='--', alpha=0.6, linewidth=2)
        ax.axvline(x=95, color=visualization_config['colors']['success'], linestyle='--', alpha=0.6, linewidth=2)
        ax.grid(axis='x', alpha=0.3)
    except Exception as e:
        _plot_no_data(ax, visualization_config, f'Error: {str(e)}', 'Shot Distribution')

def _plot_item_based_production_volume(df: pd.DataFrame, visualization_config: Dict, ax: plt.Axes) -> None:
    """Plot production volume comparison."""
    try:
        volume_data = df.sort_values('itemTotalQuantity', ascending=True)
        x_pos = range(len(volume_data))

        # Create overlapping bars
        bars1 = ax.barh(x_pos, volume_data['itemTotalQuantity'],
                        alpha=0.6, label='Total Production',
                        color=visualization_config['colors']['primary'], height=0.6)
        bars2 = ax.barh(x_pos, volume_data['itemGoodQuantity'],
                        alpha=0.9, label='Good Production',
                        color=visualization_config['colors']['success'], height=0.6)

        # Add value labels
        for i, (total_qty, good_qty) in enumerate(zip(volume_data['itemTotalQuantity'],
                                                        volume_data['itemGoodQuantity'])):
            percentage = (good_qty / total_qty * 100) if total_qty > 0 else 0
            combined_text = f'{int(good_qty)}/{int(total_qty)} ({percentage:.1f}%)'
            ax.text(total_qty + max(volume_data['itemTotalQuantity']) * 0.01, i,
                    combined_text, va='center', ha='left', fontsize=8,
                    color=visualization_config['colors']['primary'], fontweight='bold')

        ax.set_yticks(x_pos)
        ax.set_yticklabels(volume_data['itemNameShort'], fontsize=9)
        ax.set_xlabel('Quantity', fontweight='bold', fontsize=10)
        ax.set_title('Production Volume Comparison', fontweight='bold', fontsize=12, pad=15)
        ax.legend(loc='lower right', fontsize=8, framealpha=0.9)
        ax.grid(axis='x', alpha=0.3)
        ax.set_xlim(0, max(volume_data['itemTotalQuantity']) * 1.15)
    except Exception as e:
        _plot_no_data(ax, visualization_config, f'Error: {str(e)}', 'Shot Distribution')

def _plot_item_based_total_shots(df: pd.DataFrame, visualization_config: Dict, ax: plt.Axes) -> None:
    """Plot total shots analysis."""
    try:
        total_shots_data = df[df['moldTotalShots'] > 0].sort_values('moldTotalShots', ascending=True)

        if len(total_shots_data) == 0:
            _plot_no_data(ax, visualization_config, 'No Total Shots data available', 'Total Shots Analysis')
            return

        # Create color gradient
        norm = plt.Normalize(vmin=total_shots_data['moldTotalShots'].min(),
                            vmax=total_shots_data['moldTotalShots'].max())
        colors = plt.cm.viridis(norm(total_shots_data['moldTotalShots']))

        bars = ax.barh(range(len(total_shots_data)), total_shots_data['moldTotalShots'],
                        color=colors, alpha=0.8, edgecolor='white', linewidth=1)

        ax.set_yticks(range(len(total_shots_data)))
        ax.set_yticklabels(total_shots_data['itemNameShort'], fontsize=9)
        ax.set_xlabel('Total Shots', fontweight='bold', fontsize=10)
        ax.set_title('Total Shots by Product', fontweight='bold', fontsize=12, pad=15)

        # Add value labels
        max_shots = total_shots_data['moldTotalShots'].max()
        for i, (bar, shots) in enumerate(zip(bars, total_shots_data['moldTotalShots'])):
            width = bar.get_width()
            ax.text(width + max_shots * 0.01, bar.get_y() + bar.get_height()/2,
                    f'{int(shots):,}', ha='left', va='center',
                    fontsize=8, fontweight='bold')

        ax.grid(axis='x', alpha=0.3)
    except Exception as e:
        _plot_no_data(ax, visualization_config, f'Error: {str(e)}', 'Shot Distribution')

def _plot_item_based_machine_usage(df: pd.DataFrame, visualization_config: Dict, ax: plt.Axes) -> None:
    """Plot machine usage analysis."""
    try:
        # Calculate total usage and sort
        df['total_usage'] = df['usedMachineNums'] + df['usedComponentNums'] + df['usedMoldNums']
        machine_data = df.sort_values('total_usage', ascending=True)

        x_pos = range(len(machine_data))
        bar_width = 0.25

        colors = [visualization_config['colors']['primary'], 
                 visualization_config['colors']['warning'], 
                 visualization_config['colors']['success']]
        labels = ['Machines', 'Components', 'Molds']
        data_cols = ['usedMachineNums', 'usedComponentNums', 'usedMoldNums']

        for i, (data_col, color, label) in enumerate(zip(data_cols, colors, labels)):
            ax.bar([x + (i - 1) * bar_width for x in x_pos],
                    machine_data[data_col], width=bar_width, label=label,
                    color=color, alpha=0.8, edgecolor='white', linewidth=0.5)

        ax.set_xticks(x_pos)
        ax.set_xticklabels(machine_data['itemNameShort'], fontsize=9, rotation=45, ha='right')
        ax.set_ylabel('Number of Units', fontweight='bold', fontsize=10)
        ax.set_title('Resource Usage per Product', fontweight='bold', fontsize=12, pad=15)

        max_val = max(machine_data['usedMachineNums'].max(),
                        machine_data['usedComponentNums'].max(),
                        machine_data['usedMoldNums'].max())
        if max_val > 0:
            ax.set_yticks(np.arange(0, max_val + 1, max(1, max_val // 10)))

        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8, framealpha=0.9)
        ax.grid(axis='y', alpha=0.3)
        ax.set_xlim(-0.5, len(machine_data) - 0.5)
    except Exception as e:
        _plot_no_data(ax, visualization_config, f'Error: {str(e)}', 'Shot Distribution')

def _plot_item_based_cavity_vs_shots(df: pd.DataFrame, visualization_config: Dict, ax: plt.Axes) -> None:
    """Plot cavity vs shots scatter analysis."""
    try:
        scatter_data = df[['moldTotalShots', 'avgCavity', 'itemNameShort']].dropna()

        if len(scatter_data) == 0:
            _plot_no_data(ax, visualization_config, 'No valid data for scatter plot', 'Cavity vs Shots Analysis')
            return

        # Create scatter plot
        scatter = ax.scatter(scatter_data['moldTotalShots'], scatter_data['avgCavity'],
                            s=120, alpha=0.7, c=scatter_data['avgCavity'],
                            cmap='plasma', edgecolors='white', linewidth=2)

        # Add labels with or without adjustText
        if ADJUSTTEXT_AVAILABLE and len(scatter_data) <= 20:
            texts = []
            for x, y, label in zip(scatter_data['moldTotalShots'],
                                    scatter_data['avgCavity'],
                                    scatter_data['itemNameShort']):
                texts.append(ax.text(x, y, str(label), fontsize=8))
            adjust_text(texts, ax=ax, arrowprops=dict(arrowstyle='-', color='gray', lw=0.5))
        else:
            # Simple labeling for points
            for x, y, label in zip(scatter_data['moldTotalShots'],
                                    scatter_data['avgCavity'],
                                    scatter_data['itemNameShort']):
                ax.annotate(str(label), (x, y), xytext=(5, 5),
                            textcoords='offset points', fontsize=8)

        ax.set_xlabel('Total Shots', fontweight='bold', fontsize=10)
        ax.set_ylabel('Average Cavity', fontweight='bold', fontsize=10)
        ax.set_title('Cavity vs Shots Relationship', fontweight='bold', fontsize=12, pad=15)
        ax.grid(alpha=0.3)

        # Add colorbar
        try:
            cbar = plt.colorbar(scatter, ax=ax)
            cbar.set_label('Average Cavity', rotation=270, labelpad=15,
                            fontweight='bold', fontsize=9)
        except Exception as e:
            logger.error(f"Could not add colorbar: {e}")

        # Add trend line
        if len(scatter_data) > 2:
            try:
                z = np.polyfit(scatter_data['moldTotalShots'], scatter_data['avgCavity'], 1)
                p = np.poly1d(z)
                x_trend = np.linspace(scatter_data['moldTotalShots'].min(),
                                    scatter_data['moldTotalShots'].max(), 100)
                ax.plot(x_trend, p(x_trend), color=visualization_config['colors']['danger'],
                        linestyle='--', alpha=0.8, linewidth=2, label='Trend')
                ax.legend(fontsize=8, framealpha=0.9)
            except Exception as e:
                logger.error(f"Could not add trend line: {e}")
    except Exception as e:
        _plot_no_data(ax, visualization_config, f'Error: {str(e)}', 'Shot Distribution')

def _plot_item_based_shots_share(df: pd.DataFrame, visualization_config: Dict, ax: plt.Axes) -> None:
    """Plot shots share pie chart."""
    try:
        prod_data = df[df['moldTotalShots'] > 0].sort_values('moldTotalShots', ascending=False)

        if len(prod_data) == 0:
            _plot_no_data(ax, visualization_config, 'No Shots data', 'Shots Share')
            return

        # Prepare data for pie chart
        if len(prod_data) > 6:
            top_6 = prod_data.head(6)
            others_sum = prod_data.tail(len(prod_data) - 6)['moldTotalShots'].sum()
            labels = list(top_6['itemNameShort']) + ['Others']
            sizes = list(top_6['moldTotalShots']) + [others_sum]
        else:
            labels = prod_data['itemNameShort']
            sizes = prod_data['moldTotalShots']

        colors = visualization_config['color_list'][:len(sizes)]
        wedges, texts, autotexts = ax.pie(sizes, labels=labels, autopct='%1.1f%%',
                                            startangle=90, colors=colors,
                                            wedgeprops=dict(width=0.8, edgecolor='white', linewidth=2),
                                            textprops={'fontsize': 8, 'fontweight': 'bold'})

        ax.set_title('Shots Distribution by Product', fontweight='bold', fontsize=12, pad=15)

        for autotext in autotexts:
            autotext.set_color(visualization_config['colors']['dark'])
            autotext.set_fontweight('bold')
            autotext.set_fontsize(8)
    except Exception as e:
        _plot_no_data(ax, visualization_config, f'Error: {str(e)}', 'Shot Distribution')

def _plot_item_based_production_share(df: pd.DataFrame, visualization_config: Dict, ax: plt.Axes) -> None:
    """Plot production share pie chart."""
    try:
        prod_data = df[df['itemGoodQuantity'] > 0].sort_values('itemGoodQuantity', ascending=False)

        if len(prod_data) == 0:
            _plot_no_data(ax, visualization_config, 'No production data', 'Production Share')
            return

        # Prepare data
        if len(prod_data) > 6:
            top_6 = prod_data.head(6)
            others_sum = prod_data.tail(len(prod_data) - 6)['itemGoodQuantity'].sum()
            labels = list(top_6['itemNameShort']) + ['Others']
            sizes = list(top_6['itemGoodQuantity']) + [others_sum]
        else:
            labels = prod_data['itemNameShort']
            sizes = prod_data['itemGoodQuantity']

        colors = visualization_config['color_list'][:len(sizes)]
        wedges, texts, autotexts = ax.pie(sizes, labels=labels, autopct='%1.1f%%',
                                            startangle=90, colors=colors,
                                            wedgeprops=dict(width=0.8, edgecolor='white', linewidth=2),
                                            textprops={'fontsize': 8, 'fontweight': 'bold'})

        ax.set_title('Production Share by Product', fontweight='bold', fontsize=12, pad=15)

        for autotext in autotexts:
            autotext.set_color(visualization_config['colors']['dark'])
            autotext.set_fontweight('bold')
            autotext.set_fontsize(8)
    except Exception as e:
        _plot_no_data(ax, visualization_config, f'Error: {str(e)}', 'Shot Distribution')