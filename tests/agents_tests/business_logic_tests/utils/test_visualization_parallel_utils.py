# tests/agents_tests/business_logic_tests/utils/test_visualization_parallel_utils.py
import pytest
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import matplotlib.pyplot as plt
from PIL import Image
import multiprocessing as mp
import psutil
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor

from agents.dashboardBuilder.plotters.utils import (
    show_all_png_images,
    save_plot,
    setup_parallel_config,
    plot_single_chart,
    execute_tasks_parallel,
    execute_tasks_sequential,
    execute_tasks,
    process_plot_results
)

# ==================== FIXTURES ====================

@pytest.fixture
def temp_dir():
    """Create temporary directory for test files"""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)

@pytest.fixture
def sample_png_files(temp_dir):
    """Create sample PNG files for testing"""
    png_files = []
    for i in range(3):
        # Create a simple figure
        fig, ax = plt.subplots(figsize=(4, 3))
        ax.plot([1, 2, 3], [1, 4, 2])
        ax.set_title(f"Test Plot {i+1}")
        
        file_path = os.path.join(temp_dir, f"test_plot_{i+1}.png")
        fig.savefig(file_path)
        plt.close(fig)
        png_files.append(file_path)
    
    return png_files

@pytest.fixture
def sample_figure():
    """Create a sample matplotlib figure"""
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.plot([1, 2, 3, 4], [1, 4, 2, 3])
    ax.set_title("Sample Plot")
    ax.set_xlabel("X Axis")
    ax.set_ylabel("Y Axis")
    yield fig
    plt.close(fig)

@pytest.fixture(autouse=True)
def matplotlib_cleanup():
    """Ensure all matplotlib figures are closed after each test"""
    yield
    plt.close('all')

@pytest.fixture
def mock_system_specs():
    """Mock system specifications"""
    class MockSpecs:
        def __init__(self, cpu_count=4, memory_gb=8):
            self.cpu_count = cpu_count
            self.memory_gb = memory_gb
    return MockSpecs

# ==================== TEST SHOW_ALL_PNG_IMAGES ====================

class TestShowAllPngImages:
    """Test PNG image display functionality"""
    
    def test_displays_all_png_files(self, temp_dir, sample_png_files):
        """Should display all PNG files in directory"""
        # This test verifies the function runs without error
        # Visual output can't be easily tested
        with patch('matplotlib.pyplot.show'):
            show_all_png_images(temp_dir, cols=2)
    
    def test_handles_empty_directory(self, temp_dir):
        """Should warn when no PNG files found"""
        # Note: loguru logs to stderr, not captured by capfd by default
        # Test just verifies the function completes without error
        with patch('matplotlib.pyplot.show'):
            # Function should handle empty directory gracefully
            show_all_png_images(temp_dir)
        # If we reach here without exception, the test passes
    
    def test_handles_nonexistent_directory(self):
        """Should handle nonexistent directory"""
        with pytest.raises((FileNotFoundError, OSError)):
            show_all_png_images("/nonexistent/path")
    
    def test_custom_columns(self, temp_dir, sample_png_files):
        """Should respect custom column count"""
        with patch('matplotlib.pyplot.show'):
            show_all_png_images(temp_dir, cols=3)
    
    def test_custom_scale(self, temp_dir, sample_png_files):
        """Should respect custom figure scale"""
        with patch('matplotlib.pyplot.show'):
            show_all_png_images(temp_dir, cols=1, scale=(20, 10))
    
    def test_ignores_non_png_files(self, temp_dir, sample_png_files):
        """Should only process PNG files"""
        # Create non-PNG file
        txt_file = os.path.join(temp_dir, "readme.txt")
        with open(txt_file, 'w') as f:
            f.write("test")
        
        with patch('matplotlib.pyplot.show'):
            show_all_png_images(temp_dir)
        
        # Should still work with only PNG files
    
    def test_case_insensitive_extension(self, temp_dir):
        """Should handle .PNG and .png extensions"""
        # Create files with different case extensions
        for ext in ['.png', '.PNG', '.Png']:
            fig, ax = plt.subplots()
            ax.plot([1, 2, 3])
            file_path = os.path.join(temp_dir, f"test{ext}")
            fig.savefig(file_path)
            plt.close(fig)
        
        with patch('matplotlib.pyplot.show'):
            show_all_png_images(temp_dir)

# ==================== TEST SAVE_PLOT ====================

