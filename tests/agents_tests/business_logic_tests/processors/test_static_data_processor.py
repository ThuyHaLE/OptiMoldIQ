# tests/agents_tests/business_logic_tests/processors/test_static_data_processor.py

import pytest
import pandas as pd
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from agents.dataPipelineOrchestrator.processors.static_data_processor import StaticDataProcessor
from agents.dataPipelineOrchestrator.configs.output_formats import (
    DataProcessingReport,
    ProcessingStatus,
    ErrorType
)

class TestStaticDataProcessorProcessData:
    """Test cases for process_data method"""
    
    @pytest.fixture
    def temp_item_info_file(self):
        """Create temporary itemInfo Excel file"""
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            df = pd.DataFrame({
                'itemCode': ['ITEM001', 'ITEM002', 'ITEM003'],
                'itemName': ['Product A', 'Product B', 'Product C']
            })
            df.to_excel(tmp.name, index=False)
            yield tmp.name
        os.unlink(tmp.name)
    
    @pytest.fixture
    def temp_machine_info_file(self):
        """Create temporary machineInfo Excel file"""
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            df = pd.DataFrame({
                'machineNo': ['M001', 'M002', 'M003'],
                'machineCode': ['MC01', 'MC02', 'MC03'],
                'machineName': ['Machine 1', 'Machine 2', 'Machine 3'],
                'manufacturerName': ['Maker A', 'Maker B', 'Maker C'],
                'machineTonnage': [100, 150, 200],
                'changedTime': [1, 2, 3],
                'layoutStartDate': ['2024-01-01', '2024-01-15', '2024-02-01'],
                'layoutEndDate': ['2024-12-31', '2024-12-31', '2024-12-31'],
                'previousMachineCode': ['MC00', 'MC01', 'MC02']
            })
            df.to_excel(tmp.name, index=False)
            yield tmp.name
        os.unlink(tmp.name)
    
    @pytest.fixture
    def temp_item_composition_file(self):
        """Create temporary itemCompositionSummary Excel file"""
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            df = pd.DataFrame({
                'itemCode': ['ITEM001', 'ITEM002'],
                'itemName': ['Product A', 'Product B'],
                'plasticResinCode': [101, 102],
                'plasticResin': ['PP', 'PE'],
                'plasticResinQuantity': [50.5, 75.3],
                'colorMasterbatchCode': [201, 202],
                'colorMasterbatch': ['Blue', 'Red'],
                'colorMasterbatchQuantity': [5.0, 7.5],
                'additiveMasterbatchCode': [301, 302],
                'additiveMasterbatch': ['UV', 'Anti-static'],
                'additiveMasterbatchQuantity': [2.5, 3.0]
            })
            df.to_excel(tmp.name, index=False)
            yield tmp.name
        os.unlink(tmp.name)
    
    def test_process_data_success_item_info(self, temp_item_info_file):
        """Test successful processing of itemInfo"""
        custom_schema = {
            'itemInfo': {
                'path': temp_item_info_file,
                'dtypes': StaticDataProcessor.DATA_TYPES['itemInfo']['dtypes']
            }
        }
        
        processor = StaticDataProcessor(
            data_name='itemInfo',
            database_schema=custom_schema
        )
        
        result = processor.process_data()
        
        assert result.status == ProcessingStatus.SUCCESS
        assert isinstance(result.data, pd.DataFrame)
        assert len(result.data) == 3
        assert result.error_type == ErrorType.NONE
        assert result.error_message == ""
        assert result.metadata['data_name'] == 'itemInfo'
        assert result.metadata['records_processed'] == 3
        assert 'log' in result.metadata
    
    def test_process_data_success_machine_info(self, temp_machine_info_file):
        """Test successful processing of machineInfo"""
        custom_schema = {
            'machineInfo': {
                'path': temp_machine_info_file,
                'dtypes': StaticDataProcessor.DATA_TYPES['machineInfo']['dtypes']
            }
        }
        
        processor = StaticDataProcessor(
            data_name='machineInfo',
            database_schema=custom_schema
        )
        
        result = processor.process_data()
        
        assert result.status == ProcessingStatus.SUCCESS
        assert len(result.data) == 3
        assert result.metadata['records_processed'] == 3
    
    def test_process_data_success_item_composition(self, temp_item_composition_file):
        """Test successful processing of itemCompositionSummary with special cases"""
        custom_schema = {
            'itemCompositionSummary': {
                'path': temp_item_composition_file,
                'dtypes': StaticDataProcessor.DATA_TYPES['itemCompositionSummary']['dtypes']
            }
        }
        
        processor = StaticDataProcessor(
            data_name='itemCompositionSummary',
            database_schema=custom_schema
        )
        
        result = processor.process_data()
        
        assert result.status == ProcessingStatus.SUCCESS
        assert len(result.data) == 2
        # Check that special case columns are handled
        assert 'plasticResinCode' in result.data.columns
        assert 'colorMasterbatchCode' in result.data.columns
        assert 'additiveMasterbatchCode' in result.data.columns
    
    def test_process_data_missing_schema_fields_new_data_type(self):
        custom_schema = {
            'test': {
                'path': '/path/to/file.csv',
                # Missing 'dtypes' field
            }
        }
        
        processor = StaticDataProcessor(
            data_name='test',
            database_schema=custom_schema
        )
        
        result = processor.process_data()
        
        assert result.status == ProcessingStatus.ERROR
        assert result.error_type == ErrorType.SCHEMA_MISMATCH
    
    def test_process_data_unsupported_file_extension(self):
        """Test processing with unsupported file extension"""
        custom_schema = {
            'itemInfo': {
                'path': '/path/to/file.csv',  # Unsupported extension
                'dtypes': {'itemCode': 'string'}
            }
        }
        
        processor = StaticDataProcessor(
            data_name='itemInfo',
            database_schema=custom_schema
        )
        
        result = processor.process_data()
        
        assert result.status == ProcessingStatus.ERROR
        assert result.error_type == ErrorType.UNSUPPORTED_DATA_TYPE
    
    def test_process_data_unsupported_extension_case_insensitive(self):
        """Test that file extension check is case-insensitive"""
        custom_schema = {
            'itemInfo': {
                'path': '/path/to/file.XLSX',  # Uppercase extension
                'dtypes': {'itemCode': 'string'}
            }
        }
        
        processor = StaticDataProcessor(
            data_name='itemInfo',
            database_schema=custom_schema
        )
        
        result = processor.process_data()
        
        assert result.status == ProcessingStatus.SUCCESS
        assert result.error_type == ErrorType.NONE
    
    def test_process_data_nonexistent_file(self):
        """Test processing with non-existent file"""
        custom_schema = {
            'itemInfo': {
                'path': '/nonexistent/path/file.xlsx',
                'dtypes': {'itemCode': 'string'}
            }
        }
        
        processor = StaticDataProcessor(
            data_name='itemInfo',
            database_schema=custom_schema
        )
        
        result = processor.process_data()
        
        assert result.status == ProcessingStatus.ERROR
        assert result.error_type == ErrorType.FILE_NOT_FOUND
    
    def test_process_data_corrupted_file(self):
        """Test processing corrupted Excel file"""
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            # Write invalid content
            tmp.write(b"This is not a valid Excel file")
            tmp_path = tmp.name
        
        try:
            custom_schema = {
                'itemInfo': {
                    'path': tmp_path,
                    'dtypes': StaticDataProcessor.DATA_TYPES['itemInfo']['dtypes']
                }
            }
            
            processor = StaticDataProcessor(
                data_name='itemInfo',
                database_schema=custom_schema
            )
            
            result = processor.process_data()
            
            assert result.status == ProcessingStatus.ERROR
            assert result.error_type == ErrorType.FILE_READ_ERROR
            assert 'Failed to read file' in result.error_message
        finally:
            os.unlink(tmp_path)
    
    def test_process_data_empty_file(self):
        """Test processing empty Excel file"""
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            df = pd.DataFrame()
            df.to_excel(tmp.name, index=False)
            tmp_path = tmp.name
        
        try:
            custom_schema = {
                'itemInfo': {
                    'path': tmp_path,
                    'dtypes': StaticDataProcessor.DATA_TYPES['itemInfo']['dtypes']
                }
            }
            
            processor = StaticDataProcessor(
                data_name='itemInfo',
                database_schema=custom_schema
            )
            
            result = processor.process_data()
            
            # Should succeed but with empty dataframe
            assert result.status == ProcessingStatus.SUCCESS
            assert result.data.empty
            assert result.metadata['records_processed'] == 0
        finally:
            os.unlink(tmp_path)
    
    def test_process_data_with_null_values(self):
        """Test processing file with various null values"""
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            df = pd.DataFrame({
                'itemCode': ['ITEM001', 'nan', 'ITEM003', None],
                'itemName': ['Product A', 'null', '', 'Product D']
            })
            df.to_excel(tmp.name, index=False)
            tmp_path = tmp.name
        
        try:
            custom_schema = {
                'itemInfo': {
                    'path': tmp_path,
                    'dtypes': StaticDataProcessor.DATA_TYPES['itemInfo']['dtypes']
                }
            }
            
            processor = StaticDataProcessor(
                data_name='itemInfo',
                database_schema=custom_schema
            )
            
            result = processor.process_data()
            
            assert result.status == ProcessingStatus.SUCCESS
            assert len(result.data) == 4
            # Null-like strings should be converted to pd.NA
            assert pd.isna(result.data.loc[1, 'itemCode'])  # 'nan' → NA
        finally:
            os.unlink(tmp_path)
    
    def test_process_data_with_special_case_columns(self, temp_item_composition_file):
        """Test that SPEC_CASES columns are properly handled"""
        custom_schema = {
            'itemCompositionSummary': {
                'path': temp_item_composition_file,
                'dtypes': StaticDataProcessor.DATA_TYPES['itemCompositionSummary']['dtypes']
            }
        }
        
        processor = StaticDataProcessor(
            data_name='itemCompositionSummary',
            database_schema=custom_schema
        )
        
        result = processor.process_data()
        
        assert result.status == ProcessingStatus.SUCCESS
        # Special case columns should be string type
        assert result.data['plasticResinCode'].dtype == 'string'
        assert result.data['colorMasterbatchCode'].dtype == 'string'
        assert result.data['additiveMasterbatchCode'].dtype == 'string'

