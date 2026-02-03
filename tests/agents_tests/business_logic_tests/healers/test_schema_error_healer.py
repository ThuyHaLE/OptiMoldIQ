import pytest

from agents.dataPipelineOrchestrator.healers.schema_error_healer import (
    SchemaErrorHealer
)
from agents.dataPipelineOrchestrator.configs.healing_configs import (
    ProcessingStatus,
    ProcessingScale,
    RecoveryAction,
    RecoveryDecision,
    Priority,
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
    No decision satisfies LOCAL + ROLLBACK_TO_BACKUP + PENDING
    → early return
    """
    decisions = [
        make_decision(scale=ProcessingScale.GLOBAL)
    ]

    healer = SchemaErrorHealer(success_report, decisions)
    updated_decisions, final_report = healer.heal()

    assert final_report is success_report
    assert updated_decisions[0].status == ProcessingStatus.PENDING

def test_heal_no_backup_schema_file(mocker, base_validation_result, recovery_actions):
    healer = SchemaErrorHealer(base_validation_result, recovery_actions)

    mocker.patch.object(healer.schema_path, "exists", return_value=False)

    decisions, final = healer.heal()

    for d in decisions:
        if d.action == RecoveryAction.ROLLBACK_TO_BACKUP:
            assert d.status == ProcessingStatus.ERROR

    assert final == base_validation_result

def test_heal_backup_schema_validation_success(mocker, success_report):
    """
    Backup schema exists and validation SUCCESS
    → decision SUCCESS
    → final_validation_result replaced
    """
    mocker.patch("pathlib.Path.exists", return_value=True)

    backup_validation = DataProcessingReport(
        status=ProcessingStatus.SUCCESS,
        data={"schema": "ok"}
    )

    mock_validator = mocker.Mock()
    mock_validator.validate.return_value = backup_validation

    mocker.patch(
        "agents.dataPipelineOrchestrator.healers.schema_error_healer.SchemaValidator",
        return_value=mock_validator
    )

    decision = make_decision()
    healer = SchemaErrorHealer(success_report, [decision])

    updated_decisions, final_report = healer.heal()

    assert updated_decisions[0].status == ProcessingStatus.SUCCESS
    assert final_report is backup_validation

def test_heal_backup_schema_validation_failure(mocker, success_report):
    """
    Backup schema exists but validation FAILS
    → decision status = validation status
    → final_validation_result NOT replaced
    """
    mocker.patch("pathlib.Path.exists", return_value=True)

    backup_validation = DataProcessingReport(
        status=ProcessingStatus.ERROR,
        data=None,
        error_message="schema mismatch"
    )

    mock_validator = mocker.Mock()
    mock_validator.validate.return_value = backup_validation

    mocker.patch(
        "agents.dataPipelineOrchestrator.healers.schema_error_healer.SchemaValidator",
        return_value=mock_validator
    )

    decision = make_decision()
    healer = SchemaErrorHealer(success_report, [decision])

    updated_decisions, final_report = healer.heal()

    assert updated_decisions[0].status == ProcessingStatus.ERROR
    assert final_report is success_report

def test_heal_exception_during_validation(mocker, success_report):
    """
    Exception raised during schema validation
    → decision status = ERROR
    """
    mocker.patch("pathlib.Path.exists", return_value=True)

    mock_validator = mocker.Mock()
    mock_validator.validate.side_effect = RuntimeError("boom")

    mocker.patch(
        "agents.dataPipelineOrchestrator.healers.schema_error_healer.SchemaValidator",
        return_value=mock_validator
    )

    decision = make_decision()
    healer = SchemaErrorHealer(success_report, [decision])

    updated_decisions, final_report = healer.heal()

    assert updated_decisions[0].status == ProcessingStatus.ERROR
    assert final_report is success_report