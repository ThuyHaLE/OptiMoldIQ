# tests/agents_tests/business_logic_tests/processors/test_data_pipeline_processor.py

import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path

from agents.dataPipelineOrchestrator.processors.data_pipeline_processor import DataPipelineProcessor
from agents.dataPipelineOrchestrator.configs.output_formats import DataProcessingReport
from agents.dataPipelineOrchestrator.configs.healing_configs import (
    ProcessingStatus, ErrorType, AgentType
)

@pytest.fixture
def valid_config(tmp_path):
    cfg = MagicMock()
    cfg.databaseSchemas_path = tmp_path / "schema.json"
    cfg.annotation_path = tmp_path / "annotation.json"
    cfg.manual_review_notifications_dir = tmp_path / "manual"

    cfg.validate_requirements.return_value = (True, [])
    return cfg


def make_report(
    status=ProcessingStatus.SUCCESS,
    error_type=ErrorType.NONE,
    data=None,
    error_message=""
):
    return DataProcessingReport(
        status=status,
        error_type=error_type,
        error_message=error_message,
        data=data
    )

# TEST 1 — Happy path (schema OK, collect OK)
@patch("agents.dataPipelineOrchestrator.processors.data_pipeline_processor.SchemaValidator")
@patch("agents.dataPipelineOrchestrator.processors.data_pipeline_processor.DataCollector")
def test_run_pipeline_success(
    mock_collector_cls,
    mock_validator_cls,
    valid_config
):
    # Schema OK
    mock_validator = mock_validator_cls.return_value
    mock_validator.validate.return_value = make_report(
        status=ProcessingStatus.SUCCESS,
        data={"db1": {}, "db2": {}}
    )

    # Collector OK cho mọi db
    mock_collector = mock_collector_cls.return_value
    mock_collector.process_data.return_value = make_report(
        status=ProcessingStatus.SUCCESS,
        data={"rows": 10}
    )

    processor = DataPipelineProcessor(valid_config)
    result = processor.run_pipeline()

    assert result.status == ProcessingStatus.SUCCESS
    assert result.error_type == ErrorType.NONE
    assert set(result.collected_data.keys()) == {"db1", "db2"}


# TEST 2 — Schema fail + healing FAIL
@patch("agents.dataPipelineOrchestrator.processors.data_pipeline_processor.SchemaValidator")
@patch.object(DataPipelineProcessor, "_process_healing_mechanism")
def test_schema_validation_fail_and_healing_fail(
    mock_healing,
    mock_validator_cls,
    valid_config
):
    mock_validator = mock_validator_cls.return_value
    mock_validator.validate.return_value = make_report(
        status=ProcessingStatus.ERROR,
        error_type=ErrorType.SCHEMA_MISMATCH,
        error_message="Invalid schema"
    )

    mock_healing.return_value = (False, mock_validator.validate.return_value)

    processor = DataPipelineProcessor(valid_config)
    result = processor.run_pipeline()

    assert result.status == ProcessingStatus.ERROR
    assert result.error_type == ErrorType.SCHEMA_MISMATCH
    assert "Schema validation: HEALING FAILED" in result.metadata["log"]

# TEST 3 — Schema failed but healing SUCCESS
@patch("agents.dataPipelineOrchestrator.processors.data_pipeline_processor.SchemaValidator")
@patch.object(DataPipelineProcessor, "_process_healing_mechanism")
@patch("agents.dataPipelineOrchestrator.processors.data_pipeline_processor.DataCollector")
def test_schema_fail_but_healing_success(
    mock_collector_cls,
    mock_healing,
    mock_validator_cls,
    valid_config
):
    bad_schema = make_report(
        status=ProcessingStatus.ERROR,
        error_type=ErrorType.SCHEMA_MISMATCH
    )

    healed_schema = make_report(
        status=ProcessingStatus.SUCCESS,
        data={"db1": {}}
    )

    mock_validator_cls.return_value.validate.return_value = bad_schema
    mock_healing.return_value = (True, healed_schema)

    mock_collector_cls.return_value.process_data.return_value = make_report(
        status=ProcessingStatus.SUCCESS,
        data={"rows": 5}
    )

    processor = DataPipelineProcessor(valid_config)
    result = processor.run_pipeline()

    assert result.status == ProcessingStatus.SUCCESS
    assert "db1" in result.collected_data

# TEST 4 — DataCollector fail 1 db → all-or-nothing FAIL
@patch("agents.dataPipelineOrchestrator.processors.data_pipeline_processor.SchemaValidator")
@patch("agents.dataPipelineOrchestrator.processors.data_pipeline_processor.DataCollector")
@patch.object(DataPipelineProcessor, "_process_healing_mechanism")
def test_data_collection_partial_fail(
    mock_healing,
    mock_collector_cls,
    mock_validator_cls,
    valid_config
):
    mock_validator_cls.return_value.validate.return_value = make_report(
        status=ProcessingStatus.SUCCESS,
        data={"db1": {}, "db2": {}}
    )

    def collector_side_effect(db_type, schema):
        collector = MagicMock()
        if db_type == "db1":
            collector.process_data.return_value = make_report(
                status=ProcessingStatus.SUCCESS,
                data={"rows": 1}
            )
        else:
            collector.process_data.return_value = make_report(
                status=ProcessingStatus.ERROR,
                error_type=ErrorType.DATA_PROCESSING_ERROR,
                error_message="fail db2"
            )
        return collector

    mock_collector_cls.side_effect = collector_side_effect

    mock_healing.return_value = (
        False,
        make_report(
            status=ProcessingStatus.ERROR,
            error_type=ErrorType.DATA_PROCESSING_ERROR
        )
    )

    processor = DataPipelineProcessor(valid_config)
    result = processor.run_pipeline()

    assert result.status == ProcessingStatus.ERROR
    assert result.error_type == ErrorType.DATA_PROCESSING_ERROR
    assert result.metadata["failed_db_types"] == ["db2"]