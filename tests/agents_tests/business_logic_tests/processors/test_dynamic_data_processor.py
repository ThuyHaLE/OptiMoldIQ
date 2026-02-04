# tests/agents_tests/business_logic_tests/processors/test_dynamic_data_processor.py

import pytest
import pandas as pd
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from agents.dataPipelineOrchestrator.processors.dynamic_data_processor import DynamicDataProcessor
from agents.dataPipelineOrchestrator.configs.output_formats import (
    DataProcessingReport,
    ProcessingStatus,
    ErrorType
)

class TestDynamicDataProcessorProcessData:
    """Test cases for process_data method"""
    
    @pytest.fixture
    def temp_data_folder(self):
        """Create temporary folder with test data files"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            df1 = pd.DataFrame({
                'recordDate': [44927, 44928],
                'workingShift': ['1', '3'],
                'machineNo': ['M1', 'M2'],
                'machineCode': ['MC1', 'MC2'],
                'itemCode': ['I1', 'I2'],
                'itemName': ['Item1', 'Item2'],
                'colorChanged': ['Y', 'N'],
                'moldChanged': ['N', 'Y'],
                'machineChanged': ['N', 'N'],
                'poNote': ['Note1', 'Note2'],
                'moldNo': ['MLD1', 'MLD2'],
                'moldShot': [100, 200],
                'moldCavity': [4, 8],
                'itemTotalQuantity': [1000, 2000],
                'itemGoodQuantity': [950, 1900],
                'itemBlackSpot': [10, 20],
                'itemOilDeposit': [5, 10],
                'itemScratch': [5, 15],
                'itemCrack': [10, 20],
                'itemSinkMark': [5, 10],
                'itemShort': [5, 15],
                'itemBurst': [5, 5],
                'itemBend': [0, 5],
                'itemStain': [5, 10],
                'otherNG': [0, 0],
                'plasticResine': ['PR1', 'PR2'],
                'plasticResineCode': [101, 102],
                'plasticResineLot': ['L1', 'L2'],
                'colorMasterbatch': ['CM1', 'CM2'],
                'colorMasterbatchCode': [201, 202],
                'additiveMasterbatch': ['AM1', 'AM2'],
                'additiveMasterbatchCode': [301, 302]
            })
            
            df2 = pd.DataFrame({
                'recordDate': [44929, 44930],
                'workingShift': ['1', '3'],
                'machineNo': ['M3', 'M4'],
                'machineCode': ['MC3', 'MC4'],
                'itemCode': ['I3', 'I4'],
                'itemName': ['Item3', 'Item4'],
                'colorChanged': ['Y', 'N'],
                'moldChanged': ['N', 'Y'],
                'machineChanged': ['Y', 'N'],
                'poNote': ['Note3', 'Note4'],
                'moldNo': ['MLD3', 'MLD4'],
                'moldShot': [150, 250],
                'moldCavity': [6, 10],
                'itemTotalQuantity': [1500, 2500],
                'itemGoodQuantity': [1400, 2400],
                'itemBlackSpot': [15, 25],
                'itemOilDeposit': [10, 15],
                'itemScratch': [10, 20],
                'itemCrack': [15, 25],
                'itemSinkMark': [10, 15],
                'itemShort': [10, 20],
                'itemBurst': [10, 10],
                'itemBend': [5, 10],
                'itemStain': [10, 15],
                'otherNG': [5, 5],
                'plasticResine': ['PR3', 'PR4'],
                'plasticResineCode': [103, 104],
                'plasticResineLot': ['L3', 'L4'],
                'colorMasterbatch': ['CM3', 'CM4'],
                'colorMasterbatchCode': [203, 204],
                'additiveMasterbatch': ['AM3', 'AM4'],
                'additiveMasterbatchCode': [303, 304]
            })
            
            # Save as Excel files with date in filename
            file1_path = Path(tmpdir) / 'monthlyReports_202401_data.xlsb'
            file2_path = Path(tmpdir) / 'monthlyReports_202402_data.xlsb'
            
            # Use xlsx for testing since xlsb requires special engine
            file1_path = Path(tmpdir) / 'monthlyReports_202401_data.xlsx'
            file2_path = Path(tmpdir) / 'monthlyReports_202402_data.xlsx'
            
            with pd.ExcelWriter(file1_path, engine='openpyxl') as writer:
                df1.to_excel(writer, sheet_name='Sheet1', index=False)
            
            with pd.ExcelWriter(file2_path, engine='openpyxl') as writer:
                df2.to_excel(writer, sheet_name='Sheet1', index=False)
            
            yield tmpdir
    
    @pytest.fixture
    def temp_po_folder(self):
        """Create temporary folder with purchase order test files"""
        with tempfile.TemporaryDirectory() as tmpdir:
            df = pd.DataFrame({
                'poReceivedDate': ['2024-01-01', '2024-01-02'],
                'poNo': ['PO001', 'PO002'],
                'poETA': ['2024-02-01', '2024-02-02'],
                'itemCode': ['I1', 'I2'],
                'itemName': ['Item1', 'Item2'],
                'itemQuantity': [100, 200],
                'plasticResinCode': ['PR1', 'PR2'],
                'plasticResin': ['Resin1', 'Resin2'],
                'plasticResinQuantity': [50.0, 100.0],
                'colorMasterbatchCode': ['CM1', 'CM2'],
                'colorMasterbatch': ['Color1', 'Color2'],
                'colorMasterbatchQuantity': [10.0, 20.0],
                'additiveMasterbatchCode': ['AM1', 'AM2'],
                'additiveMasterbatch': ['Add1', 'Add2'],
                'additiveMasterbatchQuantity': [5.0, 10.0]
            })
            
            file_path = Path(tmpdir) / 'purchaseOrder_202401_data.xlsx'
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Sheet1', index=False)
            
            yield tmpdir
    
    def test_process_data_success_product_records(self, temp_data_folder):
        """Test successful processing of product records"""
        custom_schema = {
            'productRecords': {
                'path': str(temp_data_folder),
                'name_start': 'monthlyReports_',
                'file_extension': '.xlsx',
                'sheet_name': 'Sheet1',
                'required_fields': DynamicDataProcessor.DATA_TYPES['productRecords']['required_fields'],
                'dtypes': DynamicDataProcessor.DATA_TYPES['productRecords']['dtypes']
            }
        }
        
        processor = DynamicDataProcessor(
            data_name='productRecords',
            database_schema=custom_schema
        )
        
        result = processor.process_data()
        
        assert result.status == ProcessingStatus.SUCCESS
        assert isinstance(result.data, pd.DataFrame)
        assert len(result.data) == 4  # 2 files × 2 rows each
        assert result.metadata['data_name'] == 'productRecords'
        assert result.metadata['success_files_count'] == 2
        assert result.metadata['failed_files_count'] == 0
        assert result.metadata['records_processed'] == 4
        assert 'log' in result.metadata
    
    def test_process_data_success_purchase_orders(self, temp_po_folder):
        """Test successful processing of purchase orders"""
        custom_schema = {
            'purchaseOrders': {
                'path': str(temp_po_folder),
                'name_start': 'purchaseOrder_',
                'file_extension': '.xlsx',
                'sheet_name': 'Sheet1',
                'required_fields': DynamicDataProcessor.DATA_TYPES['purchaseOrders']['required_fields'],
                'dtypes': DynamicDataProcessor.DATA_TYPES['purchaseOrders']['dtypes']
            }
        }
        
        processor = DynamicDataProcessor(
            data_name='purchaseOrders',
            database_schema=custom_schema
        )
        
        result = processor.process_data()
        
        assert result.status == ProcessingStatus.SUCCESS
        assert isinstance(result.data, pd.DataFrame)
        assert len(result.data) == 2
        assert result.metadata['success_files_count'] == 1
    
    def test_process_data_missing_schema_fields_new_data_type(self):
        """
        Test case: Data type mới (not available in DATA_TYPES) 
        và database_schema thiếu required fields
        """
        # Setup: new data type, not default
        processor = DynamicDataProcessor(
            data_name='newDataType',  # Not avalable in DATA_TYPES
            database_schema={
                'newDataType': {
                    'path': '/some/path',
                    'name_start': 'new_',
                    # Missing: file_extension, sheet_name, required_fields, dtypes
                }
            }
        )
        
        result = processor.process_data()
        
        assert result.status == ProcessingStatus.ERROR
        assert result.error_type == ErrorType.FILE_NOT_FOUND

    def test_process_data_partial_override_with_defaults(self):
        """
        Test case: Override một vài fields của data type có sẵn
        Đây là use case hợp lệ - không nên báo lỗi
        """
        # Setup: override only path, get another fields from default
        processor = DynamicDataProcessor(
            data_name='productRecords',  # only in DATA_TYPES
            database_schema={
                'productRecords': {
                    'path': '/custom/path'  # only override path
                }
            }
        )
        
        # Verify merge worked correctly
        assert processor.folder_path == '/custom/path'  # Override
        assert processor.name_start == 'monthlyReports_'  # From default
        assert processor.file_extension == '.xlsb'  # From default
        
        # Process will fail because folder did not exist, but NOT because of schema
        result = processor.process_data()
        assert result.error_type != ErrorType.SCHEMA_MISMATCH


    def test_process_data_complete_override_valid(self, tmp_path):
        """
        Test case: Override all fields - valid
        """
        # Create temp directory
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        
        processor = DynamicDataProcessor(
            data_name='productRecords',
            database_schema={
                'productRecords': {
                    'path': str(data_dir),
                    'name_start': 'custom_',
                    'file_extension': '.csv',
                    'sheet_name': 'CustomSheet',
                    'required_fields': ['field1', 'field2'],
                    'dtypes': {'field1': 'string', 'field2': 'Int64'}
                }
            }
        )
        
        # Verify all fields were overridden
        assert processor.folder_path == str(data_dir)
        assert processor.name_start == 'custom_'
        assert processor.file_extension == '.csv'
        
        # Process will SKIP because there is not any file, but schema OK
        result = processor.process_data()
        assert result.error_type != ErrorType.SCHEMA_MISMATCH

    def test_process_data_no_database_schema_uses_defaults(self):
        """
        Test case: Not provide database_schema, use all default
        """
        processor = DynamicDataProcessor(
            data_name='productRecords',
            database_schema=None
        )
        
        # Verify defaults were loaded
        assert processor.folder_path == 'database/dynamicDatabase/monthlyReports_history'
        assert processor.name_start == 'monthlyReports_'
        assert processor.file_extension == '.xlsb'
        assert processor.sheet_name == 'Sheet1'
        
        # Schema is complete, not raise error SCHEMA_MISMATCH
        result = processor.process_data()
        assert result.error_type != ErrorType.SCHEMA_MISMATCH

    def test_process_data_empty_schema_for_existing_type(self):
        """
        Test case: Provide empty schema for avalable data type
        Then, use all default
        """
        processor = DynamicDataProcessor(
            data_name='productRecords',
            database_schema={
                'productRecords': {}  # Empty override
            }
        )
        
        # Should use all defaults
        assert processor.folder_path == 'database/dynamicDatabase/monthlyReports_history'
        assert processor.name_start == 'monthlyReports_'
        
        result = processor.process_data()
        assert result.error_type != ErrorType.SCHEMA_MISMATCH

    def test_process_data_schema_mismatch_attribute_is_none(self):
        """
        Test case: Schema has key but its value = None
        After setattr, attribute will be None → need validate
        """
        processor = DynamicDataProcessor(
            data_name='newDataType',
            database_schema={
                'newDataType': {
                    'path': '/some/path',
                    'name_start': 'prefix_',
                    'file_extension': None,  # Explicitly None
                    'sheet_name': None,
                    'required_fields': None,
                    'dtypes': None
                }
            }
        )
        
        result = processor.process_data()
        
        assert result.status == ProcessingStatus.ERROR
        assert result.error_type == ErrorType.FILE_NOT_FOUND
        assert "endswith() argument must be str" in result.error_message.lower() \
            or "must be str, not none" in result.error_message.lower()
    
    def test_process_data_no_matching_files(self, temp_data_folder):
        """Test processing when no files match the pattern - returns ERROR"""
        custom_schema = {
            'productRecords': {
                'path': str(temp_data_folder),
                'name_start': 'nonexistent_',
                'file_extension': '.xlsx',
                'sheet_name': 'Sheet1',
                'required_fields': ['field1'],
                'dtypes': {'field1': 'string'}
            }
        }
        
        processor = DynamicDataProcessor(
            data_name='productRecords',
            database_schema=custom_schema
        )
        
        result = processor.process_data()
        
        # Should return ERROR when no files found
        assert result.status == ProcessingStatus.ERROR
        assert result.error_type == ErrorType.FILE_NOT_FOUND
        assert 'no files found' in result.error_message.lower()

    def test_process_data_folder_vs_no_files_distinction(self):
        """Test that we distinguish between missing folder (ERROR) and no files yet (SKIP)"""
        
        processor1 = DynamicDataProcessor(
            data_name='productRecords',
            database_schema={
                'productRecords': {
                    'path': '/completely/wrong/path',
                    'name_start': 'test_',
                    'file_extension': '.xlsx',
                    'sheet_name': 'Sheet1',
                    'required_fields': ['field1'],
                    'dtypes': {'field1': 'string'}
                }
            }
        )
        
        result1 = processor1.process_data()
        assert result1.status == ProcessingStatus.ERROR
        assert result1.error_type == ErrorType.FILE_NOT_FOUND
        assert 'Source folder not found' in result1.error_message
        
        with tempfile.TemporaryDirectory() as tmpdir:
            processor2 = DynamicDataProcessor(
                data_name='productRecords',
                database_schema={
                    'productRecords': {
                        'path': str(tmpdir),
                        'name_start': 'future_data_',
                        'file_extension': '.xlsx',
                        'sheet_name': 'Sheet1',
                        'required_fields': ['field1'],
                        'dtypes': {'field1': 'string'}
                    }
                }
            )
            
            result2 = processor2.process_data()
            assert result2.status == ProcessingStatus.ERROR
            assert result2.error_type == ErrorType.FILE_NOT_FOUND
            assert 'no any source file existed' in result2.error_message.lower()

    def test_process_data_empty_folder_path(self):
        """Test processing with empty folder path"""
        custom_schema = {
            'productRecords': {
                'path': '',  # Empty path
                'name_start': 'test_',
                'file_extension': '.xlsx',
                'sheet_name': 'Sheet1',
                'required_fields': ['field1'],
                'dtypes': {'field1': 'string'}
            }
        }
        
        processor = DynamicDataProcessor(
            data_name='productRecords',
            database_schema=custom_schema
        )
        
        result = processor.process_data()
        
        assert result.status == ProcessingStatus.ERROR
        assert result.error_type == ErrorType.FILE_NOT_VALID
        assert 'Source folder path is empty' in result.error_message
    
    def test_process_data_nonexistent_folder(self):
        """Test processing with non-existent folder"""
        custom_schema = {
            'productRecords': {
                'path': '/nonexistent/folder/path',
                'name_start': 'test_',
                'file_extension': '.xlsx',
                'sheet_name': 'Sheet1',
                'required_fields': ['field1'],
                'dtypes': {'field1': 'string'}
            }
        }
        
        processor = DynamicDataProcessor(
            data_name='productRecords',
            database_schema=custom_schema
        )
        
        result = processor.process_data()
        
        assert result.status == ProcessingStatus.ERROR
        assert result.error_type == ErrorType.FILE_NOT_FOUND
        assert 'Source folder not found' in result.error_message
    
    def test_process_data_with_corrupted_files(self, temp_data_folder):
        """Test processing with corrupted/invalid files"""
        # Create a corrupted file
        corrupted_file = Path(temp_data_folder) / 'monthlyReports_202403_corrupted.xlsx'
        with open(corrupted_file, 'w') as f:
            f.write("This is not a valid Excel file")
        
        custom_schema = {
            'productRecords': {
                'path': str(temp_data_folder),
                'name_start': 'monthlyReports_',
                'file_extension': '.xlsx',
                'sheet_name': 'Sheet1',
                'required_fields': DynamicDataProcessor.DATA_TYPES['productRecords']['required_fields'],
                'dtypes': DynamicDataProcessor.DATA_TYPES['productRecords']['dtypes']
            }
        }
        
        processor = DynamicDataProcessor(
            data_name='productRecords',
            database_schema=custom_schema
        )
        
        result = processor.process_data()
        
        # Should have partial success (2 valid files, 1 corrupted)
        assert result.status == ProcessingStatus.PARTIAL_SUCCESS
        assert result.metadata['success_files_count'] == 2
        assert result.metadata['failed_files_count'] == 1
        assert result.error_type == ErrorType.FILE_READ_ERROR
    
    def test_process_data_missing_required_fields(self, temp_data_folder):
        """Test processing files missing required fields"""
        # Create file with missing fields
        df_incomplete = pd.DataFrame({
            'recordDate': [44927],
            'workingShift': ['1'],
            # Missing many required fields
        })
        
        file_path = Path(temp_data_folder) / 'monthlyReports_202403_incomplete.xlsx'
        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            df_incomplete.to_excel(writer, sheet_name='Sheet1', index=False)
        
        custom_schema = {
            'productRecords': {
                'path': str(temp_data_folder),
                'name_start': 'monthlyReports_',
                'file_extension': '.xlsx',
                'sheet_name': 'Sheet1',
                'required_fields': DynamicDataProcessor.DATA_TYPES['productRecords']['required_fields'],
                'dtypes': DynamicDataProcessor.DATA_TYPES['productRecords']['dtypes']
            }
        }
        
        processor = DynamicDataProcessor(
            data_name='productRecords',
            database_schema=custom_schema
        )
        
        result = processor.process_data()
        
        # Should have partial success
        assert result.status == ProcessingStatus.PARTIAL_SUCCESS
        assert result.metadata['failed_files_count'] >= 1
    
    def test_process_data_all_files_fail(self):
        """Test when all files fail to process"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create only corrupted files
            for i in range(3):
                file_path = Path(tmpdir) / f'monthlyReports_20240{i+1}_bad.xlsx'
                with open(file_path, 'w') as f:
                    f.write("Invalid Excel content")
            
            custom_schema = {
                'productRecords': {
                    'path': str(tmpdir),
                    'name_start': 'monthlyReports_',
                    'file_extension': '.xlsx',
                    'sheet_name': 'Sheet1',
                    'required_fields': ['field1'],
                    'dtypes': {'field1': 'string'}
                }
            }
            
            processor = DynamicDataProcessor(
                data_name='productRecords',
                database_schema=custom_schema
            )
            
            result = processor.process_data()
            
            assert result.status == ProcessingStatus.ERROR
            assert result.error_type == ErrorType.FILE_READ_ERROR
            assert 'No files could be processed successfully' in result.error_message
    
    def test_process_data_with_duplicates(self, temp_data_folder):
        """Test processing files with duplicate records"""
        # Create file with duplicate data
        df_dup = pd.DataFrame({
            'recordDate': [44927, 44927],  # Duplicate
            'workingShift': ['1', '1'],
            'machineNo': ['M1', 'M1'],
            'machineCode': ['MC1', 'MC1'],
            'itemCode': ['I1', 'I1'],
            'itemName': ['Item1', 'Item1'],
            'colorChanged': ['Y', 'Y'],
            'moldChanged': ['N', 'N'],
            'machineChanged': ['N', 'N'],
            'poNote': ['Note1', 'Note1'],
            'moldNo': ['MLD1', 'MLD1'],
            'moldShot': [100, 100],
            'moldCavity': [4, 4],
            'itemTotalQuantity': [1000, 1000],
            'itemGoodQuantity': [950, 950],
            'itemBlackSpot': [10, 10],
            'itemOilDeposit': [5, 5],
            'itemScratch': [5, 5],
            'itemCrack': [10, 10],
            'itemSinkMark': [5, 5],
            'itemShort': [5, 5],
            'itemBurst': [5, 5],
            'itemBend': [0, 0],
            'itemStain': [5, 5],
            'otherNG': [0, 0],
            'plasticResine': ['PR1', 'PR1'],
            'plasticResineCode': [101, 101],
            'plasticResineLot': ['L1', 'L1'],
            'colorMasterbatch': ['CM1', 'CM1'],
            'colorMasterbatchCode': [201, 201],
            'additiveMasterbatch': ['AM1', 'AM1'],
            'additiveMasterbatchCode': [301, 301]
        })
        
        file_path = Path(temp_data_folder) / 'monthlyReports_202403_dup.xlsx'
        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            df_dup.to_excel(writer, sheet_name='Sheet1', index=False)
        
        custom_schema = {
            'productRecords': {
                'path': str(temp_data_folder),
                'name_start': 'monthlyReports_',
                'file_extension': '.xlsx',
                'sheet_name': 'Sheet1',
                'required_fields': DynamicDataProcessor.DATA_TYPES['productRecords']['required_fields'],
                'dtypes': DynamicDataProcessor.DATA_TYPES['productRecords']['dtypes']
            }
        }
        
        processor = DynamicDataProcessor(
            data_name='productRecords',
            database_schema=custom_schema
        )
        
        result = processor.process_data()
        
        assert result.status == ProcessingStatus.SUCCESS
        # Duplicates should be removed
        assert 'duplicate' in result.metadata['log'].lower()
    
    @patch('agents.dataPipelineOrchestrator.processors.processor_utils.get_source_files')
    def test_process_data_unexpected_error(self, mock_get_files):
        """Test handling of unexpected errors during processing"""
        mock_get_files.side_effect = Exception("Unexpected error occurred")
        
        custom_schema = {
            'productRecords': {
                'path': '/some/path',
                'name_start': 'test_',
                'file_extension': '.xlsx',
                'sheet_name': 'Sheet1',
                'required_fields': ['field1'],
                'dtypes': {'field1': 'string'}
            }
        }
        
        processor = DynamicDataProcessor(
            data_name='productRecords',
            database_schema=custom_schema
        )
        
        result = processor.process_data()
        
        assert result.status == ProcessingStatus.ERROR
        assert result.error_type == ErrorType.DATA_PROCESSING_ERROR
        assert 'Unexpected error' in result.error_message
    
    def test_process_data_logs_generation(self, temp_data_folder):
        """Test that processing generates proper logs"""
        custom_schema = {
            'productRecords': {
                'path': str(temp_data_folder),
                'name_start': 'monthlyReports_',
                'file_extension': '.xlsx',
                'sheet_name': 'Sheet1',
                'required_fields': DynamicDataProcessor.DATA_TYPES['productRecords']['required_fields'],
                'dtypes': DynamicDataProcessor.DATA_TYPES['productRecords']['dtypes']
            }
        }
        
        processor = DynamicDataProcessor(
            data_name='productRecords',
            database_schema=custom_schema
        )
        
        result = processor.process_data()
        
        log = result.metadata.get('log', '')
        
        # Check log contains expected information
        assert 'Processing Summary' in log
        assert 'DynamicDataProcessor results:' in log
        assert 'Data is validated' in log
        assert 'Source folder verified' in log
        assert 'Found' in log and 'files to process' in log
        assert 'processing completed' in log
    
    def test_process_data_metadata_structure(self, temp_po_folder):
        """Test that metadata has correct structure"""
        custom_schema = {
            'purchaseOrders': {
                'path': str(temp_po_folder),
                'name_start': 'purchaseOrder_',
                'file_extension': '.xlsx',
                'sheet_name': 'Sheet1',
                'required_fields': DynamicDataProcessor.DATA_TYPES['purchaseOrders']['required_fields'],
                'dtypes': DynamicDataProcessor.DATA_TYPES['purchaseOrders']['dtypes']
            }
        }
        
        processor = DynamicDataProcessor(
            data_name='purchaseOrders',
            database_schema=custom_schema
        )
        
        result = processor.process_data()
        
        # Check metadata structure
        assert 'data_name' in result.metadata
        assert 'folder_path' in result.metadata
        assert 'success_files_count' in result.metadata
        assert 'failed_files_count' in result.metadata
        assert 'records_processed' in result.metadata
        assert 'log' in result.metadata
        
        assert isinstance(result.metadata['success_files_count'], int)
        assert isinstance(result.metadata['failed_files_count'], int)
        assert isinstance(result.metadata['records_processed'], int)


