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

    mocker.patch.object(healer.annotation_path, "exists", return_value=False)

    decisions, final_result = healer.heal()

    for d in decisions:
        if d.action == RecoveryAction.ROLLBACK_TO_BACKUP:
            assert d.status == ProcessingStatus.ERROR

    assert final_result == base_collector_result


def test_heal_backup_success(mocker, base_collector_result, recovery_actions):
    healer = DataCollectorHealer(base_collector_result, recovery_actions)

    mocker.patch.object(healer.annotation_path, "exists", return_value=True)
    mocker.patch("agents.dataPipelineOrchestrator.healers.data_collector_healer.json.load",
                 return_value={"db1": "path1"})

    fake_report = DataProcessingReport(
        status=ProcessingStatus.SUCCESS,
        data={},
    )

    mocker.patch(
        "agents.dataPipelineOrchestrator.healers.data_collector_healer.load_existing_data",
        return_value=fake_report
    )

    decisions, final_result = healer.heal()

    assert final_result.status == ProcessingStatus.SUCCESS


def test_heal_backup_partial_failure(mocker, base_collector_result, recovery_actions):
    healer = DataCollectorHealer(base_collector_result, recovery_actions)

    mocker.patch.object(healer.annotation_path, "exists", return_value=True)
    mocker.patch(
        "agents.dataPipelineOrchestrator.healers.data_collector_healer.json.load",
        return_value={"db1": "path1", "db2": "path2"}
    )

    success = DataProcessingReport(status=ProcessingStatus.SUCCESS, data={})
    fail = DataProcessingReport(status=ProcessingStatus.ERROR, data={}, error_message="boom")

    mocker.patch(
        "agents.dataPipelineOrchestrator.healers.data_collector_healer.load_existing_data",
        side_effect=[success, fail]
    )

    decisions, final_result = healer.heal()

    assert final_result == base_collector_result
    for d in decisions:
        if d.action == RecoveryAction.ROLLBACK_TO_BACKUP:
            assert d.status == ProcessingStatus.ERROR

def test_heal_invalid_json_annotation(mocker, base_collector_result, recovery_actions):
    healer = DataCollectorHealer(base_collector_result, recovery_actions)

    mocker.patch.object(healer.annotation_path, "exists", return_value=True)
    mocker.patch(
        "agents.dataPipelineOrchestrator.healers.data_collector_healer.json.load",
        side_effect=json.JSONDecodeError("msg", "doc", 0)
    )

    decisions, _ = healer.heal()

    for d in decisions:
        if d.action == RecoveryAction.ROLLBACK_TO_BACKUP:
            assert d.status == ProcessingStatus.ERROR