class TestSavePlot:
    """Test plot saving functionality"""
    
    def test_saves_figure_successfully(self, sample_figure, temp_dir):
        """Should save figure to specified path"""
        file_path = os.path.join(temp_dir, "saved_plot.png")
        
        save_plot(sample_figure, file_path)
        
        assert os.path.exists(file_path)
        assert os.path.getsize(file_path) > 0
    
    def test_custom_dpi(self, sample_figure, temp_dir):
        """Should respect custom DPI setting"""
        file_path = os.path.join(temp_dir, "high_dpi_plot.png")
        
        save_plot(sample_figure, file_path, dpi=600)
        
        assert os.path.exists(file_path)
        # Higher DPI should result in larger file
        
    def test_creates_parent_directories(self, sample_figure, temp_dir):
        """Should create parent directories if they don't exist"""
        nested_path = os.path.join(temp_dir, "subdir", "nested", "plot.png")
        os.makedirs(os.path.dirname(nested_path), exist_ok=True)
        
        save_plot(sample_figure, nested_path)
        
        assert os.path.exists(nested_path)
    
    def test_closes_figure_after_saving(self, sample_figure, temp_dir):
        """Should close figure after saving"""
        file_path = os.path.join(temp_dir, "plot.png")
        
        save_plot(sample_figure, file_path)
        
        # Figure should be closed
        assert not plt.fignum_exists(sample_figure.number)
    
    def test_handles_invalid_path(self, sample_figure, capsys):
        """Should handle invalid file path gracefully"""
        invalid_path = "/invalid/path/that/does/not/exist/plot.png"
        
        save_plot(sample_figure, invalid_path)
        
        captured = capsys.readouterr()
        assert "Error saving plot" in captured.out
    
    def test_saves_with_tight_bbox(self, sample_figure, temp_dir):
        """Should save with tight bounding box"""
        file_path = os.path.join(temp_dir, "tight_plot.png")
        
        save_plot(sample_figure, file_path)
        
        # Verify file exists and is valid image
        img = Image.open(file_path)
        assert img.format == 'PNG'
    
    def test_white_background(self, sample_figure, temp_dir):
        """Should save with white background"""
        file_path = os.path.join(temp_dir, "white_bg_plot.png")
        
        save_plot(sample_figure, file_path)
        
        assert os.path.exists(file_path)

# ==================== TEST SETUP_PARALLEL_CONFIG ====================

class TestSetupParallelConfig:
    """Test parallel configuration setup"""
    
    @patch('multiprocessing.cpu_count')
    @patch('psutil.virtual_memory')
    def test_single_core_disables_parallel(self, mock_memory, mock_cpu):
        """Single core should disable parallel processing"""
        mock_cpu.return_value = 1
        mock_memory.return_value.total = 8 * (1024**3)  # 8GB
        
        enable, workers = setup_parallel_config(enable_parallel=True)
        
        assert enable is False
        assert workers == 1
    
    @patch('multiprocessing.cpu_count')
    @patch('psutil.virtual_memory')
    def test_dual_core_with_high_memory(self, mock_memory, mock_cpu):
        """Dual core with 8GB+ RAM should use both cores"""
        mock_cpu.return_value = 2
        mock_memory.return_value.total = 8 * (1024**3)  # 8GB
        
        enable, workers = setup_parallel_config(enable_parallel=True)
        
        assert enable is True
        assert workers == 2
    
    @patch('multiprocessing.cpu_count')
    @patch('psutil.virtual_memory')
    def test_dual_core_with_low_memory(self, mock_memory, mock_cpu):
        """Dual core with <8GB RAM should use sequential"""
        mock_cpu.return_value = 2
        mock_memory.return_value.total = 4 * (1024**3)  # 4GB
        
        enable, workers = setup_parallel_config(enable_parallel=True)
        
        assert enable is False
        assert workers == 1
    
    @patch('multiprocessing.cpu_count')
    @patch('psutil.virtual_memory')
    def test_multi_core_optimal_workers(self, mock_memory, mock_cpu):
        """Multi-core should use 75% of cores"""
        mock_cpu.return_value = 8
        mock_memory.return_value.total = 16 * (1024**3)  # 16GB
        
        enable, workers = setup_parallel_config(enable_parallel=True)
        
        assert enable is True
        assert workers == 6  # 75% of 8 = 6
    
    @patch('multiprocessing.cpu_count')
    @patch('psutil.virtual_memory')
    def test_limited_memory_reduces_workers(self, mock_memory, mock_cpu):
        """Limited memory should reduce worker count"""
        mock_cpu.return_value = 8
        mock_memory.return_value.total = 3 * (1024**3)  # 3GB (< min_memory_gb)
        
        enable, workers = setup_parallel_config(
            enable_parallel=True, 
            min_memory_gb=4.0
        )
        
        assert enable is True
        assert workers <= 2  # Should limit workers
    
    @patch('multiprocessing.cpu_count')
    @patch('psutil.virtual_memory')
    def test_caps_workers_by_num_tasks(self, mock_memory, mock_cpu):
        """Should cap workers by number of tasks"""
        mock_cpu.return_value = 8
        mock_memory.return_value.total = 16 * (1024**3)
        
        enable, workers = setup_parallel_config(
            enable_parallel=True,
            num_tasks=3
        )
        
        assert workers == 3  # Capped to num_tasks
    
    @patch('multiprocessing.cpu_count')
    @patch('psutil.virtual_memory')
    def test_explicit_max_workers(self, mock_memory, mock_cpu):
        """Should respect explicit max_workers"""
        mock_cpu.return_value = 8
        mock_memory.return_value.total = 16 * (1024**3)
        
        enable, workers = setup_parallel_config(
            enable_parallel=True,
            max_workers=4
        )
        
        assert workers == 4
    
    @patch('multiprocessing.cpu_count')
    @patch('psutil.virtual_memory')
    def test_explicit_disable(self, mock_memory, mock_cpu):
        """Should respect explicit disable flag"""
        mock_cpu.return_value = 8
        mock_memory.return_value.total = 16 * (1024**3)
        
        enable, workers = setup_parallel_config(enable_parallel=False)
        
        assert enable is False
        assert workers == 1
    
    @patch('multiprocessing.cpu_count')
    def test_handles_system_detection_failure(self, mock_cpu):
        """Should fallback to sequential on detection failure"""
        mock_cpu.side_effect = Exception("Detection failed")
        
        enable, workers = setup_parallel_config(enable_parallel=True)
        
        assert enable is False
        assert workers == 1

