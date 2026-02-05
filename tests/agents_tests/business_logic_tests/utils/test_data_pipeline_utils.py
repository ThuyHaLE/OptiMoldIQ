# tests/agents_tests/business_logic_tests/utils/test_data_pipeline_utils.py

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
from datetime import datetime

from agents.dataPipelineOrchestrator.utils import (
    load_existing_data, dataframes_equal_fast, 
    ProcessingStatus, ErrorType, DataProcessingReport)

class TestLoadExistingData:
    """Test suite for load_existing_data function"""
    
    def test_load_valid_xlsx(self, tmp_path):
        """Test loading a valid .xlsx file"""
        # Create test data
        df = pd.DataFrame({
            "A": [1, 2, 3],
            "B": ["x", "y", "z"],
            "C": [1.1, 2.2, 3.3]
        })
        
        xlsx_path = tmp_path / "test.xlsx"
        df.to_excel(xlsx_path, index=False)
        
        # Load and verify
        result = load_existing_data(xlsx_path)
        
        assert result.status == ProcessingStatus.SUCCESS
        assert result.error_type == ErrorType.NONE
        assert result.error_message == ''
        pd.testing.assert_frame_equal(result.data, df)
        assert result.metadata["file_path"] == str(xlsx_path)
    
    def test_load_valid_parquet(self, tmp_path):
        """Test loading a valid .parquet file"""
        df = pd.DataFrame({
            "id": [1, 2, 3],
            "name": ["Alice", "Bob", "Charlie"],
            "score": [95.5, 87.3, 91.2]
        })
        
        parquet_path = tmp_path / "test.parquet"
        df.to_parquet(parquet_path, index=False)
        
        result = load_existing_data(parquet_path)
        
        assert result.status == ProcessingStatus.SUCCESS
        pd.testing.assert_frame_equal(result.data, df)
        assert result.metadata["file_path"] == str(parquet_path)
    
    def test_load_nonexistent_file(self, tmp_path):
        """Test loading a file that doesn't exist"""
        nonexistent_path = tmp_path / "nonexistent.xlsx"
        
        result = load_existing_data(nonexistent_path)
        
        assert result.status == ProcessingStatus.ERROR
        assert result.error_type == ErrorType.FILE_NOT_FOUND
        assert "File not found" in result.error_message
        assert result.data.empty
    
    def test_load_unsupported_format(self, tmp_path):
        """Test loading a file with unsupported extension"""
        csv_path = tmp_path / "test.csv"
        df = pd.DataFrame({"A": [1, 2, 3]})
        df.to_csv(csv_path, index=False)
        
        result = load_existing_data(csv_path)
        
        assert result.status == ProcessingStatus.ERROR
        assert result.error_type == ErrorType.UNSUPPORTED_DATA_TYPE
        assert "Unsupported file extension '.csv'" in result.error_message
        assert ".xlsb" in result.error_message
        assert ".xlsx" in result.error_message
        assert ".parquet" in result.error_message
        assert result.data.empty
    
    def test_load_corrupted_xlsx(self, tmp_path):
        """Test loading a corrupted .xlsx file"""
        corrupted_path = tmp_path / "corrupted.xlsx"
        corrupted_path.write_bytes(b"This is not a valid Excel file")
        
        result = load_existing_data(corrupted_path)
        
        assert result.status == ProcessingStatus.ERROR
        assert result.error_type == ErrorType.FILE_READ_ERROR
        assert "Failed to read .xlsx file" in result.error_message
        assert result.data.empty
    
    def test_load_empty_xlsx(self, tmp_path):
        """Test loading an empty Excel file"""
        empty_df = pd.DataFrame()
        xlsx_path = tmp_path / "empty.xlsx"
        empty_df.to_excel(xlsx_path, index=False)
        
        result = load_existing_data(xlsx_path)
        
        assert result.status == ProcessingStatus.SUCCESS
        assert result.data.empty
    
    def test_load_with_string_path(self, tmp_path):
        """Test loading with string path instead of Path object"""
        df = pd.DataFrame({"A": [1, 2, 3]})
        xlsx_path = tmp_path / "test.xlsx"
        df.to_excel(xlsx_path, index=False)
        
        # Pass as string
        result = load_existing_data(str(xlsx_path))
        
        assert result.status == ProcessingStatus.SUCCESS
        pd.testing.assert_frame_equal(result.data, df)
    
    def test_load_large_parquet(self, tmp_path):
        """Test loading a large parquet file"""
        # Create larger dataset
        large_df = pd.DataFrame({
            "id": range(10000),
            "value": np.random.rand(10000),
            "category": np.random.choice(["A", "B", "C"], 10000)
        })
        
        parquet_path = tmp_path / "large.parquet"
        large_df.to_parquet(parquet_path, index=False)
        
        result = load_existing_data(parquet_path)
        
        assert result.status == ProcessingStatus.SUCCESS
        assert len(result.data) == 10000
        pd.testing.assert_frame_equal(result.data, large_df)
    
    def test_load_excel_with_special_characters(self, tmp_path):
        """Test loading Excel with special characters in data"""
        df = pd.DataFrame({
            "name": ["Nguyễn Văn A", "Trần Thị B", "Lê Minh C"],
            "email": ["test@example.com", "user@test.com", "admin@site.com"],
            "notes": ["Special: !@#$%", "Unicode: ñ ü ö", "Math: ∑ ∫ √"]
        })
        
        xlsx_path = tmp_path / "special_chars.xlsx"
        df.to_excel(xlsx_path, index=False)
        
        result = load_existing_data(xlsx_path)
        
        assert result.status == ProcessingStatus.SUCCESS
        pd.testing.assert_frame_equal(result.data, df)
    
    def test_load_with_datetime_columns(self, tmp_path):
        """Test loading file with datetime columns"""
        df = pd.DataFrame({
            "date": pd.date_range("2024-01-01", periods=5),
            "value": [10, 20, 30, 40, 50]
        })
        
        parquet_path = tmp_path / "datetime.parquet"
        df.to_parquet(parquet_path, index=False)
        
        result = load_existing_data(parquet_path)
        
        assert result.status == ProcessingStatus.SUCCESS
        pd.testing.assert_frame_equal(result.data, df)
    
    def test_load_with_mixed_types(self, tmp_path):
        """Test loading file with mixed data types"""
        df = pd.DataFrame({
            "int_col": [1, 2, 3],
            "float_col": [1.1, 2.2, 3.3],
            "str_col": ["a", "b", "c"],
            "bool_col": [True, False, True],
            "datetime_col": pd.date_range("2024-01-01", periods=3)
        })
        
        parquet_path = tmp_path / "mixed_types.parquet"
        df.to_parquet(parquet_path, index=False)
        
        result = load_existing_data(parquet_path)
        
        assert result.status == ProcessingStatus.SUCCESS
        pd.testing.assert_frame_equal(result.data, df)


