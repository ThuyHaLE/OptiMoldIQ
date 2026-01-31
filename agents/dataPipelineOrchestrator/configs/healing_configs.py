# agents/dataPipelineOrchestrator/configs/healing_configs.py

from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Optional

class ProcessingStatus(Enum):
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    SKIP = "skipped"
    PENDING = "pending"
    WARNING = "warning"
    ERROR = "error"

class ErrorType(Enum):
    NONE = ""
    FILE_NOT_VALID = "file_not_valid"
    FILE_NOT_FOUND = "file_not_found"
    FILE_READ_ERROR = "file_read_error"
    MISSING_FIELDS = "missing_fields"
    DATA_PROCESSING_ERROR = "data_processing_error"
    PARQUET_SAVE_ERROR = "parquet_save_error"
    UNSUPPORTED_DATA_TYPE = "unsupported_data_type"
    HASH_COMPARISON_ERROR = "hash_comparison_error"
    DATA_CORRUPTION = "data_corruption"
    SCHEMA_MISMATCH = "schema_mismatch"
    INVALID_JSON = "invalid_json"
    INVALID_SCHEMA_STRUCTURE = "invalid_schema_structure"

class Priority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class ErrorInfo:
    """Information about an error type - not the handling logic"""
    error_type: ErrorType
    severity: Priority
    description: str
    common_causes: List[str]
    prevention_tips: List[str]
    escalation_threshold: int = 3

