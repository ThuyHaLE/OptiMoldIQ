# tests/agents_tests/business_logic_tests/utils/test_visualization_config.py

import pytest
import json
import tempfile
from pathlib import Path
import matplotlib.pyplot as plt
from agents.dashboardBuilder.plotters.utils import load_visualization_config

class LoguruCapture:
    """Helper class to capture loguru logs"""
    def __init__(self):
        self.messages = []
        self.handler_id = None
    
    def __enter__(self):
        from loguru import logger
        
        def sink(message):
            self.messages.append(message)
        
        self.handler_id = logger.add(sink, format="{message}")
        return self
    
    def __exit__(self, *args):
        from loguru import logger
        if self.handler_id is not None:
            logger.remove(self.handler_id)
    
    @property
    def text(self):
        return '\n'.join(str(msg) for msg in self.messages)

@pytest.fixture
def loguru_caplog():
    """Fixture to capture loguru logs"""
    return LoguruCapture()

@pytest.fixture
def default_config():
    """Sample default config"""
    return {
        "colors": {
            "moldCount": "#3498DB",
            "itemCount": "#9B59B6",
            "dark": "#2C3E50",
        },
        "sns_style": "seaborn-v0_8",
        "palette_name": "muted",
        "figsize": None,
        "gridspec_kw": {
            'hspace': 0.4,
            'wspace': 0.3,
        },
        "text_colors": None,
    }

