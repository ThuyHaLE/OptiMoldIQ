# tests/agents_tests/business_logic_tests/healers/test_data_pipeline_healing_mechanism.py

from unittest.mock import MagicMock, patch
from agents.dataPipelineOrchestrator.processors.data_pipeline_processor import DataPipelineProcessor
from agents.dataPipelineOrchestrator.configs.healing_configs import (
    ProcessingStatus, ErrorType, AgentType, ProcessingScale
)
from agents.dataPipelineOrchestrator.configs.output_formats import DataProcessingReport


def make_action(scale, status, action="rollback"):
    act = MagicMock()
    act.scale = scale
    act.status = status
    act.action.value = action
    act.priority.name = "HIGH"
    return act


@patch("agents.dataPipelineOrchestrator.processors.data_pipeline_processor.get_recovery_actions_for_agent_error")
@patch("agents.dataPipelineOrchestrator.processors.data_pipeline_processor.ManualReviewNotifier")
def test_healing_local_success(
    mock_notifier_cls,
    mock_get_actions,
    valid_config
):
    processor = DataPipelineProcessor(valid_config)

    # chuẩn bị context như trong run_pipeline
    processor.log_entries = []
    processor.pipeline_result.recovery_actions = {}

    # ===== Failed input =====
    failed_report = DataProcessingReport(
        status=ProcessingStatus.ERROR,
        error_type=ErrorType.SCHEMA_MISMATCH,
        error_message="schema broken",
        data=None
    )

    # ===== Recovery actions =====
    local_action = make_action(ProcessingScale.LOCAL, ProcessingStatus.SUCCESS)
    mock_get_actions.return_value = [local_action]

    # ===== Local healer mock =====
    local_healer = MagicMock()
    local_healer_instance = local_healer.return_value
    local_healer_instance.heal.return_value = (
        [local_action],
        DataProcessingReport(
            status=ProcessingStatus.SUCCESS,
            data={"db1": {}}
        )
    )

    # ===== Execute =====
    success, result = processor._process_healing_mechanism(
        result_name=AgentType.SCHEMA_VALIDATOR,
        result_data=failed_report,
        notification_path="/tmp/notify.txt",
        local_healer=local_healer
    )

    # ===== Assertions =====
    assert success is True
    assert result.status == ProcessingStatus.SUCCESS

    assert processor.pipeline_result.status == ProcessingStatus.SUCCESS
    assert processor.pipeline_result.error_type == ErrorType.NONE

    assert processor.pipeline_result.recovery_actions[
        AgentType.SCHEMA_VALIDATOR.value
    ] == [local_action]

    # notifier KHÔNG được gọi
    mock_notifier_cls.assert_not_called()

    # log đúng behavior
    assert any(
        "Local recovery successful" in line
        for line in processor.log_entries
    )

    # healer được gọi
    local_healer_instance.heal.assert_called_once()