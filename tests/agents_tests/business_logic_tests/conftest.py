# tests/agents_tests/business_logic_tests/conftest.py

"""Shared fixtures for business logic tests"""
import pytest
import pandas as pd
from pathlib import Path
from datetime import datetime

# ============================================
# DATA FIXTURES
# ============================================

@pytest.fixture
def sample_machine_data():
    """Sample machine data for testing tools"""
    return pd.DataFrame({
        'machineCode': ['M001', 'M002', 'M003'],
        'machineTonnage': ['100', '200', '300'],
        'recordDate': pd.to_datetime(['2024-01-01'] * 3)
    })

@pytest.fixture
def sample_mold_data():
    """Sample mold data for testing tools"""
    return pd.DataFrame({
        'moldNo': ['MOLD_A', 'MOLD_B', 'MOLD_C'],
        'machineTonnage': ['100', '200', '100/200']
    })

@pytest.fixture
def sample_production_data():
    """Sample production data"""
    return pd.DataFrame({
        'poNo': ['PO001', 'PO002'],
        'itemCode': ['ITEM_A', 'ITEM_B'],
        'itemName': ['Product A', 'Product B'],
        'moldNo': ['MOLD_A', 'MOLD_B'],
        'machineCode': ['M001', 'M002'],
        'quantity': [100, 200]
    })

# ============================================
# FILE FIXTURES
# ============================================

@pytest.fixture
def temp_log_file(tmp_path):
    """Temporary log file for testing notifiers"""
    return tmp_path / "test.log"

@pytest.fixture
def temp_output_dir(tmp_path):
    """Temporary output directory"""
    output_dir = tmp_path / "outputs"
    output_dir.mkdir()
    return output_dir

# ============================================
# VALIDATION FIXTURES
# ============================================

@pytest.fixture
def sample_validation_error():
    """Sample validation error for testing healers"""
    from agents.dataPipelineOrchestrator.configs.output_formats import (
        ProcessingStatus,
        DataProcessingReport,
        ErrorType,
    )
    
    return DataProcessingReport(
        status=ProcessingStatus.ERROR,
        data=None,
        error_type=ErrorType.SCHEMA_MISMATCH,
        error_message="Schema validation failed",
        metadata={"expected": ["id", "name"], "missing": ["name"]}
    )