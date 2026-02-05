# tests/agents_tests/business_logic_tests/collectors/test_data_collector.py

import pytest
import pandas as pd
from unittest.mock import MagicMock, patch

from agents.dataPipelineOrchestrator.collectors.data_collector import DataCollector
from agents.dataPipelineOrchestrator.configs.output_formats import (
    DataProcessingReport,
    ProcessingStatus,
    ErrorType,
)

def make_processor_report(
    status=ProcessingStatus.SUCCESS,
    data=None,
    error_message="",
    metadata=None
):
    return DataProcessingReport(
        status=status,
        data=data,
        error_type=ErrorType.DATA_PROCESSING_ERROR if status != ProcessingStatus.SUCCESS else ErrorType.NONE,
        error_message=error_message,
        metadata=metadata or {}
    )

# TEST 1 — Unsupported database_type
def test_unsupported_database_type():
    collector = DataCollector(
        database_type="weirdDB",
        database_schema={"db1": {}}
    )

    result = collector.process_data()

    assert result.status == ProcessingStatus.ERROR
    assert result.error_type == ErrorType.UNSUPPORTED_DATA_TYPE
    assert "Unsupported database_type" in result.error_message

# TEST 2 — dynamicDB, all DBs SUCCESS
@patch("agents.dataPipelineOrchestrator.collectors.data_collector.DynamicDataProcessor")
def test_dynamic_db_all_success(mock_processor_cls):
    schema = {"db1": {}, "db2": {}}

    df = pd.DataFrame({"a": [1, 2]})

    processor_instance = mock_processor_cls.return_value
    processor_instance.process_data.return_value = make_processor_report(
        status=ProcessingStatus.SUCCESS,
        data=df,
        metadata={"log": "ok"}
    )

    collector = DataCollector("dynamicDB", schema)
    result = collector.process_data()

    assert result.status == ProcessingStatus.SUCCESS
    assert result.error_type == ErrorType.NONE
    assert set(result.data.keys()) == {"db1", "db2"}
    assert all(isinstance(v, pd.DataFrame) for v in result.data.values())

# TEST 3 — PARTIAL_SUCCESS (1 db fail)
@patch("agents.dataPipelineOrchestrator.collectors.data_collector.DynamicDataProcessor")
def test_partial_success(mock_processor_cls):
    schema = {"db1": {}, "db2": {}}

    def processor_side_effect(db_name, *_):
        proc = MagicMock()
        if db_name == "db1":
            proc.process_data.return_value = make_processor_report(
                status=ProcessingStatus.SUCCESS,
                data=pd.DataFrame({"x": [1]}),
                metadata={"log": "ok"}
            )
        else:
            proc.process_data.return_value = make_processor_report(
                status=ProcessingStatus.ERROR,
                data=None,
                error_message="boom",
                metadata={"data_name": db_name, "log": "fail"}
            )
        return proc

    mock_processor_cls.side_effect = processor_side_effect

    collector = DataCollector("dynamicDB", schema)
    result = collector.process_data()

    assert result.status == ProcessingStatus.PARTIAL_SUCCESS
    assert result.error_type == ErrorType.DATA_PROCESSING_ERROR
    assert "Partial success" in result.error_message
    assert "db2" in result.error_message

# TEST 4 — ALL DBs FAIL
@patch("agents.dataPipelineOrchestrator.collectors.data_collector.StaticDataProcessor")
def test_all_fail(mock_processor_cls):
    schema = {"db1": {}, "db2": {}}

    processor_instance = mock_processor_cls.return_value
    processor_instance.process_data.return_value = make_processor_report(
        status=ProcessingStatus.ERROR,
        data=None,
        error_message="dead",
        metadata={"log": "fail"}
    )

    collector = DataCollector("staticDB", schema)
    result = collector.process_data()

    assert result.status == ProcessingStatus.ERROR
    assert result.error_type == ErrorType.DATA_PROCESSING_ERROR
    assert "No files could be processed successfully" in result.error_message

# TEST 5 — Exception trong processor
@patch("agents.dataPipelineOrchestrator.collectors.data_collector.DynamicDataProcessor")
def test_exception_during_processing(mock_processor_cls):
    schema = {"db1": {}}

    processor_instance = mock_processor_cls.return_value
    processor_instance.process_data.side_effect = RuntimeError("crash")

    collector = DataCollector("dynamicDB", schema)
    result = collector.process_data()

    assert result.status == ProcessingStatus.ERROR
    assert result.error_type == ErrorType.DATA_PROCESSING_ERROR
    assert "Unexpected error" in result.error_message