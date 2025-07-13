"""
This module defines the static configuration and metadata for the multi-agent healing system.

It includes:
- Error types and associated recovery actions
- Agent configurations and error tolerances
- Trigger mappings between agents based on status

Note: Actual execution logic (e.g. retries, notifications) is handled by the runtime agent orchestrator.
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

class ProcessingStatus(Enum):
    PENDING = 'pending'
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    PARTIAL_SUCCESS = "partial_success"

class ErrorType(Enum):
    FILE_NOT_FOUND = "file_not_found"
    FILE_READ_ERROR = "file_read_error"
    MISSING_FIELDS = "missing_fields"
    DATA_PROCESSING_ERROR = "data_processing_error"
    PARQUET_SAVE_ERROR = "parquet_save_error"
    UNSUPPORTED_DATA_TYPE = "unsupported_data_type"
    HASH_COMPARISON_ERROR = "hash_comparison_error"
    DATA_CORRUPTION = "data_corruption"
    SCHEMA_MISMATCH = "schema_mismatch"

class RecoveryAction(Enum):
    RETRY_PROCESSING = "retry_processing"
    ROLLBACK_TO_BACKUP = "rollback_to_backup"
    TRIGGER_MANUAL_REVIEW = "trigger_manual_review"
    VALIDATE_SCHEMA = "validate_schema"

class AgentType(Enum):
    DATA_COLLECTOR = "DataCollector"
    DATA_LOADER = "DataLoader"
    ADMIN_NOTIFICATION_AGENT = 'AdminNotificationAgent'
    DATA_VALIDATOR = 'ValidationOrchestrator'

class ProcessingScale(Enum):
    LOCAL = "local"
    GLOBAL = "global"

class Priority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

# Information structures
@dataclass
class AgentExecutionInfo:
    agent_id: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    status: ProcessingStatus = ProcessingStatus.SUCCESS
    summary: Dict[str, Any] = field(default_factory=dict)
    details: List[Dict[str, Any]] = field(default_factory=list)
    healing_actions: List[RecoveryAction] = field(default_factory=list)
    trigger_agents: List[AgentType] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class RecoveryActionInfo:
    """Information about a recovery action - not the execution itself"""
    action: RecoveryAction
    description: str
    priority: Priority
    estimated_time_seconds: int
    prerequisites: List[str]
    success_criteria: List[str]
    rollback_possible: bool = True

@dataclass
class ErrorInfo:
    """Information about an error type - not the handling logic"""
    error_type: ErrorType
    severity: Priority
    description: str
    common_causes: List[str]
    prevention_tips: List[str]
    escalation_threshold: int = 3

@dataclass
class AgentConfig:
    """Configuration information for agents - not execution logic"""
    agent_type: AgentType
    max_retries: int
    timeout_seconds: int
    memory_limit_mb: int
    dependencies: List[AgentType]
    trigger_on_status: Dict[ProcessingStatus, List[AgentType]]
    error_tolerance: Dict[ErrorType, int]
    recovery_actions: Dict[ErrorType, List[RecoveryAction]]
    wait_for_dependencies: bool = True

    # Additional metadata
    description: str = ""
    responsible_team: str = ""
    sla_seconds: int = 0
    health_check_interval: int = 30

# Recovery action information catalog
RECOVERY_ACTION_CATALOG = {
    RecoveryAction.RETRY_PROCESSING: RecoveryActionInfo(
        action=RecoveryAction.RETRY_PROCESSING,
        description="Retry the failed operation with same parameters",
        priority=Priority.LOW,
        estimated_time_seconds=30,
        prerequisites=["Error is transient", "Retry count < max_retries"],
        success_criteria=["Operation completes successfully"],
        rollback_possible=True
    ),

    RecoveryAction.TRIGGER_MANUAL_REVIEW: RecoveryActionInfo(
        action=RecoveryAction.TRIGGER_MANUAL_REVIEW,
        description="Send notification to system administrators",
        priority=Priority.HIGH,
        estimated_time_seconds=5,
        prerequisites=["Error exceeds threshold", "Notification system available"],
        success_criteria=["Notification sent successfully"],
        rollback_possible=False
    ),

    RecoveryAction.ROLLBACK_TO_BACKUP: RecoveryActionInfo(
        action=RecoveryAction.ROLLBACK_TO_BACKUP,
        description="Restore from last known good backup",
        priority=Priority.HIGH,
        estimated_time_seconds=300,
        prerequisites=["Backup available", "Corruption detected"],
        success_criteria=["System restored to working state"],
        rollback_possible=False
    ),

    RecoveryAction.VALIDATE_SCHEMA: RecoveryActionInfo(
        action=RecoveryAction.VALIDATE_SCHEMA,
        description="Validate data against expected schema and attempt correction",
        priority=Priority.MEDIUM,
        estimated_time_seconds=60,
        prerequisites=["Schema definition available", "Data accessible"],
        success_criteria=["Data conforms to schema", "Validation passes"],
        rollback_possible=True
    ),
}

# Error information catalog
ERROR_CATALOG = {
    ErrorType.FILE_NOT_FOUND: ErrorInfo(
        error_type=ErrorType.FILE_NOT_FOUND,
        severity=Priority.CRITICAL,
        description="Expected file does not exist at specified path",
        common_causes=["File moved or deleted", "Incorrect path", "Permission issues"],
        prevention_tips=["Verify file paths", "Check file permissions", "Use file existence checks"],
        escalation_threshold=3
    ),

    ErrorType.FILE_READ_ERROR: ErrorInfo(
        error_type=ErrorType.FILE_READ_ERROR,
        severity=Priority.CRITICAL,
        description="File exists but could not be read properly",
        common_causes=["Corrupted file", "Unsupported format", "Permission denied", "File locked by another process"],
        prevention_tips=["Ensure file format is correct", "Avoid file corruption during save", "Avoid parallel access when reading", "Use try-except block with logging"],
        escalation_threshold=3
    ),

    ErrorType.MISSING_FIELDS: ErrorInfo(
        error_type=ErrorType.MISSING_FIELDS,
        severity=Priority.MEDIUM,
        description="One or more required columns or fields are missing in the data source",
        common_causes=["Schema changes", "Incorrect data extraction", "Manually edited source files"],
        prevention_tips=["Validate input files before processing", "Check for required columns using schema definitions", "Automate schema enforcement"],
        escalation_threshold=3
    ),

    ErrorType.DATA_PROCESSING_ERROR: ErrorInfo(
        error_type=ErrorType.DATA_PROCESSING_ERROR,
        severity=Priority.MEDIUM,
        description="Unexpected error occurred during data transformation or computation",
        common_causes=["Invalid input values", "Incorrect data types", "Logic errors in processing functions"],
        prevention_tips=["Add data validation before processing", "Use type-checking and conversion", "Write unit tests for transformation logic"],
        escalation_threshold=3
    ),

    ErrorType.PARQUET_SAVE_ERROR: ErrorInfo(
        error_type=ErrorType.PARQUET_SAVE_ERROR,
        severity=Priority.MEDIUM,
        description="Failed to save dataframe as a Parquet file",
        common_causes=["Disk full", "Write permission denied", "Incompatible schema or column types"],
        prevention_tips=["Ensure sufficient disk space", "Check file system permissions", "Validate dataframe schema before saving"],
        escalation_threshold=3
    ),

    ErrorType.UNSUPPORTED_DATA_TYPE: ErrorInfo(
        error_type=ErrorType.UNSUPPORTED_DATA_TYPE,
        severity=Priority.MEDIUM,
        description="The provided data type identifier is not supported",
        common_causes=["Unexpected or new data type", "Incorrect naming convention"],
        prevention_tips=["Ensure the file name or data source uses a valid prefix", "Update the required fields list if needed"],
        escalation_threshold=3
    ),

    ErrorType.HASH_COMPARISON_ERROR: ErrorInfo(
        error_type=ErrorType.HASH_COMPARISON_ERROR,
        severity=Priority.CRITICAL,
        description="Failed to compare dataframes (hash type)",
        common_causes=[
            "Inconsistent hashing method used between sources",
            "Data was modified during hash generation",
            "Corrupted or partially loaded dataframe"
        ],
        prevention_tips=[
            "Ensure consistent hashing function is used across modules",
            "Avoid changing dataframe between load and hash comparison",
            "Use stable and deterministic serialization (e.g., sort index/columns)"
        ],
        escalation_threshold=3
    ),

    ErrorType.DATA_CORRUPTION: ErrorInfo(
        error_type=ErrorType.DATA_CORRUPTION,
        severity=Priority.HIGH,
        description="Data integrity compromised during processing",
        common_causes=[
            "Incomplete or corrupted file read (e.g., parquet, csv)",
            "Unexpected nulls or outliers in critical fields",
            "Encoding issues or binary corruption during file transfer"
        ],
        prevention_tips=[
            "Validate file integrity using checksums before processing",
            "Introduce input schema validation before ingestion",
            "Avoid abrupt termination during file writing"
        ],
        escalation_threshold=2
    ),

    ErrorType.SCHEMA_MISMATCH: ErrorInfo(
        error_type=ErrorType.SCHEMA_MISMATCH,
        severity=Priority.MEDIUM,
        description="Data schema does not match expected format",
        common_causes=[
            "Mismatch between actual columns and expected schema",
            "Changes in upstream schema not propagated to validator",
            "Incorrect or outdated schema definition"
        ],
        prevention_tips=[
            "Version-control schema definitions and validate on load",
            "Log and monitor schema changes from upstream data",
            "Use automated schema validators with clear expected formats"
        ],
        escalation_threshold=3
    ),
}

# Agent recovery strategy mapping (information only)
AGENT_ERROR_RECOVERY_MAPPING = {
    AgentType.DATA_COLLECTOR: {
        ErrorType.FILE_NOT_FOUND: [
            (Priority.CRITICAL, ProcessingScale.LOCAL, RecoveryAction.ROLLBACK_TO_BACKUP, ProcessingStatus.PENDING),
            (Priority.HIGH, ProcessingScale.GLOBAL, RecoveryAction.TRIGGER_MANUAL_REVIEW, ProcessingStatus.PENDING)
            ],
        ErrorType.MISSING_FIELDS: [
            (Priority.CRITICAL, ProcessingScale.LOCAL, RecoveryAction.ROLLBACK_TO_BACKUP, ProcessingStatus.PENDING),
            (Priority.HIGH, ProcessingScale.GLOBAL, RecoveryAction.TRIGGER_MANUAL_REVIEW, ProcessingStatus.PENDING)
            ],
        ErrorType.FILE_READ_ERROR: [
            (Priority.CRITICAL, ProcessingScale.LOCAL, RecoveryAction.ROLLBACK_TO_BACKUP, ProcessingStatus.PENDING),
            (Priority.HIGH, ProcessingScale.GLOBAL, RecoveryAction.TRIGGER_MANUAL_REVIEW, ProcessingStatus.PENDING)
            ],

        ErrorType.UNSUPPORTED_DATA_TYPE: [
            (Priority.CRITICAL, ProcessingScale.LOCAL, RecoveryAction.ROLLBACK_TO_BACKUP, ProcessingStatus.PENDING),
            (Priority.HIGH, ProcessingScale.GLOBAL, RecoveryAction.TRIGGER_MANUAL_REVIEW, ProcessingStatus.PENDING)
            ],
        ErrorType.PARQUET_SAVE_ERROR: [
            (Priority.CRITICAL, ProcessingScale.LOCAL, RecoveryAction.ROLLBACK_TO_BACKUP, ProcessingStatus.PENDING),
            (Priority.HIGH, ProcessingScale.GLOBAL, RecoveryAction.TRIGGER_MANUAL_REVIEW, ProcessingStatus.PENDING)
            ],
        ErrorType.DATA_PROCESSING_ERROR: [
            (Priority.CRITICAL, ProcessingScale.LOCAL, RecoveryAction.ROLLBACK_TO_BACKUP, ProcessingStatus.PENDING),
            (Priority.HIGH, ProcessingScale.GLOBAL, RecoveryAction.TRIGGER_MANUAL_REVIEW, ProcessingStatus.PENDING)
            ],
    },

    AgentType.DATA_LOADER: {
        ErrorType.HASH_COMPARISON_ERROR: [
            (Priority.CRITICAL, ProcessingScale.LOCAL, RecoveryAction.ROLLBACK_TO_BACKUP, ProcessingStatus.PENDING),
            (Priority.HIGH, ProcessingScale.GLOBAL, RecoveryAction.TRIGGER_MANUAL_REVIEW, ProcessingStatus.PENDING)
            ],
        ErrorType.FILE_NOT_FOUND: [
            (Priority.CRITICAL, ProcessingScale.LOCAL, RecoveryAction.ROLLBACK_TO_BACKUP, ProcessingStatus.PENDING),
            (Priority.HIGH, ProcessingScale.GLOBAL, RecoveryAction.TRIGGER_MANUAL_REVIEW, ProcessingStatus.PENDING)
            ],
        ErrorType.DATA_CORRUPTION: [
            (Priority.CRITICAL, ProcessingScale.LOCAL, RecoveryAction.ROLLBACK_TO_BACKUP, ProcessingStatus.PENDING),
            (Priority.HIGH, ProcessingScale.LOCAL, RecoveryAction.RETRY_PROCESSING, ProcessingStatus.PENDING),
            (Priority.HIGH, ProcessingScale.GLOBAL, RecoveryAction.TRIGGER_MANUAL_REVIEW, ProcessingStatus.PENDING)
            ],
        ErrorType.PARQUET_SAVE_ERROR: [
            (Priority.CRITICAL, ProcessingScale.LOCAL, RecoveryAction.ROLLBACK_TO_BACKUP, ProcessingStatus.PENDING),
            (Priority.HIGH, ProcessingScale.GLOBAL, RecoveryAction.TRIGGER_MANUAL_REVIEW, ProcessingStatus.PENDING)
            ],
        ErrorType.FILE_READ_ERROR: [
            (Priority.CRITICAL, ProcessingScale.LOCAL, RecoveryAction.ROLLBACK_TO_BACKUP, ProcessingStatus.PENDING),
            (Priority.HIGH, ProcessingScale.LOCAL, RecoveryAction.RETRY_PROCESSING, ProcessingStatus.PENDING),
            (Priority.HIGH, ProcessingScale.GLOBAL, RecoveryAction.TRIGGER_MANUAL_REVIEW, ProcessingStatus.PENDING)
            ],
        ErrorType.SCHEMA_MISMATCH: [
            (Priority.CRITICAL, ProcessingScale.LOCAL, RecoveryAction.ROLLBACK_TO_BACKUP, ProcessingStatus.PENDING),
            (Priority.HIGH, ProcessingScale.LOCAL, RecoveryAction.RETRY_PROCESSING, ProcessingStatus.PENDING),
            (Priority.HIGH, ProcessingScale.LOCAL, RecoveryAction.VALIDATE_SCHEMA, ProcessingStatus.PENDING),
            (Priority.HIGH, ProcessingScale.GLOBAL, RecoveryAction.TRIGGER_MANUAL_REVIEW, ProcessingStatus.PENDING)
            ],
    },

    AgentType.ADMIN_NOTIFICATION_AGENT: {
        # Notification agent typically doesn't have recovery actions, just logs
    },

    AgentType.DATA_VALIDATOR: {
        # Notification agent typically doesn't have recovery actions, just logs
    },
}

# Agent trigger mapping - what agents to trigger based on status
AGENT_TRIGGER_MAPPING = {
    AgentType.DATA_COLLECTOR: {
        ProcessingStatus.SUCCESS: [AgentType.DATA_LOADER],
        ProcessingStatus.PARTIAL_SUCCESS: [AgentType.DATA_LOADER, AgentType.ADMIN_NOTIFICATION_AGENT],
        ProcessingStatus.ERROR: [AgentType.ADMIN_NOTIFICATION_AGENT],
        ProcessingStatus.WARNING: [AgentType.DATA_LOADER, AgentType.ADMIN_NOTIFICATION_AGENT]
    },

    AgentType.DATA_LOADER: {
        ProcessingStatus.SUCCESS: [AgentType.DATA_VALIDATOR],
        ProcessingStatus.PARTIAL_SUCCESS: [AgentType.DATA_VALIDATOR, AgentType.ADMIN_NOTIFICATION_AGENT],
        ProcessingStatus.ERROR: [AgentType.ADMIN_NOTIFICATION_AGENT],
        ProcessingStatus.WARNING: [AgentType.DATA_VALIDATOR, AgentType.ADMIN_NOTIFICATION_AGENT]
    },

    AgentType.DATA_VALIDATOR: {
        ProcessingStatus.SUCCESS: [],  # End of pipeline
        ProcessingStatus.PARTIAL_SUCCESS: [AgentType.ADMIN_NOTIFICATION_AGENT],
        ProcessingStatus.ERROR: [AgentType.ADMIN_NOTIFICATION_AGENT],
        ProcessingStatus.WARNING: [AgentType.ADMIN_NOTIFICATION_AGENT]
    },

    AgentType.ADMIN_NOTIFICATION_AGENT: {
        ProcessingStatus.SUCCESS: [],  # Notification sent, no further triggers
        ProcessingStatus.ERROR: [],    # Failed to send notification, manual intervention needed
    },
}

# Agent configuration catalog
AGENT_CONFIGS = {
    AgentType.DATA_COLLECTOR: AgentConfig(
        agent_type=AgentType.DATA_COLLECTOR,
        max_retries=3,
        timeout_seconds=300,
        memory_limit_mb=2048,
        dependencies=[],
        trigger_on_status=AGENT_TRIGGER_MAPPING[AgentType.DATA_COLLECTOR],
        error_tolerance={
            ErrorType.FILE_READ_ERROR: 2,
            ErrorType.MISSING_FIELDS: 1,
            ErrorType.UNSUPPORTED_DATA_TYPE: 2,
        },
        recovery_actions=AGENT_ERROR_RECOVERY_MAPPING[AgentType.DATA_COLLECTOR],
        wait_for_dependencies=False,
        description="Collects data from various sources and prepares for processing",
        responsible_team="Data Engineering",
        sla_seconds=300,
        health_check_interval=30
    ),

    AgentType.DATA_LOADER: AgentConfig(
        agent_type=AgentType.DATA_LOADER,
        max_retries=3,
        timeout_seconds=600,
        memory_limit_mb=4096,
        dependencies=[AgentType.DATA_COLLECTOR],
        trigger_on_status=AGENT_TRIGGER_MAPPING[AgentType.DATA_LOADER],
        error_tolerance={
            ErrorType.FILE_READ_ERROR: 2,
            ErrorType.DATA_CORRUPTION: 1,
            ErrorType.HASH_COMPARISON_ERROR: 2,
        },
        recovery_actions=AGENT_ERROR_RECOVERY_MAPPING[AgentType.DATA_LOADER],
        wait_for_dependencies=True,
        description="Loads and processes data from collectors",
        responsible_team="Data Engineering",
        sla_seconds=600,
        health_check_interval=60
    ),

    AgentType.DATA_VALIDATOR: AgentConfig(
        agent_type=AgentType.DATA_VALIDATOR,
        max_retries=2,
        timeout_seconds=180,
        memory_limit_mb=1024,
        dependencies=[AgentType.DATA_LOADER],
        trigger_on_status=AGENT_TRIGGER_MAPPING[AgentType.DATA_VALIDATOR],
        error_tolerance={
            ErrorType.SCHEMA_MISMATCH: 1,
            ErrorType.DATA_CORRUPTION: 0,
        },
        recovery_actions=AGENT_ERROR_RECOVERY_MAPPING[AgentType.DATA_VALIDATOR],
        wait_for_dependencies=True,
        description="Validates data quality and schema compliance",
        responsible_team="Data Quality",
        sla_seconds=180,
        health_check_interval=30
    ),

    AgentType.ADMIN_NOTIFICATION_AGENT: AgentConfig(
        agent_type=AgentType.ADMIN_NOTIFICATION_AGENT,
        max_retries=3,
        timeout_seconds=30,
        memory_limit_mb=256,
        dependencies=[],
        trigger_on_status=AGENT_TRIGGER_MAPPING[AgentType.ADMIN_NOTIFICATION_AGENT],
        error_tolerance={},
        recovery_actions=AGENT_ERROR_RECOVERY_MAPPING[AgentType.ADMIN_NOTIFICATION_AGENT],
        wait_for_dependencies=False,
        description="Sends notifications to administrators about system issues",
        responsible_team="Operations",
        sla_seconds=30,
        health_check_interval=60
    ),
}

def get_agent_config(agent_type: AgentType) -> Optional[AgentConfig]:
    """Get configuration for specific agent type"""
    return AGENT_CONFIGS.get(agent_type)

def get_recovery_actions_for_agent_error(agent_type: AgentType, error_type: ErrorType, 
                                         context: Optional[Dict] = None ) -> List[Tuple[Priority, ProcessingScale, RecoveryAction]]:
    """Get recovery actions with context consideration"""
    base_actions = AGENT_ERROR_RECOVERY_MAPPING.get(agent_type, {}).get(error_type, [])
    
    if context:
        # Skip retry if retry_count exceeded
        if context.get('retry_count', 0) >= context.get('max_retries', 3):
            return [action for action in base_actions 
                   if action[2] != RecoveryAction.RETRY_PROCESSING]
    
    return base_actions

def get_triggered_agents(agent_type: AgentType, status: ProcessingStatus) -> List[AgentType]:
    """Get list of agents that should be triggered based on agent status"""
    return AGENT_TRIGGER_MAPPING.get(agent_type, {}).get(status, [])

def validate_configuration() -> List[str]:
    """Validate the configuration for consistency issues"""
    issues = []

    # Check if all agent types have configurations
    for agent_type in AgentType:
        if agent_type not in AGENT_CONFIGS:
            issues.append(f"Missing configuration for {agent_type}")

    # Check if all dependencies are configured
    for agent_type, config in AGENT_CONFIGS.items():
        for dep in config.dependencies:
            if dep not in AGENT_CONFIGS:
                issues.append(f"{agent_type} depends on unconfigured agent {dep}")

    # Check if all referenced agents in triggers exist
    for agent_type, triggers in AGENT_TRIGGER_MAPPING.items():
        for status, triggered_agents in triggers.items():
            for triggered_agent in triggered_agents:
                if triggered_agent not in AGENT_CONFIGS:
                    issues.append(f"{agent_type} triggers unconfigured agent {triggered_agent}")

    return issues