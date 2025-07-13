from pathlib import Path
from typing import Dict, Any
from loguru import logger

from agents.dataPipelineOrchestrator.data_collector import DataCollector
from agents.dataPipelineOrchestrator.data_loader import DataLoaderAgent
from agents.dataPipelineOrchestrator.data_pipeline_orchestrator_healing_rules import ManualReviewNotifier

class MockNotificationHandler:
    """Mock notification handler for testing"""
    def send_notification(self, recipient: str, subject: str, message: str, priority: str) -> bool:
        print(f"Sending notification to: {recipient}")
        print(f"Subject: {subject}")
        print(f"Priority: {priority}")
        print("Message:")
        print(message)
        return True


class DataPipelineOrchestrator:
    def __init__(self, 
                 dynamic_db_source_dir: str = "database/dynamicDatabase",
                 databaseSchemas_path: str = "database/databaseSchemas.json",
                 annotation_path: str = 'agents/shared_db/DataLoaderAgent/newest/path_annotations.json',
                 default_dir: str = "agents/shared_db"
                 ):
        
        self.logger = logger.bind(class_="DataPipelineOrchestrator")
        self.dynamic_db_source_dir = dynamic_db_source_dir
        self.databaseSchemas_path = databaseSchemas_path
        self.annotation_path = annotation_path
        self.default_dir = Path(default_dir)
        self.output_dir = self.default_dir / "DataPipelineOrchestrator"
        
        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize notification system
        self.notification_handler = MockNotificationHandler()
        self.notifier = ManualReviewNotifier(self.notification_handler, self.output_dir)

    def run_pipeline(self, **kwargs) -> Dict[str, Any]:
        """
        Run the complete data pipeline with proper error handling and notifications
        """
        self.logger.info("🚀 Starting DataPipelineOrchestrator...")
        
        # Phase 1: Data Collection
        collector_result = self._run_data_collector()
        
        # Phase 2: Data Loading (with conditional logic based on Phase 1 result)
        loader_result = self._run_data_loader(collector_result)
        
        # Final pipeline result
        pipeline_result = self._create_pipeline_result(collector_result, loader_result)
        
        self.logger.info("✅ DataPipelineOrchestrator completed")
        return pipeline_result

    def _run_data_collector(self) -> Any:
        """Run Phase 1: DataCollector"""
        self.logger.info("📊 Phase 1: Running DataCollector...")
        
        try:
            collector = DataCollector(self.dynamic_db_source_dir, self.default_dir)
            result = collector.process_all_data()
            
            if result.status == 'success':
                self.logger.info("✅ Phase 1: DataCollector completed successfully")
            else:
                self.logger.warning("⚠️ Phase 1: DataCollector failed")
                self._handle_data_collector_failure(result)
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Phase 1: DataCollector error: {str(e)}")
            # Create error result object
            return self._create_error_result("DataCollector", str(e))

    def _run_data_loader(self, collector_result: Any) -> Any:
        """Run Phase 2: DataLoaderAgent with conditional logic"""
        
        # Determine if we should proceed based on collector result
        should_proceed = self._should_proceed_to_data_loader(collector_result)
        
        if not should_proceed:
            self.logger.info("⏹️ Phase 2: Skipping DataLoaderAgent due to unrecoverable collector failure")
            return None
        
        self.logger.info("📋 Phase 2: Running DataLoaderAgent...")
        
        try:
            loader = DataLoaderAgent(self.databaseSchemas_path, self.annotation_path, self.default_dir)
            result = loader.process_all_data()
            
            if result.status == 'success':
                self.logger.info("✅ Phase 2: DataLoaderAgent completed successfully")
            else:
                self.logger.warning("⚠️ Phase 2: DataLoaderAgent failed")
                self._handle_data_loader_failure(result)
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Phase 2: DataLoaderAgent error: {str(e)}")
            return self._create_error_result("DataLoaderAgent", str(e))

    def _should_proceed_to_data_loader(self, collector_result: Any) -> bool:
        """Determine if we should proceed to data loader based on collector result"""
        
        # If collector was successful, proceed
        if collector_result.status == 'success':
            return True
        
        # If collector failed, check if rollback was successful
        if hasattr(collector_result, 'healing_actions') or hasattr(collector_result, 'details'):
            rollback_success = self.notifier.check_rollback_success(collector_result)
            
            if rollback_success:
                self.logger.info("🔄 Rollback successful - proceeding to DataLoader despite collector failure")
                return True
            else:
                self.logger.warning("❌ Rollback failed - stopping pipeline")
                return False
        
        # If no healing actions info, don't proceed
        return False

    def _handle_data_collector_failure(self, result: Any) -> None:
        """Handle DataCollector failure by sending notification"""
        self.logger.info("📧 Sending notification for DataCollector failure...")
        
        try:
            self.notifier.trigger_manual_review(result)
        except Exception as e:
            self.logger.error(f"Failed to send notification for DataCollector: {str(e)}")

    def _handle_data_loader_failure(self, result: Any) -> None:
        """Handle DataLoaderAgent failure by sending notification"""
        self.logger.info("📧 Sending notification for DataLoaderAgent failure...")
        
        try:
            self.notifier.trigger_manual_review(result)
        except Exception as e:
            self.logger.error(f"Failed to send notification for DataLoaderAgent: {str(e)}")

    def _create_error_result(self, component: str, error_message: str) -> Any:
        """Create standardized error result"""
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
        """Create final pipeline result summary"""
        
        # Determine overall pipeline status
        if (collector_result.status == 'success' and 
            loader_result and loader_result.status == 'success'):
            overall_status = 'success'
        elif (collector_result.status != 'success' and 
              loader_result and loader_result.status == 'success'):
            overall_status = 'partial_success'  # Collector failed but loader succeeded due to rollback
        else:
            overall_status = 'failed'
        
        return {
            'overall_status': overall_status,
            'collector_result': collector_result,
            'loader_result': loader_result,
            'timestamp': self._get_timestamp()
        }

    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()