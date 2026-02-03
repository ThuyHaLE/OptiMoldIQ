# tests/agents_tests/business_logic_tests/healers/conftest.py

"""Shared fixtures for healer tests"""

import pytest
from agents.dataPipelineOrchestrator.configs.output_formats import (
    DataProcessingReport,
)
from agents.dataPipelineOrchestrator.configs.healing_configs import (
    ProcessingStatus,
    ProcessingScale,
    RecoveryAction,
    RecoveryDecision,
    Priority,
    ErrorType,
)


@pytest.fixture
def base_collector_result():
    """Base collector result for testing data collector healers"""
    return DataProcessingReport(
        status=ProcessingStatus.ERROR,
        data=None,
        error_type=ErrorType.DATA_COLLECTION_ERROR,
        error_message="Data collection failed",
        metadata={}
    )


@pytest.fixture
def base_validation_result():
    """Base validation result for testing schema error healers"""
    return DataProcessingReport(
        status=ProcessingStatus.ERROR,
        data=None,
        error_type=ErrorType.SCHEMA_MISMATCH,
        error_message="Schema validation failed",
        metadata={}
    )


@pytest.fixture
def recovery_actions():
    """Recovery actions for testing healers"""
    return [
        RecoveryDecision(
            priority=Priority.CRITICAL,
            scale=ProcessingScale.LOCAL,
            action=RecoveryAction.ROLLBACK_TO_BACKUP,
            status=ProcessingStatus.PENDING
        )
    ]