class TestDataframesEqualFast:
    """Test suite for dataframes_equal_fast function"""
    
    def test_identical_dataframes(self):
        """Test two identical dataframes"""
        df1 = pd.DataFrame({
            "A": [1, 2, 3],
            "B": ["x", "y", "z"]
        })
        df2 = df1.copy()
        
        assert dataframes_equal_fast(df1, df2) is True
    
    def test_different_shapes(self):
        """Test dataframes with different shapes"""
        df1 = pd.DataFrame({"A": [1, 2, 3]})
        df2 = pd.DataFrame({"A": [1, 2]})
        
        assert dataframes_equal_fast(df1, df2) is False
    
    def test_different_columns(self):
        """Test dataframes with different number of columns"""
        df1 = pd.DataFrame({"A": [1, 2, 3]})
        df2 = pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})
        
        assert dataframes_equal_fast(df1, df2) is False
    
    def test_different_values(self):
        """Test dataframes with same shape but different values"""
        df1 = pd.DataFrame({"A": [1, 2, 3]})
        df2 = pd.DataFrame({"A": [1, 2, 4]})
        
        assert dataframes_equal_fast(df1, df2) is False
    
    def test_different_column_names(self):
        """Test dataframes with different column names"""
        df1 = pd.DataFrame({"A": [1, 2, 3]})
        df2 = pd.DataFrame({"B": [1, 2, 3]})
        
        assert dataframes_equal_fast(df1, df2) is False
    
    def test_both_empty(self):
        """Test two empty dataframes"""
        df1 = pd.DataFrame()
        df2 = pd.DataFrame()
        
        assert dataframes_equal_fast(df1, df2) is True
    
    def test_one_empty_one_not(self):
        """Test one empty and one non-empty dataframe"""
        df1 = pd.DataFrame()
        df2 = pd.DataFrame({"A": [1, 2, 3]})
        
        assert dataframes_equal_fast(df1, df2) is False
    
    def test_different_row_order_same_data(self):
        """Test dataframes with same data but different row order"""
        df1 = pd.DataFrame({
            "A": [1, 2, 3],
            "B": ["x", "y", "z"]
        })
        df2 = pd.DataFrame({
            "A": [3, 1, 2],
            "B": ["z", "x", "y"]
        })
        
        # Should be True because function sorts before comparing
        assert dataframes_equal_fast(df1, df2) is True
    
    def test_different_column_order(self):
        """Test dataframes with same data but different column order"""
        df1 = pd.DataFrame({
            "A": [1, 2, 3],
            "B": ["x", "y", "z"]
        })
        df2 = pd.DataFrame({
            "B": ["x", "y", "z"],
            "A": [1, 2, 3]
        })
        
        # Should be True because function sorts columns
        assert dataframes_equal_fast(df1, df2) is True
    
    def test_with_nan_values(self):
        """Test dataframes with NaN values"""
        df1 = pd.DataFrame({
            "A": [1, np.nan, 3],
            "B": ["x", "y", "z"]
        })
        df2 = df1.copy()
        
        assert dataframes_equal_fast(df1, df2) is True
    
    def test_different_nan_positions(self):
        """Test dataframes with NaN in different positions"""
        df1 = pd.DataFrame({
            "A": [1, np.nan, 3],
            "B": ["x", "y", "z"]
        })
        df2 = pd.DataFrame({
            "A": [np.nan, 2, 3],
            "B": ["x", "y", "z"]
        })
        
        assert dataframes_equal_fast(df1, df2) is False
    
    def test_large_dataframes(self):
        """Test with large dataframes"""
        size = 100000
        df1 = pd.DataFrame({
            "A": np.random.rand(size),
            "B": np.random.choice(["x", "y", "z"], size),
            "C": np.random.randint(0, 100, size)
        })
        df2 = df1.copy()
        
        assert dataframes_equal_fast(df1, df2) is True
    
    def test_with_datetime_columns(self):
        """Test dataframes with datetime columns"""
        df1 = pd.DataFrame({
            "date": pd.date_range("2024-01-01", periods=5),
            "value": [10, 20, 30, 40, 50]
        })
        df2 = df1.copy()
        
        assert dataframes_equal_fast(df1, df2) is True
    
    def test_with_categorical_columns(self):
        """Test dataframes with categorical columns"""
        df1 = pd.DataFrame({
            "category": pd.Categorical(["A", "B", "C", "A", "B"]),
            "value": [1, 2, 3, 4, 5]
        })
        df2 = df1.copy()
        
        assert dataframes_equal_fast(df1, df2) is True
    
    def test_with_mixed_types(self):
        """Test dataframes with mixed data types"""
        df1 = pd.DataFrame({
            "int_col": [1, 2, 3],
            "float_col": [1.1, 2.2, 3.3],
            "str_col": ["a", "b", "c"],
            "bool_col": [True, False, True],
            "datetime_col": pd.date_range("2024-01-01", periods=3)
        })
        df2 = df1.copy()
        
        assert dataframes_equal_fast(df1, df2) is True
    
    def test_float_precision_differences(self):
        """Test dataframes with slight float precision differences"""
        df1 = pd.DataFrame({"A": [1.0000000001, 2.0, 3.0]})
        df2 = pd.DataFrame({"A": [1.0000000002, 2.0, 3.0]})
        
        # Should be False due to precision difference
        assert dataframes_equal_fast(df1, df2) is False
    
    def test_string_case_sensitivity(self):
        """Test string comparison is case sensitive"""
        df1 = pd.DataFrame({"A": ["abc", "def", "ghi"]})
        df2 = pd.DataFrame({"A": ["ABC", "def", "ghi"]})
        
        assert dataframes_equal_fast(df1, df2) is False
    
    def test_with_duplicates(self):
        """Test dataframes with duplicate rows"""
        df1 = pd.DataFrame({
            "A": [1, 2, 2, 3],
            "B": ["x", "y", "y", "z"]
        })
        df2 = df1.copy()
        
        assert dataframes_equal_fast(df1, df2) is True
    
    def test_with_index_differences(self):
        """Test dataframes with different indices but same data"""
        df1 = pd.DataFrame({"A": [1, 2, 3]}, index=[0, 1, 2])
        df2 = pd.DataFrame({"A": [1, 2, 3]}, index=[5, 6, 7])
        
        # Should be True because reset_index is called
        assert dataframes_equal_fast(df1, df2) is True
    
    def test_with_multiindex(self):
        """Test dataframes with MultiIndex"""
        arrays = [
            ["A", "A", "B", "B"],
            [1, 2, 1, 2]
        ]
        index = pd.MultiIndex.from_arrays(arrays, names=["letter", "number"])
        
        df1 = pd.DataFrame({"value": [10, 20, 30, 40]}, index=index)
        df2 = df1.copy()
        
        assert dataframes_equal_fast(df1, df2) is True
    
    def test_exception_fallback(self):
        """Test that function falls back to .equals() on exception"""
        # Create dataframe that might cause sorting issues
        df1 = pd.DataFrame({
            "A": [1, 2, 3],
            "B": [{"x": 1}, {"y": 2}, {"z": 3}]  # Dict column can't be sorted
        })
        df2 = df1.copy()
        
        # Should still work via fallback
        result = dataframes_equal_fast(df1, df2)
        assert isinstance(result, bool)
    
    def test_single_row_dataframes(self):
        """Test comparison of single-row dataframes"""
        df1 = pd.DataFrame({"A": [1], "B": ["x"]})
        df2 = pd.DataFrame({"A": [1], "B": ["x"]})
        
        assert dataframes_equal_fast(df1, df2) is True
    
    def test_single_column_dataframes(self):
        """Test comparison of single-column dataframes"""
        df1 = pd.DataFrame({"A": [1, 2, 3, 4, 5]})
        df2 = pd.DataFrame({"A": [1, 2, 3, 4, 5]})
        
        assert dataframes_equal_fast(df1, df2) is True
    
    def test_unicode_strings(self):
        """Test dataframes with Unicode strings"""
        df1 = pd.DataFrame({
            "name": ["Nguyễn", "Trần", "Lê"],
            "city": ["Hà Nội", "Sài Gòn", "Đà Nẵng"]
        })
        df2 = df1.copy()
        
        assert dataframes_equal_fast(df1, df2) is True
    
    def test_extreme_values(self):
        """Test dataframes with extreme numeric values"""
        df1 = pd.DataFrame({
            "small": [1e-300, 2e-300, 3e-300],
            "large": [1e300, 2e300, 3e300]
        })
        df2 = df1.copy()
        
        assert dataframes_equal_fast(df1, df2) is True