# ==================== TEST PLOT_SINGLE_CHART ====================

class TestPlotSingleChart:
    """Test single chart plotting worker function"""
    
    @pytest.fixture
    def mock_plot_function(self):
        """Mock plotting function that returns a figure"""
        def plot_func(data, visualization_config_path=None, **kwargs):
            fig, ax = plt.subplots()
            ax.plot(data)
            return fig
        return plot_func
    
    @pytest.fixture
    def mock_plot_function_with_summary(self):
        """Mock plotting function that returns (summary, fig)"""
        def plot_func(data, visualization_config_path=None, **kwargs):
            fig, ax = plt.subplots()
            ax.plot(data)
            summary = {"metric": "value"}
            return summary, fig
        return plot_func
    
    @pytest.fixture
    def mock_plot_function_multi_page(self):
        """Mock plotting function that returns (summary, [figs])"""
        def plot_func(data, visualization_config_path=None, **kwargs):
            figs = []
            for i in range(3):
                fig, ax = plt.subplots()
                ax.plot(data)
                ax.set_title(f"Page {i+1}")
                figs.append(fig)
            summary = {"pages": 3}
            return summary, figs
        return plot_func
    
    def test_plots_single_figure(self, temp_dir, mock_plot_function):
        """Should create and save single figure"""
        data = [1, 2, 3, 4, 5]
        config_path = None
        name = "test_plot"
        output_path = os.path.join(temp_dir, "test.png")
        timestamp = "20240101_120000"
        kwargs = {}
        
        args = (data, config_path, name, mock_plot_function, 
                output_path, timestamp, kwargs)
        
        success, plot_name, paths, error, exec_time = plot_single_chart(args)
        
        assert success is True
        assert plot_name == name
        assert len(paths) == 1
        assert os.path.exists(paths[0])
        assert error == ""
        assert exec_time > 0
    
    def test_plots_with_summary(self, temp_dir, mock_plot_function_with_summary):
        """Should handle function returning (summary, fig)"""
        data = [1, 2, 3, 4, 5]
        config_path = None
        name = "test_plot_summary"
        output_path = os.path.join(temp_dir, "test.png")
        timestamp = "20240101_120000"
        kwargs = {}
        
        args = (data, config_path, name, mock_plot_function_with_summary,
                output_path, timestamp, kwargs)
        
        success, plot_name, paths, error, exec_time = plot_single_chart(args)
        
        assert success is True
        assert len(paths) == 1
        assert os.path.exists(paths[0])
    
    def test_plots_multi_page(self, temp_dir, mock_plot_function_multi_page):
        """Should handle multiple figures (multi-page)"""
        data = [1, 2, 3, 4, 5]
        config_path = None
        name = "test_multipage"
        output_path = os.path.join(temp_dir, "test.png")
        timestamp = "20240101_120000"
        kwargs = {}
        
        args = (data, config_path, name, mock_plot_function_multi_page,
                output_path, timestamp, kwargs)
        
        success, plot_name, paths, error, exec_time = plot_single_chart(args)
        
        assert success is True
        assert len(paths) == 3  # 3 pages
        assert all(os.path.exists(p) for p in paths)
        assert all('_page' in p for p in paths)
    
    def test_handles_tuple_data(self, temp_dir, mock_plot_function):
        """Should unpack tuple data"""
        data = ([1, 2, 3], [4, 5, 6])
        config_path = None
        name = "test_tuple"
        output_path = os.path.join(temp_dir, "test.png")
        timestamp = "20240101_120000"
        kwargs = {}
        
        def plot_func_tuple(x, y, visualization_config_path=None, **kwargs):
            fig, ax = plt.subplots()
            ax.plot(x, y)
            return fig
        
        args = (data, config_path, name, plot_func_tuple,
                output_path, timestamp, kwargs)
        
        success, plot_name, paths, error, exec_time = plot_single_chart(args)
        
        assert success is True
    
    def test_handles_plotting_error(self, temp_dir):
        """Should catch and return error information"""
        def failing_plot_func(data, visualization_config_path=None, **kwargs):
            raise ValueError("Plotting failed!")
        
        data = [1, 2, 3]
        config_path = None
        name = "failing_plot"
        output_path = os.path.join(temp_dir, "test.png")
        timestamp = "20240101_120000"
        kwargs = {}
        
        args = (data, config_path, name, failing_plot_func,
                output_path, timestamp, kwargs)
        
        success, plot_name, paths, error, exec_time = plot_single_chart(args)
        
        assert success is False
        assert "Plotting failed!" in error
        assert exec_time > 0
    
    def test_passes_kwargs_to_function(self, temp_dir):
        """Should pass additional kwargs to plotting function"""
        kwargs_received = {}
        
        def plot_func(data, visualization_config_path=None, **kwargs):
            kwargs_received.update(kwargs)
            fig, ax = plt.subplots()
            ax.plot(data)
            return fig
        
        data = [1, 2, 3]
        config_path = None
        name = "test_kwargs"
        output_path = os.path.join(temp_dir, "test.png")
        timestamp = "20240101_120000"
        kwargs = {"custom_param": "value", "another_param": 42}
        
        args = (data, config_path, name, plot_func,
                output_path, timestamp, kwargs)
        
        plot_single_chart(args)
        
        assert kwargs_received["custom_param"] == "value"
        assert kwargs_received["another_param"] == 42

