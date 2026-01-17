import os
from loguru import logger
import matplotlib.pyplot as plt
from PIL import Image
import seaborn as sns
import matplotlib.colors as mcolors
from typing import Optional, Dict, Tuple, Any, Callable, List
import json
from matplotlib.colors import to_rgba, to_hex
import multiprocessing as mp
import psutil
import time
import traceback
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed

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

def setup_parallel_config(
        enable_parallel: bool = True,
        max_workers: Optional[int] = None,
        num_tasks: Optional[int] = None,
        min_memory_gb: float = 4.0,
    ) -> Tuple[bool, int]:
    """
    Setup parallel processing configuration based on system resources.
    
    Args:
        enable_parallel: Whether to enable parallel processing
        max_workers: Maximum number of workers (None for auto-detect)
        num_tasks: Number of tasks to process (used to cap workers)
        min_memory_gb: Minimum RAM threshold for full parallelization
        
    Returns:
        Tuple of (enable_parallel: bool, max_workers: int)
    """
    
    try:
        # Get system information
        cpu_count = mp.cpu_count()
        memory_gb = psutil.virtual_memory().total / (1024**3)
        
        logger.info("System specs: {} CPU cores, {:.1f}GB RAM", cpu_count, memory_gb)
        
        # Determine optimal worker count if not specified
        if max_workers is None:
            if cpu_count == 1:
                # Single core - no parallel benefit
                max_workers = 1
                enable_parallel = False
            elif cpu_count == 2:
                # Dual core (like Colab) - can still benefit from 2 workers if enough RAM
                if memory_gb >= 8:
                    max_workers = 2  # Use both cores
                    logger.info("Colab-style environment detected. Using both cores.")
                else:
                    max_workers = 1
                    logger.warning("Limited RAM with dual core. Using sequential processing.")
            else:
                # Multi-core systems
                if memory_gb < min_memory_gb:
                    max_workers = max(1, min(2, cpu_count // 2))
                    logger.warning("Limited RAM detected. Limiting workers to {}", max_workers)
                elif memory_gb < 8:
                    max_workers = max(2, min(3, cpu_count // 2))
                else:
                    max_workers = max(2, int(cpu_count * 0.75))
        
        # Cap workers by number of tasks if provided
        if num_tasks is not None and max_workers > num_tasks:
            max_workers = num_tasks
            logger.info("Capping workers to {} (number of tasks)", max_workers)
        
        # Final check - disable if explicitly disabled or only 1 worker needed
        if not enable_parallel or max_workers <= 1:
            enable_parallel = False
            max_workers = 1
            logger.info("Parallel processing disabled. Workers: {}", max_workers)
        else:
            logger.info("Parallel processing enabled. Workers: {}", max_workers)
            
    except Exception as e:
        logger.warning("Failed to detect system specs: {}. Using sequential processing.", e)
        enable_parallel = False
        max_workers = 1
    
    return enable_parallel, max_workers

def plot_single_chart(args: Tuple[Any, str, Callable, str, str, Dict]
                      ) -> Tuple[bool, str, list, str, float]:
    """
    Worker function to create a single plot.
    Returns: (success, plot_name, error_message, execution_time)
    """
    data, config_path, name, func, path, timestamp_file, kwargs = args
    start_time = time.time()

    path_collection = []

    try:
        # Create the plot - pass visualization_config_path as keyword argument
        if isinstance(data, tuple):
            result = func(*data, visualization_config_path=config_path, **kwargs)
        else:
            result = func(data, visualization_config_path=config_path, **kwargs)

        # Handle different return types
        if isinstance(result, tuple):
            # Result is (summary, fig) or (summary, figs)
            summary, fig_or_figs = result
            
            if isinstance(fig_or_figs, list):
                # Multiple figures - save each one
                for idx, fig in enumerate(fig_or_figs):
                    fig_path = path.replace('.png', f'_page{idx+1}.png')
                    fig.savefig(fig_path, dpi=300, bbox_inches="tight", pad_inches=0.5)
                    path_collection.append(fig_path)
                    plt.close(fig)

            else:
                # Single figure
                fig_or_figs.savefig(path, dpi=300, bbox_inches="tight", pad_inches=0.5)
                path_collection.append(path)
                plt.close(fig_or_figs)

        else:
            # Result is just a figure
            result.savefig(path, dpi=300, bbox_inches="tight", pad_inches=0.5)
            path_collection.append(path)
            plt.close(result)
            
        execution_time = time.time() - start_time
        return True, name, path_collection, "", execution_time

    except Exception as e:
        execution_time = time.time() - start_time
        error_msg = f"Failed to create plot '{name}': {str(e)}\n{traceback.format_exc()}"
        return False, name, path_collection, error_msg, execution_time

def execute_tasks_parallel(
        tasks: List[Any],
        worker_function: Callable,
        max_workers: int,
        executor_type: str = "process",
        task_name_extractor: Optional[Callable[[Any], str]] = None
    ) -> Tuple[List[Tuple], List[str]]:
    """
    Execute tasks in parallel using ProcessPoolExecutor or ThreadPoolExecutor.
    
    Args:
        tasks: List of task arguments to pass to worker_function
        worker_function: Function that processes a single task
        max_workers: Maximum number of parallel workers
        executor_type: "process" or "thread" (default: "process" for CPU-bound tasks)
        task_name_extractor: Optional function to extract task name from task for logging
                            If None, uses index
    """
    successful_results = []
    failed_results = []
    
    # Choose executor type
    ExecutorClass = ProcessPoolExecutor if executor_type == "process" else ThreadPoolExecutor
    
    logger.info("Starting parallel execution with {} workers for {} tasks (executor: {})",
             max_workers, len(tasks), executor_type)
    
    start_time = time.time()
    
    try:
        with ExecutorClass(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_task = {executor.submit(worker_function, task): task for task in tasks}
            
            # Collect results as they complete
            for future in as_completed(future_to_task):
                task = future_to_task[future]
                task_name = task_name_extractor(task) if task_name_extractor else str(tasks.index(task))
                
                try:
                    result = future.result()
                    # Assume worker function returns (success, name, data, error_msg, exec_time)
                    # Adjust based on your actual return format
                    successful_results.append(result)
                    logger.debug("✅ Completed task: {}", task_name)
                    
                except Exception as e:
                    error_msg = f"Task execution failed for {task_name}: {str(e)}"
                    failed_results.append(error_msg)
                    logger.error("❌ {}", error_msg)
        
        total_time = time.time() - start_time
        logger.info("Parallel execution completed in {:.1f}s. Success: {}, Failed: {}",
                total_time, len(successful_results), len(failed_results))
        
    except Exception as e:
        logger.error("Parallel execution framework failed: {}", str(e))
        raise
    
    return successful_results, failed_results

def execute_tasks_sequential(
        tasks: List[Any],
        worker_function: Callable,
        task_name_extractor: Optional[Callable[[Any], str]] = None
    ) -> Tuple[List[Tuple], List[str]]:
    """
    Execute tasks sequentially (fallback method).
    
    Args:
        tasks: List of task arguments to pass to worker_function
        worker_function: Function that processes a single task
        task_name_extractor: Optional function to extract task name from task for logging
    
    Returns:
        Tuple of (successful_results: List, failed_results: List[str])
    """

    successful_results = []
    failed_results = []
    
    logger.info("Starting sequential execution for {} tasks", len(tasks))
    start_time = time.time()
    
    for i, task in enumerate(tasks):
        task_name = task_name_extractor(task) if task_name_extractor else f"task_{i}"
        
        try:
            result = worker_function(task)
            successful_results.append(result)
            logger.debug("✅ Completed task: {}", task_name)
            
        except Exception as e:
            error_msg = f"Task execution failed for {task_name}: {str(e)}"
            failed_results.append(error_msg)
            logger.error("❌ {}", error_msg)
    
    total_time = time.time() - start_time
    logger.info("Sequential execution completed in {:.1f}s", total_time)
    
    return successful_results, failed_results

def execute_tasks(
        tasks: List[Any],
        worker_function: Callable,
        enable_parallel: bool = True,
        max_workers: int = 1,
        executor_type: str = "process",
        task_name_extractor: Optional[Callable[[Any], str]] = None
    ) -> Tuple[List[Tuple], List[str]]:
    """
    Execute tasks either in parallel or sequentially based on configuration.
    
    This is a convenience wrapper that automatically chooses between parallel
    and sequential execution based on enable_parallel flag and number of tasks.
    
    Args:
        tasks: List of task arguments
        worker_function: Function that processes a single task
        enable_parallel: Whether to use parallel processing
        max_workers: Maximum number of workers for parallel execution
        executor_type: "process" or "thread"
        task_name_extractor: Function to extract task name for logging
    
    Returns:
        Tuple of (successful_results: List, failed_results: List[str])
    """
    if enable_parallel and len(tasks) > 1:
        return execute_tasks_parallel(
            tasks=tasks,
            worker_function=worker_function,
            max_workers=max_workers,
            executor_type=executor_type,
            task_name_extractor=task_name_extractor
        )
    else:
        return execute_tasks_sequential(
            tasks=tasks,
            worker_function=worker_function,
            task_name_extractor=task_name_extractor
        )
    
def process_plot_results(raw_results: List[Tuple]) -> Tuple[List[str], List[str]]:
    """
    Process raw plotting results into success/failure lists.
    
    Args:
        raw_results: List of (success, name, path_collection, error_msg, exec_time)
        logger_instance: Logger to use
    
    Returns:
        Tuple of (successful_plots: List[str], failed_plots: List[str])
    """

    successful_plots = []
    failed_plots = []
    
    for result in raw_results:
        success, name, path_collection, error_msg, exec_time = result
        if success:
            path_collection_str = '\n'.join(path_collection)
            successful_plots.append(
                f"  ⤷ Saved new plots for {name} ({exec_time:.1f}s): \n - {path_collection_str}"
            )
            logger.info("✅ Created plot: {} ({:.1f}s)", name, exec_time)
        else:
            failed_plots.append(error_msg)
            logger.error("❌ {}", error_msg)
    
    return successful_plots, failed_plots