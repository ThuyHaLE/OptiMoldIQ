import pandas as pd
import numpy as np
import warnings
from typing import List
from loguru import logger
from agents.decorators import validate_init_dataframes
from datetime import datetime
from pathlib import Path
import os

from agents.utils import ConfigReportMixin
from agents.utils import load_annotation_path, read_change_log
from configs.shared.shared_source_config import SharedSourceConfig
from agents.autoPlanner.initialPlanner.optimizer.hybrid_optimizer.config.hybrid_suggest_config import MoldCapacityColumns

# Decorator to validate DataFrames are initialized with the correct schema
# This ensures that required DataFrames have all necessary columns before processing
@validate_init_dataframes(lambda self: {
    "moldInfo_df": list(self.databaseSchemas_data['staticDB']['moldInfo']['dtypes'].keys()),
    "moldSpecificationSummary_df": list(self.databaseSchemas_data['staticDB']['moldSpecificationSummary']['dtypes'].keys()),
    "mold_stability_index": list(self.sharedDatabaseSchemas_data["mold_stability_index"]['dtypes'].keys()),
})

class ItemMoldCapacityOptimizer(ConfigReportMixin):

    """
    Optimize mold production capacity using historical stability data.
    Workflow:
    1. Identify molds that have been used before (from the Mold Stability Index).
    2. Determine molds that have never been used by comparing against the full mold list.
    3. For unused molds:
        - Calculate theoretical capacity based on mold and machine specifications.
        - Estimate realistic capacity considering operational constraints.
    4. Merge used and unused mold data into one table.
    5. For each item code, assign priority to molds with the highest estimated capacity.

    This process helps select the most efficient mold for production,
    balancing proven historical performance with potential unused mold capacity.
    """

    REQUIRED_FIELDS = {
        'shared_source_config': {
            'mold_stability_index_change_log_path': str,
            'annotation_path': str,
            'databaseSchemas_path': str,
            'sharedDatabaseSchemas_path': str
            },
        'efficiency': float,
        'loss': float
        }

    def __init__(self,
                 shared_source_config: SharedSourceConfig, 
                 efficiency: float = 0.85,
                 loss: float = 0.03
                 ):
        
        """
        Initialize the ItemMoldCapacityOptimizer.
        
        Args:
            shared_source_config: SharedSourceConfig containing processing parameters
            Including:
                - mold_stability_index_change_log_path: Path to the MoldStabilityIndexCalculator change log
                - annotation_path: Path to the JSON file containing path annotations
                - databaseSchemas_path: Path to database schemas JSON file for validation
                - sharedDatabaseSchemas_path: Path to shared database schemas JSON file for validation
            efficiency: Production efficiency factor (0.0 to 1.0)
            loss: Production loss factor (0.0 to 1.0)
        """
        
        self._capture_init_args()

        # Initialize logger with class name for better tracking
        self.logger = logger.bind(class_="ItemMoldCapacityOptimizer")

        # Validate efficiency and loss parameters
        if not 0.0 <= efficiency <= 1.0:
            raise ValueError(f"Efficiency must be between 0.0 and 1.0, got {efficiency}")
        if not 0.0 <= loss <= 1.0:
            raise ValueError(f"Loss must be between 0.0 and 1.0, got {loss}")
        if efficiency <= loss:
            raise ValueError(
                f"Efficiency ({efficiency}) must be greater than loss ({loss})"
            )
    
        # Validate required configs
        is_valid, errors = shared_source_config.validate_requirements(self.REQUIRED_FIELDS['shared_source_config'])
        if not is_valid:
            raise ValueError(
                f"{self.__class__.__name__} config validation failed:\n" +
                "\n".join(f"  - {e}" for e in errors)
            )
        self.logger.info("✓ Validation for shared_source_config requirements: PASSED!")

        self.config = shared_source_config
        self.efficiency = efficiency
        self.loss = loss

        # Load database schema configuration for column validation
        self.load_schema_and_annotations()
        self._load_dataframes()

        # Load mold stability index containing performance consistency metrics
        self.mold_stability_index = self._load_mold_stability_index(self.config.mold_stability_index_change_log_path)

    def load_schema_and_annotations(self):
        """Load database schemas and path annotations from configuration files."""
        self.databaseSchemas_data = self._load_annotation_from_config(
            self.config.databaseSchemas_path
        )
        self.sharedDatabaseSchemas_data = self._load_annotation_from_config(
            self.config.sharedDatabaseSchemas_path
        )
        self.path_annotation = self._load_annotation_from_config(
            self.config.annotation_path
        )
    
    def _load_annotation_from_config(self, config_path):
        """Helper function to load annotation from a config path."""
        return load_annotation_path(
            Path(config_path).parent,
            Path(config_path).name
        )
    
    def _load_dataframes(self) -> None:

        """
        Load all required DataFrames from parquet files with consistent error handling.

        This method loads the following DataFrames:
        - productRecords_df: Production records with item, mold, machine data
        - machineInfo_df: Machine specifications and tonnage information
        - moldSpecificationSummary_df: Mold specifications and compatible items
        - moldInfo_df: Detailed mold information including tonnage requirements
        """

        # Define the mapping between path annotation keys and DataFrame attribute names
        dataframes_to_load = [
            ('moldSpecificationSummary', 'moldSpecificationSummary_df'),
            ('moldInfo', 'moldInfo_df')
        ]

        # Load each DataFrame with error handling
        for path_key, attr_name in dataframes_to_load:
            path = self.path_annotation.get(path_key)

            # Validate path exists
            if not path or not os.path.exists(path):
                self.logger.error("Path to '{}' not found or does not exist: {}", path_key, path)
                raise FileNotFoundError(f"Path to '{path_key}' not found or does not exist: {path}")

            try:
                # Load DataFrame from parquet file
                df = pd.read_parquet(path)
                setattr(self, attr_name, df)
                self.logger.debug("{}: {} - {}", path_key, df.shape, list(df.columns))
            except Exception as e:
                self.logger.error("Failed to load {}: {}", path_key, str(e))
                raise
    
    def _detect_invalid_molds(self) -> List[str]:
        """Identify and report invalid molds."""
        invalid_molds = self.mold_stability_index[
            ~self.mold_stability_index['moldNo'].isin(self.moldInfo_df['moldNo'])
        ]['moldNo'].tolist()
        
        has_issues = len(invalid_molds) > 0
        if has_issues:
            self.logger.warning(
                f"Found {len(invalid_molds)} molds in historical data "
                f"but not in moldInfo: {invalid_molds[:5]}..."  # Show first 5
            )
        return invalid_molds
    
    def process(self) -> tuple[List[str], pd.DataFrame, str]:

        """
        Process and combine mold information from specification and detail datasets.
        """

        if self.moldSpecificationSummary_df.empty or self.moldInfo_df.empty:
            self.logger.error("Invalid dataframe with moldSpecificationSummary or moldInfo !!!")
            raise
        
        try:
            self.logger.info("Starting ItemMoldCapacityOptimizer ...")

            # Generate config header using mixin
            timestamp_start = datetime.now()
            timestamp_str = timestamp_start.strftime("%Y-%m-%d %H:%M:%S")
            config_header = self._generate_config_report(timestamp_str, required_only=True)

            optimization_log_lines = [config_header]
            optimization_log_lines.append(f"--Processing Summary--")
            optimization_log_lines.append(f"⤷ {self.__class__.__name__} results:")

            # Step 1: Identify molds that have been used before (load from the Mold Stability Index)
            self.logger.info("✓ Step 1: Mold stability index already loaded and validated in __init__")

            # Detect invalid mold list
            invalid_molds = self._detect_invalid_molds()
            optimization_log_lines.append(
                f"Found {len(invalid_molds)} mold(s) not in moldInfo (need double-check or update information): {invalid_molds}")
            
            # Step 2: Determine molds that have never been used by comparing against the full mold list.
            unused_molds = self._detect_unused_molds()
            optimization_log_lines.append(
                f"Found {len(unused_molds)} mold(s) not in historical data (never used): {unused_molds}")

            # Step 3: Consolidate used and unused mold capacity
            optimization_log_lines.append(f"Start process with efficiency: {self.efficiency} - loss: {self.loss}")
            updated_mold_stability_index = self._consolidate_all_molds_capacity(self.moldInfo_df, 
                                                                               unused_molds, 
                                                                               self.mold_stability_index, 
                                                                               self.efficiency, 
                                                                               self.loss)

            # Step 4: Assign molds priority for item code with the highest estimated capacity.
            item_mold_priority_df = self._assign_priority_mold(updated_mold_stability_index)

            # Calculate processing time
            timestamp_end = datetime.now()
            processing_time = (timestamp_end - timestamp_start).total_seconds()

            # Add summary statistics
            optimization_log_lines.append(f"--Assignment Results--")
            optimization_log_lines.append(f"⤷ Processing time: {processing_time:.2f} seconds")
            optimization_log_lines.append(f"⤷ End time: {timestamp_end.strftime('%Y-%m-%d %H:%M:%S')}")
            optimization_log_lines.append(f"--Priority Mold Assignment--")
            optimization_log_lines.append(f"⤷ Total: {len(item_mold_priority_df)} records, {item_mold_priority_df['itemCode'].nunique()} items")
            optimization_log_lines.append(f"⤷ Priority molds: {item_mold_priority_df['isPriority'].sum()}/{len(item_mold_priority_df)}")
            optimization_log_lines.append(f"⤷ Coverage: {(item_mold_priority_df.groupby('itemCode')['isPriority'].sum() > 0).sum()}/{item_mold_priority_df['itemCode'].nunique()} items")

            optimization_log_str = "\n".join(optimization_log_lines)
            self.logger.info("✅ Process finished!!!")

            return invalid_molds, item_mold_priority_df, optimization_log_str
        
        except Exception as e:
            self.logger.error("Failed to process ItemMoldCapacityOptimizer: {}", str(e))
            raise RuntimeError(f"ItemMoldCapacityOptimizer processing failed: {str(e)}") from e
            
    #-------------------------------------------#
    # STEP 1: LOAD MOLD STABILITY INDEX         #
    #-------------------------------------------#
    def _load_mold_stability_index(self,
                                   mold_stability_index_change_log_path) -> pd.DataFrame:
        """
        Load mold stability index data from the nearest monthly report or create initial structure.

        The mold stability index contains metrics about how consistently each mold performs,
        including cavity stability, cycle time consistency, and overall reliability measures.

        Returns:
            pd.DataFrame: Mold stability index with performance consistency metrics
        """
        # Attempt to find the latest mold stability index file from change log

        self.logger.info("Loading mold stability index...")
        stability_path = read_change_log(
            Path(mold_stability_index_change_log_path).parent,
            Path(mold_stability_index_change_log_path).name
        )

        # Handle case where no historical stability index exists
        if stability_path is None:
            self.logger.warning("Cannot find stability index file {}",
                                mold_stability_index_change_log_path
                                )
            self.logger.info("Creating initial mold stability index structure...")
            return self._create_initial_stability_index()
        
        # Load existing stability index from Excel file
        try:
            self.logger.info("Loading existing mold stability index from: {}", stability_path)
            stability_index = pd.read_excel(stability_path)
            self.logger.debug("Loaded stability index with shape: {}", stability_index.shape)
            return stability_index
        except Exception as e:
            self.logger.error("Failed to load stability index from {}: {}", stability_path, str(e))
            self.logger.info("Falling back to initial stability index structure...")
            return self._create_initial_stability_index()
        
    def _create_initial_stability_index(self) -> pd.DataFrame:
        """Create an empty DataFrame with the required column structure."""
        return pd.DataFrame(columns=MoldCapacityColumns.REQUIRED)

    #-------------------------------------------#
    # STEP 2: DETECT UNUSED MOLDS               #
    #-------------------------------------------#
    def _detect_unused_molds(self):
        """Identify unused molds (in moldInfo but not in historical records)"""
        return self.moldInfo_df[
            ~self.moldInfo_df['moldNo'].isin(self.mold_stability_index['moldNo'])]['moldNo'].tolist()

    #-------------------------------------------#
    # STEP 3: CONSOLIDATE ALL MOLD CAPACITY     #
    #-------------------------------------------#
    def _consolidate_all_molds_capacity(self,
                                        moldInfo_df: pd.DataFrame,
                                        unused_molds: List[str],
                                        used_molds_df: pd.DataFrame,
                                        efficiency: float,
                                        loss: float) -> pd.DataFrame:

        """
        Deal with unused molds:
            - Calculate theoretical capacity based on mold and machine specifications.
            - Estimate realistic capacity considering operational constraints.
        Then, merge unused molds with used molds data.

        Args:
            moldInfo_df: Complete mold information dataframe
            unused_molds: List of unused mold numbers
            used_molds_df: DataFrame of historically used molds
            efficiency: Production efficiency factor
            loss: Production loss factor

        Returns:
            Combined dataframe with all molds
        """

        # Define merge columns
        merge_cols = [
            'moldNo', 'moldName', 'acquisitionDate', 'machineTonnage',
            'moldCavityStandard', 'moldSettingCycle', 'theoreticalMoldHourCapacity',
            'estimatedMoldHourCapacity', 'balancedMoldHourCapacity'
        ]

        # Calculate capacity for all molds first
        capacity_df = ItemMoldCapacityOptimizer.compute_hourly_capacity(moldInfo_df, efficiency, loss)

        # Filter only unused molds and select required columns
        available_merge_cols = [col for col in merge_cols if col in capacity_df.columns]
        partial_df = capacity_df[capacity_df['moldNo'].isin(unused_molds)][available_merge_cols]

        # Create empty dataframe with same structure as used_molds_df
        empty_df = pd.DataFrame(columns=used_molds_df.columns)

        # Reindex unused molds to match used molds structure
        unused_molds_df = partial_df.reindex(columns=empty_df.columns, fill_value=None)

        # Combine all molds
        if used_molds_df.empty:
            all_molds_df = unused_molds_df.copy()
        else:
            all_molds_df = pd.concat([used_molds_df, unused_molds_df], ignore_index=True)

        return all_molds_df
    
    @staticmethod
    def compute_hourly_capacity(df: pd.DataFrame, 
                                efficiency: float, 
                                loss: float) -> pd.DataFrame:

        """
        Calculate mold production capacity per hour.

        Args:
            df: Mold info dataframe with columns 'moldSettingCycle', 'moldCavityStandard'
            efficiency: Production efficiency factor (0.0 to 1.0)
            loss: Production loss factor (0.0 to 1.0)

        Returns:
            Updated dataframe with capacity calculations

        Raises:
            ValueError: If required columns are missing
        """

        if df.empty:
            return df

        # Validate required columns
        required_cols = ['moldSettingCycle', 'moldCavityStandard']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            logger.error("Missing required columns: {}", missing_cols)
            raise ValueError(f"Missing required columns: {missing_cols}")

        df = df.copy()

        # Handle zero or negative values - replace with NaN for proper calculation
        df['moldSettingCycle'] = df['moldSettingCycle'].replace([0, np.inf, -np.inf], np.nan)
        df['moldCavityStandard'] = df['moldCavityStandard'].replace([0, np.inf, -np.inf], np.nan)

        # Calculate capacities with error handling
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")

            # Theoretical capacity: items per hour = (3600 seconds/hour) / (cycle time) * cavities
            df['theoreticalMoldHourCapacity'] = (
                3600 / df['moldSettingCycle'] * df['moldCavityStandard']
            ).fillna(0).round(2)

            # Estimated capacity considering efficiency and loss
            df['estimatedMoldHourCapacity'] = (
                df['theoreticalMoldHourCapacity'] * (efficiency - loss)
            ).fillna(0).round(2)

            # Ensure non-negative values
            df['estimatedMoldHourCapacity'] = df['estimatedMoldHourCapacity'].clip(lower=0)

            # Balanced capacity (currently same as estimated) if historical mold stability index not available
            df['balancedMoldHourCapacity'] = df['estimatedMoldHourCapacity']

        return df

    #--------------------------------------------#
    # STEP 4: ASSIGN MOLD PRIORITY FOR ITEM CODE # 
    #--------------------------------------------#
    def _assign_priority_mold(self,
                              updated_mold_stability_index: pd.DataFrame) -> pd.DataFrame:

        """
        Mark the mold with the highest capacity for each itemCode.
        In case of tie in capacity, selects the mold with the latest acquisition date.
        """

        merge_cols = [
            'moldNo', 'moldName', 'acquisitionDate', 'moldCavityStandard',
            'moldSettingCycle', 'machineTonnage', 'theoreticalMoldHourCapacity',
            'balancedMoldHourCapacity']

        # Merge specification data with mold details
        moldSpec_df_exploded = self.expand_item_mold_specifications()
        available_cols = [col for col in merge_cols if col in updated_mold_stability_index.columns]
        merged_df = moldSpec_df_exploded.merge(
            updated_mold_stability_index[available_cols],
            how='left',
            on=['moldNo']
        )

        if merged_df.empty:
            return merged_df

        item_mold_priority_df = merged_df.copy()

        # Convert acquisitionDate to datetime if not already
        item_mold_priority_df['acquisitionDate'] = pd.to_datetime(
            item_mold_priority_df['acquisitionDate'], errors='coerce'
        )

        # Group by itemCode and find priority molds
        item_mold_priority_df = item_mold_priority_df.sort_values(
            by=['itemCode', 'balancedMoldHourCapacity', 'acquisitionDate'],
            ascending=[True, False, False],
            na_position='last'
        )

        # Mark first record per itemCode as priority
        item_mold_priority_df['isPriority'] = False
        priority_mask = ~item_mold_priority_df.duplicated(subset=['itemCode'], keep='first')
        item_mold_priority_df.loc[priority_mask, 'isPriority'] = True

        return item_mold_priority_df
    
    def expand_item_mold_specifications(self) -> pd.DataFrame:
        """
        Expand moldList into individual item-mold pairs.
        
        Processes the moldList column by splitting delimited mold numbers
        and creating separate rows for each item-mold combination.
        
        Args:
            moldSpec_df: DataFrame with moldList column (molds separated by '/')
            
        Returns:
            Expanded DataFrame with one row per item-mold pair
        """

        # Process moldList column safely
        moldSpec_df = self.moldSpecificationSummary_df.copy()

        # Handle missing or null moldList values
        moldSpec_df['moldList'] = moldSpec_df['moldList'].fillna('')
        moldSpec_df['moldList'] = moldSpec_df['moldList'].astype(str)

        # Split moldList by '/' delimiter and explode into separate rows
        moldSpec_df['moldList'] = moldSpec_df['moldList'].str.split('/')
        moldSpec_df_exploded = moldSpec_df.explode('moldList', ignore_index=True)

        # Clean up moldList values
        moldSpec_df_exploded['moldList'] = moldSpec_df_exploded['moldList'].str.strip()
        moldSpec_df_exploded = moldSpec_df_exploded[moldSpec_df_exploded['moldList'] != '']

        # Rename for merging
        moldSpec_df_exploded.rename(columns={'moldList': 'moldNo'}, inplace=True)

        return moldSpec_df_exploded