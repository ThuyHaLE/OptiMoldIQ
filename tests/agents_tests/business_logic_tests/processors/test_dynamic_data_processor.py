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
    
    def test_schema_level_key_missing(self):
        """
        # Test schema-level key missing only (not value validation)
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
        assert result.error_type == ErrorType.SCHEMA_MISMATCH

    def test_process_data_partial_override_with_defaults(self):
        """
        Test case: Override some fields of default data type
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
        
        # Process will fail because folder did not exist, but NOT because of schema
        result = processor.process_data()
        assert result.error_type == ErrorType.FILE_NOT_FOUND
    
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

class TestDynamicDataProcessorConstants:
    """Test class constants and configuration"""
    
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