class TestStaticDataProcessorFailMethod:
    """Test cases for _fail helper method"""
    
    def test_fail_returns_correct_structure(self):
        """Test that _fail method returns proper DataProcessingReport"""
        processor = StaticDataProcessor(data_name='itemInfo')
        
        result = processor._fail(
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
        assert result.metadata['data_name'] == 'itemInfo'
    
    def test_fail_with_file_path(self):
        """Test _fail includes file_path if available"""
        custom_schema = {
            'itemInfo': {
                'path': '/test/path.xlsx',
                'dtypes': {'itemCode': 'string'}
            }
        }
        
        processor = StaticDataProcessor(
            data_name='itemInfo',
            database_schema=custom_schema
        )
        
        result = processor._fail(
            error_type=ErrorType.FILE_READ_ERROR,
            msg="Test error",
            log_entries="Log"
        )
        
        assert result.metadata['file_path'] == '/test/path.xlsx'
    
    def test_fail_without_file_path(self):
        """Test _fail when path attribute doesn't exist"""
        processor = StaticDataProcessor(data_name='unknownType')
        
        # Remove path attribute if it exists
        if hasattr(processor, 'path'):
            delattr(processor, 'path')
        
        result = processor._fail(
            error_type=ErrorType.SCHEMA_MISMATCH,
            msg="Test error",
            log_entries="Log"
        )
        
        assert result.metadata['file_path'] is None

class TestStaticDataProcessorConstants:
    """Test class constants and configuration"""
    
    def test_data_types_structure(self):
        """Test DATA_TYPES constant structure"""
        expected_types = [
            'itemCompositionSummary',
            'itemInfo',
            'machineInfo',
            'moldInfo',
            'moldSpecificationSummary',
            'resinInfo'
        ]
        
        for data_type in expected_types:
            assert data_type in StaticDataProcessor.DATA_TYPES
            assert 'path' in StaticDataProcessor.DATA_TYPES[data_type]
            assert 'dtypes' in StaticDataProcessor.DATA_TYPES[data_type]
    
    def test_spec_cases_list(self):
        """Test SPEC_CASES constant"""
        assert StaticDataProcessor.SPEC_CASES == [
            'plasticResinCode',
            'colorMasterbatchCode',
            'additiveMasterbatchCode'
        ]
    
    def test_attr_map_completeness(self):
        """Test ATTR_MAP covers all schema keys"""
        expected_keys = {'path', 'dtypes'}
        
        assert set(StaticDataProcessor.ATTR_MAP.keys()) == expected_keys
    
    def test_all_paths_end_with_xlsx(self):
        """Test that all default paths use .xlsx extension"""
        for data_type, config in StaticDataProcessor.DATA_TYPES.items():
            path = config['path']
            assert path.endswith('.xlsx'), f"{data_type} path doesn't end with .xlsx"
    
    def test_item_composition_dtypes(self):
        """Test itemCompositionSummary has correct dtypes"""
        dtypes = StaticDataProcessor.DATA_TYPES['itemCompositionSummary']['dtypes']
        
        assert dtypes['itemCode'] == 'string'
        assert dtypes['plasticResinQuantity'] == 'Float64'
        assert dtypes['colorMasterbatchQuantity'] == 'Float64'
        assert dtypes['additiveMasterbatchQuantity'] == 'Float64'
    
    def test_machine_info_dtypes(self):
        """Test machineInfo has correct dtypes"""
        dtypes = StaticDataProcessor.DATA_TYPES['machineInfo']['dtypes']
        
        assert dtypes['machineTonnage'] == 'Int64'
        assert dtypes['changedTime'] == 'Int64'
        assert dtypes['layoutStartDate'] == 'datetime64[ns]'
        assert dtypes['layoutEndDate'] == 'datetime64[ns]'


class TestStaticDataProcessorIntegration:
    """Integration tests for complete workflows"""
    
    def test_end_to_end_item_info_workflow(self):
        """Test complete workflow for itemInfo processing"""
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            df = pd.DataFrame({
                'itemCode': ['ITEM001', 'ITEM002', 'ITEM003', 'ITEM004'],
                'itemName': ['Product A', 'Product B', 'Product C', 'Product D']
            })
            df.to_excel(tmp.name, index=False)
            tmp_path = tmp.name
        
        try:
            custom_schema = {
                'itemInfo': {
                    'path': tmp_path,
                    'dtypes': StaticDataProcessor.DATA_TYPES['itemInfo']['dtypes']
                }
            }
            
            processor = StaticDataProcessor(
                data_name='itemInfo',
                database_schema=custom_schema
            )
            
            result = processor.process_data()
            
            # Comprehensive assertions
            assert result.status == ProcessingStatus.SUCCESS
            assert len(result.data) == 4
            assert result.metadata['records_processed'] == 4
            assert result.error_type == ErrorType.NONE
            assert result.error_message == ""
            
            # Check data types
            assert result.data['itemCode'].dtype == 'string'
            assert result.data['itemName'].dtype == 'string'
            
            # Check data content
            assert 'ITEM001' in result.data['itemCode'].values
            assert 'Product A' in result.data['itemName'].values
        finally:
            os.unlink(tmp_path)
    
    def test_end_to_end_machine_info_workflow(self):
        """Test complete workflow for machineInfo processing"""
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            df = pd.DataFrame({
                'machineNo': ['M001', 'M002'],
                'machineCode': ['MC01', 'MC02'],
                'machineName': ['Machine 1', 'Machine 2'],
                'manufacturerName': ['Maker A', 'Maker B'],
                'machineTonnage': [100, 150],
                'changedTime': [1, 2],
                'layoutStartDate': ['2024-01-01', '2024-01-15'],
                'layoutEndDate': ['2024-12-31', '2024-12-31'],
                'previousMachineCode': ['MC00', 'MC01']
            })
            df.to_excel(tmp.name, index=False)
            tmp_path = tmp.name
        
        try:
            custom_schema = {
                'machineInfo': {
                    'path': tmp_path,
                    'dtypes': StaticDataProcessor.DATA_TYPES['machineInfo']['dtypes']
                }
            }
            
            processor = StaticDataProcessor(
                data_name='machineInfo',
                database_schema=custom_schema
            )
            
            result = processor.process_data()
            
            assert result.status == ProcessingStatus.SUCCESS
            assert len(result.data) == 2
            
            # Check integer columns
            assert result.data['machineTonnage'].dtype == 'Int64'
            assert result.data['changedTime'].dtype == 'Int64'
            
            # Check datetime columns
            assert pd.api.types.is_datetime64_any_dtype(result.data['layoutStartDate'])
            assert pd.api.types.is_datetime64_any_dtype(result.data['layoutEndDate'])
        finally:
            os.unlink(tmp_path)
    
    def test_error_recovery_workflow(self):
        """Test that errors are properly reported and don't crash"""
        # Test with non-existent file
        processor = StaticDataProcessor(data_name='itemInfo')
        result = processor.process_data()
        
        assert result.status == ProcessingStatus.ERROR
        assert result.data.empty
        assert 'log' in result.metadata
        
        # Log should contain error information
        assert '❌' in result.metadata['log']


class TestStaticDataProcessorEdgeCases:
    """Test edge cases and boundary conditions"""
    
    def test_process_single_row_file(self):
        """Test processing file with single row"""
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            df = pd.DataFrame({
                'itemCode': ['ITEM001'],
                'itemName': ['Product A']
            })
            df.to_excel(tmp.name, index=False)
            tmp_path = tmp.name
        
        try:
            custom_schema = {
                'itemInfo': {
                    'path': tmp_path,
                    'dtypes': StaticDataProcessor.DATA_TYPES['itemInfo']['dtypes']
                }
            }
            
            processor = StaticDataProcessor(
                data_name='itemInfo',
                database_schema=custom_schema
            )
            
            result = processor.process_data()
            
            assert result.status == ProcessingStatus.SUCCESS
            assert len(result.data) == 1
        finally:
            os.unlink(tmp_path)
    
    def test_process_large_file(self):
        """Test processing file with many rows"""
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            df = pd.DataFrame({
                'itemCode': [f'ITEM{i:05d}' for i in range(1000)],
                'itemName': [f'Product {i}' for i in range(1000)]
            })
            df.to_excel(tmp.name, index=False)
            tmp_path = tmp.name
        
        try:
            custom_schema = {
                'itemInfo': {
                    'path': tmp_path,
                    'dtypes': StaticDataProcessor.DATA_TYPES['itemInfo']['dtypes']
                }
            }
            
            processor = StaticDataProcessor(
                data_name='itemInfo',
                database_schema=custom_schema
            )
            
            result = processor.process_data()
            
            assert result.status == ProcessingStatus.SUCCESS
            assert len(result.data) == 1000
            assert result.metadata['records_processed'] == 1000
        finally:
            os.unlink(tmp_path)
    
    def test_unicode_characters_in_data(self):
        """Test processing file with unicode characters"""
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            df = pd.DataFrame({
                'itemCode': ['ITEM001', 'ITEM002', 'ITEM003'],
                'itemName': ['製品A', 'Продукт B', 'Producto C']  # Japanese, Russian, Spanish
            })
            df.to_excel(tmp.name, index=False)
            tmp_path = tmp.name
        
        try:
            custom_schema = {
                'itemInfo': {
                    'path': tmp_path,
                    'dtypes': StaticDataProcessor.DATA_TYPES['itemInfo']['dtypes']
                }
            }
            
            processor = StaticDataProcessor(
                data_name='itemInfo',
                database_schema=custom_schema
            )
            
            result = processor.process_data()
            
            assert result.status == ProcessingStatus.SUCCESS
            assert '製品A' in result.data['itemName'].values
        finally:
            os.unlink(tmp_path)