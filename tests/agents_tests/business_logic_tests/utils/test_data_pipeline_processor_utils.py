# tests/agents_tests/business_logic_tests/utils/test_data_pipeline_processor_utils.py

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os

# Import the functions to test
from agents.dataPipelineOrchestrator.processors.processor_utils import (
    safe_convert,
    check_null_str,
    process_static_database,
    get_source_files,
    process_single_file,
    merge_and_process_dfs
)

from agents.dataPipelineOrchestrator.configs.output_formats import (
    DataProcessingReport,
    ProcessingStatus,
    ErrorType
)

class TestSafeConvert:
    """Test cases for safe_convert function"""
    
    def test_convert_int(self):
        """Test converting integer values"""
        assert safe_convert(123) == "123"
        assert safe_convert(0) == "0"
        assert safe_convert(-456) == "-456"
    
    def test_convert_float(self):
        """Test converting float values"""
        assert safe_convert(123.0) == "123"
        assert safe_convert(456.99) == "456"
        assert safe_convert(0.0) == "0"
    
    def test_convert_string(self):
        """Test converting string values"""
        assert safe_convert("hello") == "hello"
        assert safe_convert("123") == "123"
    
    def test_convert_nan(self):
        """Test handling NaN values"""
        result = safe_convert(np.nan)
        assert pd.isna(result)
        
        result = safe_convert(pd.NA)
        assert pd.isna(result)
    
    def test_convert_none(self):
        """Test handling None values"""
        result = safe_convert(None)
        assert pd.isna(result)


class TestCheckNullStr:
    """Test cases for check_null_str function"""
    
    def test_detect_null_strings(self):
        """Test detection of null-like string values"""
        df = pd.DataFrame({
            'col1': ['value1', 'nan', 'value2'],
            'col2': ['null', 'value3', 'none'],
            'col3': ['', 'n/a', 'NA']
        })
        
        result = check_null_str(df)
        
        # Check that all suspect values are detected
        assert 'nan' in result
        assert 'null' in result
        assert 'none' in result
        assert '' in result
        assert 'n/a' in result or 'NA' in result
    
    def test_no_null_strings(self):
        """Test with dataframe containing no null-like strings"""
        df = pd.DataFrame({
            'col1': ['value1', 'value2', 'value3'],
            'col2': ['data1', 'data2', 'data3']
        })
        
        result = check_null_str(df)
        assert len(result) == 0
    
    def test_case_insensitive_detection(self):
        """Test that detection is case-insensitive"""
        df = pd.DataFrame({
            'col1': ['NaN', 'NULL', 'None', 'N/A']
        })
        
        result = check_null_str(df)
        assert len(result) > 0


class TestProcessStaticDatabase:
    """Test cases for process_static_database function"""
    
    @pytest.fixture
    def temp_excel_file(self):
        """Create a temporary Excel file for testing"""
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            df = pd.DataFrame({
                'col1': [1, 2, 3],
                'col2': ['a', 'b', 'c'],
                'col3': [1.1, 2.2, 3.3]
            })
            df.to_excel(tmp.name, index=False)
            yield tmp.name
        os.unlink(tmp.name)
    
    @pytest.fixture
    def temp_empty_excel_file(self):
        """Create a temporary empty Excel file"""
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            df = pd.DataFrame()
            df.to_excel(tmp.name, index=False)
            yield tmp.name
        os.unlink(tmp.name)
    
    def test_process_valid_file(self, temp_excel_file):
        """Test processing a valid Excel file"""
        dtypes = {'col1': 'int64', 'col2': 'string', 'col3': 'float64'}
        
        result = process_static_database(
            db_path=temp_excel_file,
            db_name='test_db',
            spec_cases=[],
            dtypes=dtypes
        )
        
        assert result.status == ProcessingStatus.SUCCESS
        assert isinstance(result.data, pd.DataFrame)
        assert len(result.data) == 3
        assert result.metadata['records_processed'] == 3
        assert result.metadata['db_name'] == 'test_db'
    
    def test_process_empty_file(self, temp_empty_excel_file):
        """Test processing an empty Excel file"""
        result = process_static_database(
            db_path=temp_empty_excel_file,
            db_name='empty_db',
            spec_cases=[],
            dtypes={}
        )
        
        assert result.status == ProcessingStatus.SUCCESS
        assert result.data.empty
        assert 'empty' in result.metadata['warning'].lower()
    
    def test_process_nonexistent_file(self):
        """Test processing a file that doesn't exist"""
        result = process_static_database(
            db_path='/nonexistent/file.xlsx',
            db_name='test_db',
            spec_cases=[],
            dtypes={}
        )
        
        assert result.status == ProcessingStatus.ERROR
        assert result.error_type == ErrorType.FILE_READ_ERROR
        assert 'Failed to read file' in result.error_message
    
    def test_process_with_spec_cases(self, temp_excel_file):
        """Test processing with special case columns"""
        dtypes = {'col1': 'string', 'col2': 'string', 'col3': 'float64'}
        
        result = process_static_database(
            db_path=temp_excel_file,
            db_name='test_db',
            spec_cases=['col1'],
            dtypes=dtypes
        )
        
        assert result.status == ProcessingStatus.SUCCESS
        assert result.data['col1'].dtype == 'string'
    
    def test_invalid_dtype_conversion(self, temp_excel_file):
        """Test with invalid dtype conversion"""
        # Try to convert string column to int
        dtypes = {'col1': 'int64', 'col2': 'int64', 'col3': 'float64'}
        
        result = process_static_database(
            db_path=temp_excel_file,
            db_name='test_db',
            spec_cases=[],
            dtypes=dtypes
        )
        
        assert result.status == ProcessingStatus.PARTIAL_SUCCESS
        assert result.error_type == ErrorType.DATA_PROCESSING_ERROR


