from loguru import logger
import pandas as pd
from typing import Dict, List
import inspect
from functools import wraps

def validate_dataframe(df: pd.DataFrame, required_columns: List[str]) -> None:
  missing = [col for col in required_columns if col not in df.columns]
  if missing:
      logger.error("❌ Missing columns in input dataframe: {}", missing)
      raise ValueError(f"Missing required columns: {missing}")
  
  if df.empty:
    logger.warning("⚠️ DataFrame is empty. No rows to plot or process.")

  logger.debug("Dataframe with shape: {} and columns: {}", df.shape, list(df.columns))

def validate_input(dataframes_columns: Dict[str, List[str]]):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get func args names
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()

            # Check DataFrame by args names
            for df_name, required_columns in dataframes_columns.items():
                if df_name not in bound_args.arguments:
                    raise ValueError(f"Argument '{df_name}' not found in function call")
                df = bound_args.arguments[df_name]
                if not isinstance(df, pd.DataFrame):
                    raise TypeError(f"Argument '{df_name}' is not a pandas DataFrame")
                validate_dataframe(df, required_columns)
            return func(*args, **kwargs)
        return wrapper
    return decorator

def validate_init_dataframes(dataframes_columns: Dict[str, List[str]]):
    def decorator(cls):
        original_init = cls.__init__

        @wraps(original_init)
        def new_init(self, *args, **kwargs):
            original_init(self, *args, **kwargs)

            for attr_name, required_columns in dataframes_columns.items():
                df = getattr(self, attr_name, None)
                if not isinstance(df, pd.DataFrame):
                    raise TypeError(f"❌ Attribute '{attr_name}' is not a pandas DataFrame in class '{cls.__name__}'")
                validate_dataframe(df, required_columns)
        cls.__init__ = new_init
        return cls
    return decorator