from loguru import logger
import pandas as pd
from typing import Dict, List, Union, Callable
from functools import wraps

def validate_dataframe(df: pd.DataFrame, required_columns: List[str]) -> None:
    if not hasattr(df, "columns"):
        raise TypeError("Expected a DataFrame-like object with .columns attribute")

    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        logger.error("❌ Missing columns in input dataframe: {}", missing)
        raise ValueError(f"Missing required columns: {missing}")

    if df.empty:
        logger.warning("⚠️ DataFrame is empty. No rows to plot or process.")

    logger.debug("✅ DataFrame OK - Shape: {}, Columns: {}", df.shape, list(df.columns))


def validate_init_dataframes(dataframes_columns: Union[Dict[str, List[str]], Callable]) -> Callable:
    def decorator(cls):
        original_init = cls.__init__

        @wraps(original_init)
        def new_init(self, *args, **kwargs):
            original_init(self, *args, **kwargs)

            # Hỗ trợ truyền callable để lấy schema sau khi self được init
            resolved_columns = dataframes_columns(self) if callable(dataframes_columns) else dataframes_columns

            for attr_name, required_columns in resolved_columns.items():
                df = getattr(self, attr_name, None)
                if not isinstance(df, pd.DataFrame):
                    raise TypeError(
                        f"❌ Attribute '{attr_name}' is not a pandas DataFrame in class '{cls.__name__}'"
                    )
                validate_dataframe(df, required_columns)

        cls.__init__ = new_init
        return cls

    return decorator