class TestDynamicDataProcessorFailMethod:
    """Test cases for _fail helper method"""
    
    def test_fail_returns_correct_structure(self):
        """Test that _fail method returns proper DataProcessingReport"""
        processor = DynamicDataProcessor(data_name='productRecords')
        
        result = processor._fail(
            status=ProcessingStatus.ERROR,
            error_type=ErrorType.FILE_NOT_FOUND,
            msg="Test error message",
            log_entries="Test log entry"
        )
        
        assert isinstance(result, DataProcessingReport)
        assert result.status == ProcessingStatus.ERROR
        assert result.error_type == ErrorType.FILE_NOT_FOUND
        assert result.error_message == "Test error message"
        assert result.data.empty
        assert result.metadata['log'] == "Test log entry"
        assert result.metadata['data_name'] == 'productRecords'
    
    def test_fail_with_folder_path(self):
        """Test _fail includes folder_path if available"""
        custom_schema = {
            'productRecords': {
                'path': '/test/path',
                'name_start': 'test_',
                'file_extension': '.xlsx',
                'sheet_name': 'Sheet1',
                'required_fields': ['field1'],
                'dtypes': {'field1': 'string'}
            }
        }
        
        processor = DynamicDataProcessor(
            data_name='productRecords',
            database_schema=custom_schema
        )
        
        result = processor._fail(
            status=ProcessingStatus.ERROR,
            error_type=ErrorType.FILE_READ_ERROR,
            msg="Test error",
            log_entries="Log"
        )
        
        assert result.metadata['folder_path'] == '/test/path'


