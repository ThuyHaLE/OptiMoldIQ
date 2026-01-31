# agents/dataPipelineOrchestrator/collectors/data_collector.py

from agents.dataPipelineOrchestrator.configs.output_formats import DataProcessingReport, ProcessingStatus, ErrorType

from agents.dataPipelineOrchestrator.processors.dynamic_data_processor import DynamicDataProcessor
from agents.dataPipelineOrchestrator.processors.static_data_processor import StaticDataProcessor

from configs.shared.config_report_format import ConfigReportMixin
from loguru import logger
from datetime import datetime
from typing import Dict, Any
import pandas as pd
import copy

class DataCollector(ConfigReportMixin):

    """
    Collects and processes data from various sources.
    Handles dynamic and static databases from Excel files.
    """

    def __init__(self, 
                 database_type: str,
                 database_schema: Dict | None = None):

        # Capture initialization arguments for reporting
        self._capture_init_args()

        # Initialize logger for this class
        self.logger = logger.bind(class_="DataCollector")
        
        self.database_type = database_type

        if not database_schema:
            self.database_schema = {}
            self.logger.debug("database schema not found.")
        else:
            self.database_schema = copy.deepcopy(database_schema)

    def process_data(self) -> Dict[str, Any]:
        
        class_id = self.__class__.__name__
        self.logger.info(f"{class_id} ...")

        # Generate config header using mixin
        start_time = datetime.now()
        timestamp_str = start_time.strftime("%Y-%m-%d %H:%M:%S")
        config_header = self._generate_config_report(timestamp_str)

        # Initialize log entries
        log_entries = [
            config_header,
            f"--Processing Summary--",
            f"⤷ {class_id} results:"
            ]
        
        results = {}
        success_dbs = [] # Successfully database
        failed_dbs = [] # Database that failed processing
        
        def build_metadata(end_time: datetime) -> Dict[str, Any]:
            """Build metadata for the processing report."""
            return {
                "total_database": len(self.database_schema),
                "successful": len(success_dbs),
                "failed": len(failed_dbs),
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "processing_duration": f"{(end_time - start_time).total_seconds():.2f}s",
                "log": "\n".join(log_entries)
                }

        try:
            
            #--------------------------------#
            # Q: Is database type supported? #
            #--------------------------------#

            if self.database_type == "dynamicDB":
                processor_class = DynamicDataProcessor
            elif self.database_type == "staticDB":
                processor_class = StaticDataProcessor
            else:
                error_msg = (f"Unsupported database_type: '{self.database_type}'. Expected: 'dynamicDB' or 'staticDB'")
                log_entries.append(f"  ❌ {error_msg}")
                self.logger.error(error_msg)
                
                return DataProcessingReport(
                    status=ProcessingStatus.ERROR,
                    data=results,
                    error_type=ErrorType.UNSUPPORTED_DATA_TYPE,
                    error_message=error_msg,
                    metadata=build_metadata(datetime.now())
                )

            #-------------------------------------------------#
            # Q: Can process and all databases individually ? #
            #-------------------------------------------------#

            # Process each database
            for db_name in self.database_schema:
                processor = processor_class(db_name, self.database_schema)
                processor_result = processor.process_data()
                        
                # processor_class using DataProcessingReport format, 
                # .status only in [ProcessingStatus.ERROR, ProcessingStatus.SUCCESS, 
                # ProcessingStatus.PARTIAL_SUCCESS]

                # Store result (DataFrame or empty DataFrame on error)
                results[db_name] = (
                    processor_result.data 
                    if processor_result.status != ProcessingStatus.ERROR 
                       and isinstance(processor_result.data, pd.DataFrame)
                    else pd.DataFrame()
                )
                
                # Track success/failure
                if processor_result.status == ProcessingStatus.SUCCESS:
                    success_dbs.append(processor_result)
                    log_entries.extend([
                        f"      ✅ Success: {db_name}",
                        f"Details: \n{processor_result.metadata.get('log', '')}"
                    ])
                else:
                    failed_dbs.append(processor_result)
                    log_entries.extend([
                        f"      ❌ Failed: {db_name}",
                        f"Details: \n{processor_result.metadata.get('log', '')}"
                    ])

            log_entries.append(
                f"  ⤷ Files processed: {len(success_dbs)}/{len(self.database_schema)} successful"
            )

            #-------------------------------------------------------#
            # Q: Is there any database were processed successfully? #
            #-------------------------------------------------------#
            if not success_dbs:
                error_msg = f"No files could be processed successfully"
                log_entries.append(f"  ❌ {error_msg}")
                self.logger.error(error_msg)

                return DataProcessingReport(
                    status=ProcessingStatus.ERROR,
                    data=results,
                    error_type=ErrorType.DATA_PROCESSING_ERROR,
                    error_message=error_msg,
                    metadata=build_metadata(datetime.now())
                    )
            
            # Handle partial success
            final_status = ProcessingStatus.SUCCESS
            final_error_type = ErrorType.NONE
            final_error_message = ""

            if failed_dbs:
                error_msg = f"Partial success: {len(failed_dbs)} files failed"
                log_entries.append(f"  ⚠️ {error_msg}")
                self.logger.error(error_msg)

                final_status = ProcessingStatus.PARTIAL_SUCCESS
                final_error_type = ErrorType.DATA_PROCESSING_ERROR

                error_details = [f"{f.metadata.get('data_name', 'unknown')}: {f.error_message}" for f in failed_dbs]
                final_error_message = "\n".join([error_msg, *error_details])

            end_time = datetime.now()
            log_entries.append(f"[{end_time.strftime('%Y-%m-%d %H:%M:%S')}] {class_id} completed.")

            self.logger.info("✅ Process finished!!!")

            return DataProcessingReport(
                status=final_status,
                data=results,
                error_type=final_error_type,
                error_message=final_error_message,
                metadata=build_metadata(end_time)
                )
        
        except Exception as e:
            # Handle unexpected errors during processing
            error_msg = f"Unexpected error in {class_id}: {e}"
            log_entries.append(f"  ❌ {error_msg}")
            self.logger.error(error_msg)

            return DataProcessingReport(
                status=ProcessingStatus.ERROR,
                data=results,
                error_type=ErrorType.DATA_PROCESSING_ERROR, 
                error_message=error_msg,
                metadata=build_metadata(datetime.now())
                )