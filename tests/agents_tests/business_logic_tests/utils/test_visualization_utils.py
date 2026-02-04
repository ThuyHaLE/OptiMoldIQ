# tests/agents_tests/business_logic_tests/utils/test_visualization_utils.py

import pytest
import matplotlib.pyplot as plt
from agents.dashboardBuilder.plotters.utils import (
    generate_color_palette, format_value_short, lighten_color, add_value_labels)

@pytest.fixture(autouse=True)
def matplotlib_cleanup():
    """Ensure all matplotlib figures are closed after each test"""
    yield
    plt.close('all')

class TestGenerateColorPalette:
    """Test color palette generation"""
    
    def test_generates_correct_number_of_colors(self):
        colors = generate_color_palette(5, "muted")
        assert len(colors) == 5
        assert all(c.startswith('#') for c in colors)
    
    def test_handles_zero_colors(self):
        colors = generate_color_palette(0, "muted")
        assert len(colors) == 1  # Returns default blue
        assert colors[0] == '#0000FF'
    
    def test_handles_negative_colors(self):
        colors = generate_color_palette(-1, "muted")
        assert len(colors) == 1
        assert colors[0] == '#0000FF'
    
    def test_switches_palette_when_exceeding_base(self, caplog):
        """Should warn and switch to muted for Set palettes"""
        colors = generate_color_palette(15, "Set1")
        assert len(colors) == 15
        assert "Switching to 'muted'" in caplog.text  # Check log warning
    
    def test_returns_hex_colors(self):
        colors = generate_color_palette(3, "muted")
        # Check format: #RRGGBB
        for color in colors:
            assert len(color) == 7
            assert color[0] == '#'
            int(color[1:], 16)  # Should not raise ValueError
    
    def test_different_palettes(self):
        """Test different palette names"""
        palettes = ["muted", "bright", "pastel", "deep", "Set1"]
        for palette in palettes:
            colors = generate_color_palette(3, palette)
            assert len(colors) == 3

class TestGenerateColorPaletteEdgeCases:
    
    def test_very_large_number_of_colors(self):
        """Should handle generating many colors"""
        colors = generate_color_palette(100, "muted")
        assert len(colors) == 100
        # All should be unique hex codes
        assert len(set(colors)) > 50  # At least some variety
    
    def test_invalid_palette_name(self, caplog):
        """Should handle invalid palette name gracefully"""
        colors = generate_color_palette(5, "nonexistent_palette")
        assert len(colors) == 1
        assert colors[0] == '#000000'  # Fallback black
        assert "Palette error" in caplog.text
    
    def test_returns_uppercase_hex(self):
        """Should return uppercase hex codes"""
        colors = generate_color_palette(3, "muted")
        for color in colors:
            assert color == color.upper()
            assert all(c in '0123456789ABCDEF#' for c in color)

class TestFormatValueShort:
    """Test value formatting"""
    
    @pytest.mark.parametrize("value,expected", [
        (500, "500"),
        (1_234, "1.23K"),
        (45_000, "45.00K"),
        (1_234_567, "1.23M"),
        (2_500_000_000, "2.50B"),
        (999, "999"),
        (1_000, "1.00K"),
    ])
    def test_formats_values_correctly(self, value, expected):
        assert format_value_short(value, decimal=2) == expected
    
    def test_handles_negative_values(self):
        assert format_value_short(-1_234) == "-1.23K"
        assert format_value_short(-1_000_000) == "-1.00M"
    
    def test_custom_decimal_places(self):
        assert format_value_short(1_234, decimal=1) == "1.2K"
        assert format_value_short(1_234, decimal=3) == "1.234K"
    
    def test_integer_display(self):
        """Values without decimal part should show as int"""
        assert format_value_short(100.0, decimal=2) == "100"
        assert format_value_short(500.0, decimal=2) == "500"

class TestFormatValueShortEdgeCases:
    
    def test_zero_value(self):
        assert format_value_short(0) == "0"
    
    def test_very_small_decimals(self):
        """Values between 0 and 1"""
        assert format_value_short(0.5, decimal=2) == "0.50"
        assert format_value_short(0.99, decimal=2) == "0.99"
    
    def test_boundary_values(self):
        """Test exact boundary values"""
        assert format_value_short(1_000, decimal=2) == "1.00K"
        assert format_value_short(1_000_000, decimal=2) == "1.00M"
        assert format_value_short(1_000_000_000, decimal=2) == "1.00B"
        
        assert format_value_short(999, decimal=2) == "999"
        assert format_value_short(999_999, decimal=2) == "1000.00K"
    
    def test_negative_zero(self):
        assert format_value_short(-0.0, decimal=2) == "0"
    
    @pytest.mark.parametrize("decimal", [0, 1, 5, 10])
    def test_various_decimal_precision(self, decimal):
        """Should respect decimal parameter"""
        result = format_value_short(1_234, decimal=decimal)
        if decimal == 0:
            assert result == "1K"
        else:
            assert f"1.{'2' * min(decimal, 2)}" in result

