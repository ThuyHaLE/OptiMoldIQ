# tests/agents_tests/business_logic_tests/healers/test_data_collector_healer.py

import json
import pytest

from agents.dataPipelineOrchestrator.healers.data_collector_healer import (
    DataCollectorHealer
)
from agents.dataPipelineOrchestrator.configs.healing_configs import (
    ProcessingStatus,
    ProcessingScale,
    RecoveryAction,
    RecoveryDecision,
    Priority,
    ErrorType,
)
from agents.dataPipelineOrchestrator.configs.output_formats import (
    DataProcessingReport
)


# =========================
# Fixtures & helpers
# =========================

@pytest.fixture
def success_report():
    return DataProcessingReport(
        status=ProcessingStatus.SUCCESS,
        data={}
    )


def make_decision(
    scale=ProcessingScale.LOCAL,
    action=RecoveryAction.ROLLBACK_TO_BACKUP,
    status=ProcessingStatus.PENDING
):
    return RecoveryDecision(
        priority=Priority.CRITICAL,
        scale=scale,
        action=action,
        status=status
    )


# =========================
# Tests
# =========================

def test_heal_no_decision_to_heal(success_report):
    """
    No LOCAL + ROLLBACK_TO_BACKUP + PENDING decision
    → early return, nothing changes
    """
    decisions = [
        make_decision(scale=ProcessingScale.GLOBAL)
    ]

    healer = DataCollectorHealer(success_report, decisions)
    updated_decisions, final_report = healer.heal()

    assert final_report is success_report
    assert updated_decisions[0].status == ProcessingStatus.PENDING


def test_heal_no_annotation_file(mocker, base_collector_result, recovery_actions):
    healer = DataCollectorHealer(base_collector_result, recovery_actions)

    # Mock pathlib.Path.exists instead of the instance method
    mocker.patch('pathlib.Path.exists', return_value=False)

    decisions, final_result = healer.heal()

    for d in decisions:
        if d.action == RecoveryAction.ROLLBACK_TO_BACKUP:
            assert d.status == ProcessingStatus.ERROR

    assert final_result == base_collector_result


def test_heal_backup_success(mocker, base_collector_result, recovery_actions):
    # Mock pathlib.Path.exists to return True for annotation file
    mocker.patch('pathlib.Path.exists', return_value=True)
    
    # Mock json.load to return annotation data with valid file extension
    mock_open = mocker.mock_open(read_data='{"db1": "backup/data.xlsx"}')
    mocker.patch('builtins.open', mock_open)
    mocker.patch('json.load', return_value={"db1": "backup/data.xlsx"})

    fake_report = DataProcessingReport(
        status=ProcessingStatus.SUCCESS,
        data={},
    )

    # Mock load_existing_data BEFORE creating the healer
    # Mock it in the healer's module where it's imported
    mocker.patch(
        "agents.dataPipelineOrchestrator.healers.data_collector_healer.load_existing_data",
        return_value=fake_report
    )

    # Now create the healer and call heal()
    healer = DataCollectorHealer(base_collector_result, recovery_actions)
    decisions, final_result = healer.heal()

    assert final_result.status == ProcessingStatus.SUCCESS


def test_heal_backup_partial_failure(mocker, base_collector_result, recovery_actions):
    # Mock pathlib.Path.exists to return True for annotation file
    mocker.patch('pathlib.Path.exists', return_value=True)
    
    # Mock json.load to return annotation data with valid file extensions
    mock_open = mocker.mock_open(read_data='{"db1": "backup/data1.xlsx", "db2": "backup/data2.parquet"}')
    mocker.patch('builtins.open', mock_open)
    mocker.patch('json.load', return_value={"db1": "backup/data1.xlsx", "db2": "backup/data2.parquet"})

    success = DataProcessingReport(status=ProcessingStatus.SUCCESS, data={})
    fail = DataProcessingReport(status=ProcessingStatus.ERROR, data={}, error_message="boom")

    # Mock load_existing_data in the healer's module where it's imported
    mocker.patch(
        "agents.dataPipelineOrchestrator.healers.data_collector_healer.load_existing_data",
        side_effect=[success, fail]
    )

    # Now create the healer and call heal()
    healer = DataCollectorHealer(base_collector_result, recovery_actions)
    decisions, final_result = healer.heal()

    assert final_result == base_collector_result
    for d in decisions:
        if d.action == RecoveryAction.ROLLBACK_TO_BACKUP:
            assert d.status == ProcessingStatus.ERROR

def test_heal_invalid_json_annotation(mocker, base_collector_result, recovery_actions):
    healer = DataCollectorHealer(base_collector_result, recovery_actions)

    # Mock pathlib.Path.exists instead of the instance method
    mocker.patch('pathlib.Path.exists', return_value=True)
    
    # Mock json.load to raise JSONDecodeError
    mocker.patch(
        "json.load",
        side_effect=json.JSONDecodeError("msg", "doc", 0)
    )

    decisions, _ = healer.heal()

    for d in decisions:
        if d.action == RecoveryAction.ROLLBACK_TO_BACKUP:
            assert d.status == ProcessingStatus.ERROR