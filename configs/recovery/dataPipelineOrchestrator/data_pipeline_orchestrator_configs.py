"""
This module defines the static configuration and metadata for the multi-agent healing system.

It includes:
- Error types and associated recovery actions
- Agent configurations and error tolerances
- Trigger mappings between agents based on status

Note: Actual execution logic (e.g. retries, notifications) is handled by the runtime agent orchestrator.
"""

from typing import Dict, List, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

class ProcessingStatus(Enum):
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
    SCHEMA_VALIDATION_ERROR = "schema_validation_error"
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
    status: str = ProcessingStatus.SUCCESS.value
    summary: Dict[str, Any] = field(default_factory=dict)
    details: List[Dict[str, Any]] = field(default_factory=list)
    healing_actions: List[str] = field(default_factory=list)
    trigger_agents: List[str] = field(default_factory=list)
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
    trigger_list: List[AgentType]
    error_tolerance: Dict[ErrorType, int]
    healing_mechanism: Dict[AgentType, int]
    wait_for_dependencies: bool = True
    trigger_on_status: List[ProcessingStatus] = field(default_factory=list)

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
        description="Restore from last known good backup",
        priority=Priority.HIGH,
        estimated_time_seconds=300,
        prerequisites=["Backup available", "Corruption detected"],
        success_criteria=["System restored to working state"],
        rollback_possible=False
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

    ErrorType.SCHEMA_VALIDATION_ERROR: ErrorInfo(
        error_type=ErrorType.SCHEMA_VALIDATION_ERROR,
        severity=Priority.MEDIUM,
        description="Data does not conform to the expected schema",
        common_causes=["Data type mismatch", "Unexpected nulls in non-nullable fields", "Missing required columns"],
        prevention_tips=["Define and enforce schema expectations", "Validate data types early", "Log schema mismatches for debugging"],
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
        severity=Priority.MEDIUM,
        description="Failed to process single database",
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
        escalation_threshold=3
    ),

    ErrorType.SCHEMA_MISMATCH: ErrorInfo(
        error_type=ErrorType.SCHEMA_MISMATCH,
        severity=Priority.MEDIUM,
        description="Failed to process static DB",
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
        ErrorType.FILE_NOT_FOUND: [RecoveryAction.TRIGGER_MANUAL_REVIEW.value],
        ErrorType.MISSING_FIELDS: [RecoveryAction.TRIGGER_MANUAL_REVIEW.value],
        ErrorType.FILE_READ_ERROR: [RecoveryAction.RETRY_PROCESSING.value, RecoveryAction.TRIGGER_MANUAL_REVIEW.value],
        ErrorType.SCHEMA_VALIDATION_ERROR: [RecoveryAction.RETRY_PROCESSING.value, RecoveryAction.TRIGGER_MANUAL_REVIEW.value],
        ErrorType.PARQUET_SAVE_ERROR: [RecoveryAction.RETRY_PROCESSING.value, RecoveryAction.TRIGGER_MANUAL_REVIEW.value],
        ErrorType.DATA_PROCESSING_ERROR: [RecoveryAction.RETRY_PROCESSING.value, RecoveryAction.TRIGGER_MANUAL_REVIEW.value],
    },

    AgentType.DATA_LOADER: {
        ErrorType.FILE_NOT_FOUND: [RecoveryAction.ROLLBACK_TO_BACKUP.value, RecoveryAction.TRIGGER_MANUAL_REVIEW.value],
        ErrorType.DATA_CORRUPTION: [RecoveryAction.ROLLBACK_TO_BACKUP.value, RecoveryAction.TRIGGER_MANUAL_REVIEW.value],
        ErrorType.PARQUET_SAVE_ERROR: [RecoveryAction.RETRY_PROCESSING.value, RecoveryAction.TRIGGER_MANUAL_REVIEW.value],
        ErrorType.HASH_COMPARISON_ERROR: [RecoveryAction.RETRY_PROCESSING.value, RecoveryAction.TRIGGER_MANUAL_REVIEW.value],
        ErrorType.SCHEMA_MISMATCH: [RecoveryAction.VALIDATE_SCHEMA.value, RecoveryAction.TRIGGER_MANUAL_REVIEW.value],
        ErrorType.FILE_READ_ERROR: [RecoveryAction.RETRY_PROCESSING.value, RecoveryAction.ROLLBACK_TO_BACKUP.value, RecoveryAction.TRIGGER_MANUAL_REVIEW.value],    
    },
}

AGENT_TRIGGER_MAPPING = {
    AgentType.DATA_COLLECTOR: {
        ProcessingStatus.SUCCESS: [AgentType.DATA_LOADER.value],
        ProcessingStatus.PARTIAL_SUCCESS: [AgentType.ADMIN_NOTIFICATION_AGENT.value],
        ProcessingStatus.ERROR: [AgentType.ADMIN_NOTIFICATION_AGENT.value]
    },

    AgentType.DATA_LOADER: {
        ProcessingStatus.SUCCESS: [AgentType.DATA_VALIDATOR.value],
        ProcessingStatus.PARTIAL_SUCCESS: [AgentType.ADMIN_NOTIFICATION_AGENT.value],
        ProcessingStatus.ERROR: [AgentType.ADMIN_NOTIFICATION_AGENT.value]
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
        trigger_list=AGENT_TRIGGER_MAPPING.get(AgentType.DATA_COLLECTOR, {}),
        error_tolerance={
            ErrorType.FILE_READ_ERROR: 2,
            ErrorType.MISSING_FIELDS: 1,
        },
        healing_mechanism = AGENT_ERROR_RECOVERY_MAPPING.get(AgentType.DATA_COLLECTOR, {}),
        wait_for_dependencies=False,
        trigger_on_status=[ProcessingStatus.SUCCESS.value, ProcessingStatus.PARTIAL_SUCCESS.value],
        description="Collects data from various sources and prepares for processing",
        responsible_team="Data Engineering",
        sla_seconds=300
    ),

    AgentType.DATA_LOADER: AgentConfig(
        agent_type=AgentType.DATA_LOADER,
        max_retries=3,
        timeout_seconds=300,
        memory_limit_mb=2048,
        dependencies=[AgentType.DATA_COLLECTOR],
        trigger_list=AGENT_TRIGGER_MAPPING.get(AgentType.DATA_LOADER, {}),
        error_tolerance={
            ErrorType.FILE_READ_ERROR: 2,
            ErrorType.MISSING_FIELDS: 1,
        },
        healing_mechanism = AGENT_ERROR_RECOVERY_MAPPING.get(AgentType.DATA_LOADER, {}),
        wait_for_dependencies=True,
        trigger_on_status=[ProcessingStatus.SUCCESS.value, ProcessingStatus.PARTIAL_SUCCESS.value],
        description="Loads data from various sources and prepares for processing",
        responsible_team="Data Engineering",
        sla_seconds=300
    ),
}

def get_agent_config(agent_type: AgentType) -> AgentConfig:
    """Get configuration for specific agent type"""
    return AGENT_CONFIGS.get(agent_type)