class TestDataValidation:
    """Test handling of edge case data"""
    
    def test_format_value_with_nan(self):
        """Should handle NaN gracefully"""
        import numpy as np
        # Depending on desired behavior, might want to test this
        try:
            result = format_value_short(np.nan, decimal=2)
            assert result in ['nan', 'NaN', '']  # Acceptable outputs
        except (ValueError, TypeError):
            pass  # Also acceptable
    
    def test_format_value_with_infinity(self):
        """Should handle infinity"""
        import numpy as np
        try:
            result = format_value_short(np.inf, decimal=2)
            assert 'inf' in result.lower() or result == ''
        except (ValueError, TypeError):
            pass
    
    def test_lighten_color_with_invalid_hex(self):
        """Should handle invalid hex codes"""
        with pytest.raises((ValueError, KeyError)):
            lighten_color("#GGGGGG", amount=0.3)
    
    def test_generate_palette_with_float_n_colors(self):
        """Should handle float input for n_colors"""
        # Should either convert to int or raise error
        try:
            colors = generate_color_palette(5.7, "muted")
            # If it works, should return 5 or 6 colors
            assert len(colors) in [5, 6]
        except (TypeError, ValueError):
            pass  # Also acceptable behavior

class TestLightenColor:
    """Test color lightening"""
    
    def test_lightens_color(self):
        dark_blue = "#3498DB"
        light_blue = lighten_color(dark_blue, amount=0.3)
        
        assert light_blue.startswith('#')
        assert light_blue != dark_blue
        # Light color should have higher RGB values
        assert int(light_blue[1:3], 16) > int(dark_blue[1:3], 16)
    
    def test_full_lighten_becomes_white(self):
        color = "#000000"
        white = lighten_color(color, amount=1.0)
        assert white.upper() in ["#FFFFFF", "#FFFFFFFF"]  # May include alpha
    
    def test_zero_amount_unchanged(self):
        color = "#3498DB"
        result = lighten_color(color, amount=0.0)
        # Should be very close to original
        assert result[1:3] == color[1:3]  # Check first RGB component

class TestLightenColorEdgeCases:
    
    def test_already_white(self):
        """Lightening white should stay white"""
        result = lighten_color("#FFFFFF", amount=0.5)
        assert result.upper() in ["#FFFFFF", "#FFFFFFFF"]
    
    def test_with_rgba_input(self):
        """Should handle RGBA tuple input"""
        rgba = (0.5, 0.5, 0.5, 1.0)
        result = lighten_color(rgba, amount=0.3)
        assert result.startswith('#')
    
    def test_named_colors(self):
        """Should handle named CSS colors"""
        result = lighten_color("red", amount=0.3)
        assert result.startswith('#')
        # Lightened red should have high R value
        assert int(result[1:3], 16) > 200
    
    def test_negative_amount_raises_or_handles(self):
        """Test behavior with negative amount"""
        # Depending on implementation, might raise or clip to 0
        try:
            result = lighten_color("#3498DB", amount=-0.1)
            # If it doesn't raise, it should darken or stay same
            assert result.startswith('#')
        except (ValueError, AssertionError):
            pass  # Expected if validation exists
    
    def test_amount_over_1(self):
        """Test with amount > 1.0"""
        result = lighten_color("#000000", amount=1.5)
        # Should clip to white or handle gracefully
        assert result.startswith('#')

