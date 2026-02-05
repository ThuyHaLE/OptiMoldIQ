# tests/agents_tests/business_logic_tests/utils/test_utils.py

import pytest
import pandas as pd
import json
import shutil
from pathlib import Path
from datetime import datetime
import tempfile
import os

from agents.utils import (
     load_json, camel_to_snake, save_output_with_versioning,
     archive_old_files, write_excel_data, write_text_report,
     update_weight_and_save_confidence_report, append_change_log,
     load_annotation_path, read_change_log, extract_latest_saved_files,
     log_dict_as_table, get_latest_change_row, rank_nonzero
     )

class TestLoadJson:
    """Test suite for load_json function"""
    
    def test_load_valid_json(self, tmp_path):
        """Test loading a valid JSON file"""
        test_data = {"key": "value", "number": 123}
        json_file = tmp_path / "test.json"
        
        with open(json_file, 'w') as f:
            json.dump(test_data, f)
        
        result = load_json(str(json_file))
        assert result == test_data
    
    def test_load_nonexistent_file(self):
        """Test loading a non-existent file"""
        result = load_json("nonexistent.json")
        assert result is None
    
    def test_load_invalid_extension(self, tmp_path):
        """Test loading a file with wrong extension"""
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("not json")
        
        result = load_json(str(txt_file))
        assert result is None
    
    def test_load_invalid_json_format(self, tmp_path):
        """Test loading a file with invalid JSON"""
        json_file = tmp_path / "invalid.json"
        json_file.write_text("{invalid json content")
        
        result = load_json(str(json_file))
        assert result is None
    
    def test_load_empty_json(self, tmp_path):
        """Test loading an empty JSON object"""
        json_file = tmp_path / "empty.json"
        json_file.write_text("{}")
        
        result = load_json(str(json_file))
        assert result == {}


class TestCamelToSnake:
    """Test suite for camel_to_snake function"""
    
    def test_simple_camel_case(self):
        """Test simple camelCase conversion"""
        assert camel_to_snake("camelCase") == "camel_case"
    
    def test_pascal_case(self):
        """Test PascalCase conversion"""
        assert camel_to_snake("PascalCase") == "pascal_case"
    
    def test_multiple_capitals(self):
        """Test multiple consecutive capitals"""
        assert camel_to_snake("XMLHttpRequest") == "xml_http_request"
    
    def test_numbers_in_name(self):
        """Test names with numbers"""
        assert camel_to_snake("html2pdf") == "html2pdf"
    
    def test_already_snake_case(self):
        """Test already snake_case string"""
        assert camel_to_snake("already_snake") == "already_snake"
    
    def test_single_word(self):
        """Test single word"""
        assert camel_to_snake("word") == "word"


class TestArchiveOldFiles:
    """Test suite for archive_old_files function"""
    
    def test_archive_files(self, tmp_path):
        """Test archiving files from newest to historical"""
        newest_dir = tmp_path / "newest"
        historical_dir = tmp_path / "historical_db"
        newest_dir.mkdir()
        
        # Create test files
        (newest_dir / "file1.txt").write_text("content1")
        (newest_dir / "file2.txt").write_text("content2")
        
        result = archive_old_files(newest_dir, historical_dir)
        
        # Check files moved
        assert not (newest_dir / "file1.txt").exists()
        assert not (newest_dir / "file2.txt").exists()
        assert (historical_dir / "file1.txt").exists()
        assert (historical_dir / "file2.txt").exists()
        assert "Moved old file" in result
    
    def test_archive_empty_directory(self, tmp_path):
        """Test archiving when newest directory is empty"""
        newest_dir = tmp_path / "newest"
        historical_dir = tmp_path / "historical_db"
        newest_dir.mkdir()
        
        result = archive_old_files(newest_dir, historical_dir)
        assert result == ""


class TestWriteExcelData:
    """Test suite for write_excel_data function"""
    
    def test_write_single_dataframe(self, tmp_path):
        """Test writing a single DataFrame to Excel"""
        df = pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})
        excel_path = tmp_path / "test.xlsx"
        
        result = write_excel_data(excel_path, df)
        
        assert excel_path.exists()
        assert "Saved new file" in result
        
        # Verify content
        loaded_df = pd.read_excel(excel_path)
        pd.testing.assert_frame_equal(df, loaded_df)
    
    def test_write_multiple_sheets(self, tmp_path):
        """Test writing multiple DataFrames as sheets"""
        df1 = pd.DataFrame({"A": [1, 2], "B": [3, 4]})
        df2 = pd.DataFrame({"X": [5, 6], "Y": [7, 8]})
        data_dict = {"Sheet1": df1, "Sheet2": df2}
        
        excel_path = tmp_path / "multi_sheet.xlsx"
        result = write_excel_data(excel_path, data_dict)
        
        assert excel_path.exists()
        
        # Verify sheets
        loaded_df1 = pd.read_excel(excel_path, sheet_name="Sheet1")
        loaded_df2 = pd.read_excel(excel_path, sheet_name="Sheet2")
        pd.testing.assert_frame_equal(df1, loaded_df1)
        pd.testing.assert_frame_equal(df2, loaded_df2)
    
    def test_write_invalid_type(self, tmp_path):
        """Test writing invalid data type raises TypeError"""
        excel_path = tmp_path / "test.xlsx"
        
        with pytest.raises(TypeError):
            write_excel_data(excel_path, "invalid data")
    
    def test_write_invalid_dict_contents(self, tmp_path):
        """Test writing dict with invalid contents raises TypeError"""
        excel_path = tmp_path / "test.xlsx"
        invalid_dict = {"sheet": "not a dataframe"}
        
        with pytest.raises(TypeError):
            write_excel_data(excel_path, invalid_dict)