# Fixtures for common test scenarios
@pytest.fixture
def sample_excel_data():
    """Fixture providing sample Excel data"""
    return pd.DataFrame({
        "id": [1, 2, 3, 4, 5],
        "name": ["Alice", "Bob", "Charlie", "David", "Eve"],
        "score": [95.5, 87.3, 91.2, 88.7, 93.1],
        "passed": [True, True, True, True, True]
    })


@pytest.fixture
def sample_parquet_data():
    """Fixture providing sample Parquet data"""
    return pd.DataFrame({
        "timestamp": pd.date_range("2024-01-01", periods=100, freq="H"),
        "sensor_id": np.random.randint(1, 10, 100),
        "temperature": np.random.uniform(20, 30, 100),
        "humidity": np.random.uniform(40, 60, 100)
    })


@pytest.fixture
def temp_dir():
    """Fixture providing a temporary directory"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


# Integration tests
class TestIntegration:
    """Integration tests combining both functions"""
    
    def test_load_and_compare_workflow(self, tmp_path):
        """Test workflow of saving, loading, and comparing dataframes"""
        # Create original data
        original_df = pd.DataFrame({
            "A": [1, 2, 3, 4, 5],
            "B": ["a", "b", "c", "d", "e"],
            "C": [1.1, 2.2, 3.3, 4.4, 5.5]
        })
        
        # Save to different formats
        xlsx_path = tmp_path / "data.xlsx"
        parquet_path = tmp_path / "data.parquet"
        
        original_df.to_excel(xlsx_path, index=False)
        original_df.to_parquet(parquet_path, index=False)
        
        # Load both
        xlsx_result = load_existing_data(xlsx_path)
        parquet_result = load_existing_data(parquet_path)
        
        # Verify both loaded successfully
        assert xlsx_result.status == ProcessingStatus.SUCCESS
        assert parquet_result.status == ProcessingStatus.SUCCESS
        
        # Compare loaded data with original
        assert dataframes_equal_fast(xlsx_result.data, original_df)
        assert dataframes_equal_fast(parquet_result.data, original_df)
        
        # Compare loaded data with each other
        assert dataframes_equal_fast(xlsx_result.data, parquet_result.data)


# Performance tests
class TestPerformance:
    """Performance tests for large datasets"""
    
    @pytest.mark.slow
    def test_large_dataframe_comparison_performance(self):
        """Test performance with very large dataframes"""
        import time
        
        size = 1_000_000
        df1 = pd.DataFrame({
            "id": range(size),
            "value": np.random.rand(size),
            "category": np.random.choice(["A", "B", "C", "D"], size)
        })
        df2 = df1.copy()
        
        start = time.time()
        result = dataframes_equal_fast(df1, df2)
        elapsed = time.time() - start
        
        assert result is True
        assert elapsed < 5.0  # Should complete in less than 5 seconds
        print(f"\nLarge dataframe comparison took {elapsed:.2f} seconds")