class TestGetSourceFiles:
    """Test cases for get_source_files function"""
    
    @pytest.fixture
    def temp_folder_with_files(self):
        """Create a temporary folder with test files"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            Path(tmpdir, 'data_202401_report.xlsx').touch()
            Path(tmpdir, 'data_202402_report.xlsx').touch()
            Path(tmpdir, 'data_202312_report.xlsx').touch()
            Path(tmpdir, 'other_file.xlsx').touch()
            yield tmpdir
    
    def test_find_matching_files(self, temp_folder_with_files):
        """Test finding files that match the pattern"""
        result = get_source_files(
            folder_path=temp_folder_with_files,
            name_start='data_',
            file_extension='.xlsx'
        )
        
        assert result.status == ProcessingStatus.SUCCESS
        assert len(result.data) == 3
        # Check files are sorted by date
        assert '202312' in result.data[0].name
        assert '202402' in result.data[-1].name
    
    def test_no_matching_files(self, temp_folder_with_files):
        """Test when no files match the pattern"""
        result = get_source_files(
            folder_path=temp_folder_with_files,
            name_start='nonexistent_',
            file_extension='.xlsx'
        )
        
        assert result.status == ProcessingStatus.ERROR
        assert result.error_type == ErrorType.FILE_NOT_FOUND
        assert 'No files found' in result.error_message
    
    def test_nonexistent_folder(self):
        """Test with a folder that doesn't exist"""
        result = get_source_files(
            folder_path='/nonexistent/folder',
            name_start='data_',
            file_extension='.xlsx'
        )
        
        assert result.status == ProcessingStatus.ERROR
        assert result.error_type == ErrorType.FILE_NOT_FOUND


