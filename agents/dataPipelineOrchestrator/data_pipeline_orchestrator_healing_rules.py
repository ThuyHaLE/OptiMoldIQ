from loguru import logger
from typing import Dict, Optional

# Import healing system constants for error handling and recovery
from configs.recovery.dataPipelineOrchestrator.data_pipeline_orchestrator_configs import AgentExecutionInfo

class ManualReviewNotifier:

    """
    Handles manual review notifications for data pipeline orchestrator.
    
    This class creates and sends notifications when manual review is required
    for failed or problematic agent executions. It formats execution information
    into readable notification messages and saves them to files.
    """

    def __init__(self, notification_handler):

        """
        Initialize the manual review notifier.
        
        Args:
            notification_handler: Handler for sending notifications (email, etc.)
            dest: Destination directory for saving notification files
        """

        self.notification_handler = notification_handler
    
    def trigger_manual_review(self, 
                              execution_info: AgentExecutionInfo, 
                              detail: Optional[Dict] = None
                              ) -> bool:
        
        """
        Trigger manual review notification for failed agent execution.
        
        This method creates a comprehensive notification message containing
        execution details, errors, healing actions, and metadata. It saves
        the notification to a file and sends it via the notification handler.
        
        Args:
            execution_info: Structured information about agent execution
            detail: Additional contextual information (optional)
            
        Returns:
            bool: True if notification was sent successfully, False otherwise
        """

        logger.info("Triggering manual review notification...")

        try:
            # Create notification message with execution details
            agent_id, message = self.create_notification_message(execution_info, detail)

            # Send notification via handler (email, etc.)
            success = self.notification_handler.send_notification(
                recipient="admin@company.com",
                subject=f"Manual Review Required: {agent_id}",
                message=message,
                priority="HIGH"  # High priority for manual review requests
            )

            if success:
                logger.info("Manual review notification sent successfully")
                return True
            else:
                logger.error("Failed to send manual review notification")
                return False

        except Exception as e:
            logger.error(f"Error sending notification: {str(e)}")
            return False

    def create_notification_message(self, 
                                    execution_info: AgentExecutionInfo, 
                                    detail: Optional[Dict] = None) -> str:
        
        """
        Create comprehensive notification message from execution info.
        
        Builds a structured notification message containing all relevant
        information about the failed execution including summary, errors,
        healing actions, and metadata.
        
        Args:
            execution_info: Structured execution information
            detail: Additional contextual details (optional)
            
        Returns:
            tuple: (agent_id, formatted_message)
        """
        
        # Create header with basic agent information
        agent_id, message = self._create_header(execution_info)
        
        # Add execution summary statistics
        message += self._create_summary_section(execution_info)
        
        # Add detailed error information
        message += self._create_error_details_section(execution_info)
        
        # Add healing/recovery actions taken
        message += self._create_healing_actions_section(execution_info)
        
        # Add system metadata (memory, disk usage, etc.)
        message += self._create_metadata_section(execution_info)
        
        # Add additional contextual information if provided
        if detail:
            message += self._create_contextual_info_section(detail)
        
        # Add footer separator
        message += "\n" + "="*80 + "\n"
        
        return agent_id, message
    
    def _create_header(self, execution_info: AgentExecutionInfo) -> str:
        
        """
        Create notification header with basic agent information.
        
        Args:
            execution_info: Agent execution information
            
        Returns:
            tuple: (agent_id, header_string)
        """

        return execution_info.agent_id, f"""
{"="*80}
                    MANUAL REVIEW NOTIFICATION
{"="*80}

Agent ID     : {execution_info.agent_id}
Status       : {execution_info.status.upper()}
Timestamp    : {execution_info.timestamp}

"""

    def _create_summary_section(self, execution_info: AgentExecutionInfo) -> str:
        
        """
        Create summary section with execution statistics.
        
        Shows high-level statistics about the execution including
        success/failure counts and file processing metrics.
        
        Args:
            execution_info: Agent execution information
            
        Returns:
            str: Formatted summary section
        """

        summary = execution_info.summary
        return f"""{"-"*30} SUMMARY {"-"*30}
Total Databases     : {summary.get('total_databases', 'N/A')}
Successful          : {summary.get('successful', 'N/A')}
Failed              : {summary.get('failed', 'N/A')}
Warnings            : {summary.get('warnings', 'N/A')}
Changed Files       : {summary.get('changed_files', 'N/A')}
Files Saved         : {summary.get('files_saved', 'N/A')}

"""

    def _create_error_details_section(self, execution_info: AgentExecutionInfo) -> str:
        
        """
        Create detailed error information section.
        
        Iterates through execution details to find and format error information
        including error types, messages, and recovery actions attempted.
        
        Args:
            execution_info: Agent execution information
            
        Returns:
            str: Formatted error details section
        """

        if not execution_info.details:
            return f"""{"-"*25} ERROR DETAILS {"-"*25}
No error details available.

"""
        
        message = f"""{"-"*25} ERROR DETAILS {"-"*25}
"""
        
        error_count = 0
        for detail in execution_info.details:
            if detail.get("status") == "error":
                error_count += 1
                message += f"""
ERROR #{error_count}:
  Data Type      : {detail.get("data_type", "Unknown")}
  Error Type     : {detail.get("error_type", "Unknown")}
  Error Message  : {detail.get("error_message", "N/A")}
  
  Recovery Actions:"""
                
                recovery_actions = detail.get("recovery_actions", [])
                if recovery_actions:
                    for i, action_tuple in enumerate(recovery_actions, 1):
                        priority, scale, action, status = action_tuple
                        priority_name = self._get_enum_name(priority)
                        scale_value = self._get_enum_value(scale)
                        action_name = self._get_enum_name(action)
                        status_value = self._get_enum_value(status)
                        
                        message += f"""
    {i}. [{priority_name}] {action_name} at {scale_value} → Status: {status_value}"""
                else:
                    message += "\n    No recovery actions available"
                
                message += "\n"
        
        if error_count == 0:
            message += "No errors found in details.\n"
        
        message += "\n"
        return message

    def _create_healing_actions_section(self, execution_info: AgentExecutionInfo) -> str:
        
        """
        Create healing actions section.
        
        Shows all healing/recovery actions that were attempted during
        the execution, including their priority, scale, and status.
        
        Args:
            execution_info: Agent execution information
            
        Returns:
            str: Formatted healing actions section
        """

        if not execution_info.healing_actions:
            return f"""{"-"*22} HEALING ACTIONS {"-"*22}
No healing actions available.

"""
        
        message = f"""{"-"*22} HEALING ACTIONS {"-"*22}
"""
        
        for i, action_tuple in enumerate(execution_info.healing_actions, 1):
            priority, scale, action, status = action_tuple
            priority_name = self._get_enum_name(priority)
            scale_value = self._get_enum_value(scale)
            action_name = self._get_enum_name(action)
            status_value = self._get_enum_value(status)
            
            message += f"{i}. [{priority_name}] {action_name} at {scale_value} → Status: {status_value}\n"
        
        message += "\n"
        return message

    def _create_metadata_section(self, execution_info: AgentExecutionInfo) -> str:
        
        """
        Create metadata section with system information.
        
        Shows technical metadata about the execution including
        processing duration, memory usage, disk usage, and trigger agents.
        
        Args:
            execution_info: Agent execution information
            
        Returns:
            str: Formatted metadata section
        """

        if not execution_info.metadata:
            return f"""{"-"*26} METADATA {"-"*26}
No metadata available.

"""
        
        metadata = execution_info.metadata
        memory = metadata.get("memory_usage", {})
        disk = metadata.get("disk_usage", {})
        
        return f"""{"-"*26} METADATA {"-"*26}
Duration (s)        : {metadata.get('processing_duration_seconds', 'N/A')}
Memory Usage (MB)   : {memory.get('memory_mb', 'N/A')} ({memory.get('memory_percent', 'N/A')}%)
Disk Output (MB)    : {disk.get('output_directory_mb', 'N/A')}
Disk Free Space (MB): {disk.get('available_space_mb', 'N/A')}
Trigger Agents      : {', '.join(execution_info.trigger_agents) if execution_info.trigger_agents else 'N/A'}

"""

    def _create_contextual_info_section(self, detail: Dict) -> str:
        
        """
        Create contextual information section.
        
        Adds additional context information that was passed as detail parameter.
        This provides extra information beyond the standard execution info.
        
        Args:
            detail: Dictionary containing additional contextual information
            
        Returns:
            str: Formatted contextual info section
        """

        return f"""{"-"*22} CONTEXTUAL INFO {"-"*22}
Data Type        : {detail.get('data_type', 'N/A')}
Error Type       : {detail.get('error_type', 'N/A')}
Error Message    : {detail.get('error_message', 'N/A')}
Files Processed  : {detail.get('files_processed', 'N/A')}
Records Processed: {detail.get('records_processed', 'N/A')}

"""

    def _get_enum_name(self, enum_value) -> str:
        
        """
        Safely extract enum name from enum value.
        
        Handles various enum formats and provides fallback for non-enum values.
        
        Args:
            enum_value: Enum value or other object
            
        Returns:
            str: Enum name or string representation
        """

        try:
            if hasattr(enum_value, 'name'):
                return enum_value.name
            return str(enum_value)
        except:
            return str(enum_value)
    
    def _get_enum_value(self, enum_value) -> str:
        
        """
        Safely extract enum value from enum object.
        
        Handles various enum formats and provides fallback for non-enum values.
        
        Args:
            enum_value: Enum value or other object
            
        Returns:
            str: Enum value or string representation
        """

        try:
            if hasattr(enum_value, 'value'):
                return str(enum_value.value)
            return str(enum_value)
        except:
            return str(enum_value)

    def check_rollback_success(self, execution_info: AgentExecutionInfo) -> bool:

        """
        Check if ROLLBACK_TO_BACKUP action was successful.
        
        Searches through healing actions and recovery actions to find
        any successful rollback operations. This is important for
        determining if the system was able to recover from failures.
        
        Args:
            execution_info: Agent execution information
            
        Returns:
            bool: True if successful rollback found, False otherwise
        """

        # Check in healing_actions
        if execution_info.healing_actions:
            for action_tuple in execution_info.healing_actions:
                priority, scale, action, status = action_tuple
                if (self._is_rollback_action(action) and 
                    self._is_success_status(status)):
                    logger.info("Found successful ROLLBACK_TO_BACKUP in healing_actions")
                    return True
        
        # Check in details recovery_actions
        if execution_info.details:
            for detail in execution_info.details:
                recovery_actions = detail.get("recovery_actions", [])
                for action_tuple in recovery_actions:
                    priority, scale, action, status = action_tuple
                    if (self._is_rollback_action(action) and 
                        self._is_success_status(status)):
                        logger.info("Found successful ROLLBACK_TO_BACKUP in recovery_actions")
                        return True
        
        logger.info("No successful ROLLBACK_TO_BACKUP found")
        return False
    
    def _is_rollback_action(self, action) -> bool:
        
        """
        Check if action is a rollback to backup action.
        
        Handles different enum formats and string representations
        to identify rollback actions.
        
        Args:
            action: Action enum or string
            
        Returns:
            bool: True if action is rollback, False otherwise
        """

        try:
            if hasattr(action, 'value'):
                return action.value == 'rollback_to_backup'
            elif hasattr(action, 'name'):
                return action.name == 'ROLLBACK_TO_BACKUP'
            else:
                return str(action) == 'rollback_to_backup'
        except:
            return False
    
    def _is_success_status(self, status) -> bool:
        
        """
        Check if status indicates successful execution.
        
        Handles different enum formats and string representations
        to identify success status.
        
        Args:
            status: Status enum or string
            
        Returns:
            bool: True if status is success, False otherwise
        """
        
        try:
            if hasattr(status, 'value'):
                return status.value == 'success'
            elif hasattr(status, 'name'):
                return status.name == 'SUCCESS'
            else:
                return str(status) == 'success'
        except:
            return False