class TestDynamicDataProcessorConstants:
    """Test class constants and configuration"""
    
    def test_data_types_structure(self):
        """Test DATA_TYPES constant structure"""
        assert 'productRecords' in DynamicDataProcessor.DATA_TYPES
        assert 'purchaseOrders' in DynamicDataProcessor.DATA_TYPES
        
        # Check productRecords structure
        pr = DynamicDataProcessor.DATA_TYPES['productRecords']
        assert 'path' in pr
        assert 'name_start' in pr
        assert 'file_extension' in pr
        assert 'sheet_name' in pr
        assert 'required_fields' in pr
        assert 'dtypes' in pr
        
        # Check purchaseOrders structure
        po = DynamicDataProcessor.DATA_TYPES['purchaseOrders']
        assert 'path' in po
        assert 'name_start' in po
        assert 'file_extension' in po
        assert 'sheet_name' in po
        assert 'required_fields' in po
        assert 'dtypes' in po
    
    def test_spec_cases_list(self):
        """Test SPEC_CASES constant"""
        assert DynamicDataProcessor.SPEC_CASES == [
            'plasticResinCode',
            'colorMasterbatchCode',
            'additiveMasterbatchCode'
        ]
    
    def test_attr_map_completeness(self):
        """Test ATTR_MAP covers all schema keys"""
        expected_keys = {
            'path', 'name_start', 'file_extension',
            'sheet_name', 'required_fields', 'dtypes'
        }
        
        assert set(DynamicDataProcessor.ATTR_MAP.keys()) == expected_keys
    
    def test_product_records_required_fields(self):
        """Test productRecords has all required fields"""
        required = DynamicDataProcessor.DATA_TYPES['productRecords']['required_fields']
        
        essential_fields = [
            'recordDate', 'workingShift', 'machineNo', 'itemCode',
            'plasticResineCode', 'colorMasterbatchCode', 'additiveMasterbatchCode'
        ]
        
        for field in essential_fields:
            assert field in required
    
    def test_purchase_orders_required_fields(self):
        """Test purchaseOrders has all required fields"""
        required = DynamicDataProcessor.DATA_TYPES['purchaseOrders']['required_fields']
        
        essential_fields = [
            'poReceivedDate', 'poNo', 'poETA', 'itemCode',
            'plasticResinCode', 'colorMasterbatchCode', 'additiveMasterbatchCode'
        ]
        
        for field in essential_fields:
            assert field in required


