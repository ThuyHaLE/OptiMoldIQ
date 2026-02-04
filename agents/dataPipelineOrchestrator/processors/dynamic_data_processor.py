# agents/dataPipelineOrchestrator/processors/dynamic_data_processor.py

from agents.dataPipelineOrchestrator.processors.processor_utils import get_source_files, merge_and_process_dfs, process_single_file
from agents.dataPipelineOrchestrator.configs.output_formats import DataProcessingReport, ProcessingStatus, ErrorType

from configs.shared.config_report_format import ConfigReportMixin

import os
from loguru import logger
from datetime import datetime
from typing import Dict
from pathlib import Path
import pandas as pd
import copy
    
class DynamicDataProcessor(ConfigReportMixin):

    DATA_TYPES = {
        "productRecords": {
            "path": "database/dynamicDatabase/monthlyReports_history",
            "name_start": "monthlyReports_",
            "file_extension": ".xlsb",
            "sheet_name": "Sheet1",
            "required_fields": [
                'recordDate', 'workingShift', 'machineNo', 'machineCode', 
                'itemCode', 'itemName', 'colorChanged', 
                'moldChanged', 'machineChanged', 'poNote', 'moldNo', 
                'moldShot', 'moldCavity', 'itemTotalQuantity',
                'itemGoodQuantity', 'itemBlackSpot', 'itemOilDeposit', 
                'itemScratch', 'itemCrack', 'itemSinkMark', 
                'itemShort', 'itemBurst', 'itemBend', 'itemStain', 
                'otherNG', 'plasticResine', 'plasticResineCode',
                'plasticResineLot', 'colorMasterbatch', 'colorMasterbatchCode', 
                'additiveMasterbatch', 'additiveMasterbatchCode'
                ],
            'dtypes': {
                "recordDate": "datetime64[ns]",
                "workingShift": "string", "machineNo": "string",
                "machineCode": "string", "itemCode": "string",
                "itemName": "string", "colorChanged": "string",
                "moldChanged": "string", "machineChanged": "string",
                "poNote": "string", "moldNo": "string",
                "moldShot": "Int64", "moldCavity": "Int64",  
                "itemTotalQuantity": "Int64", "itemGoodQuantity": "Int64",
                "itemBlackSpot": "Int64", "itemOilDeposit": "Int64",
                "itemScratch": "Int64", "itemCrack": "Int64",
                "itemSinkMark": "Int64", "itemShort": "Int64",
                "itemBurst": "Int64", "itemBend": "Int64",
                "itemStain": "Int64", "otherNG": "Int64",
                "plasticResin": "string", "plasticResinCode": "string",
                "plasticResinLot": "string", "colorMasterbatch": "string",
                "colorMasterbatchCode": "string", "additiveMasterbatch": "string",
                "additiveMasterbatchCode": "string"
                }
            },
        "purchaseOrders": {
            "path": "database/dynamicDatabase/purchaseOrders_history",
            "name_start": "purchaseOrder_",
            "file_extension": ".xlsx",
            "sheet_name": "Sheet1",
            "required_fields": [
                'poReceivedDate', 'poNo', 'poETA', 'itemCode', 
                'itemName', 'itemQuantity', 'plasticResinCode', 
                'plasticResin', 'plasticResinQuantity', 
                'colorMasterbatchCode', 'colorMasterbatch', 
                'colorMasterbatchQuantity', 'additiveMasterbatchCode', 
                'additiveMasterbatch', 'additiveMasterbatchQuantity'
                ],
            'dtypes': {
                "poReceivedDate": "datetime64[ns]", "poNo": "string",
                "poETA": "datetime64[ns]", "itemCode": "string",
                "itemName": "string", "itemQuantity": "Int64",
                "plasticResinCode": "string", "plasticResin": "string",
                "plasticResinQuantity": "Float64", "colorMasterbatchCode": "string",
                "colorMasterbatch": "string", "colorMasterbatchQuantity": "Float64",
                "additiveMasterbatchCode": "string", "additiveMasterbatch": "string",
                "additiveMasterbatchQuantity": "Float64"
                }
            }
        }
    
    # Special handling for material code columns
    SPEC_CASES = ['plasticResinCode', 'colorMasterbatchCode', 'additiveMasterbatchCode']

    # Atribute map
    ATTR_MAP = {
        "path": "folder_path",
        "name_start": "name_start",
        "file_extension": "file_extension",
        "sheet_name": "sheet_name",
        "required_fields": "required_fields",
        "dtypes": "dtypes",
    }

    def __init__(self,
                 data_name: str,
                 database_schema: Dict | None = None):
        
        self._capture_init_args()
        self.logger = logger.bind(class_="DynamicDataProcessor")

        self.data_name = data_name

        if not database_schema:
            self.database_schema = {}
            self.logger.debug("database_schema not found.")
        else:
            self.database_schema = copy.deepcopy(database_schema)

        default_schema = self.DATA_TYPES.get(self.data_name, {})
        override_schema = self.database_schema.get(self.data_name, {})
        self.data_schema = {**default_schema,
                            **override_schema}

    def process_data(self) -> DataProcessingReport:
        """
        Process a specific data type (product records or purchase orders).
        """

        # Generate config header
        start_time = datetime.now()
        timestamp_str = start_time.strftime("%Y-%m-%d %H:%M:%S")
        config_header = self._generate_config_report(timestamp_str)

        log_entries = [
            config_header,
            "--Processing Summary--",
            f"⤷ {self.__class__.__name__} results:"
            ]

        try:
            #-----------------------------------------------------------------------------#
            # Q: Does the schema provide sufficient information to process this database? #
            #-----------------------------------------------------------------------------#

            missing_fields = [schema_key for schema_key in self.ATTR_MAP.keys() 
                              if schema_key not in self.data_schema]

            if missing_fields:
                error_msg = (
                    f"Schema for '{self.data_name}' is missing required fields: "
                    f"{missing_fields}"
                )
                log_entries.append(f"  ❌ {error_msg}")

                return self._fail(
                    status=ProcessingStatus.ERROR,
                    error_type=ErrorType.SCHEMA_MISMATCH,
                    msg=error_msg,
                    log_entries="\n".join(log_entries),
                )
            
            #---------------------------------------------#
            # Q: Is the data folder source path provided? #
            #---------------------------------------------#

            for schema_key, attr_name in self.ATTR_MAP.items():
                setattr(self, attr_name, self.data_schema[schema_key])

            if not self.folder_path: # "" or None
                error_msg = f"Source folder path is empty: {self.folder_path}"
                log_entries.append(f"  ❌ {error_msg}")
                return self._fail(
                    status=ProcessingStatus.ERROR, 
                    error_type=ErrorType.FILE_NOT_VALID, 
                    msg=error_msg, 
                    log_entries="\n".join(log_entries))
            
            log_entries.append(f"  ⤷ Data is validated: {self.data_name}")

            #--------------------------------#
            # Q: data source folder existed? #
            #--------------------------------#
            
            if not Path(self.folder_path).exists():
                error_msg = f"Source folder not found: {self.folder_path}"
                log_entries.append(f"  ❌ {error_msg}")

                return self._fail(
                    status=ProcessingStatus.ERROR, 
                    error_type=ErrorType.FILE_NOT_FOUND, 
                    msg=error_msg, 
                    log_entries="\n".join(log_entries))
            
            log_entries.append(f"  ⤷ Source folder verified: {self.folder_path}")
        
            #--------------------------------------------------------------------#
            # Q: Can get and validate source files from the data source folder ? #
            #--------------------------------------------------------------------#

            files_result = get_source_files(self.folder_path, 
                                            self.name_start, 
                                            self.file_extension)
            
            # get_source_files using DataProcessingReport format, 
            # .status only in [ProcessingStatus.ERROR, ProcessingStatus.SUCCESS] 

            if files_result.status != ProcessingStatus.SUCCESS:
                log_entries.append(f"  ❌ {files_result.error_message}")
                
                return self._fail(
                    status=files_result.status, 
                    error_type=files_result.error_type, 
                    msg=files_result.error_message, 
                    log_entries="\n".join(log_entries))
            
            #---------------------------------------#
            # Q: Is there any source file existed?  #
            #---------------------------------------#

            source_file_list = files_result.data
            log_entries.append(f"  ⤷ Found {len(source_file_list)} files to process\n")

            if not source_file_list:
                error_msg = f"There is no any source file existed"
                log_entries.append(f"  ❌ {error_msg}")
                return self._fail(
                    status=ProcessingStatus.SKIP, 
                    error_type=ErrorType.NONE,  
                    msg=error_msg, 
                    log_entries="\n".join(log_entries))
            
            #----------------------------------------------------#
            # Q: Can process and all source files individually ? #
            #----------------------------------------------------#
            
            success_files = [] # Successfully processed dataframes
            failed_files = [] # Files that failed processing

            for idx, file_path in enumerate(source_file_list, 1):
                log_entries.append(f"    [{idx}/{len(source_file_list)}] Processing: {file_path}\n")
                file_result = process_single_file(file_path, self.sheet_name, 
                                                  self.file_extension, self.required_fields)

                # process_single_file using DataProcessingReport format, 
                # .status only in [ProcessingStatus.ERROR, ProcessingStatus.SUCCESS]

                if file_result.status == ProcessingStatus.SUCCESS:
                    success_files.append(file_result)
                    log_entries.append(f"      ✅ Success: {file_path}")
                else:
                    failed_files.append(file_result)
                    log_entries.append(f"      ❌ Failed: {file_path}")

            # Summary of file processing
            log_entries.append(f"  ⤷ Files processed: {len(success_files)}/{len(source_file_list)} successful")

            #----------------------------------------------------------#
            # Q: Is there any source file were processed successfully? #
            #----------------------------------------------------------#
            if not success_files:
                error_msg = f"No files could be processed successfully"
                log_entries.append(f"  ❌ {error_msg}")

                return self._fail(
                    status=ProcessingStatus.ERROR, 
                    error_type=ErrorType.FILE_READ_ERROR, 
                    msg=error_msg, 
                    log_entries="\n".join(log_entries))

            # Determine final status based on processing results
            final_status = ProcessingStatus.SUCCESS
            final_error_type = ErrorType.NONE
            final_error_message = ''

            if failed_files:
                error_msg = f"Partial success: {len(failed_files)} files failed"
                log_entries.append(f"  ⚠️ {error_msg}")
                final_status = ProcessingStatus.PARTIAL_SUCCESS
                final_error_type = ErrorType.FILE_READ_ERROR

                error_details = [f"{f.metadata.get('file_path', 'unknown')}: {f.error_message}" for f in failed_files]
                final_error_message += "\n".join([error_msg, *error_details])

            #-------------------------------------------------#
            # Can merge successfully processed source files ? #
            #-------------------------------------------------#
            merged_dfs = [f.data for f in success_files]
            
            merge_result = merge_and_process_dfs(self.data_name, 
                                                 merged_dfs, 
                                                 self.SPEC_CASES, 
                                                 self.dtypes)

            # merge_and_process_dfs using DataProcessingReport format, 
            # .status only in [ProcessingStatus.ERROR, ProcessingStatus.SUCCESS, 
            # ProcessingStatus.PARTIAL_SUCCESS]

            if merge_result.status != ProcessingStatus.SUCCESS:
                log_entries.append(f"  ❌ {merge_result.error_message}")

                final_status = ProcessingStatus.ERROR
                final_error_type = merge_result.error_type
                final_error_message+=f"\n{merge_result.error_message}"

            else:
                log_entries.append(f"  ✅ Merging results succesfull.")
                log_entries.append(f"    ⤷ Merging {len(merged_dfs)} dataframes...\n")

            records_processed = (
                len(merge_result.data)
                if final_status != ProcessingStatus.ERROR
                and isinstance(merge_result.data, pd.DataFrame)
                else 0
            )
            
            log_entries.append(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {self.data_name} processing completed\n")

            return DataProcessingReport(
                    status=final_status,
                    data=merge_result.data,
                    error_type=final_error_type,
                    error_message=final_error_message,
                    metadata={
                        'data_name': self.data_name,
                        'folder_path': self.folder_path,
                        'success_files_count': len(success_files),
                        'failed_files_count': len(failed_files),
                        'records_processed': records_processed,
                        'log': "\n".join(log_entries)
                        }
                    )

        except Exception as e:
            # Handle unexpected errors during processing
            error_msg = f"Unexpected error in {self.data_name}: {e}"
            log_entries.append(f"  ❌ {error_msg}")

            return self._fail(
                status=ProcessingStatus.ERROR, 
                error_type=ErrorType.DATA_PROCESSING_ERROR, 
                msg=error_msg, 
                log_entries="\n".join(log_entries))

    def _fail(self, status, error_type, msg, log_entries: str):
        return DataProcessingReport(
            status=status,
            data=pd.DataFrame(),
            error_type=error_type,
            error_message=msg,
            metadata={
                "data_name": self.data_name,
                "folder_path": getattr(self, "folder_path", None),
                "log": log_entries
                }
            )