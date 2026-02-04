# agents/dataPipelineOrchestrator/processors/static_data_processor.py

from agents.dataPipelineOrchestrator.processors.processor_utils import process_static_database
from agents.dataPipelineOrchestrator.configs.output_formats import DataProcessingReport, ProcessingStatus, ErrorType

from pathlib import Path
from loguru import logger
from datetime import datetime
from typing import Dict
import pandas as pd
import copy
from configs.shared.config_report_format import ConfigReportMixin

class StaticDataProcessor(ConfigReportMixin):

    DATA_TYPES = {
        "itemCompositionSummary": {
            "path": "database/staticDatabase/itemCompositionSummary.xlsx",
            "dtypes": {
                "itemCode": "string",
                "itemName": "string",
                "plasticResinCode": "string",
                "plasticResin": "string",
                "plasticResinQuantity": "Float64",
                "colorMasterbatchCode": "string",
                "colorMasterbatch": "string",
                "colorMasterbatchQuantity": "Float64",
                "additiveMasterbatchCode": "string",
                "additiveMasterbatch": "string",
                "additiveMasterbatchQuantity": "Float64"
            }
        },
        "itemInfo": {
            "path": "database/staticDatabase/itemInfo.xlsx",
            "dtypes": {
                "itemCode": "string",
                "itemName": "string"
            }
        },
        "machineInfo": {
            "path": "database/staticDatabase/machineInfo.xlsx",
            "dtypes": {
                "machineNo": "string",
                "machineCode": "string",
                "machineName": "string",
                "manufacturerName": "string",
                "machineTonnage": "Int64",
                "changedTime": "Int64",
                "layoutStartDate": "datetime64[ns]",
                "layoutEndDate": "datetime64[ns]",
                "previousMachineCode": "string"
            }
        },
        "moldInfo": {
            "path": "database/staticDatabase/moldInfo.xlsx",
            "dtypes": {
                "moldNo": "string",
                "moldName": "string",
                "moldCavityStandard": "Int64",
                "moldSettingCycle": "Int64",
                "machineTonnage": "string",
                "acquisitionDate": "datetime64[ns]",
                "itemsWeight": "Float64",
                "runnerWeight": "Float64"
            }
        },
        "moldSpecificationSummary": {
            "path": "database/staticDatabase/moldSpecificationSummary.xlsx",
            "dtypes": {
                "itemCode": "string",
                "itemName": "string",
                "itemType": "string",
                "moldNum": "Int64",
                "moldList": "string"
            }
        },
        "resinInfo": {
            "path": "database/staticDatabase/resineInfo.xlsx",
            "dtypes": {
                "resinCode": "string",
                "resinName": "string",
                "resinType": "string",
                "colorType": "string"
            }
        }
    }

    # Special handling for material code columns
    SPEC_CASES = ['plasticResinCode', 'colorMasterbatchCode', 'additiveMasterbatchCode']

    # Atribute map
    ATTR_MAP = {
        "path": "path",
        "dtypes": "dtypes"
    }

    def __init__(self,
                 data_name: str,
                 database_schema: Dict | None = None):
        
        self._capture_init_args()
        self.logger = logger.bind(class_="StaticDataProcessor")
        
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
        Process a single database with comprehensive error handling and logging.
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
                error_msg = (f"Schema for '{self.data_name}' is missing required fields: {missing_fields}")
                log_entries.append(f"  ❌ {error_msg}")

                return self._fail(
                    error_type=ErrorType.SCHEMA_MISMATCH,
                    msg=error_msg,
                    log_entries="\n".join(log_entries),
                )
            
            #--------------------------------------#
            # Q: Is the data source path provided? #
            #--------------------------------------#
            
            for schema_key, attr_name in self.ATTR_MAP.items():
                setattr(self, attr_name, self.data_schema[schema_key])

            if not self.path: # "" or None
                error_msg = f"Source file path is empty: {self.path}"
                log_entries.append(f"  ❌ {error_msg}")
                return self._fail(
                    error_type=ErrorType.FILE_NOT_VALID, 
                    msg=error_msg, 
                    log_entries="\n".join(log_entries))
    
            log_entries.append(f"  ⤷ Data is validated: {self.data_name}")
            
            #-------------------------------------------------------------------------#
            # Q: Is the file extension supported? (Currently only .xlsx is supported) #
            #-------------------------------------------------------------------------#

            file_extension = Path(self.path).suffix.lower()
            if file_extension != '.xlsx':
                error_msg = f"Unsupported file extension: {file_extension}"
                log_entries.append(f"  ❌ {error_msg}")
                
                return self._fail(
                    error_type=ErrorType.UNSUPPORTED_DATA_TYPE, 
                    msg=error_msg, 
                    log_entries="\n".join(log_entries))
            
            #------------------------------------------------#
            # Q: Does the file path exist on the filesystem? #
            #------------------------------------------------#

            if not Path(self.path).exists():
                error_msg = f"File path not found: {self.path}"
                log_entries.append(f"  ❌ {error_msg}")

                return self._fail(
                    error_type=ErrorType.FILE_NOT_FOUND, 
                    msg=error_msg, 
                    log_entries="\n".join(log_entries))
            
            log_entries.append(f"  ⤷ Source file verified: {self.path}")

            #---------------------------------------#
            # Q: Is the file at this path loadable? #
            #---------------------------------------#

            file_result = process_static_database(
                self.path, self.data_name, 
                self.SPEC_CASES, self.dtypes)
            
            # process_static_database using DataProcessingReport format, 
            # .status only in [ProcessingStatus.ERROR, ProcessingStatus.SUCCESS, 
            # ProcessingStatus.PARTIAL_SUCCESS]

            if file_result.status != ProcessingStatus.SUCCESS:
                log_entries.append(f"  ❌ {file_result.error_message}")
                return self._fail(
                    error_type=file_result.error_type, 
                    msg=file_result.error_message, 
                    log_entries="\n".join(log_entries))
            
            log_entries.append(f"  ✅ Processing data succesfull.")

            records_processed = (
                len(file_result.data)
                if file_result.status != ProcessingStatus.ERROR
                and isinstance(file_result.data, pd.DataFrame)
                else 0
            )

            log_entries.append(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {self.data_name} processing completed\n")

            return DataProcessingReport(
                    status=ProcessingStatus.SUCCESS,
                    data=file_result.data,
                    error_type=ErrorType.NONE,
                    error_message="",
                    metadata={
                        'data_name': self.data_name,
                        "file_path": self.path,
                        'records_processed': records_processed,
                        'log': "\n".join(log_entries)
                        }
                    )
        
        except Exception as e:
            # Handle unexpected errors during processing
            error_msg = f"Unexpected error in {self.data_name}: {e}"
            log_entries.append(f"  ❌ {error_msg}")

            return self._fail(
                error_type=ErrorType.DATA_PROCESSING_ERROR, 
                msg=error_msg, 
                log_entries="\n".join(log_entries))

    def _fail(self, error_type, msg, log_entries: str):
        return DataProcessingReport(
            status=ProcessingStatus.ERROR,
            data=pd.DataFrame(),
            error_type=error_type,
            error_message=msg,
            metadata={
                "data_name": self.data_name,
                "file_path": getattr(self, "path", None),
                "log": log_entries
            }
        )