class TestProcessSingleFile:
    """Test cases for process_single_file function"""
    
    @pytest.fixture
    def temp_excel_with_sheet(self):
        """Create temporary Excel file with specific sheet"""
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            df = pd.DataFrame({
                'field1': [1, 2, 3],
                'field2': ['a', 'b', 'c'],
                'field3': [1.1, 2.2, 3.3],
                'extra_field': ['x', 'y', 'z']
            })
            with pd.ExcelWriter(tmp.name, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Sheet1', index=False)
            yield tmp.name
        os.unlink(tmp.name)
    
    def test_process_valid_xlsx_file(self, temp_excel_with_sheet):
        """Test processing a valid XLSX file"""
        required_fields = ['field1', 'field2', 'field3']
        
        result = process_single_file(
            file_path=temp_excel_with_sheet,
            sheet_name='Sheet1',
            file_extension='.xlsx',
            required_fields=required_fields
        )
        
        assert result.status == ProcessingStatus.SUCCESS
        assert list(result.data.columns) == required_fields
        assert len(result.data) == 3
    
    def test_missing_required_fields(self, temp_excel_with_sheet):
        """Test when required fields are missing"""
        required_fields = ['field1', 'nonexistent_field']
        
        result = process_single_file(
            file_path=temp_excel_with_sheet,
            sheet_name='Sheet1',
            file_extension='.xlsx',
            required_fields=required_fields
        )
        
        assert result.status == ProcessingStatus.ERROR
        assert result.error_type == ErrorType.MISSING_FIELDS
        assert 'nonexistent_field' in result.error_message
    
    def test_unsupported_file_extension(self, temp_excel_with_sheet):
        """Test with unsupported file extension"""
        result = process_single_file(
            file_path=temp_excel_with_sheet,
            sheet_name='Sheet1',
            file_extension='.csv',
            required_fields=['field1']
        )
        
        assert result.status == ProcessingStatus.ERROR
        assert result.error_type == ErrorType.UNSUPPORTED_DATA_TYPE
    
    def test_nonexistent_file(self):
        """Test with a file that doesn't exist"""
        result = process_single_file(
            file_path='/nonexistent/file.xlsx',
            sheet_name='Sheet1',
            file_extension='.xlsx',
            required_fields=['field1']
        )
        
        assert result.status == ProcessingStatus.ERROR
        assert result.error_type == ErrorType.FILE_READ_ERROR


class TestMergeAndProcessDfs:
    """Test cases for merge_and_process_dfs function"""
    
    @pytest.fixture
    def sample_dataframes(self):
        """Create sample dataframes for testing"""
        df1 = pd.DataFrame({
            'col1': [1, 2, 3],
            'col2': ['a', 'b', 'c']
        })
        df2 = pd.DataFrame({
            'col1': [4, 5, 6],
            'col2': ['d', 'e', 'f']
        })
        return [df1, df2]
    
    @pytest.fixture
    def dataframes_with_duplicates(self):
        """Create dataframes with duplicate rows"""
        df1 = pd.DataFrame({
            'col1': [1, 2, 3],
            'col2': ['a', 'b', 'c']
        })
        df2 = pd.DataFrame({
            'col1': [3, 4, 5],
            'col2': ['c', 'd', 'e']
        })
        return [df1, df2]
    
    def test_merge_valid_dataframes(self, sample_dataframes):
        """Test merging valid dataframes"""
        dtypes = {'col1': 'int64', 'col2': 'string'}
        
        result = merge_and_process_dfs(
            db_name='test_db',
            merged_dfs=sample_dataframes,
            spec_cases=[],
            dtypes=dtypes
        )
        
        assert result.status == ProcessingStatus.SUCCESS
        assert len(result.data) == 6
        assert result.metadata['records_processed'] == 6
    
    def test_merge_with_duplicates(self, dataframes_with_duplicates):
        """Test merging dataframes with duplicate rows"""
        dtypes = {'col1': 'int64', 'col2': 'string'}
        
        result = merge_and_process_dfs(
            db_name='test_db',
            merged_dfs=dataframes_with_duplicates,
            spec_cases=[],
            dtypes=dtypes
        )
        
        assert result.status == ProcessingStatus.SUCCESS
        assert 'duplicate' in result.metadata['warning'].lower()
    
    def test_merge_empty_dataframes(self):
        """Test merging all empty dataframes"""
        empty_dfs = [pd.DataFrame(), pd.DataFrame()]
        
        result = merge_and_process_dfs(
            db_name='test_db',
            merged_dfs=empty_dfs,
            spec_cases=[],
            dtypes={}
        )
        
        assert result.status == ProcessingStatus.ERROR
        assert result.error_type == ErrorType.FILE_NOT_FOUND
        assert 'All merged DataFrames are empty' in result.error_message
    
    def test_merge_with_some_empty(self, sample_dataframes):
        """Test merging with some empty dataframes"""
        mixed_dfs = sample_dataframes + [pd.DataFrame()]
        dtypes = {'col1': 'int64', 'col2': 'string'}
        
        result = merge_and_process_dfs(
            db_name='test_db',
            merged_dfs=mixed_dfs,
            spec_cases=[],
            dtypes=dtypes
        )
        
        assert result.status == ProcessingStatus.SUCCESS
        assert 'empty DataFrame' in result.metadata['warning']
    
    def test_no_input_dataframes(self):
        """Test with no input dataframes"""
        result = merge_and_process_dfs(
            db_name='test_db',
            merged_dfs=[],
            spec_cases=[],
            dtypes={}
        )
        
        assert result.status == ProcessingStatus.ERROR
        assert 'No input DataFrames' in result.error_message
    
    def test_product_records_specific_processing(self):
        """Test productRecords-specific processing"""
        df = pd.DataFrame({
            'plasticResine': ['resin1', 'resin2'],
            'plasticResineCode': [101, 102],
            'recordDate': [44927, 44928],  # Excel serial dates
            'workingShift': ['day', 'night']
        })
        
        dtypes = {
            'plasticResin': 'string',
            'plasticResinCode': 'int64',
            'recordDate': 'object',
            'workingShift': 'string'
        }
        
        result = merge_and_process_dfs(
            db_name='productRecords',
            merged_dfs=[df],
            spec_cases=[],
            dtypes=dtypes
        )
        
        assert result.status == ProcessingStatus.SUCCESS
        assert 'plasticResin' in result.data.columns
        assert 'workingShift' in result.data.columns
        # Check that working shift is uppercase
        assert all(result.data['workingShift'].str.isupper())
    
    def test_purchase_orders_date_conversion(self):
        """Test purchaseOrders-specific date processing"""
        df = pd.DataFrame({
            'poReceivedDate': ['2024-01-01', '2024-01-02'],
            'poETA': ['2024-02-01', '2024-02-02'],
            'poNumber': ['PO001', 'PO002']
        })
        
        dtypes = {
            'poReceivedDate': 'object',
            'poETA': 'object',
            'poNumber': 'string'
        }
        
        result = merge_and_process_dfs(
            db_name='purchaseOrders',
            merged_dfs=[df],
            spec_cases=[],
            dtypes=dtypes
        )
        
        assert result.status == ProcessingStatus.SUCCESS
        # Dates should be converted to datetime
        assert pd.api.types.is_datetime64_any_dtype(result.data['poReceivedDate'])
        assert pd.api.types.is_datetime64_any_dtype(result.data['poETA'])
    
    def test_invalid_dtype_conversion(self, sample_dataframes):
        """Test with invalid dtype conversion"""
        # Try to convert string to int
        dtypes = {'col1': 'int64', 'col2': 'int64'}
        
        result = merge_and_process_dfs(
            db_name='test_db',
            merged_dfs=sample_dataframes,
            spec_cases=[],
            dtypes=dtypes
        )
        
        assert result.status == ProcessingStatus.PARTIAL_SUCCESS
        assert result.error_type == ErrorType.DATA_PROCESSING_ERROR
    
    def test_spec_cases_processing(self, sample_dataframes):
        """Test special cases processing"""
        dtypes = {'col1': 'string', 'col2': 'string'}
        
        result = merge_and_process_dfs(
            db_name='test_db',
            merged_dfs=sample_dataframes,
            spec_cases=['col1'],
            dtypes=dtypes
        )
        
        assert result.status == ProcessingStatus.SUCCESS
        # All values in col1 should be strings
        assert all(isinstance(v, str) for v in result.data['col1'].dropna())


class TestDataProcessingReport:
    """Test DataProcessingReport properties"""
    
    def test_is_success(self):
        report = DataProcessingReport(
            status=ProcessingStatus.SUCCESS,
            data=pd.DataFrame()
        )
        assert report.is_success is True
        assert report.is_error is False
        assert report.ok is True
    
    def test_is_error(self):
        report = DataProcessingReport(
            status=ProcessingStatus.ERROR,
            data=pd.DataFrame(),
            error_type=ErrorType.FILE_NOT_FOUND
        )
        assert report.is_error is True
        assert report.is_success is False
        assert report.ok is False
    
    def test_is_warning(self):
        report = DataProcessingReport(
            status=ProcessingStatus.WARNING,
            data=pd.DataFrame()
        )
        assert report.is_warning is True
        assert report.ok is True
    
    def test_partial_success_ok(self):
        report = DataProcessingReport(
            status=ProcessingStatus.PARTIAL_SUCCESS,
            data=pd.DataFrame()
        )
        assert report.ok is True
        assert report.is_success is False