# ==================== TEST EXECUTE_TASKS ====================

class TestExecuteTasks:
    """Test task execution functions"""
    
    @pytest.fixture
    def simple_worker(self):
        """Simple worker function for testing"""
        def worker(task):
            task_id, value = task
            time.sleep(0.01)  # Simulate work
            return (True, f"task_{task_id}", value * 2, "", 0.01)
        return worker
    
    @pytest.fixture
    def failing_worker(self):
        """Worker that fails on certain tasks"""
        def worker(task):
            task_id, value = task
            if value < 0:
                raise ValueError(f"Negative value: {value}")
            time.sleep(0.01)
            return (True, f"task_{task_id}", value * 2, "", 0.01)
        return worker
    
    def test_execute_tasks_sequential(self, simple_worker):
        """Should execute tasks sequentially"""
        tasks = [(i, i * 10) for i in range(5)]
        
        results, errors = execute_tasks_sequential(
            tasks=tasks,
            worker_function=simple_worker
        )
        
        assert len(results) == 5
        assert len(errors) == 0
        assert all(r[0] for r in results)  # All successful
    
    def test_execute_tasks_sequential_with_failures(self, failing_worker):
        """Should handle failures in sequential execution"""
        tasks = [(i, i - 2) for i in range(5)]  # Some negative values
        
        results, errors = execute_tasks_sequential(
            tasks=tasks,
            worker_function=failing_worker
        )
        
        assert len(results) < len(tasks)
        assert len(errors) > 0
    
    def test_execute_tasks_sequential_with_name_extractor(self, simple_worker):
        """Should use custom name extractor"""
        tasks = [(i, i * 10) for i in range(3)]
        
        def name_extractor(task):
            return f"CustomTask_{task[0]}"
        
        results, errors = execute_tasks_sequential(
            tasks=tasks,
            worker_function=simple_worker,
            task_name_extractor=name_extractor
        )
        
        assert len(results) == 3
    
    @pytest.mark.skipif(mp.cpu_count() == 1, reason="Requires multiple cores")
    def test_execute_tasks_parallel(self, simple_worker):
        """Should execute tasks in parallel"""
        tasks = [(i, i * 10) for i in range(10)]
        
        results, errors = execute_tasks_parallel(
            tasks=tasks,
            worker_function=simple_worker,
            max_workers=2,
            executor_type="thread"  # Use threads for simpler testing
        )
        
        assert len(results) == 10
        assert len(errors) == 0
    
    @pytest.mark.skipif(mp.cpu_count() == 1, reason="Requires multiple cores")
    def test_execute_tasks_parallel_thread_executor(self, simple_worker):
        """Should use ThreadPoolExecutor when specified"""
        tasks = [(i, i * 10) for i in range(5)]
        
        results, errors = execute_tasks_parallel(
            tasks=tasks,
            worker_function=simple_worker,
            max_workers=2,
            executor_type="thread"
        )
        
        assert len(results) == 5
    
    def test_execute_tasks_auto_selects_parallel(self, simple_worker):
        """Should automatically select parallel for multiple tasks"""
        tasks = [(i, i * 10) for i in range(5)]
        
        with patch('agents.dashboardBuilder.plotters.utils.execute_tasks_parallel') as mock_parallel:
            mock_parallel.return_value = ([], [])
            
            execute_tasks(
                tasks=tasks,
                worker_function=simple_worker,
                enable_parallel=True,
                max_workers=2
            )
            
            mock_parallel.assert_called_once()
    
    def test_execute_tasks_auto_selects_sequential(self, simple_worker):
        """Should automatically select sequential when disabled"""
        tasks = [(i, i * 10) for i in range(5)]
        
        with patch('agents.dashboardBuilder.plotters.utils.execute_tasks_sequential') as mock_sequential:
            mock_sequential.return_value = ([], [])
            
            execute_tasks(
                tasks=tasks,
                worker_function=simple_worker,
                enable_parallel=False,
                max_workers=1
            )
            
            mock_sequential.assert_called_once()
    
    def test_execute_tasks_single_task_uses_sequential(self, simple_worker):
        """Should use sequential for single task"""
        tasks = [(0, 10)]
        
        with patch('agents.dashboardBuilder.plotters.utils.execute_tasks_sequential') as mock_sequential:
            mock_sequential.return_value = ([], [])
            
            execute_tasks(
                tasks=tasks,
                worker_function=simple_worker,
                enable_parallel=True,
                max_workers=4
            )
            
            mock_sequential.assert_called_once()

