import os
from loguru import logger
import matplotlib.pyplot as plt
from PIL import Image
import seaborn as sns
import matplotlib.colors as mcolors
from typing import Optional, Dict
import json
from matplotlib.colors import to_rgba, to_hex

def load_visualization_config(default_config, 
                              visualization_config_path: Optional[str] = None
                              ) -> Dict:
    """Load visualization configuration with fallback to defaults."""

    def deep_update(base: dict, updates: dict) -> Dict:
        for k, v in updates.items():
            if v is None or not v in updates.values():
                continue
            if isinstance(v, dict) and isinstance(base.get(k), Dict):
                base[k] = deep_update(base.get(k, {}), v)
            else:
                base[k] = v
        return base

    config = default_config.copy()

    if visualization_config_path:
        try:
            with open(visualization_config_path, "r") as f:
                user_cfg = json.load(f)
            config = deep_update(config, user_cfg)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.warning(f"Could not load config from {visualization_config_path}: {e}")

    return config

def show_all_png_images(folder_path, 
                        cols=1, 
                        scale=(16, 8)):
    """Display all .png images in a folder in a grid layout."""
    png_files = [f for f in os.listdir(folder_path) if f.lower().endswith('.png')]

    if not png_files:
        logger.warning("No .png files found in the folder.")
        return

    num_images = len(png_files)
    rows = (num_images + cols - 1) // cols

    plt.figure(figsize=(cols * scale[0], rows * scale[1]))

    for i, filename in enumerate(png_files):
        img_path = os.path.join(folder_path, filename)
        img = Image.open(img_path)

        plt.subplot(rows, cols, i + 1)
        plt.imshow(img)
        plt.title(filename, fontsize=10)
        plt.axis('off')

    plt.tight_layout()
    plt.show()
    plt.close()


def save_plot(fig, 
              file_path, 
              dpi=300):
    """Helper function to save a matplotlib figure."""
    try:
        fig.savefig(
            file_path,
            dpi=dpi,
            bbox_inches='tight',
            facecolor='white',
            edgecolor='none'
        )
        print(f"Plot saved successfully to: {file_path}")
    except Exception as e:
        print(f"Error saving plot: {e}")
    finally:
        plt.close(fig)


def generate_color_palette(n_colors, 
                           palette_name="muted"):
    """Generate a color palette with the specified number of colors."""
    base_colors_dict = {
        "Set1": 9, "Set2": 8, "Set3": 12,
        "muted": 10, "pastel": 10, "bright": 10,
        "deep": 10, "colorblind": 8,
        "tab10": 10, "tab20": 20,
    }

    logger.info(
        f'Used Seaborn palette: {palette_name}.\n'
        'Supported palettes (name - base color count):\n'
        '"Set1 - 9", "Set2 - 8", "Set3 - 12" (grouping);\n'
        '"muted - 10", "pastel - 10", "bright - 10" (dashboard friendly);\n'
        '"deep - 10" (default), "colorblind - 8" (accessibility);\n'
        '"tab10 - 10", "tab20 - 20" (similar to matplotlib).\n'
        'Note: Palettes like "muted", "bright", etc. can interpolate for more colors.'
    )

    def show_colors(color_list):
        fig, ax = plt.subplots(figsize=(len(color_list), 1))
        for i, color in enumerate(color_list):
            ax.add_patch(plt.Rectangle((i, 0), 1, 1, color=color))
        ax.set_xlim(0, len(color_list))
        ax.set_ylim(0, 1)
        ax.axis('off')
        plt.show()
        plt.close()

    if n_colors <= 0:
        hex_colors = ['#0000FF']  # Default blue
    else:
        try:
            base_max = base_colors_dict.get(palette_name, 10)
            if n_colors > base_max and palette_name in ["Set1", "Set2", "Set3"]:
                logger.warning(
                    f"Palette '{palette_name}' has only {base_max} unique colors. "
                    "Switching to 'muted' for interpolation."
                )
                palette_name = "muted"

            colors = sns.color_palette(palette_name, n_colors=n_colors)
            hex_colors = [mcolors.to_hex(c).upper() for c in colors]

        except ValueError as e:
            logger.error(f"Palette error: {e}")
            hex_colors = ['#000000']

    logger.info(f'Generated hex colors for ({palette_name}): {hex_colors}')
    show_colors(hex_colors)

    return hex_colors

def lighten_color(color,
                  amount=0.3):
    """
    Lighten a given color by mixing it with white.
    """
    c = to_rgba(color)
    white = (1, 1, 1, 1)
    new_color = tuple((1 - amount) * x + amount * y for x, y in zip(c, white))
    return to_hex(new_color)


def format_value_short(val, 
                       decimal=2):
    """
    Convert a large numeric value into a short human-readable format.
    """
    abs_val = abs(val)
    if abs_val >= 1_000_000_000:
        return f"{val/1_000_000_000:.{decimal}f}B"
    elif abs_val >= 1_000_000:
        return f"{val/1_000_000:.{decimal}f}M"
    elif abs_val >= 1_000:
        return f"{val/1_000:.{decimal}f}K"
    else:
        # Show as integer if no decimal part, otherwise use specified decimal
        return f"{int(val)}" if val == int(val) else f"{val:.{decimal}f}"

def add_value_labels(ax,
                     orientation='h',
                     float_type=False,
                     short_format=False):
    """
    Add value labels to each bar in a bar chart.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        The axes containing the bars to annotate.
    orientation : {'h', 'v'}, default='h'
        Orientation of the bars ('h' for horizontal, 'v' for vertical).
    float_type : bool, default=False
        If True, display values as floats with two decimal places;
        otherwise, display as integers with thousand separators.
    short_format : bool, default=False
        If True, display values in short format (K, M, B).
    """

    for container in ax.containers:
        if short_format:
            labels = [format_value_short(v) if v > 0 else '' for v in container.datavalues]
        elif float_type:
            labels = [f'{v:.2f}' if v > 0 else '' for v in container.datavalues]
        else:
            labels = [f'{int(v):,}' if v > 0 else '' for v in container.datavalues]

        ax.bar_label(container,
                     labels=labels,
                     padding=3,
                     fontsize=8)