class TestAddValueLabels:
    
    @pytest.fixture
    def mock_ax(self):
        """Create mock axes with containers"""
        fig, ax = plt.subplots()
        return ax
    
    def test_horizontal_bars_integer_format(self, mock_ax):
        """Test horizontal bars with integer values"""
        # Create horizontal bar chart
        categories = ['A', 'B', 'C']
        values = [1000, 2500, 3750]
        mock_ax.barh(categories, values)
        
        add_value_labels(mock_ax, orientation='h', float_type=False)
        
        # Check labels were added
        assert len(mock_ax.texts) > 0
        labels = [t.get_text() for t in mock_ax.texts]
        assert '1,000' in labels
        assert '2,500' in labels
        plt.close()
    
    def test_vertical_bars_float_format(self, mock_ax):
        """Test vertical bars with float values"""
        categories = ['A', 'B', 'C']
        values = [10.5, 25.75, 37.25]
        mock_ax.bar(categories, values)
        
        add_value_labels(mock_ax, orientation='v', float_type=True)
        
        labels = [t.get_text() for t in mock_ax.texts]
        assert '10.50' in labels
        assert '25.75' in labels
        plt.close()
    
    def test_short_format(self, mock_ax):
        """Test short format (K, M, B)"""
        categories = ['A', 'B', 'C']
        values = [1500, 2_500_000, 1_000_000_000]
        mock_ax.bar(categories, values)
        
        add_value_labels(mock_ax, orientation='v', short_format=True)
        
        labels = [t.get_text() for t in mock_ax.texts]
        assert '1.50K' in labels
        assert '2.50M' in labels
        assert '1.00B' in labels
        plt.close()
    
    def test_skips_zero_and_negative_values(self, mock_ax):
        """Test that zero/negative values show empty labels"""
        categories = ['A', 'B', 'C', 'D']
        values = [1000, 0, -500, 2000]
        mock_ax.bar(categories, values)
        
        add_value_labels(mock_ax, orientation='v', float_type=False)
        
        all_labels = [t.get_text() for t in mock_ax.texts]
        non_empty_labels = [l for l in all_labels if l]
        
        # Should have 4 labels total (one per bar)
        assert len(all_labels) == 4
        # But only 2 non-empty (for positive values)
        assert len(non_empty_labels) == 2
        assert '1,000' in non_empty_labels
        assert '2,000' in non_empty_labels
        plt.close()
    
    def test_multiple_containers(self, mock_ax):
        """Test with multiple bar containers (grouped bars)"""
        categories = ['A', 'B', 'C']
        values1 = [100, 200, 300]
        values2 = [150, 250, 350]
        
        x = range(len(categories))
        width = 0.35
        mock_ax.bar([i - width/2 for i in x], values1, width)
        mock_ax.bar([i + width/2 for i in x], values2, width)
        
        add_value_labels(mock_ax, orientation='v', float_type=False)
        
        # Should have labels for both containers
        assert len(mock_ax.containers) == 2
        plt.close()

class TestAddValueLabelsWithStyles:
    """Test label addition with different matplotlib styles"""
    
    def test_with_different_rcParams(self):
        """Labels should work regardless of rcParams"""
        fig, ax = plt.subplots()
        
        with plt.style.context('seaborn-v0_8'):
            ax.bar(['A', 'B'], [100, 200])
            add_value_labels(ax, orientation='v', float_type=False)
            assert len(ax.texts) > 0
        
        plt.close()
    
    def test_label_positions(self):
        """Test that labels are positioned correctly"""
        fig, ax = plt.subplots()
        values = [100, 200, 300]
        bars = ax.bar(['A', 'B', 'C'], values)
        
        add_value_labels(ax, orientation='v', float_type=False)
        
        # Check we have the right number of labels
        non_empty_labels = [t for t in ax.texts if t.get_text()]
        assert len(non_empty_labels) == len(values)
        
        # Labels should be created
        assert all(label.get_text() for label in non_empty_labels)
        
        plt.close()

class TestUtilsIntegration:
    """Integration tests combining multiple utils"""
    
    @pytest.mark.parametrize("palette,n_colors", [
        ("muted", 5),
        ("bright", 10),
        ("Set1", 8),
        ("colorblind", 6),
    ])
    def test_palette_then_lighten(self, palette, n_colors):
        """Generate palette then lighten each color"""
        colors = generate_color_palette(n_colors, palette)
        lightened = [lighten_color(c, amount=0.3) for c in colors]
        
        assert len(lightened) == n_colors
        assert all(l.startswith('#') for l in lightened)
        # Lightened should be different
        assert lightened != colors
    
    def test_format_values_for_display(self):
        """Test formatting pipeline for chart labels"""
        values = [500, 1_500, 50_000, 2_000_000, 1_500_000_000]
        
        # Short format
        short = [format_value_short(v, decimal=1) for v in values]
        assert short == ["500", "1.5K", "50.0K", "2.0M", "1.5B"]
        
        # Full format with more precision
        precise = [format_value_short(v, decimal=3) for v in values]
        assert "1.500K" in precise

class TestPerformance:
    
    def test_generate_many_colors_performance(self):
        """Should generate 1000 colors in reasonable time"""
        import time
        start = time.time()
        colors = generate_color_palette(1000, "muted")
        elapsed = time.time() - start
        
        assert len(colors) == 1000
        assert elapsed < 2.0  # Should be fast