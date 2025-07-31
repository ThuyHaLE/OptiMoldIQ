import pandas as pd
from typing import Dict, List, Tuple, Optional, Any

from loguru import logger
from agents.utils import read_change_log

class ProcessDashboardReports:

    """
    A comprehensive class for processing production tracking data from Excel sheets.

    This class handles multiple aspects of manufacturing data including:
    - Machine quantity mapping and production tracking
    - Mold shot counting and equipment usage
    - Daily production quantity analysis
    - Production status monitoring
    - Material component mapping

    Each method returns structured data suitable for reporting and analysis.
    """

    def __init__(self,
                 excel_file_path: str = None,
                 folder_path: str = 'agents/shared_db/OrderProgressTracker', 
                 target_name: str = "change_log.txt",
                 limit_range: Tuple[Optional[int], Optional[int]] = (0, 30)):

        """
        Initialize the ProcessMockReports with Excel file path.

        Args:
            excel_file_path (str): Path to the Excel file containing production data
            folder_path (str): Folder name includes shared database of OrderProgressTracker
            target_name (str): Name of changelog of OrderProgressTracker
            limit_range (Tuple[Optional[int], Optional[int]]): Range for data slicing (start, end)

        Raises:
            FileNotFoundError: If the Excel file doesn't exist
            ValueError: If the file is not a valid Excel file
        """

        self.logger = logger.bind(class_="ProcessDashboardReports")

        self.excel_file_path = excel_file_path

        # Load production report
        if self.excel_file_path == None:
          self.excel_file_path = read_change_log(folder_path, target_name)
        
        self.limit_range = limit_range

        try:
            self.logger.info("Start load data from source path {}", self.excel_file_path)
            excel_file = pd.ExcelFile(self.excel_file_path)
            self.sheet_names = excel_file.sheet_names
            excel_file.close()  # Properly close the file
        except FileNotFoundError:
            self.logger.error("Excel file not found: {}", self.excel_file_path)
            raise FileNotFoundError(f"Excel file not found: {self.excel_file_path}")
        except Exception as e:
            self.logger.error("Invalid Excel file: {}. Error: {}", self.excel_file_path, str(e))
            raise ValueError(f"Invalid Excel file: {self.excel_file_path}. Error: {str(e)}")

    def _safe_read_excel(self, sheet_name: str) -> pd.DataFrame:

        """
        Safely read Excel sheet with error handling.

        Args:
            sheet_name (str): Name of the sheet to read

        Returns:
            pd.DataFrame: DataFrame containing sheet data

        Raises:
            ValueError: If sheet doesn't exist or cannot be read
        """

        try:
            if sheet_name not in self.sheet_names:
                self.logger.error("Sheet '{}' not found in Excel file", sheet_name)
                raise ValueError(f"Sheet '{sheet_name}' not found in Excel file")

            df = pd.read_excel(self.excel_file_path, sheet_name=sheet_name)
            self.logger.info("Successfully loaded sheet '{}' with {} rows", sheet_name, len(df))
            return df
        except Exception as e:
            self.logger.error("Error reading sheet '{}': {}", sheet_name, str(e))
            raise ValueError(f"Cannot read sheet '{sheet_name}': {str(e)}")

    def _apply_limit_range(self, df_or_list) -> Any:

        """
        Apply limit range to DataFrame or list.

        Args:
            df_or_list: DataFrame or list to slice

        Returns:
            Sliced data
        """

        start, end = self.limit_range
        if start == None:
          start = 0
        if end == None:
          end = len(df_or_list)
        self.logger.info("Apply limit range: {}:{}", start, end)

        return df_or_list[start:end]

    def get_sheet_summary(self) -> Dict[str, Any]:

        """
        Get summary of all available sheets in the Excel file.

        Returns:
            Dict[str, Any]: Summary containing sheet names and their purposes
        """

        return {
            "total_sheets": len(self.sheet_names),
            "sheet_names": self.sheet_names,
            "sheet_details": {
                "productionStatus": {"Description": "Main production status tracking",
                                     "Dataframe review": pd.read_excel(
                                        self.excel_file_path,
                                        sheet_name='productionStatus').head().to_dict()
                                    },
                "materialComponentMap": {"Description": "Material and component mappings",
                                         "Dataframe review": pd.read_excel(
                                            self.excel_file_path,
                                            sheet_name='materialComponentMap').head().to_dict()
                                         },
                "moldShotMap": {"Description": "Mold shot tracking and equipment usage",
                                "Dataframe review": pd.read_excel(
                                    self.excel_file_path,
                                    sheet_name='moldShotMap').head().to_dict()
                                },
                "machineQuantityMap": {"Description": "Machine capacity and quantity mappings",
                                       "Dataframe review": pd.read_excel(
                                           self.excel_file_path,
                                           sheet_name='machineQuantityMap').head().to_dict()
                                       },
                "dayQuantityMap": {"Description": "Daily production quantity tracking",
                                   "Dataframe review": pd.read_excel(
                                       self.excel_file_path,
                                       sheet_name='dayQuantityMap').head().to_dict()
                                   },
                "notWorkingStatus": {"Description": "Non-working time and downtime tracking",
                                     "Dataframe review": pd.read_excel(
                                        self.excel_file_path,
                                        sheet_name='notWorkingStatus').head().to_dict()
                                     },
                "item_invalid_warnings": {"Description": "Data validation warnings for items",
                                          "Dataframe review": pd.read_excel(
                                            self.excel_file_path,
                                            sheet_name='item_invalid_warnings').head().to_dict()
                                          },
                "po_mismatch_warnings": {"Description": "Purchase order mismatch alerts",
                                         "Dataframe review": pd.read_excel(
                                            self.excel_file_path,
                                            sheet_name='po_mismatch_warnings').head().to_dict()
                },
            }
        }

    def process_machine_quantity_map(self) -> List[Dict[str, Any]]:

        """
        Process machine quantity mapping data to show production by machine.

        Groups production data by machine code and extracts machine number and details.
        Each machine entry contains multiple production items with quantities.

        Returns:
            List[Dict[str, Any]]: List of dictionaries with structure:
                [
                    {
                        'index': int,
                        'machineNo': str,  # Format: 'NO.XX'
                        'details': str,    # Machine details/model
                        'items': [
                            {
                                'poItemInfo': str,  # Format: 'PO | ItemCode | ItemName'
                                'moldedQuantity': int
                            }
                        ]
                    }
                ]
        """

        try:
            # Load and prepare data
            df = self._safe_read_excel('machineQuantityMap')

            # Check required columns
            required_cols = ['poNo', 'itemCode', 'itemName', 'machineCode', 'moldedQuantity']
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                self.logger.error("Missing required columns: {}", missing_cols)
                raise ValueError(f"Missing required columns: {missing_cols}")

            # Create poItemInfo
            df['poItemInfo'] = df.apply(
                lambda row: f"{row['poNo']} | {row['itemCode']} | {row['itemName']}",
                axis=1
            )

            # Group by machine and get slice of data
            grouped_data = df.groupby('machineCode')[['poItemInfo', 'moldedQuantity']] \
                .apply(lambda x: x.to_dict(orient='records')).reset_index(name='items')

            # Apply data slice
            grouped_data = self._apply_limit_range(grouped_data)

            # Extract machine number and details from machine code
            machine_parts = grouped_data['machineCode'].str.extract(r'(NO\.\d+)(_.*)')
            grouped_data['machineNo'] = machine_parts[0]
            grouped_data['details'] = machine_parts[1].str.replace('_', '', 1) if not machine_parts[1].isna().all() else ''

            # Fill NaN values
            grouped_data['machineNo'] = grouped_data['machineNo'].fillna(grouped_data['machineCode'])
            grouped_data['details'] = grouped_data['details'].fillna('')

            return grouped_data[['machineNo', 'details', 'items']].reset_index().to_dict(orient="records")

        except Exception as e:
            self.logger.error("Error processing machine quantity map: {}", str(e))
            return []

    def process_mold_shot_map(self) -> List[Dict[str, Any]]:

        """
        Process mold shot mapping data to track shot counts by mold.

        Groups shot count data by mold number and separates mold ID from details.
        Each mold entry contains multiple items with their shot counts.

        Returns:
            List[Dict[str, Any]]: List of dictionaries with structure:
                [
                    {
                        'index': int,
                        'moldNo': str,     # Base mold number
                        'details': str,    # Mold details (e.g., 'M-001')
                        'items': [
                            {
                                'poItemInfo': str,  # Format: 'PO | ItemCode | ItemName'
                                'shotCount': int
                            }
                        ]
                    }
                ]
        """

        def split_mold_code(code: str) -> pd.Series:

            """Split mold code into base number and details."""

            if isinstance(code, str) and '-M' in code:
                idx = code.find('-M')
                return pd.Series([code[:idx], code[idx:].replace('-M', 'M')])
            return pd.Series([code, ''])

        try:
            # Load and prepare data
            df = self._safe_read_excel('moldShotMap')

            # Check required columns
            required_cols = ['poNo', 'itemCode', 'itemName', 'moldNo', 'shotCount']
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                self.logger.error("Missing required columns: {}", missing_cols)
                raise ValueError(f"Missing required columns: {missing_cols}")

            # Create poItemInfo
            df['poItemInfo'] = df.apply(
                lambda row: f"{row['poNo']} | {row['itemCode']} | {row['itemName']}",
                axis=1
            )

            # Group by mold number
            grouped_data = df.groupby(['moldNo'])[['poItemInfo', 'shotCount']] \
                .apply(lambda x: x.to_dict(orient='records')).reset_index(name='items')

            # Split mold code into number and details
            mold_parts = grouped_data['moldNo'].apply(split_mold_code)
            grouped_data['moldNo'] = mold_parts.iloc[:, 0]
            grouped_data['details'] = mold_parts.iloc[:, 1]

            # Apply limit range
            result = self._apply_limit_range(grouped_data[['moldNo', 'details', 'items']].reset_index())

            return result.to_dict(orient="records")

        except Exception as e:
            self.logger.error("Error processing mold shot map: {}", str(e))
            return []

    def process_day_quantity_map(self) -> List[Dict[str, Any]]:

        """
        Process daily quantity mapping to track production by working day.

        Groups production quantities by working day to show daily output.
        Each day entry contains multiple items produced with their quantities.

        Returns:
            List[Dict[str, Any]]: List of dictionaries with structure:
                [
                    {
                        'workingDay': str,  # Format: 'YYYY-MM-DD'
                        'details': [
                            {
                                'poItemInfo': str,     # Format: 'PO | ItemCode | ItemName'
                                'moldedQuantity': int
                            }
                        ]
                    }
                ]
        """

        try:
            # Load and prepare data
            df = self._safe_read_excel('dayQuantityMap')

            # Check required columns
            required_cols = ['poNo', 'itemCode', 'itemName', 'workingDay', 'moldedQuantity']
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                self.logger.error("Missing required columns: {}", missing_cols)
                raise ValueError(f"Missing required columns: {missing_cols}")

            # Create poItemInfo
            df['poItemInfo'] = df.apply(
                lambda row: f"{row['poNo']} | {row['itemCode']} | {row['itemName']}",
                axis=1
            )

            # Group by working day
            result = df.groupby('workingDay')[['poItemInfo', 'moldedQuantity']] \
                .apply(lambda x: x.to_dict(orient='records')).reset_index(name='details')

            # Apply limit range
            result = self._apply_limit_range(result)

            return result.to_dict(orient="records")

        except Exception as e:
            self.logger.error("Error processing day quantity map: {}", str(e))
            return []

    def process_production_status(self) -> List[Dict[str, Any]]:

        """
        Process main production status data with comprehensive tracking information.

        Extracts key production metrics including dates, quantities, status, and equipment history.
        Provides complete overview of production order lifecycle.

        Returns:
            List[Dict[str, Any]]: List of dictionaries with comprehensive production status data
        """

        try:
            # Define columns to extract
            columns = [
                'poReceivedDate', 'poNo', 'itemCode', 'itemName', 'poETA',
                'itemQuantity', 'itemRemain', 'startedDate', 'actualFinishedDate',
                'proStatus', 'etaStatus', 'itemType', 'machineHist', 'moldHist', 'moldCavity',
                'totalMoldShot', 'totalDay', 'totalShift',
                'lastestRecordTime', 'lastestMachineNo', 'lastestMoldNo',
                'warningNotes'
            ]

            # Load and prepare data
            df = self._safe_read_excel('productionStatus')

            # Check which columns exist
            available_columns = [col for col in columns if col in df.columns]
            missing_columns = [col for col in columns if col not in df.columns]

            if missing_columns:
                self.logger.error("Missing required columns: {}", missing_columns)

            # Apply limit range and select available columns
            df = self._apply_limit_range(df)[available_columns].fillna('')

            # Format datetime columns if they exist
            datetime_columns = ['poReceivedDate', 'poETA', 'startedDate', 'actualFinishedDate', 'lastestRecordTime']
            for col in datetime_columns:
                if col in df.columns and not df[col].empty:
                    try:
                        df[col] = pd.to_datetime(df[col], errors='coerce').dt.strftime('%Y-%m-%d')
                        df[col] = df[col].fillna('')
                    except Exception:
                        self.logger.error("Could not format datetime column: {}", col)

            return df.to_dict(orient="records")

        except Exception as e:
            self.logger.error("Error processing production status: {}", str(e))
            return []

    def process_material_component_map(self) -> List[Dict[str, Any]]:

        """
        Process material component mapping to track material usage by item.

        Groups material components (plastic resin, color masterbatch, additive masterbatch)
        by production order and item to show material composition.

        Returns:
            List[Dict[str, Any]]: List of dictionaries with material component data
        """

        try:
            # Load and prepare data
            df = self._safe_read_excel('materialComponentMap')

            # Check required columns
            required_cols = ['poNo', 'itemCode', 'itemName']
            material_cols = ['plasticResinCode', 'colorMasterbatchCode', 'additiveMasterbatchCode']

            missing_required = [col for col in required_cols if col not in df.columns]
            if missing_required:
                self.logger.error("Missing required columns: {}", missing_required)
                raise ValueError(f"Missing required columns: {missing_required}")

            # Check material columns and use available ones
            available_material_cols = [col for col in material_cols if col in df.columns]
            if not available_material_cols:
                self.logger.error("No material component columns found")
                return []

            # Create materialComponentInfo from available columns
            material_info_parts = []
            for col in material_cols:
                if col in df.columns:
                    material_info_parts.append(df[col].fillna(''))
                else:
                    material_info_parts.append(pd.Series([''] * len(df)))

            df['materialComponentInfo'] = material_info_parts[0].astype(str) + ' | ' + \
                                        material_info_parts[1].astype(str) + ' | ' + \
                                        material_info_parts[2].astype(str)

            # Group by PO and item information
            result = df.groupby(['poNo', 'itemCode', 'itemName'])[['materialComponentInfo']] \
                .apply(lambda x: x.to_dict(orient='records')).reset_index(name='details')

            # Apply limit range
            result = self._apply_limit_range(result)

            return result.to_dict(orient="records")

        except Exception as e:
            self.logger.error("Error processing material component map: {}", str(e))
            return []

    def generate_all_reports(self) -> Dict[str, Any]:

        """
        Generate all available reports in a single call.

        Returns:
            Dict[str, Any]: Dictionary containing all processed reports
        """

        try:
            return {
                'sheet_summary': self.get_sheet_summary(),
                'machine_quantity_map': self.process_machine_quantity_map(),
                'mold_shot_map': self.process_mold_shot_map(),
                'day_quantity_map': self.process_day_quantity_map(),
                'production_status': self.process_production_status(),
                'material_component_map': self.process_material_component_map()
            }
        except Exception as e:
            self.logger.error("Error generating all reports: {}", str(e))
            return {
                'error': f"Failed to generate reports: {str(e)}",
                'sheet_summary': self.get_sheet_summary()
            }