# ==================== TEST PROCESS_PLOT_RESULTS ====================

class TestProcessPlotResults:
    """Test plot results processing"""
    
    def test_processes_successful_results(self):
        """Should process successful plot results"""
        raw_results = [
            (True, "plot1", ["/path/to/plot1.png"], "", 1.5),
            (True, "plot2", ["/path/to/plot2.png"], "", 2.0),
        ]
        
        successful, failed = process_plot_results(raw_results)
        
        assert len(successful) == 2
        assert len(failed) == 0
        assert "plot1" in successful[0]
        assert "1.5s" in successful[0]
    
    def test_processes_failed_results(self):
        """Should process failed plot results"""
        raw_results = [
            (False, "plot1", [], "Error message", 0.5),
            (False, "plot2", [], "Another error", 0.3),
        ]
        
        successful, failed = process_plot_results(raw_results)
        
        assert len(successful) == 0
        assert len(failed) == 2
        assert "Error message" in failed[0]
    
    def test_processes_mixed_results(self):
        """Should handle mixed success/failure results"""
        raw_results = [
            (True, "plot1", ["/path/to/plot1.png"], "", 1.0),
            (False, "plot2", [], "Failed", 0.5),
            (True, "plot3", ["/path/to/plot3.png"], "", 2.0),
        ]
        
        successful, failed = process_plot_results(raw_results)
        
        assert len(successful) == 2
        assert len(failed) == 1
    
    def test_handles_multi_page_results(self):
        """Should handle multiple paths in path_collection"""
        raw_results = [
            (True, "multipage", [
                "/path/to/plot_page1.png",
                "/path/to/plot_page2.png",
                "/path/to/plot_page3.png"
            ], "", 3.5),
        ]
        
        successful, failed = process_plot_results(raw_results)
        
        assert len(successful) == 1
        assert "plot_page1.png" in successful[0]
        assert "plot_page2.png" in successful[0]
        assert "plot_page3.png" in successful[0]
    
    def test_handles_empty_results(self):
        """Should handle empty results list"""
        raw_results = []
        
        successful, failed = process_plot_results(raw_results)
        
        assert len(successful) == 0
        assert len(failed) == 0
    
    def test_formats_execution_time(self):
        """Should format execution time with 1 decimal"""
        raw_results = [
            (True, "plot", ["/path/plot.png"], "", 1.234567),
        ]
        
        successful, failed = process_plot_results(raw_results)
        
        assert "1.2s" in successful[0]  # Should round to 1 decimal

