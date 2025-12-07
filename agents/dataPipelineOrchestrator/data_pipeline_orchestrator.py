from pathlib import Path
from typing import Dict, Any
from loguru import logger
from datetime import datetime
import shutil
import os

from agents.utils import ConfigReportMixin
from configs.shared.shared_source_config import SharedSourceConfig

from agents.dataPipelineOrchestrator.data_collector import DataCollector
from agents.dataPipelineOrchestrator.data_loader import DataLoaderAgent
from agents.dataPipelineOrchestrator.data_pipeline_orchestrator_healing_rules import ManualReviewNotifier
from agents.autoPlanner.reportFormatters.dict_based_report_generator import DictBasedReportGenerator

class MockNotificationHandler:
    
    """
    Mock notification handler for testing purposes.
    This class simulates email/notification sending without actual external dependencies.
    """

    def send_notification(self, 
                          recipient: str, 
                          subject: str, 
                          message: str, 
                          priority: str) -> bool:

        """
        Simulate sending a notification by printing to console.
        
        Args:
            recipient: Email address or identifier of the notification recipient
            subject: Subject line of the notification
            message: Main content of the notification
            priority: Priority level (e.g., 'high', 'medium', 'low')
            
        Returns:
            bool: Always returns True to simulate successful notification
        """

        logger.info("Sending notification to: {}", recipient)
        logger.info("Subject: {}", subject)
        logger.info("Priority: {}", priority)
        logger.info("Message:\n{}", message)

        return True