@pytest.fixture
def temp_config_file():
    """Create temporary config file"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        yield f.name
    Path(f.name).unlink(missing_ok=True)

@pytest.fixture(autouse=True)
def matplotlib_cleanup():
    """Ensure all matplotlib figures are closed after each test"""
    yield
    plt.close('all')

class TestLoadVisualizationConfig:
    
    def test_returns_default_when_no_path_provided(self, default_config):
        """Should return default config when no path provided"""
        result = load_visualization_config(default_config)
        assert result == default_config
    
    def test_returns_default_when_path_is_none(self, default_config):
        """Should return default config when path is None"""
        result = load_visualization_config(default_config, None)
        assert result == default_config
    
    def test_deep_merge_nested_dict(self, default_config, temp_config_file):
        """Should deep merge nested dictionaries"""
        user_config = {
            "colors": {
                "moldCount": "#FF0000",  # Override
                "newColor": "#00FF00"     # Add new
            },
            "sns_style": "darkgrid"      # Override
        }
        
        with open(temp_config_file, 'w') as f:
            json.dump(user_config, f)
        
        result = load_visualization_config(default_config, temp_config_file)
        
        # Check overrides
        assert result["colors"]["moldCount"] == "#FF0000"
        assert result["sns_style"] == "darkgrid"
        
        # Check preserved defaults
        assert result["colors"]["itemCount"] == "#9B59B6"
        assert result["colors"]["dark"] == "#2C3E50"
        
        # Check new addition
        assert result["colors"]["newColor"] == "#00FF00"
    
    def test_deep_merge_gridspec_kw(self, default_config, temp_config_file):
        """Should deep merge gridspec_kw dictionary"""
        user_config = {
            "gridspec_kw": {
                'hspace': 0.6,  # Override
                'new_param': 0.1  # Add new
            }
        }
        
        with open(temp_config_file, 'w') as f:
            json.dump(user_config, f)
        
        result = load_visualization_config(default_config, temp_config_file)
        
        assert result["gridspec_kw"]["hspace"] == 0.6
        assert result["gridspec_kw"]["wspace"] == 0.3  # Preserved
        assert result["gridspec_kw"]["new_param"] == 0.1
    
    def test_override_none_values(self, default_config, temp_config_file):
        """Should override None values in default config"""
        user_config = {
            "figsize": (15, 10),
            "text_colors": {"Type A": "#FF0000"}
        }
        
        with open(temp_config_file, 'w') as f:
            json.dump(user_config, f)
        
        result = load_visualization_config(default_config, temp_config_file)
        
        assert result["figsize"] == [15, 10]
        assert result["text_colors"] == {"Type A": "#FF0000"}
    
    def test_handles_file_not_found(self, default_config, loguru_caplog):
        with loguru_caplog:
            result = load_visualization_config(
                default_config, 
                "/nonexistent/path/config.json"
            )
        assert result == default_config
        assert "Could not load config" in loguru_caplog.text
    
    def test_handles_invalid_json(self, default_config, temp_config_file, loguru_caplog):
        """Should log warning and return default when JSON is invalid"""
        with open(temp_config_file, 'w') as f:
            f.write("{ invalid json }")
        
        with loguru_caplog:
            result = load_visualization_config(default_config, temp_config_file)
            
            assert result == default_config
            assert "Could not load config" in loguru_caplog.text
    
    def test_handles_empty_json_file(self, default_config, temp_config_file):
        """Should handle empty JSON object"""
        with open(temp_config_file, 'w') as f:
            json.dump({}, f)
        
        result = load_visualization_config(default_config, temp_config_file)
        assert result == default_config
    
    def test_does_not_mutate_default_config(self, default_config, temp_config_file):
        """Should not mutate the original default config"""
        import copy
        original_default = copy.deepcopy(default_config)  # Deep copy
        
        user_config = {
            "colors": {"moldCount": "#FF0000"},
            "sns_style": "darkgrid"
        }
        
        with open(temp_config_file, 'w') as f:
            json.dump(user_config, f)
        
        result = load_visualization_config(default_config, temp_config_file)
        
        # Original should be unchanged at all levels
        assert default_config == original_default
        assert result != default_config
    
    def test_handles_none_values_in_user_config(self, default_config, temp_config_file):
        """Should skip None values in user config"""
        user_config = {
            "colors": {
                "moldCount": None,  # Should be skipped
                "itemCount": "#FF0000"
            }
        }
        
        with open(temp_config_file, 'w') as f:
            json.dump(user_config, f)
        
        result = load_visualization_config(default_config, temp_config_file)
        
        # None should not override
        assert result["colors"]["moldCount"] == "#3498DB"
        # Non-None should override
        assert result["colors"]["itemCount"] == "#FF0000"
    
    def test_adds_completely_new_top_level_keys(self, default_config, temp_config_file):
        """Should add new top-level keys from user config"""
        user_config = {
            "new_section": {
                "param1": "value1",
                "param2": 100
            }
        }
        
        with open(temp_config_file, 'w') as f:
            json.dump(user_config, f)
        
        result = load_visualization_config(default_config, temp_config_file)
        
        assert "new_section" in result
        assert result["new_section"]["param1"] == "value1"
        assert result["new_section"]["param2"] == 100

class TestLoadVisualizationConfigConcurrency:
    """Test thread-safety if used in multi-threaded context"""
    
    def test_concurrent_config_loading(self, default_config, temp_config_file):
        """Should handle concurrent loads safely"""
        user_config = {"colors": {"test": "#FF0000"}}
        
        with open(temp_config_file, 'w') as f:
            json.dump(user_config, f)
        
        from concurrent.futures import ThreadPoolExecutor
        
        def load_config():
            return load_visualization_config(default_config, temp_config_file)
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(load_config) for _ in range(10)]
            results = [f.result() for f in futures]
        
        # All results should be equal and correct
        assert all(r["colors"]["test"] == "#FF0000" for r in results)
        # Default should not be mutated
        assert default_config["colors"].get("test") is None

class TestDeepUpdate:
    """Test the deep_update logic separately for more granular tests"""
    
    def test_deep_update_three_levels(self, default_config, temp_config_file):
        """Should handle 3+ levels of nesting"""
        default_with_deep = {
            "level1": {
                "level2": {
                    "level3": {
                        "value": "original"
                    },
                    "other": "keep"
                }
            }
        }
        
        user_config = {
            "level1": {
                "level2": {
                    "level3": {
                        "value": "updated"
                    }
                }
            }
        }
        
        with open(temp_config_file, 'w') as f:
            json.dump(user_config, f)
        
        result = load_visualization_config(default_with_deep, temp_config_file)
        
        assert result["level1"]["level2"]["level3"]["value"] == "updated"
        assert result["level1"]["level2"]["other"] == "keep"

class TestLoadVisualizationConfigEdgeCases:
    
    def test_handles_empty_string_path(self, default_config):
        """Should handle empty string as path"""
        result = load_visualization_config(default_config, "")
        assert result == default_config
    
    def test_handles_list_values_in_config(self, default_config, temp_config_file):
        """Should handle list values in config"""
        user_config = {
            "colors": {
                "palette_list": ["#FF0000", "#00FF00", "#0000FF"]
            }
        }
        
        with open(temp_config_file, 'w') as f:
            json.dump(user_config, f)
        
        result = load_visualization_config(default_config, temp_config_file)
        assert result["colors"]["palette_list"] == ["#FF0000", "#00FF00", "#0000FF"]
    
    def test_preserves_type_of_values(self, default_config, temp_config_file):
        """Should preserve types (int, float, bool)"""
        user_config = {
            "int_val": 42,
            "float_val": 3.14,
            "bool_val": True,
            "str_val": "test"
        }
        
        with open(temp_config_file, 'w') as f:
            json.dump(user_config, f)
        
        result = load_visualization_config(default_config, temp_config_file)
        
        assert isinstance(result["int_val"], int)
        assert isinstance(result["float_val"], float)
        assert isinstance(result["bool_val"], bool)
        assert isinstance(result["str_val"], str)

class TestPerformance:
    
    def test_config_loading_performance(self, default_config, temp_config_file):
        """Config loading should be fast"""
        large_config = {
            "colors": {f"color_{i}": f"#{i:06X}" for i in range(100)}
        }
        
        with open(temp_config_file, 'w') as f:
            json.dump(large_config, f)
        
        import time
        start = time.time()
        result = load_visualization_config(default_config, temp_config_file)
        elapsed = time.time() - start
        
        assert elapsed < 0.1  # Should be very fast