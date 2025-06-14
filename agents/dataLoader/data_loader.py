import pandas as pd
from loguru import logger
from agents.dashboardBuilder.visualize_data.decorators import validate_init_dataframes
from agents.utils import save_output_with_versioning
from pathlib import Path

@validate_init_dataframes({
    "productRecords_df": [
            'machineNo', 'itemName', 'itemTotalQuantity', 'itemGoodQuantity',
            'recordDate', 'workingShift', 'moldNo', 'moldShot'
        ],
    "moldInfo_df": ['moldNo', 'moldCavityStandard', 'moldSettingCycle']
})
class DataLoaderAgent:
    def __init__(self, productRecords_path: str,
                 sheet_name=None,
                 default_dir: str = "agents/shared_db"
                 ):
        self.moldInfo_df = pd.read_excel("database/staticDatabase/moldInfo.xlsx")
        self.productRecords_df = self._check_ext_and_load_data(productRecords_path, sheet_name)

        self.default_dir = Path(default_dir)
        self.output_dir = self.default_dir / "DataLoaderAgent"

        self.logger = logger.bind(class_="DataLoaderAgent")
        self.filename_prefix = "productRecords"

        save_output_with_versioning({"productRecords": self.productRecords_df,
                                     "moldInfo": self.moldInfo_df}, self.output_dir,
                                    self.filename_prefix, file_format='xlsx')

    def _check_ext_and_load_data(self, file_path,
                                 sheet_name=None,
                                 allowed_extensions=['.xlsx', '.xls', '.xlsb', '.csv']
                                 ):
        file_extension = Path(file_path).suffix.lower()
        if file_extension in allowed_extensions:
            if file_extension == '.csv':
                return pd.read_csv(file_path)
            else:
                if sheet_name is not None:
                    logger.info(
                        "Read file '{}', sheet '{}' in {}",
                        file_path, sheet_name, pd.ExcelFile(file_path).sheet_names
                    )
                    return pd.read_excel(file_path, sheet_name=sheet_name)
                else:
                    logger.info("Read file '{}'", file_path)
                    return pd.read_excel(file_path)
        else:
            logger.error("❌ Unsupported file extension: {}. Allowed: {}", file_extension, allowed_extensions)
            raise TypeError(f"Unsupported file extension: {file_extension}. Allowed: {allowed_extensions}")