# Error information catalog
ERROR_CATALOG = {
    ErrorType.FILE_NOT_VALID: ErrorInfo(
        error_type=ErrorType.FILE_NOT_VALID,
        severity=Priority.HIGH,
        description="File exists but does not match expected structure or format",
        common_causes=[
            "Unexpected file format",
            "Renamed file with incorrect extension",
            "Manual modification breaking structure",
            "Partial or failed file export"
        ],
        prevention_tips=[
            "Validate file format before processing",
            "Use strict file extension checks",
            "Automate file generation instead of manual editing",
            "Add schema validation step after loading"
        ],
        escalation_threshold=2
    ),

    ErrorType.FILE_NOT_FOUND: ErrorInfo(
        error_type=ErrorType.FILE_NOT_FOUND,
        severity=Priority.CRITICAL,
        description="Expected file does not exist at specified path",
        common_causes=[
            "File moved or deleted", 
            "Incorrect path", 
            "Permission issues"
            ],
        prevention_tips=[
            "Verify file paths", 
            "Check file permissions", 
            "Use file existence checks"
            ],
        escalation_threshold=3
    ),

    ErrorType.FILE_READ_ERROR: ErrorInfo(
        error_type=ErrorType.FILE_READ_ERROR,
        severity=Priority.CRITICAL,
        description="File exists but could not be read properly",
        common_causes=[
            "Corrupted file", 
            "Unsupported format", 
            "Permission denied", 
            "File locked by another process"
            ],
        prevention_tips=[
            "Ensure file format is correct", 
            "Avoid file corruption during save", 
            "Avoid parallel access when reading", 
            "Use try-except block with logging"
            ],
        escalation_threshold=3
    ),

    ErrorType.MISSING_FIELDS: ErrorInfo(
        error_type=ErrorType.MISSING_FIELDS,
        severity=Priority.MEDIUM,
        description="One or more required columns or fields are missing in the data source",
        common_causes=[
            "Schema changes", 
            "Incorrect data extraction", 
            "Manually edited source files"
            ],
        prevention_tips=[
            "Validate input files before processing", 
            "Check for required columns using schema definitions", 
            "Automate schema enforcement"
            ],
        escalation_threshold=3
    ),

    ErrorType.DATA_PROCESSING_ERROR: ErrorInfo(
        error_type=ErrorType.DATA_PROCESSING_ERROR,
        severity=Priority.MEDIUM,
        description="Unexpected error occurred during data transformation or computation",
        common_causes=[
            "Invalid input values", 
            "Incorrect data types", 
            "Logic errors in processing functions"
            ],
        prevention_tips=[
            "Add data validation before processing", 
            "Use type-checking and conversion", 
            "Write unit tests for transformation logic"
            ],
        escalation_threshold=3
    ),

    ErrorType.PARQUET_SAVE_ERROR: ErrorInfo(
        error_type=ErrorType.PARQUET_SAVE_ERROR,
        severity=Priority.MEDIUM,
        description="Failed to save dataframe as a Parquet file",
        common_causes=[
            "Disk full", 
            "Write permission denied", 
            "Incompatible schema or column types"
            ],
        prevention_tips=[
            "Ensure sufficient disk space", 
            "Check file system permissions", 
            "Validate dataframe schema before saving"
            ],
        escalation_threshold=3
    ),

    ErrorType.UNSUPPORTED_DATA_TYPE: ErrorInfo(
        error_type=ErrorType.UNSUPPORTED_DATA_TYPE,
        severity=Priority.MEDIUM,
        description="The provided data type identifier is not supported",
        common_causes=[
            "Unexpected or new data type", 
            "Incorrect naming convention"
            ],
        prevention_tips=[
            "Ensure the file name or data source uses a valid prefix", 
            "Update the required fields list if needed"
            ],
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

    ErrorType.INVALID_JSON: ErrorInfo(
        error_type=ErrorType.INVALID_JSON,
        severity=Priority.HIGH,
        description="JSON file could not be parsed due to invalid syntax",
        common_causes=[
            "Malformed JSON structure",
            "Trailing commas or missing quotes",
            "Manual edits introducing syntax errors"
        ],
        prevention_tips=[
            "Validate JSON using a linter before loading",
            "Avoid manual editing of config files",
            "Use schema-aware JSON editors",
            "Add JSON validation step in pipeline"
        ],
        escalation_threshold=2
    ),

    ErrorType.INVALID_SCHEMA_STRUCTURE: ErrorInfo(
        error_type=ErrorType.INVALID_SCHEMA_STRUCTURE,
        severity=Priority.CRITICAL,
        description="Schema structure is syntactically valid but does not follow required format",
        common_causes=[
            "Missing required schema keys",
            "Incorrect nesting structure",
            "Wrong field types in schema definition",
            "Outdated schema version"
        ],
        prevention_tips=[
            "Validate schema against a formal schema contract",
            "Add automated schema structure checks",
            "Version-control schema updates",
            "Provide schema templates for contributors"
        ],
        escalation_threshold=2
    )
}

class RecoveryAction(Enum):
    RETRY_PROCESSING = "retry_processing"
    ROLLBACK_TO_BACKUP = "rollback_to_backup"
    TRIGGER_MANUAL_REVIEW = "trigger_manual_review"

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

# Recovery action information catalog
RECOVERY_ACTION_CATALOG = {
    RecoveryAction.RETRY_PROCESSING: RecoveryActionInfo(
        action=RecoveryAction.RETRY_PROCESSING,
        description="Retry the failed operation with same parameters",
        priority=Priority.LOW,
        estimated_time_seconds=30,
        prerequisites=[
            "Error is transient",
            "Retry count < max_retries"
            ],
        success_criteria=[
            "Operation completes successfully"
            ],
        rollback_possible=True
    ),

    RecoveryAction.TRIGGER_MANUAL_REVIEW: RecoveryActionInfo(
        action=RecoveryAction.TRIGGER_MANUAL_REVIEW,
        description="Send notification to system administrators",
        priority=Priority.HIGH,
        estimated_time_seconds=5,
        prerequisites=[
            "Error exceeds threshold", 
            "Notification system available"
            ],
        success_criteria=[
            "Notification sent successfully"
            ],
        rollback_possible=False
    ),

    RecoveryAction.ROLLBACK_TO_BACKUP: RecoveryActionInfo(
        action=RecoveryAction.ROLLBACK_TO_BACKUP,
        description="Restore from last known good backup",
        priority=Priority.HIGH,
        estimated_time_seconds=300,
        prerequisites=[
            "Backup available", "Corruption detected"
            ],
        success_criteria=[
            "System restored to working state"
            ],
        rollback_possible=False
    )
}

class AgentType(Enum):
    DATA_COLLECTOR = "DataCollector"
    SCHEMA_VALIDATOR = "SchemaValidator"
    ADMIN_NOTIFICATION_AGENT = 'AdminNotificationAgent'

class ProcessingScale(Enum):
    LOCAL = "local"
    GLOBAL = "global"

@dataclass
class RecoveryDecision:
    priority: Priority
    scale: ProcessingScale
    action: RecoveryAction
    status: ProcessingStatus

# Agent recovery strategy mapping (information only)
AGENT_ERROR_RECOVERY_MAPPING = {
    AgentType.DATA_COLLECTOR: {
        ErrorType.UNSUPPORTED_DATA_TYPE:[
            RecoveryDecision(priority=Priority.CRITICAL, scale=ProcessingScale.LOCAL, 
                             action=RecoveryAction.ROLLBACK_TO_BACKUP, status=ProcessingStatus.PENDING),
            RecoveryDecision(priority=Priority.HIGH, scale=ProcessingScale.GLOBAL, 
                             action=RecoveryAction.TRIGGER_MANUAL_REVIEW, status=ProcessingStatus.PENDING)
        ],
        ErrorType.DATA_PROCESSING_ERROR:[
            RecoveryDecision(priority=Priority.CRITICAL, scale=ProcessingScale.LOCAL, 
                             action=RecoveryAction.ROLLBACK_TO_BACKUP, status=ProcessingStatus.PENDING),
            RecoveryDecision(priority=Priority.HIGH, scale=ProcessingScale.GLOBAL, 
                             action=RecoveryAction.TRIGGER_MANUAL_REVIEW, status=ProcessingStatus.PENDING)
        ]
    },
    AgentType.SCHEMA_VALIDATOR: {
        ErrorType.FILE_NOT_VALID: [
            RecoveryDecision(priority=Priority.CRITICAL, scale=ProcessingScale.LOCAL, 
                             action=RecoveryAction.ROLLBACK_TO_BACKUP, status=ProcessingStatus.PENDING),
            RecoveryDecision(priority=Priority.HIGH, scale=ProcessingScale.GLOBAL, 
                             action=RecoveryAction.TRIGGER_MANUAL_REVIEW, status=ProcessingStatus.PENDING)
        ],
        ErrorType.FILE_NOT_FOUND: [
            RecoveryDecision(priority=Priority.CRITICAL, scale=ProcessingScale.LOCAL, 
                             action=RecoveryAction.ROLLBACK_TO_BACKUP, status=ProcessingStatus.PENDING),
            RecoveryDecision(priority=Priority.HIGH, scale=ProcessingScale.GLOBAL, 
                             action=RecoveryAction.TRIGGER_MANUAL_REVIEW, status=ProcessingStatus.PENDING)
        ],
        ErrorType.INVALID_JSON: [
            RecoveryDecision(priority=Priority.CRITICAL, scale=ProcessingScale.LOCAL, 
                             action=RecoveryAction.ROLLBACK_TO_BACKUP, status=ProcessingStatus.PENDING),
            RecoveryDecision(priority=Priority.HIGH, scale=ProcessingScale.GLOBAL, 
                             action=RecoveryAction.TRIGGER_MANUAL_REVIEW, status=ProcessingStatus.PENDING)
        ],
        ErrorType.FILE_READ_ERROR: [
            RecoveryDecision(priority=Priority.CRITICAL, scale=ProcessingScale.LOCAL, 
                             action=RecoveryAction.ROLLBACK_TO_BACKUP, status=ProcessingStatus.PENDING),
            RecoveryDecision(priority=Priority.HIGH, scale=ProcessingScale.GLOBAL, 
                             action=RecoveryAction.TRIGGER_MANUAL_REVIEW, status=ProcessingStatus.PENDING)
        ],
        ErrorType.MISSING_FIELDS: [
            RecoveryDecision(priority=Priority.CRITICAL, scale=ProcessingScale.LOCAL, 
                             action=RecoveryAction.ROLLBACK_TO_BACKUP, status=ProcessingStatus.PENDING),
            RecoveryDecision(priority=Priority.HIGH, scale=ProcessingScale.GLOBAL, 
                             action=RecoveryAction.TRIGGER_MANUAL_REVIEW, status=ProcessingStatus.PENDING)
        ],
        ErrorType.INVALID_SCHEMA_STRUCTURE: [
            RecoveryDecision(priority=Priority.CRITICAL, scale=ProcessingScale.LOCAL, 
                             action=RecoveryAction.ROLLBACK_TO_BACKUP, status=ProcessingStatus.PENDING),
            RecoveryDecision(priority=Priority.HIGH, scale=ProcessingScale.GLOBAL, 
                             action=RecoveryAction.TRIGGER_MANUAL_REVIEW, status=ProcessingStatus.PENDING)
        ],
        ErrorType.SCHEMA_MISMATCH: [
            RecoveryDecision(priority=Priority.CRITICAL, scale=ProcessingScale.LOCAL, 
                             action=RecoveryAction.ROLLBACK_TO_BACKUP, status=ProcessingStatus.PENDING),
            RecoveryDecision(priority=Priority.HIGH, scale=ProcessingScale.GLOBAL, 
                             action=RecoveryAction.TRIGGER_MANUAL_REVIEW, status=ProcessingStatus.PENDING)
        ],
        ErrorType.UNSUPPORTED_DATA_TYPE: [
            RecoveryDecision(priority=Priority.CRITICAL, scale=ProcessingScale.LOCAL, 
                             action=RecoveryAction.ROLLBACK_TO_BACKUP, status=ProcessingStatus.PENDING),
            RecoveryDecision(priority=Priority.HIGH, scale=ProcessingScale.GLOBAL, 
                             action=RecoveryAction.TRIGGER_MANUAL_REVIEW, status=ProcessingStatus.PENDING)
        ]
    },
}

def get_recovery_actions_for_agent_error(
        agent_type: AgentType, 
        error_type: ErrorType, 
        context: Optional[Dict] = None 
    ) -> List[RecoveryDecision]:  # ✅ Match actual return type
    """Get recovery actions with context consideration"""
    base_actions = AGENT_ERROR_RECOVERY_MAPPING.get(agent_type, {}).get(error_type, [])
    
    if context:
        # Skip retry if retry_count exceeded
        if context.get('retry_count', 0) >= context.get('max_retries', 3):
            return [action for action in base_actions 
                   if action.action != RecoveryAction.RETRY_PROCESSING]  # ✅ Use .action attribute
    
    return base_actions