class TestWriteTextReport:
    """Test suite for write_text_report function"""
    
    def test_write_valid_report(self, tmp_path):
        """Test writing a valid text report"""
        report_path = tmp_path / "report.txt"
        report_text = "This is a test report\nWith multiple lines"
        
        result = write_text_report(report_path, report_text)
        
        assert report_path.exists()
        assert "Saved report" in result
        assert report_path.read_text() == report_text
    
    def test_write_invalid_type(self, tmp_path):
        """Test writing invalid type raises TypeError"""
        report_path = tmp_path / "report.txt"
        
        with pytest.raises(TypeError):
            write_text_report(report_path, 123)


class TestAppendChangeLog:
    """Test suite for append_change_log function"""
    
    def test_append_to_existing_file(self, tmp_path):
        """Test appending to an existing log file"""
        log_path = tmp_path / "change.log"
        log_path.write_text("First line\n")
        
        append_change_log(log_path, "Second line")
        
        content = log_path.read_text()
        assert "First line" in content
        assert "Second line" in content
    
    def test_append_to_new_file(self, tmp_path):
        """Test appending to a new log file"""
        log_path = tmp_path / "new.log"
        
        append_change_log(log_path, "First entry")
        
        assert log_path.exists()
        assert log_path.read_text() == "First entry\n"
    
    def test_append_empty_string_raises_error(self, tmp_path):
        """Test appending empty string raises ValueError"""
        log_path = tmp_path / "log.txt"
        
        with pytest.raises(ValueError):
            append_change_log(log_path, "")
    
    def test_append_whitespace_only_raises_error(self, tmp_path):
        """Test appending whitespace only raises ValueError"""
        log_path = tmp_path / "log.txt"
        
        with pytest.raises(ValueError):
            append_change_log(log_path, "   ")


class TestExtractLatestSavedFiles:
    """Test suite for extract_latest_saved_files function"""
    
    def test_extract_single_file(self):
        """Test extracting single file from log"""
        log_text = """
        ============================================================
        EXPORT LOG:
        Saved new file: /path/to/file.xlsx
        """
        
        result = extract_latest_saved_files(log_text)
        assert result == ["/path/to/file.xlsx"]
    
    def test_extract_multiple_files(self):
        """Test extracting multiple files from log"""
        log_text = """
        ============================================================
        EXPORT LOG:
        Saved new file: /path/to/file1.xlsx
        Saved new file: /path/to/file2.txt
        """
        
        result = extract_latest_saved_files(log_text)
        assert len(result) == 2
        assert "/path/to/file1.xlsx" in result
        assert "/path/to/file2.txt" in result
    
    def test_extract_from_multiple_sections(self):
        """Test extracting only from latest section"""
        log_text = """
        ============================================================
        EXPORT LOG:
        Saved new file: /old/file.xlsx
        ============================================================
        EXPORT LOG:
        Saved new file: /new/file.xlsx
        """
        
        result = extract_latest_saved_files(log_text)
        assert result == ["/new/file.xlsx"]
    
    def test_extract_from_empty_log(self):
        """Test extracting from empty log"""
        result = extract_latest_saved_files("")
        assert result is None
    
    def test_extract_no_export_section(self):
        """Test extracting when no EXPORT LOG section"""
        log_text = "Some random log content"
        result = extract_latest_saved_files(log_text)
        assert result is None


class TestLogDictAsTable:
    """Test suite for log_dict_as_table function"""
    
    def test_simple_dict(self):
        """Test logging simple dictionary"""
        data = {"key1": "value1", "key2": "value2"}
        result = log_dict_as_table(data)
        
        assert "key1" in result
        assert "value1" in result
        assert "Metric" in result
        assert "Value" in result
    
    def test_dict_transpose(self):
        """Test logging dictionary with transpose"""
        data = {"A": [1, 2], "B": [3, 4]}
        result = log_dict_as_table(data, transpose=True)
        
        assert "A" in result
        assert "B" in result