class DataPipelineOrchestrator(ConfigReportMixin):

    """
    Main orchestrator class that coordinates the entire data pipeline process.
    
    This class manages a two-phase data pipeline:
    1. Data Collection Phase: Collects raw data from various sources
    2. Data Loading Phase: Processes and loads data into the target system
    
    The orchestrator includes error handling, rollback mechanisms, and notification systems
    to ensure pipeline reliability and proper error reporting.
    """

    # Define requirements
    REQUIRED_FIELDS = {
        'dynamic_db_dir': str,
        'databaseSchemas_path': str,
        'annotation_path': str,
        'data_pipeline_dir': str
    }
    
    def __init__(self, config: SharedSourceConfig):
        
        """
        Initialize the DataPipelineOrchestrator.
        
        Args:
            config: SharedSourceConfig containing processing parameters
            Including:
                - dynamic_db_dir: Directory containing dynamic database source files
                - databaseSchemas_path: Path to the database schemas JSON file
                - annotation_path: Path to the data annotations file used by DataLoaderAgent
                - data_pipeline_dir: Default directory for shared database operations
        """
        
        self._capture_init_args()

        # Initialize logger with class-specific binding for better log tracking
        self.logger = logger.bind(class_="DataPipelineOrchestrator")

        # Validate required configs
        is_valid, errors = config.validate_requirements(self.REQUIRED_FIELDS)
        if not is_valid:
            raise ValueError(
                f"{self.__class__.__name__} config validation failed:\n" +
                "\n".join(f"  - {e}" for e in errors)
            )
        self.logger.info("✓ Validation for config requirements: PASSED!")
        self.config = config

        # Set up directory paths
        self.output_dir = Path(self.config.data_pipeline_dir)
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
    
        # Initialize notification system for error reporting and manual review alerts
        self.notification_handler = MockNotificationHandler()
        self.notifier = ManualReviewNotifier(self.notification_handler)
        self.report_collection = {}

    def save_report(self) -> None:
        
        """Save the report to a file and return the filename"""

        timestamp_now = datetime.now()
        timestamp_str = timestamp_now.strftime("%Y-%m-%d %H:%M:%S")
        timestamp_file = timestamp_now.strftime("%Y%m%d_%H%M")
        log_entries = [f"[{timestamp_str}] Saving new version...\n"]

        newest_dir = self.output_dir / "newest"
        newest_dir.mkdir(parents=True, exist_ok=True)
        historical_dir = self.output_dir / "historical_db"
        historical_dir.mkdir(parents=True, exist_ok=True)

        # Move old files to historical_db
        for f in newest_dir.iterdir():
            if f.is_file():
                try:
                    dest = historical_dir / f.name
                    shutil.move(str(f), dest)
                    log_entries.append(f"  ⤷ Moved old file: {f.name} → historical_db/{f.name}\n")
                    self.logger.info("Moved old file {} to historical_db as {}", f.name, dest.name)
                except Exception as e:
                    self.logger.error("Failed to move file {}: {}", f.name, e)
                    raise OSError(f"Failed to move file {f.name}: {e}")

        # Save single phase reports        
        for agent_id, info in self.report_collection.items():
            for prefix_name, message in info.items():
                # Create timestamped output file path
                filename = f"{timestamp_file}_{agent_id}_{prefix_name}.txt"
                output_path = Path(newest_dir / filename)

                try:
                    # Convert message to string if it's not already
                    if isinstance(message, str):
                        content = message
                    else:
                        reporter = DictBasedReportGenerator(use_colors=False)
                        content = "\n".join(reporter.export_report(
                            message, 
                            title = f"{agent_id} - {prefix_name} Report"))
                    
                    with open(output_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    log_entries.append(f"  ⤷ Saved new file: {output_path}\n")
                    self.logger.info("Saved new file: {}", output_path)
                except Exception as e:
                    self.logger.error("Failed to save file {}: {}", output_path, e)
                    raise OSError(f"Failed to save file {output_path}: {e}")
        
        return "".join(log_entries)
    
    def run_pipeline(self, **kwargs) -> Dict[str, Any]:
        
        """
        Execute the complete data pipeline with proper error handling and notifications.
        
        This is the main entry point that orchestrates the entire pipeline:
        1. Runs DataCollector (Phase 1)
        2. Conditionally runs DataLoaderAgent (Phase 2) based on Phase 1 results
        3. Handles errors and sends notifications as needed
        4. Returns comprehensive pipeline results
        
        Args:
            **kwargs: Additional parameters that can be passed to pipeline components
            
        Returns:
            Dict[str, Any]: Complete pipeline execution results including:
                - overall_status: 'success', 'partial_success', or 'failed'
                - collector_result: Results from the data collection phase
                - loader_result: Results from the data loading phase
                - timestamp: Pipeline execution timestamp
        """

        agent_id = "DataPipelineOrchestrator"
        self.logger.info("🚀 Starting {}...", agent_id)

        # Generate config header using mixin
        timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        config_header = self._generate_config_report(timestamp_str,
                                                     required_only=True)

        pipeline_log_lines = [config_header]
        pipeline_log_lines.append(f"--Processing Summary--\n")
        pipeline_log_lines.append(f"⤷ {self.__class__.__name__} results:\n")
        
        # Phase 1: Data Collection
        # Collect raw data from various sources
        collector_result = self._run_data_collector()
        collector_log = collector_result.metadata['log_entries']

        # Phase 2: Data Loading 
        # Process and load data, but only if Phase 1 was successful or rollback succeeded
        loader_result = self._run_data_loader(collector_result)
        loader_log = loader_result.metadata['log_entries']

        # Create comprehensive pipeline result summary
        pipeline_result = self._create_pipeline_result(collector_result, loader_result)

        self.logger.info("✅ {} completed", agent_id)

        final_report = {
            'Agent ID' : agent_id,
            'Timestamp': self._get_timestamp(),
            'Content'  : pipeline_result
            }
        
        self.report_collection[agent_id] = {'final_report': final_report}
        
        output_exporting_log = self.save_report()
        pipeline_log_lines.append(f"{output_exporting_log}\n")

        pipeline_log_lines.append("--Details--\n")
        pipeline_log_lines.append(f"⤷ Phase 1: Data Collection\n")
        pipeline_log_lines.append(f"{collector_log}\n")
        pipeline_log_lines.append(f"⤷ Phase 2: Data Loading\n")
        pipeline_log_lines.append(f"{loader_log}\n")

        pipeline_log_str = "\n".join(pipeline_log_lines)
        
        try:
            log_path = self.output_dir / "change_log.txt"
            with open(log_path, "a", encoding="utf-8") as log_file:
                log_file.write(pipeline_log_str)
            self.logger.info("✓ Updated and saved change log: {}", log_path)
        except Exception as e:
            self.logger.error("✗ Failed to save change log {}: {}", log_path, e)

        self.logger.info("✅ All reports saved successfully")

        return pipeline_result, pipeline_log_str

    def _run_data_collector(self) -> Any:
        
        """
        Execute Phase 1: DataCollector to gather raw data from sources.
        
        This method:
        1. Initializes the DataCollector with configured source directory
        2. Processes all available data sources
        3. Handles any errors that occur during collection
        4. Triggers notifications if collection fails
        
        Returns:
            Any: DataCollector result object with status and details
        """

        agent_id = 'DataCollector'
        self.logger.info("📊 Phase 1: Running {}...", agent_id)
        
        try:
            # Initialize DataCollector with source directory and output directory
            collector = DataCollector(config = self.config)
            result = collector.process_all_data()

            # Check collection result and log appropriate message
            if result.status == 'success':
                self.logger.info("✅ Phase 1: {} completed successfully", agent_id)
                success_report = {
                    'Agent ID' : agent_id,
                    'Timestamp': self._get_timestamp(),
                    'Content'  : result
                    }
                self.report_collection[agent_id] = {'success_report': success_report}
            else:
                self.logger.warning("⚠️ Phase 1: {} failed", agent_id)
                # Handle failure by triggering manual review notification
                self.report_collection[agent_id] = {
                    'manual_review_notification': self._handle_data_collector_failure(result)}

            return result
            
        except Exception as e:
            # Handle unexpected errors during data collection
            self.logger.error(f"❌ Phase 1: DataCollector error: {str(e)}")
            # Create standardized error result object
            return self._create_error_result("DataCollector", str(e))

    def _run_data_loader(self, collector_result: Any) -> Any:
        
        """
        Execute Phase 2: DataLoaderAgent to process and load collected data.
        
        This method includes conditional logic that determines whether to proceed
        with data loading based on the collector results. It will proceed if:
        1. Data collection was successful, OR
        2. Data collection failed but rollback was successful
        
        Args:
            collector_result: Results from the data collection phase
            
        Returns:
            Any: DataLoaderAgent result object or None if skipped
        """
        
        # Determine if we should proceed based on collector result
        should_proceed = self._should_proceed_to_data_loader(collector_result)
        agent_id = 'DataLoaderAgent'
        
        if not should_proceed:
            self.logger.info("⏹️ Phase 2: Skipping {} due to unrecoverable collector failure", agent_id)
            return None
        
        self.logger.info("📋 Phase 2: Running {}...", agent_id)
        
        try:
            # Initialize DataLoaderAgent with schema and annotation paths
            loader = DataLoaderAgent(config = self.config)
            result = loader.process_all_data()
            
            # Check loading result and log appropriate message
            if result.status == 'success':
                self.logger.info("✅ Phase 2: {} completed successfully", agent_id)
                success_report = {
                    'Agent ID' : agent_id,
                    'Timestamp': self._get_timestamp(),
                    'Content'  : result
                    }
                self.report_collection[agent_id] = {'success_report': success_report}
            else:
                self.logger.warning("⚠️ Phase 2: {} failed", agent_id)
                # Handle failure by triggering manual review notification
                self.report_collection[agent_id] = {
                    'manual_review_notification': self._handle_data_loader_failure(result)}
            
            return result
            
        except Exception as e:
            # Handle unexpected errors during data loading
            self.logger.error(f"❌ Phase 2: DataLoaderAgent error: {str(e)}")
            return self._create_error_result("DataLoaderAgent", str(e))

    def _should_proceed_to_data_loader(self, collector_result: Any) -> bool:
        
        """
        Determine whether to proceed with data loading based on collector results.
        
        Decision logic:
        1. If collector was successful → proceed
        2. If collector failed but rollback was successful → proceed
        3. If collector failed and no rollback info → don't proceed
        4. If collector failed and rollback failed → don't proceed
        
        Args:
            collector_result: Results from the data collection phase
            
        Returns:
            bool: True if should proceed to data loading, False otherwise
        """
        
        # If collector was successful, always proceed
        if collector_result.status == 'success':
            return True
        
        # If collector failed, check if rollback healing actions were successful
        if hasattr(collector_result, 'healing_actions') or hasattr(collector_result, 'details'):
            rollback_success = self.notifier.check_rollback_success(collector_result)
            
            if rollback_success:
                self.logger.info("🔄 Rollback successful - proceeding to DataLoader despite collector failure")
                return True
            else:
                self.logger.warning("❌ Rollback failed - stopping pipeline")
                return False
        
        # If no healing actions info available, don't proceed
        return False

    def _handle_data_collector_failure(self, result: Any) -> None:
        
        """
        Handle DataCollector failure by sending notification for manual review.
        
        This method triggers the notification system to alert administrators
        about data collection failures that require manual intervention.
        
        Args:
            result: DataCollector result object containing failure details
        """

        self.logger.info("📧 Sending notification for DataCollector failure...")
        
        try:
            # Trigger manual review notification with failure details
            _, message = self.notifier.create_notification_message(result)
            #self.notifier.trigger_manual_review(result)
            return message
        
        except Exception as e:
            # Log if notification sending itself fails
            self.logger.error(f"Failed to send notification for DataCollector: {str(e)}")

    def _handle_data_loader_failure(self, result: Any) -> None:
        
        """
        Handle DataLoaderAgent failure by sending notification for manual review.
        
        This method triggers the notification system to alert administrators
        about data loading failures that require manual intervention.
        
        Args:
            result: DataLoaderAgent result object containing failure details
        """

        self.logger.info("📧 Sending notification for DataLoaderAgent failure...")
        
        try:
            # Trigger manual review notification with failure details
            _, message = self.notifier.create_notification_message(result)
            #self.notifier.trigger_manual_review(result)
            return message
        except Exception as e:
            # Log if notification sending itself fails
            self.logger.error(f"Failed to send notification for DataLoaderAgent: {str(e)}")

    def _create_error_result(self, component: str, error_message: str) -> Any:
        
        """
        Create a standardized error result object for consistent error handling.
        
        This method creates a uniform error structure that can be used throughout
        the pipeline for consistent error reporting and processing.
        
        Args:
            component: Name of the component that failed (e.g., 'DataCollector')
            error_message: Description of the error that occurred
            
        Returns:
            Any: Standardized error result object with status, component, and error details
        """

        from dataclasses import dataclass
        
        @dataclass
        class ErrorResult:
            status: str
            component: str
            error_message: str
            
        return ErrorResult(
            status='error',
            component=component,
            error_message=error_message
        )

    def _create_pipeline_result(self, 
                                collector_result: Any, 
                                loader_result: Any) -> Dict[str, Any]:
        
        """
        Create comprehensive pipeline result summary from individual phase results.
        
        This method analyzes results from both phases and determines the overall
        pipeline status based on the following logic:
        - 'success': Both phases succeeded
        - 'partial_success': Collector failed but loader succeeded (due to rollback)
        - 'failed': Either phase failed without recovery
        
        Args:
            collector_result: Results from the data collection phase
            loader_result: Results from the data loading phase (can be None)
            
        Returns:
            Dict[str, Any]: Complete pipeline result summary containing:
                - overall_status: Overall pipeline execution status
                - collector_result: Detailed collector results
                - loader_result: Detailed loader results
                - timestamp: Pipeline execution timestamp
        """
        
        # Determine overall pipeline status based on phase results
        if (collector_result.status == 'success' and 
            loader_result and loader_result.status == 'success'):
            overall_status = 'success'
        elif (collector_result.status != 'success' and 
              loader_result and loader_result.status == 'success'):
            # Collector failed but loader succeeded due to successful rollback
            overall_status = 'partial_success'
        else:
            overall_status = 'failed'
        
        return {
            'overall_status': overall_status,
            'collector_result': collector_result,
            'loader_result': loader_result,
            'timestamp': self._get_timestamp()
        }

    def _get_timestamp(self) -> str:
        
        """
        Get current timestamp in ISO format for pipeline result tracking.
        
        Returns:
            str: Current timestamp in ISO format (YYYY-MM-DD HH:MM:SS)
        """
        
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")