class TestDynamicDataProcessorIntegration:
    """Integration tests for complete workflows"""
    
    def test_end_to_end_product_records_workflow(self):
        """Test complete workflow from initialization to data processing"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create realistic product records data
            df = pd.DataFrame({
                'recordDate': [44927, 44928, 44929],
                'workingShift': ['1', '3', '1'],
                'machineNo': ['M001', 'M002', 'M003'],
                'machineCode': ['MC01', 'MC02', 'MC03'],
                'itemCode': ['ITEM001', 'ITEM002', 'ITEM003'],
                'itemName': ['Product A', 'Product B', 'Product C'],
                'colorChanged': ['N', 'Y', 'N'],
                'moldChanged': ['Y', 'N', 'N'],
                'machineChanged': ['N', 'N', 'Y'],
                'poNote': ['PO123', 'PO124', 'PO125'],
                'moldNo': ['MOLD01', 'MOLD02', 'MOLD03'],
                'moldShot': [1000, 1500, 2000],
                'moldCavity': [4, 6, 8],
                'itemTotalQuantity': [4000, 9000, 16000],
                'itemGoodQuantity': [3900, 8850, 15800],
                'itemBlackSpot': [20, 30, 40],
                'itemOilDeposit': [10, 15, 20],
                'itemScratch': [15, 20, 25],
                'itemCrack': [15, 20, 30],
                'itemSinkMark': [10, 15, 20],
                'itemShort': [10, 20, 30],
                'itemBurst': [5, 10, 15],
                'itemBend': [5, 10, 10],
                'itemStain': [10, 15, 20],
                'otherNG': [0, 5, 10],
                'plasticResine': ['PP', 'PE', 'ABS'],
                'plasticResineCode': [1001, 1002, 1003],
                'plasticResineLot': ['LOT001', 'LOT002', 'LOT003'],
                'colorMasterbatch': ['Blue', 'Red', 'Green'],
                'colorMasterbatchCode': [2001, 2002, 2003],
                'additiveMasterbatch': ['UV', 'Anti-static', 'Flame retardant'],
                'additiveMasterbatchCode': [3001, 3002, 3003]
            })
            
            file_path = Path(tmpdir) / 'monthlyReports_202401_final.xlsx'
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Sheet1', index=False)
            
            # Process data
            custom_schema = {
                'productRecords': {
                    'path': str(tmpdir),
                    'name_start': 'monthlyReports_',
                    'file_extension': '.xlsx',
                    'sheet_name': 'Sheet1',
                    'required_fields': DynamicDataProcessor.DATA_TYPES['productRecords']['required_fields'],
                    'dtypes': DynamicDataProcessor.DATA_TYPES['productRecords']['dtypes']
                }
            }
            
            processor = DynamicDataProcessor(
                data_name='productRecords',
                database_schema=custom_schema
            )
            
            result = processor.process_data()
            
            # Comprehensive assertions
            assert result.status == ProcessingStatus.SUCCESS
            assert len(result.data) == 3
            assert result.metadata['records_processed'] == 3
            assert result.error_type == ErrorType.NONE
            assert result.error_message == ''
            
            # Check data transformations
            assert 'plasticResin' in result.data.columns  # Renamed from plasticResine
            assert result.data['workingShift'].str.isupper().all()  # Uppercase