class TestGetLatestChangeRow:
    """Test suite for get_latest_change_row function"""
    
    def test_get_latest_row(self, tmp_path):
        """Test getting the latest change row"""
        weights_path = tmp_path / "weights_hist.xlsx"
        
        df = pd.DataFrame({
            "shiftNGRate": [0.1, 0.2, 0.3],
            "shiftCavityRate": [0.4, 0.5, 0.6],
            "change_timestamp": [
                "2024-01-01 10:00:00",
                "2024-01-02 11:00:00",
                "2024-01-03 12:00:00"
            ]
        })
        df.to_excel(weights_path, index=False)
        
        result = get_latest_change_row(str(weights_path))
        
        assert result["shiftNGRate"] == 0.3
        assert result["shiftCavityRate"] == 0.6
        assert "change_timestamp" not in result


class TestRankNonzero:
    """Test suite for rank_nonzero function"""
    
    def test_rank_all_nonzero(self):
        """Test ranking when all values are non-zero"""
        row = pd.Series([10, 5, 15, 8])
        result = rank_nonzero(row)
        
        expected = pd.Series([2, 4, 1, 3], dtype='Int64')
        pd.testing.assert_series_equal(result, expected)
    
    def test_rank_with_zeros(self):
        """Test ranking with zero values"""
        row = pd.Series([10, 0, 15, 0, 8])
        result = rank_nonzero(row)
        
        expected = pd.Series([2, 0, 1, 0, 3], dtype='Int64')
        pd.testing.assert_series_equal(result, expected)
    
    def test_rank_all_zeros(self):
        """Test ranking when all values are zero"""
        row = pd.Series([0, 0, 0])
        result = rank_nonzero(row)
        
        expected = pd.Series([0, 0, 0], dtype='Int64')
        pd.testing.assert_series_equal(result, expected)
    
    def test_rank_single_nonzero(self):
        """Test ranking with single non-zero value"""
        row = pd.Series([0, 5, 0])
        result = rank_nonzero(row)
        
        expected = pd.Series([0, 1, 0], dtype='Int64')
        pd.testing.assert_series_equal(result, expected)


class TestSaveOutputWithVersioning:
    """Test suite for save_output_with_versioning function"""
    
    def test_save_single_dataframe(self, tmp_path):
        """Test saving single DataFrame with versioning"""
        df = pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})
        
        result = save_output_with_versioning(
            data=df,
            output_dir=tmp_path,
            filename_prefix="test"
        )
        
        assert "Saving new version" in result
        assert (tmp_path / "newest").exists()
        assert (tmp_path / "historical_db").exists()
        
        # Check Excel file created
        newest_files = list((tmp_path / "newest").glob("*.xlsx"))
        assert len(newest_files) == 1
    
    def test_save_with_report(self, tmp_path):
        """Test saving with report text"""
        df = pd.DataFrame({"A": [1, 2]})
        report = "This is a test report"
        
        result = save_output_with_versioning(
            data=df,
            output_dir=tmp_path,
            filename_prefix="test",
            report_text=report
        )
        
        assert "Saved report" in result
        
        # Check report file created
        report_files = list((tmp_path / "newest").glob("*.txt"))
        assert len(report_files) == 1
    
    def test_save_multiple_sheets(self, tmp_path):
        """Test saving dictionary of DataFrames"""
        data_dict = {
            "Sheet1": pd.DataFrame({"A": [1, 2]}),
            "Sheet2": pd.DataFrame({"B": [3, 4]})
        }
        
        result = save_output_with_versioning(
            data=data_dict,
            output_dir=tmp_path,
            filename_prefix="multi"
        )
        
        assert "Saved new file" in result


class TestUpdateWeightAndSaveConfidenceReport:
    """Test suite for update_weight_and_save_confidence_report function"""
    
    def test_update_weights(self, tmp_path):
        """Test updating weights and saving report"""
        report_text = "Test confidence report"
        enhanced_weights = {
            "shiftNGRate": 0.25,
            "shiftCavityRate": 0.30,
            "shiftCycleTimeRate": 0.20,
            "shiftCapacityRate": 0.25
        }
        
        result = update_weight_and_save_confidence_report(
            report_text=report_text,
            output_dir=tmp_path,
            filename_prefix="test",
            enhanced_weights=enhanced_weights
        )
        
        assert "Saving new version" in result
        assert (tmp_path / "weights_hist.xlsx").exists()
        
        # Verify weights saved
        weights_df = pd.read_excel(tmp_path / "weights_hist.xlsx")
        assert len(weights_df) == 1
        assert weights_df.iloc[0]["shiftNGRate"] == 0.25


# Fixtures for common test data
@pytest.fixture
def sample_dataframe():
    """Fixture providing a sample DataFrame"""
    return pd.DataFrame({
        "col1": [1, 2, 3, 4, 5],
        "col2": ["a", "b", "c", "d", "e"],
        "col3": [1.1, 2.2, 3.3, 4.4, 5.5]
    })


@pytest.fixture
def sample_json_data():
    """Fixture providing sample JSON data"""
    return {
        "name": "test",
        "values": [1, 2, 3],
        "nested": {"key": "value"}
    }


# Run tests with: pytest test_utils.py -v
# Run with coverage: pytest test_utils.py --cov=your_module --cov-report=html