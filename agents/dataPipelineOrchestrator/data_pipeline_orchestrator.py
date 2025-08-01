from pathlib import Path
from typing import Dict, Any
from loguru import logger

from agents.dataPipelineOrchestrator.data_collector import DataCollector
from agents.dataPipelineOrchestrator.data_loader import DataLoaderAgent
from agents.dataPipelineOrchestrator.data_pipeline_orchestrator_healing_rules import ManualReviewNotifier

class MockNotificationHandler:
    
    """
    Mock notification handler for testing purposes.
    This class simulates email/notification sending without actual external dependencies.
    """

    def send_notification(self, recipient: str, subject: str, message: str, priority: str) -> bool:

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


class DataPipelineOrchestrator:

    """
    Main orchestrator class that coordinates the entire data pipeline process.
    
    This class manages a two-phase data pipeline:
    1. Data Collection Phase: Collects raw data from various sources
    2. Data Loading Phase: Processes and loads data into the target system
    
    The orchestrator includes error handling, rollback mechanisms, and notification systems
    to ensure pipeline reliability and proper error reporting.
    """

    def __init__(self, 
                 dynamic_db_source_dir: str = "database/dynamicDatabase",
                 databaseSchemas_path: str = "database/databaseSchemas.json",
                 annotation_path: str = 'agents/shared_db/DataLoaderAgent/newest/path_annotations.json',
                 default_dir: str = "agents/shared_db"
                 ):
        
        """
        Initialize the DataPipelineOrchestrator with configuration paths.
        
        Args:
            dynamic_db_source_dir: Directory containing dynamic database source files
            databaseSchemas_path: Path to the database schemas JSON file
            annotation_path: Path to the data annotations file used by DataLoaderAgent
            default_dir: Default directory for shared database operations
        """
        
        # Initialize logger with class-specific binding for better log tracking
        self.logger = logger.bind(class_="DataPipelineOrchestrator")

        # Store configuration paths
        self.dynamic_db_source_dir = dynamic_db_source_dir
        self.databaseSchemas_path = databaseSchemas_path
        self.annotation_path = annotation_path
        self.default_dir = Path(default_dir)
        self.output_dir = self.default_dir / "DataPipelineOrchestrator"
        
        # Create output directory if it doesn't exist
        # This ensures we have a place to store pipeline results and logs
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize notification system for error reporting and manual review alerts
        self.notification_handler = MockNotificationHandler()
        self.notifier = ManualReviewNotifier(self.notification_handler, self.output_dir)

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

        self.logger.info("🚀 Starting DataPipelineOrchestrator...")
        
        # Phase 1: Data Collection
        # Collect raw data from various sources
        collector_result = self._run_data_collector()
        
        # Phase 2: Data Loading 
        # Process and load data, but only if Phase 1 was successful or rollback succeeded
        loader_result = self._run_data_loader(collector_result)
        
        # Create comprehensive pipeline result summary
        pipeline_result = self._create_pipeline_result(collector_result, loader_result)
        
        self.logger.info("✅ DataPipelineOrchestrator completed")
        return pipeline_result

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

        self.logger.info("📊 Phase 1: Running DataCollector...")
        
        try:
            # Initialize DataCollector with source directory and output directory
            collector = DataCollector(self.dynamic_db_source_dir, self.default_dir)
            result = collector.process_all_data()
            
            # Check collection result and log appropriate message
            if result.status == 'success':
                self.logger.info("✅ Phase 1: DataCollector completed successfully")
            else:
                self.logger.warning("⚠️ Phase 1: DataCollector failed")
                # Handle failure by triggering manual review notification
                self._handle_data_collector_failure(result)
            
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
        
        if not should_proceed:
            self.logger.info("⏹️ Phase 2: Skipping DataLoaderAgent due to unrecoverable collector failure")
            return None
        
        self.logger.info("📋 Phase 2: Running DataLoaderAgent...")
        
        try:
            # Initialize DataLoaderAgent with schema and annotation paths
            loader = DataLoaderAgent(self.databaseSchemas_path, self.annotation_path, self.default_dir)
            result = loader.process_all_data()
            
            # Check loading result and log appropriate message
            if result.status == 'success':
                self.logger.info("✅ Phase 2: DataLoaderAgent completed successfully")
            else:
                self.logger.warning("⚠️ Phase 2: DataLoaderAgent failed")
                # Handle failure by triggering manual review notification
                self._handle_data_loader_failure(result)
            
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
            self.notifier.trigger_manual_review(result)
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
            self.notifier.trigger_manual_review(result)
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

    def _create_pipeline_result(self, collector_result: Any, loader_result: Any) -> Dict[str, Any]:
        
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
            str: Current timestamp in ISO format (YYYY-MM-DDTHH:MM:SS.microseconds)
        """
        
        from datetime import datetime
        return datetime.now().isoformat()