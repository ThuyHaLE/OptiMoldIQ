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


def test_heal_no_annotation_file(mocker, success_report):
    """
    Decision needs healing but annotation file does not exist
    → decision status = ERROR
    """
    mocker.patch("pathlib.Path.exists", return_value=False)

    decision = make_decision()
    healer = DataCollectorHealer(success_report, [decision])

    updated_decisions, final_report = healer.heal()

    assert updated_decisions[0].status == ProcessingStatus.ERROR
    assert final_report is success_report


def test_heal_backup_success(mocker, success_report):
    """
    Annotation exists, all databases load successfully
    → decision SUCCESS
    → final_collector_result replaced
    """
    mocker.patch("pathlib.Path.exists", return_value=True)
    mocker.patch("json.load", return_value={
        "db1": "/fake/path/db1",
        "db2": "/fake/path/db2",
    })

    mocker.patch(
        "agents.dataPipelineOrchestrator.healers.data_collector_healer.load_existing_data",
        side_effect=[
            DataProcessingReport(status=ProcessingStatus.SUCCESS, data={"a": 1}),
            DataProcessingReport(status=ProcessingStatus.SUCCESS, data={"b": 2}),
        ]
    )

    decision = make_decision()
    healer = DataCollectorHealer(success_report, [decision])

    updated_decisions, final_report = healer.heal()

    assert updated_decisions[0].status == ProcessingStatus.SUCCESS
    assert final_report.status == ProcessingStatus.SUCCESS
    assert final_report.error_type == ErrorType.NONE
    assert final_report.metadata["successful"] == 2
    assert final_report.metadata["failed"] == 0


def test_heal_backup_partial_failure(mocker, success_report):
    """
    Annotation exists but at least one database fails
    → decision ERROR
    → final_collector_result must NOT be replaced
    """
    mocker.patch("pathlib.Path.exists", return_value=True)
    mocker.patch("json.load", return_value={
        "db1": "/fake/path/db1",
        "db2": "/fake/path/db2",
    })

    mocker.patch(
        "agents.dataPipelineOrchestrator.healers.data_collector_healer.load_existing_data",
        side_effect=[
            DataProcessingReport(status=ProcessingStatus.SUCCESS, data={"a": 1}),
            DataProcessingReport(
                status=ProcessingStatus.ERROR,
                data=None,
                error_message="load failed"
            ),
        ]
    )

    decision = make_decision()
    healer = DataCollectorHealer(success_report, [decision])

    updated_decisions, final_report = healer.heal()

    assert updated_decisions[0].status == ProcessingStatus.ERROR
    # Must keep original report
    assert final_report is success_report


def test_heal_invalid_json_annotation(mocker, success_report):
    """
    Annotation file exists but JSON is invalid
    → decision ERROR
    """
    mocker.patch("pathlib.Path.exists", return_value=True)
    mocker.patch(
        "json.load",
        side_effect=json.JSONDecodeError("msg", "doc", 0)
    )

    decision = make_decision()
    healer = DataCollectorHealer(success_report, [decision])

    updated_decisions, final_report = healer.heal()

    assert updated_decisions[0].status == ProcessingStatus.ERROR
    assert final_report is success_report