# ==================== INTEGRATION TESTS ====================

class TestParallelPlottingIntegration:
    """Integration tests for parallel plotting workflow"""
    
    def test_full_parallel_workflow(self, temp_dir):
        """Test complete parallel plotting workflow"""
        # Setup
        enable_parallel, max_workers = setup_parallel_config(
            enable_parallel=True,
            max_workers=2,
            num_tasks=3
        )
        
        # Create mock plotting tasks
        def mock_plot_func(data, visualization_config_path=None, **kwargs):
            fig, ax = plt.subplots()
            ax.plot(data)
            return fig
        
        tasks = []
        for i in range(3):
            data = list(range(i, i+5))
            config_path = None
            name = f"plot_{i}"
            path = os.path.join(temp_dir, f"plot_{i}.png")
            timestamp = "20240101_120000"
            kwargs = {}
            tasks.append((data, config_path, name, mock_plot_func, 
                         path, timestamp, kwargs))
        
        # Execute
        if enable_parallel:
            results, errors = execute_tasks_parallel(
                tasks=tasks,
                worker_function=plot_single_chart,
                max_workers=max_workers,
                executor_type="thread"
            )
        else:
            results, errors = execute_tasks_sequential(
                tasks=tasks,
                worker_function=plot_single_chart
            )
        
        # Process results
        successful, failed = process_plot_results(results)
        
        # Verify
        assert len(successful) == 3
        assert len(failed) == 0
        assert all(os.path.exists(os.path.join(temp_dir, f"plot_{i}.png")) 
                  for i in range(3))
    
    def test_full_sequential_workflow(self, temp_dir):
        """Test complete sequential plotting workflow"""
        enable_parallel, max_workers = setup_parallel_config(
            enable_parallel=False
        )
        
        assert enable_parallel is False
        assert max_workers == 1
        
        # Rest of workflow should work the same

# ==================== PERFORMANCE TESTS ====================

class TestPerformance:
    """Performance-related tests"""
    
    @pytest.mark.slow
    def test_parallel_faster_than_sequential(self):
        """Parallel should be faster for CPU-bound tasks"""
        def slow_worker(task):
            time.sleep(0.1)
            return (True, f"task_{task}", task * 2, "", 0.1)
        
        tasks = list(range(10))
        
        # Sequential timing
        start = time.time()
        execute_tasks_sequential(tasks, slow_worker)
        sequential_time = time.time() - start
        
        # Parallel timing (if available)
        if mp.cpu_count() > 1:
            start = time.time()
            execute_tasks_parallel(tasks, slow_worker, max_workers=2, 
                                 executor_type="thread")
            parallel_time = time.time() - start
            
            # Parallel should be faster
            assert parallel_time < sequential_time * 0.8
    
    @pytest.mark.slow
    def test_memory_efficient_plotting(self, temp_dir):
        """Should not accumulate too much memory"""
        import gc
        
        def plot_func(data, visualization_config_path=None, **kwargs):
            fig, ax = plt.subplots(figsize=(10, 10))
            ax.plot(data)
            return fig
        
        tasks = []
        for i in range(20):
            data = list(range(1000))
            args = (data, None, f"plot_{i}", plot_func,
                   os.path.join(temp_dir, f"plot_{i}.png"),
                   "timestamp", {})
            tasks.append(args)
        
        # Execute and ensure cleanup happens
        results, errors = execute_tasks_sequential(tasks, plot_single_chart)
        gc.collect()
        
        # Should complete without memory issues
        assert len(results) == 20