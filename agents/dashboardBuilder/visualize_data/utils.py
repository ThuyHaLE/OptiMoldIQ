import os
from loguru import logger
import matplotlib.pyplot as plt
from PIL import Image
import seaborn as sns
import matplotlib.colors as mcolors

def show_all_png_images(folder_path, cols=1, scale=(16, 8)):
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


def save_plot(fig, file_path, dpi=300):
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


def generate_color_palette(n_colors, palette_name="muted"):
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