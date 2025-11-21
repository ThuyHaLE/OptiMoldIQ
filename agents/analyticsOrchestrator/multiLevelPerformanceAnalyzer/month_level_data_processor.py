import numpy as np
import pandas as pd
from typing import Tuple
from loguru import logger
from pathlib import Path
import os
from agents.decorators import validate_init_dataframes, validate_dataframe
from agents.utils import load_annotation_path
from datetime import datetime
import shutil

# Decorator to validate DataFrames are initialized with the correct schema
@validate_init_dataframes(lambda self: {
    "productRecords_df": list(self.databaseSchemas_data['dynamicDB']['productRecords']['dtypes'].keys()),
    "purchaseOrders_df": list(self.databaseSchemas_data['dynamicDB']['purchaseOrders']['dtypes'].keys()),
    "moldInfo_df": list(self.databaseSchemas_data['staticDB']['moldInfo']['dtypes'].keys()),
    "moldSpecificationSummary_df": list(self.databaseSchemas_data['staticDB']['moldSpecificationSummary']['dtypes'].keys()),
})

class MonthLevelDataProcessor:

    def __init__(self,
                 record_month: str,
                 analysis_date: str = None,
                 source_path: str = 'agents/shared_db/DataLoaderAgent/newest',
                 annotation_name: str = "path_annotations.json",
                 databaseSchemas_path: str = 'database/databaseSchemas.json',
                 default_dir: str = "agents/shared_db/MultiLevelDataAnalytics"):

        self.logger = logger.bind(class_="MonthLevelDataProcessor")

        self.record_month = record_month
        self.analysis_date = analysis_date

        # Load database schema and database paths annotation
        self.databaseSchemas_data = load_annotation_path(Path(databaseSchemas_path).parent,
                                                         Path(databaseSchemas_path).name)
        self.path_annotation = load_annotation_path(source_path,
                                                    annotation_name)

        # Load DataFrames
        self.productRecords_df = self._load_dataframe('productRecords')
        self.purchaseOrders_df = self._load_dataframe('purchaseOrders')
        self.moldSpecificationSummary_df = self._load_dataframe('moldSpecificationSummary')
        self.moldInfo_df = self._load_dataframe('moldInfo')

        self.filename_prefix = "day_level"
        self.default_dir = Path(default_dir)
        self.output_dir = self.default_dir / "MonthLevelDataProcessor"

    def _load_dataframe(self, df_name: str) -> pd.DataFrame:
        """Load a specific DataFrame with error handling."""
        df_path = self.path_annotation.get(df_name)

        if not df_path:
            error_msg = f"Path to '{df_name}' not found in annotations."
            self.logger.error("❌ {}", error_msg)
            raise KeyError(error_msg)

        if not os.path.exists(df_path):
            error_msg = f"Path to '{df_name}' does not exist: {df_path}"
            self.logger.error("❌ {}", error_msg)
            raise FileNotFoundError(error_msg)

        try:
            df = pd.read_parquet(df_path)
            self.logger.info("✅ Successfully loaded {}: {} records", df_name, len(df))
            return df
        except Exception as e:
            error_msg = f"Failed to read parquet file for '{df_name}': {e}"
            self.logger.error("❌ {}", error_msg)
            raise
    
    def data_process(self, 
                     save_output = False):
        
        self.logger.info("Start processing...")
        (analysis_timestamp, adjusted_record_month, 
         finished_df, unfinished_df, final_summary) = self.product_record_processing()
    
        if save_output: 
            # Setup directories and timestamps
            timestamp_now = datetime.now()
            timestamp_str = timestamp_now.strftime("%Y-%m-%d %H:%M:%S")
            timestamp_file = timestamp_now.strftime("%Y%m%d_%H%M")
            
            newest_dir = self.output_dir / "newest"
            newest_dir.mkdir(parents=True, exist_ok=True)
            historical_dir = self.output_dir / "historical_db"
            historical_dir.mkdir(parents=True, exist_ok=True)
            
            log_entries = [f"[{timestamp_str}] Saving new version...\n"]
            
            # Move old files to historical_db
            for f in newest_dir.iterdir():
                if f.is_file():
                    try:
                        dest = historical_dir / f.name
                        shutil.move(str(f), dest)
                        log_entries.append(f"  ⤷ Moved old file: {f.name} → historical_db/{f.name}\n")
                        self.logger.info("Moved old file {} to historical_db as {}", f.name, dest.name)
                    except Exception as e:
                        self.logger.error("Failed to move file {}: {}", f.name, e)
                        raise OSError(f"Failed to move file {f.name}: {e}")
            
            # Save day level extracted records
            try:
                excel_file_name = f"{timestamp_file}_{self.filename_prefix}_insights_{adjusted_record_month}.xlsx"
                excel_file_path = newest_dir / excel_file_name

                excel_data = {
                    "finishedRecords": finished_df,
                    "unfinishedRecords": unfinished_df
                }

                with pd.ExcelWriter(excel_file_path, engine="openpyxl") as writer:
                    for sheet_name, df in excel_data.items():
                        if not isinstance(df, pd.DataFrame):
                            df = pd.DataFrame([df])
                        df.to_excel(writer, sheet_name=sheet_name, index=False)
                log_entries.append(f"  ⤷ Saved data analysis results: {excel_file_path}\n")
                logger.info("✅ Saved data analysis results: {}", excel_file_path)
            except Exception as e:
                logger.error("❌ Failed to save file {}: {}", excel_file_name, e)
                raise OSError(f"Failed to save file {excel_file_name}: {e}")
            
            # Save analysis summary
            try:
                analysis_summary_name = f"{timestamp_file}_{self.filename_prefix}_summary_{adjusted_record_month}.txt"
                analysis_summary_path = newest_dir / analysis_summary_name
                with open(analysis_summary_path, "w", encoding="utf-8") as log_file:
                    log_file.writelines(final_summary)
                log_entries.append(f"  ⤷ Saved analysis summary: {analysis_summary_path}\n")
                self.logger.info("Updated analysis summary {}", analysis_summary_path)
            except Exception as e:
                self.logger.error("Failed to update analysis summary {}: {}", analysis_summary_path, e)
                raise OSError(f"Failed to update analysis summary {analysis_summary_path}: {e}")
            
            # Update change log
            try:
                log_path = self.output_dir / "change_log.txt"
                with open(log_path, "a", encoding="utf-8") as log_file:
                    log_file.writelines(log_entries)
                self.logger.info("Updated change log {}", log_path)
            except Exception as e:
                self.logger.error("Failed to update change log {}: {}", log_path, e)
                raise OSError(f"Failed to update change log {log_path}: {e}")
            
            return analysis_timestamp, adjusted_record_month, finished_df, unfinished_df, final_summary, log_entries
        
        else:
            return analysis_timestamp, adjusted_record_month, finished_df, unfinished_df, final_summary, None
        
    def product_record_processing(self):

        """
        Complete manufacturing analysis pipeline.

        This method performs the full end-to-end analysis of production order (PO) data,
        including validation, backlog detection, capacity estimation, and performance classification.
        It outputs two key datasets:
            - finished_df: Completed POs
            - unfinished_df: POs still in progress or not yet started

        Returns:
            tuple:
                (finished_df, unfinished_df)
        """

        # Validate input parameters and set up analysis context
        (analysis_timestamp,
         adjusted_record_month,
         validation_summary) = self._validate_analysis_parameters()

        # Filter and prepare base data for PO-level analysis
        po_based_df = self._filter_data(adjusted_record_month, analysis_timestamp)

        # Compute remaining production quantity per PO
        #   - If no good quantity recorded yet => full quantity remains
        #   - Otherwise => total - good_quantity | 0 if overproduction

        po_based_df['itemRemainQuantity'] = np.where(
            po_based_df['itemGoodQuantity'].isna(),
            po_based_df['itemQuantity'],  # Not started: full quantity remains
            np.maximum(0, po_based_df['itemQuantity'] - po_based_df['itemGoodQuantity'])
        )

        # Determine PO production status
        #   - finished: all quantities done or overproduced
        #   - in_progress: has mold history => production started
        #   - not_started: no mold history yet
        po_based_df['poStatus'] = np.where(
            po_based_df['itemRemainQuantity'] <= 0, #In some cases, there is overproduction
            'finished',
            np.where(
                po_based_df['moldHist'].notna(),
                'in_progress',
                'not_started'
            )
            )

        # Identify and quantify overproduction cases
        #   - If remaining quantity < 0 => record its absolute value
        po_based_df['overproduction_quantity'] = np.where(
            po_based_df['itemRemainQuantity'] < 0,
            abs(po_based_df['itemRemainQuantity']),
            0
        )

        # Split dataset by PO status for specific treatment
        finished_df = po_based_df[po_based_df['poStatus'] == 'finished'].copy()
        in_progress_df = po_based_df[po_based_df['poStatus'] == 'in_progress'].copy()
        not_started_df = po_based_df[po_based_df['poStatus'] == 'not_started'].copy()

        # Flag status for finished POs
        finished_df["etaStatus"] = np.where(
            finished_df["lastRecord"] < finished_df["poETA"],
            "ontime",
            "late"
        )

        # Estimate capacity for unfinished POs
        #   - not_started: use estimated item-based capacity (item → multiple molds possible)
        #   - in_progress: use calculated capacity based on historical mold usage

        # For not-started POs: estimate capacity by item type
        item_capacity_df = self._estimate_item_capacity()
        not_started_df = not_started_df.merge(item_capacity_df, how='left', on="itemCodeName")

        # For in-progress POs: calculate actual mold-level capacity
        mold_capacity_df = self._calculate_mold_capacity(in_progress_df)
        in_progress_df = in_progress_df.merge(mold_capacity_df, how='left', on="itemCodeName")

        # Combine all unfinished POs for unified analysis
        combined_df = pd.concat([in_progress_df, not_started_df], ignore_index=True)

        # Perform mold-level analysis on unfinished POs
        #   - Compute cumulative quantities and production rates
        #   - Filter to focus on rate == 1 molds (fully allocated molds)
        unfinished_df = MonthLevelDataProcessor._analyze_unfinished_pos(combined_df, analysis_timestamp)

        # Logging analysis summary and diagnostic information
        analysis_summary = MonthLevelDataProcessor._log_analysis_summary(
            adjusted_record_month, 
            analysis_timestamp, 
            po_based_df, 
            finished_df, 
            unfinished_df)
        
        self.logger.info("{}", analysis_summary)

        # Get final summary
        
        final_summary = validation_summary + "\n\n" + analysis_summary

        return analysis_timestamp, adjusted_record_month, finished_df, unfinished_df, final_summary
    

    def _validate_analysis_parameters(self) -> Tuple[pd.Timestamp, str]:

        """
        Validate and adjust analysis parameters based on available historical production data
        and business logic constraints.

        This method ensures that the analysis date (`analysis_date`) and the record month
        (`record_month`) used for manufacturing analysis are logically consistent with the
        available production records (`productRecords_df`).

        Business Rules:
            1. Analysis date looking at a past or current record_month → ✅ OK
            2. Analysis date looking at a *future* record_month → ❌ FAILED
            3. If analysis_date > max(recordDate):
                → Adjust analysis_date to the latest available recordDate
                → Adjust record_month accordingly to match that date
            4. If no historical data is available → ❌ FAILED

        Behavior:
            - If `analysis_date` is not provided, the function automatically uses
            the end of the specified `record_month` as the analysis date.
            - Ensures that both `analysis_date` and `record_month` are valid and
            correctly formatted (`YYYY-MM-DD` and `YYYY-MM` respectively).
            - Logs detailed validation steps and adjustments.

        Returns:
            Tuple[pd.Timestamp, str]:
                - validated_analysis_timestamp (pd.Timestamp):
                    The final, validated analysis date (possibly adjusted).
                - adjusted_record_month (str):
                    The corresponding record month (possibly adjusted if analysis date was shifted).

        Raises:
            ValueError:
                - If no historical production data is available.
                - If all recordDate values are null.
                - If record_month or analysis_date formats are invalid.
                - If analysis_date points to a future record_month.

        Notes:
            This function should always be called at the beginning of an analysis pipeline
            to guarantee temporal consistency between the analysis timeframe and
            available production data.
        """

        # Validate existence of historical data
        if self.productRecords_df.empty:
            self.logger.error("No historical production data available for analysis!")
            raise ValueError("No historical production data available for analysis!")

        # Find the latest record date in historical production data
        max_record_date = self.productRecords_df['recordDate'].max()

        # If all recordDate are NaN → cannot analyze anything
        if pd.isna(max_record_date):
            self.logger.error("All recordDate values are null. Cannot proceed with analysis!")
            raise ValueError("All recordDate values are null. Cannot proceed with analysis!")

        # Log historical data range for traceability
        self.logger.info(
            "Historical data available from {} to {}",
            self.productRecords_df['recordDate'].min().date(),
            max_record_date.date()
        )

        # Parse and validate record_month
        try:
            # Convert record_month string ('YYYY-MM') → pandas.Period
            requested_period = pd.Period(self.record_month, freq="M")
        except Exception as e:
            self.logger.error(
                "Invalid record_month format '{}'. Expected 'YYYY-MM'. Error: {}",
                self.record_month, e
            )
            raise ValueError(
                f"Invalid record_month format '{self.record_month}'. Expected 'YYYY-MM'. Error: {e}"
            )

        # Determine analysis date
        if self.analysis_date is None:
            # If not specified → use end of the record month as default
            analysis_timestamp = requested_period.to_timestamp(how="end").normalize()
            self.logger.info(
                "No analysis_date provided. Using the end of record_month as analysis date: {}",
                analysis_timestamp.date()
            )
        else:
            try:
                # Try converting user input string to pandas.Timestamp
                analysis_timestamp = pd.Timestamp(self.analysis_date).normalize()
                self.logger.info("Analysis date set to: {}", analysis_timestamp.date())
            except Exception as e:
                self.logger.error(
                    "Invalid analysis_date format '{}'. Expected 'YYYY-MM-DD'. Error: {}",
                    self.analysis_date, e
                )
                raise ValueError(
                    f"Invalid analysis_date format '{self.analysis_date}'. Expected 'YYYY-MM-DD'. Error: {e}"
                )

        # Business rule: no future-month analysis
        analysis_period = analysis_timestamp.to_period("M")

        # If analysis_date points to a *future* month → reject
        if analysis_period < requested_period:
            self.logger.error(
                "Invalid: Analysis date ({}) is before record_month ({}). "
                "Cannot analyze a future month from a past date!",
                analysis_timestamp.date(), requested_period
            )
            raise ValueError(
                f"Invalid: Analysis date ({analysis_timestamp.date()}) is before record_month "
                f"({requested_period}). Cannot analyze a future month from a past date!"
            )

        # Adjust analysis date if it exceeds available data
        original_analysis_date = analysis_timestamp
        adjusted_record_month = self.record_month  # Track if we adjust the month

        if analysis_timestamp > max_record_date:
            # Warn user if analysis_date goes beyond available records
            self.logger.warning(
                "Analysis date ({}) is beyond available data (max record date {})",
                analysis_timestamp.date(), max_record_date.date()
            )

            # Adjust analysis date down to max available recordDate
            analysis_timestamp = max_record_date.normalize()

            # Adjust record_month accordingly
            adjusted_period = analysis_timestamp.to_period("M")
            adjusted_record_month = adjusted_period.strftime("%Y-%m")

            self.logger.warning(
                "Adjusting analysis date to max record date ({}) and record month from {} to {}",
                analysis_timestamp.date(), requested_period, adjusted_period
            )

        # Log summary of validation results
        summary_text = MonthLevelDataProcessor._log_validation_summary(
            self.record_month,
            original_analysis_date,
            adjusted_record_month, 
            analysis_timestamp
            )
        
        self.logger.info("{}", summary_text)

        # Return validated values
        return analysis_timestamp, adjusted_record_month, summary_text

    def _detect_backlog(self,
                        record_month: str,
                        analysis_timestamp: str,
                        product_records: pd.DataFrame) -> pd.DataFrame:
        """
        Detect backlog purchase orders for a given month based on ETA and production status.

        A purchase order (PO) is considered **backlog** if:
            - Its ETA (Expected Time of Arrival) is *before* the target record month, **and**
            - Its production status is **not 'finished'**.

        This method identifies all purchase orders that were expected to arrive before the given
        month but remain unfinished as of the start of that month.

        Args:
            record_month (str):
                The target analysis month, in format `"YYYY-MM"`.
                Example: `"2024-06"`.
            product_records (pd.DataFrame):
                DataFrame containing production record details, typically including PO and
                manufacturing status information.

        Returns:
            pd.DataFrame:
                A filtered DataFrame containing all backlog purchase orders and their
                associated production status.
                Returns an empty DataFrame if no backlog is detected.

        Raises:
            ValueError:
                If `record_month` is not in valid `"YYYY-MM"` format.
            KeyError:
                If required purchase order columns are missing, or the merged DataFrame
                does not contain `'proStatus'`.

        Notes:
            - Backlog detection is performed **at the start of the record_month**.
            - Useful for identifying carryover workload or delayed production items.
        """

        # Validate and parse record_month format
        try:
            # Convert string 'YYYY-MM' to pandas.Period (monthly granularity)
            record_period = pd.Period(record_month, freq="M")
        except ValueError as e:
            raise ValueError(
                f"Invalid record_month format '{record_month}'. Expected 'YYYY-MM'"
            ) from e

        self.logger.info("Record month (requested): {}", record_period)

        # Determine the cutoff date for backlog detection
        # Cutoff = last day of previous month (before the record_month starts)
        period_timestamp = record_period.to_timestamp(how="start")
        cutoff_date = period_timestamp - pd.Timedelta(days=1)
        self.logger.info("Cut-off date: {}", cutoff_date.date())

        # Validate presence of required purchase order columns
        required_po_cols = ['poReceivedDate', 'poNo', 'poETA', 'itemCode', 'itemName', 'itemQuantity']

        # # Extract only the required fields from purchase orders
        po_df = self.purchaseOrders_df[required_po_cols].copy()

        # Generate combined item identifier for clarity
        # Combine itemCode + itemName → itemCodeName
        po_df["itemCodeName"] = MonthLevelDataProcessor._create_item_code_name(po_df)

        # Ensure ETA is datetime type for date comparison
        po_df["poETA"] = pd.to_datetime(po_df["poETA"])

        # Filter purchase orders that should have arrived before record_month
        filtered_po = po_df[po_df["poETA"] <= cutoff_date].copy()
        filtered_records = product_records[product_records['recordDate'] <= cutoff_date].copy()

        if filtered_po.empty:
            # No orders expected before cutoff → no backlog possible
            self.logger.info("No orders found with ETA <= cutoff date")
            return pd.DataFrame()

        self.logger.info("Total orders with ETA <= cutoff: {}", len(filtered_po))

        # Merge with production status to determine completion
        merged_df = MonthLevelDataProcessor._merge_purchase_status(filtered_po, filtered_records)

        # Ensure merged dataset includes production status info
        if 'proStatus' not in merged_df.columns:
            raise KeyError("Merged DataFrame missing 'proStatus' column")

        # Identify backlog orders (not finished)
        backlog_df = merged_df[merged_df["proStatus"] != 'finished'].copy()

        # Add explicit backlog flag for easier downstream filtering
        backlog_df['is_backlog'] = True

        # Reset NG quantity if any
        backlog_df['itemNGQuantity'] = 0

        # Log summary and return results
        if backlog_df.empty:
            self.logger.info("No backlog orders found")
        else:
            # Revise backlog POs (remain quantity)
            new_backlog_df = self._calculate_backlog_quantity(
                backlog_df, product_records, cutoff_date, analysis_timestamp)
            backlog_orders = new_backlog_df["poNo"].unique()
            self.logger.info("Backlog orders count: {}", len(backlog_orders))
            self.logger.debug("Backlog order numbers: {}", backlog_orders.tolist())

        return new_backlog_df
    
    def _calculate_backlog_quantity(self, 
                                    backlog_df: pd.DataFrame, 
                                    product_records_df: pd.DataFrame, 
                                    cutoff_timestamp: str,
                                    analysis_timestamp: str) -> pd.DataFrame:
        """
        Recalculate backlog item quantities using the latest production data.
        It updates backlog orders with recalculated remaining quantities based on the most recent progress.

        Args:
            backlog_df (pd.DataFrame): Backlog data containing columns
                ['poNo', 'itemQuantity', 'itemGoodQuantity', 'is_backlog'].
            product_records_df (pd.DataFrame): Product records data containing columns
                ['recordDate', 'poNote', 'itemGoodQuantity']

        Returns:
            pd.DataFrame: Updated backlog dataframe with recalculated fields:
                - itemQuantity: updated backlog quantity
                - itemGoodQuantity: matched quantity from current data
                - itemRemainQuantity: remaining quantity after deduction
        """
        # Validate dataframe
        validate_dataframe(backlog_df, ['poNo', 'itemQuantity', 'itemGoodQuantity', 'is_backlog'])
        validate_dataframe(product_records_df, ['recordDate', 'poNote', 'itemGoodQuantity'])
        
        # Records must be larger than cut-off date and smaller than analysis timestamp
        filter_mask = (
            (product_records_df['recordDate'] > cutoff_timestamp) & 
            (product_records_df['recordDate'] <= analysis_timestamp)
            )
        
        # Process product records
        now_df = product_records_df[filter_mask].copy()

        # Compute current ng quantity
        now_df['current_ng_qty'] = now_df['itemTotalQuantity'] - now_df['itemGoodQuantity']

        # Compute remaining quantity from backlog
        backlog_df['remaining_backlog_qty'] = (
            backlog_df['itemQuantity'] - backlog_df['itemGoodQuantity']
        )

        # Summarize latest production quantities (Good & NG) by PO
        now_summary = (
            now_df.groupby('poNote', as_index=False)
            .agg(
                current_good_qty=('itemGoodQuantity', 'sum'),
                current_ng_qty=('current_ng_qty', 'sum')
            )
            .rename(columns={'poNote': 'poNo'})
        )

        # Merge backlog with current production info
        merged = backlog_df.merge(now_summary, on='poNo', how='left')

        # Recalculate fields
        merged['itemQuantity'] = merged['remaining_backlog_qty']                                     # backlog quantity
        merged['itemGoodQuantity'] = merged['current_good_qty']                                      # quantity produced now
        merged['itemNGQuantity'] = merged['current_ng_qty']                                          # NG quantity produced now
        merged['itemRemainQuantity'] = merged['remaining_backlog_qty'] - merged['current_good_qty']  # remaining quantity
        merged["proStatus"] = np.where(                                                              # production status
            (merged['itemGoodQuantity'].notna()) &
            (merged["itemGoodQuantity"] >= merged["itemQuantity"]),
            "finished",
            "unfinished"
        )

        # Drop temporary column
        merged = merged.drop(columns=['remaining_backlog_qty', 'current_good_qty', 'current_ng_qty'])

        return merged

    def _filter_data(self,
                    record_month: str,
                    analysis_timestamp: str) -> pd.DataFrame:
        """
        Filter purchase orders by record_month and combine with backlog data.

        This function filters purchase orders for a given month (based on their ETA),
        merges them with production status information, and appends backlog orders
        that were expected before this month but remain unfinished.
        It ensures that the analysis includes both *current-month* and *carryover* orders.

        Business Logic:
            1. Select all purchase orders (POs) whose ETA falls within `record_month`.
            2. Merge these with production records available up to `analysis_timestamp`.
            3. Detect backlog orders from previous months (via `_detect_backlog`).
            4. Combine backlog and current-month orders into a unified dataset.

        Args:
            record_month (str):
                Target month in format `"YYYY-MM"`.
                Example: `"2024-03"`.
            analysis_timestamp (str):
                Analysis date (cutoff for production records), format `"YYYY-MM-DD HH:MM:SS"`.
                Example: `"2024-03-31 00:00:00"`.

        Returns:
            pd.DataFrame:
                Combined DataFrame containing:
                    - Purchase orders for the target month
                    - Backlog orders from earlier months
                    - Production status fields
                    - An `'is_backlog'` flag marking backlog orders (`True` / `False`)

        Raises:
            ValueError:
                If record_month format is invalid
                or if no matching data exists for that month.
            KeyError:
                If any required columns are missing from the purchase or product data.

        Notes:
            This step is part of the manufacturing analysis pipeline.
            It guarantees that backlog items are not ignored when aggregating
            monthly performance metrics.
        """

        # Validate required columns in purchase orders
        required_po_columns = ['poReceivedDate', 'poNo', 'poETA', 'itemCode', 'itemName', 'itemQuantity']

        # Validate and parse record_month
        try:
            record_period = pd.Period(record_month, freq="M")
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid record_month format '{record_month}'. Expected 'YYYY-MM'.") from e

        # Prepare purchase order dataset
        # Select essential columns from purchaseOrders_df
        purchase_orders_df = self.purchaseOrders_df[required_po_columns].copy()

        # Generate combined item identifier
        purchase_orders_df["itemCodeName"] = MonthLevelDataProcessor._create_item_code_name(purchase_orders_df)

        # Verify that the requested month exists in the data
        # Convert ETA → monthly period for filtering
        available_months = purchase_orders_df["poETA"].dt.to_period("M").dropna().unique()
        available_months_sorted = sorted(available_months)
        self.logger.info("Available months in data: {}", available_months_sorted)

        if record_period not in available_months:
            self.logger.error(
                "Requested month {} not found. Available months: {}",
                record_period,
                available_months_sorted
            )
            raise ValueError(
                f"Requested month {record_period} not found in purchase orders. "
                f"Available months: {available_months_sorted}"
            )

        # Filter POs belonging to the target month
        filtered_purchase_orders = purchase_orders_df[
            purchase_orders_df["poETA"].dt.to_period("M") == record_period
        ].copy()

        self.logger.info(
            "Filtered {} purchase orders for month: {}",
            len(filtered_purchase_orders),
            record_period
        )

        # Create a working copy of product records to avoid modifying the original DataFrame
        productRecords_df = self.productRecords_df.copy()

        # Calculate defective item quantity (ensure non-negative values)
        productRecords_df['itemNGQuantity'] = np.maximum(
            0, 
            productRecords_df['itemTotalQuantity'] - 
            productRecords_df['itemGoodQuantity'])
        
        # Filter production records up to the analysis timestamp
        filtered_product_records = productRecords_df[
            productRecords_df["recordDate"] <= analysis_timestamp].copy()

        if filtered_product_records.empty:
            # No production data available for the target analysis window
            self.logger.error(
                "No historical data available for the target month ({}). "
                "Earliest record date is {}.",
                record_month, filtered_product_records['recordDate'].min().date()
            )
            raise ValueError(
                f"No historical data available for the target month ({record_month}). "
                f"Earliest record date is {filtered_product_records['recordDate'].min().date()}."
            )

        self.logger.info("Filtered records count: {}", len(filtered_product_records))
        self.logger.info(
            "Date range: {} to {}",
            filtered_product_records['recordDate'].min().date(),
            filtered_product_records['recordDate'].max().date()
        )

        # Merge current-month POs with their production status
        purchase_status_df = MonthLevelDataProcessor._merge_purchase_status(
            filtered_purchase_orders, filtered_product_records)

        # Mark as non-backlog
        purchase_status_df['is_backlog'] = False

        # Detect backlog POs (unfinished from earlier months)
        backlog_df = self._detect_backlog(record_month, analysis_timestamp, filtered_product_records)

        if not backlog_df.empty:
            self.logger.info(
                "Found {} backlog orders and {} current orders",
                len(backlog_df),
                len(purchase_status_df)
            )

            # Combine backlog and current-month datasets
            combined_df = pd.concat([backlog_df, purchase_status_df], ignore_index=True)

            self.logger.info("Combined dataset size: {} orders", len(combined_df))
            
            # Return consolidated results
            return combined_df

        else:
            self.logger.info("Found 0 backlog orders and {} current orders", len(purchase_status_df))
            self.logger.info("Dataset size: {} orders", len(purchase_status_df))
            
            return purchase_status_df

    def _compute_mold_capacity(self, 
                               df: pd.DataFrame, 
                               mold_col: str, 
                               mold_num_col: str) -> pd.DataFrame:
        """

        Estimate item production capacity based on mold technical specifications.

        This function estimates the theoretical production capacity for each item
        using the corresponding mold information. The calculation is based on
        the mold's cycle time and number of cavities, assuming continuous operation.

        Steps:
        1. Expand mold history to individual mold records
        2. Merge with mold technical data (cavity & cycle time)
        3. Calculate per-mold hourly capacity
        4. Aggregate total and average capacity per item

        Steps:
        1. Expand mold history/ mold list (`mold_col`) to individual mold records
        2. Merge with mold technical data (cavity & cycle time)
        3. Calculate per-mold hourly capacity
        4. Aggregate total and average capacity per item (`mold_num_col`)

        """

        exploded_df = (
            df.assign(moldNo=df[mold_col].str.split("/"))
            .explode("moldNo")
            .reset_index(drop=True)
        )
        exploded_df["moldNo"] = exploded_df["moldNo"].str.strip()
        
        merged_df = exploded_df.merge(
            self.moldInfo_df[['moldNo', 'moldName', 'moldCavityStandard', 'moldSettingCycle']],
            how='left',
            on='moldNo'
        )
        
        merged_df["moldMaxHourCapacity"] = np.where(
            (merged_df["moldSettingCycle"].notna()) &
            (merged_df["moldSettingCycle"] > 0) &
            (merged_df["moldCavityStandard"].notna()) &
            (merged_df["moldCavityStandard"] > 0),
            (3600 / merged_df["moldSettingCycle"]) * merged_df["moldCavityStandard"],
            0
        )
        
        grouped_df = merged_df.groupby("itemCodeName", as_index=False).agg(
            moldNum=(mold_num_col, "first"),
            moldList=(mold_col, "first"),
            totalItemCapacity=("moldMaxHourCapacity", "sum")
        )
        
        grouped_df["avgItemCapacity"] = np.where(
            (grouped_df["moldNum"].notna()) & (grouped_df["moldNum"] > 0),
            grouped_df["totalItemCapacity"] / grouped_df["moldNum"],
            0
        )
        
        return grouped_df[["itemCodeName", 'moldNum', 'moldList', 'totalItemCapacity', "avgItemCapacity"]]

    def _estimate_item_capacity(self) -> pd.DataFrame:
        # Estimate item production capacity based on mold technical specifications for each item (its available mold list).
        if self.moldSpecificationSummary_df.empty:
            return pd.DataFrame(columns=['itemCodeName', 'moldNum', 'moldList', 'totalItemCapacity', 'avgItemCapacity'])
        
        df = self.moldSpecificationSummary_df.copy()
        df["itemCodeName"] = self._create_item_code_name(df)
        return self._compute_mold_capacity(df, "moldList", "moldNum")

    def _calculate_mold_capacity(self, in_progress_df: pd.DataFrame) -> pd.DataFrame:
        # Estimate item production capacity based on mold technical specifications for used mold historical records.
        df = in_progress_df.copy()
        return self._compute_mold_capacity(df, "moldHist", "moldHistNum")

    @staticmethod
    def _create_item_code_name(df):
        """
        Create a combined item identifier in the format "itemCode(itemName)".

        This helper function is used to uniquely identify each product by combining
        its code and name, ensuring human-readable and distinct item labels across
        different datasets (e.g., molds, purchase orders, production records).

        Args:
            df: DataFrame containing at least 'itemCode' and 'itemName' columns.

        Returns:
            pd.Series: Combined string column
        """
        # Combine item code and item name to form a unique label
        return df["itemCode"].astype(str) + "(" + df["itemName"].astype(str) + ")"

    @staticmethod
    def _process_pro_status(product_records_df: pd.DataFrame) -> pd.DataFrame:
        """
        Aggregate production records to summarize the production status per PO (Purchase Order).

        This function condenses multiple production records belonging to the same
        PO into one row, summarizing production time range, total produced quantity,
        and mold usage information.

        Args:
            product_records_df: DataFrame containing raw production records with columns:
                - poNote: Purchase order number
                - recordDate: Production record timestamp
                - itemGoodQuantity: Produced quantity in each record
                - moldNo: Mold number used

        Returns:
            pd.DataFrame with aggregated production status per PO, including:
                - poNo: Purchase order number
                - firstRecord: Earliest record date
                - lastRecord: Latest record date
                - itemGoodQuantity: Total produced quantity
                - moldHistNum: Number of unique molds used
                - moldHist: Slash-separated list of molds used
        """
        # Group by PO to summarize production data
        pro_status = (
            product_records_df
            .groupby("poNote")
            .agg(
                firstRecord=("recordDate", "min"),            # First production record
                lastRecord=("recordDate", "max"),             # Last production record
                itemGoodQuantity=("itemGoodQuantity", "sum"), # Total produced quantity
                moldHistNum=("moldNo", "nunique"),            # Number of unique molds used
                moldHist=("moldNo", lambda x: "/".join(sorted(x.dropna().unique()))) # Mold list
            )
            .reset_index()
            .rename(columns={"poNote": "poNo"})               # Rename for consistency
        )

        # Return summarized PO-level production data
        return pro_status

    @staticmethod
    def _merge_purchase_status(purchase_orders, product_records):
        """
        Merge purchase order data with production records to determine manufacturing and ETA status.

        This method links purchase orders with their corresponding production
        records, evaluates whether they are finished or still in progress, and
        classifies their delivery timeliness based on ETA comparison.

        Args:
            purchase_orders: DataFrame containing purchase order details, must include:
                - poNo: Purchase order number
                - poETA: Expected Time of Arrival (datetime)
                - itemQuantity: Ordered quantity

            product_records: DataFrame containing production data used for aggregation.

        Returns:
            pd.DataFrame with purchase and production info merged, including:
                - proStatus: 'finished' if produced quantity >= ordered quantity, else 'unfinished'
                - etaStatus:
                    * 'ontime': Finished before ETA, or unfinished but ETA not passed
                    * 'late': Finished after ETA, or unfinished and ETA already passed
                    * 'unknown': No production record found
        """

        # Aggregate production status per PO
        pro_status = MonthLevelDataProcessor._process_pro_status(product_records)

        # Merge purchase orders with production data
        merged_df = purchase_orders.merge(pro_status, how='left', on='poNo')

        # Determine production completion status
        # "finished" if produced quantity >= ordered quantity, else "unfinished"
        merged_df["proStatus"] = np.where(
            (merged_df['itemGoodQuantity'].notna()) &
            (merged_df["itemGoodQuantity"] >= merged_df["itemQuantity"]),
            "finished",
            "unfinished"
        )

        # Return the merged DataFrame with production and delivery status
        return merged_df

    @staticmethod
    def _analyze_unfinished_pos(unfinished_df: pd.DataFrame,
                                analysis_timestamp):

        """
        Analyze unfinished Purchase Orders (POs) by mold usage and estimate production lead times.

        This function examines ongoing or delayed POs grouped by mold usage to evaluate
        production progress, identify potential capacity constraints, and forecast
        remaining lead times. It calculates cumulative production loads and compares
        estimated processing durations with expected delivery timelines (ETA) to detect
        risks of overcapacity or overdue orders.

        Parameters
        ----------
        unfinished_df : pandas.DataFrame
            DataFrame containing unfinished PO records with the following columns:
            - **moldList** : str
            - **poReceivedDate** : datetime
            - **poETA** : datetime
            - **itemRemainQuantity** : float
            - **totalItemCapacity** : float
            - **avgItemCapacity** : float
            - *(optional)* **lastRecord** : datetime

        analysis_timestamp : datetime
            The timestamp representing the "current" moment of analysis
            (used to calculate remaining lead time and overdue status).

        Returns
        -------
        pandas.DataFrame
            A DataFrame with enhanced analytical metrics, including:
            - **accumulatedQuantity**, **accumulatedRate** : cumulative remaining quantity per mold.
            - **poOTD**, **poRLT** : order-to-delivery time and remaining lead time.
            - **avgEstimatedLeadtime**, **totalEstimatedLeadtime** : estimated lead times based on mold capacity.
            - **avgCumsumLT**, **totalCumsumLT** : cumulative lead times across unfinished POs in the same mold.
            - **is_overdue** : bool flag for orders behind schedule.
            - **etaStatus** : categorical status (“ontime” or “late”).
            - **capacityWarning** : bool flag for overcapacity risk.
            - **capacitySeverity** : categorical severity label ("normal", "high", "critical").

        Notes
        -----
        - All lead time estimations are normalized to **days**.
        - Overcapacity detection compares cumulative required time vs. remaining ETA window.
        - The function assumes `poETA` and `poReceivedDate` are timezone-aware or consistent.
        """

        HOURS_PER_DAY = 24

        # Preprocess and normalize mold list
        df = unfinished_df.copy()

        # Ensure moldList is sorted (so that same molds appear consistently)
        df['moldList'] = df['moldList'].str.split('/').apply(lambda x: '/'.join(sorted(x)) if x is not None else None)

        # Sort by mold and PO date to prepare for cumulative sum
        merged_df = (df
                    .sort_values(['moldList', 'poReceivedDate', 'poETA'])
                    .assign(
                        # Cumulative remaining quantity per mold (sum of unfinished items)
                        accumulatedQuantity=lambda x: x.groupby('moldList')['itemRemainQuantity'].cumsum())
                    )

        # Compute remained quantity per PO
        merged_df['completionProgress'] = (1 - merged_df['itemRemainQuantity']/merged_df['itemQuantity']).round(2)
        
        # Group by 'moldList'
        grouped = merged_df.groupby('moldList')

        # Compute total remaining quantity per mold
        merged_df['totalRemainByMold'] = grouped['itemRemainQuantity'].transform('sum')

        #Compute accumulated rate (progress ratio of each PO in mold group)
        merged_df['accumulatedRate'] = np.where(
            merged_df['totalRemainByMold'] == 0,
            np.nan,
            merged_df['accumulatedQuantity'] / merged_df['totalRemainByMold']
        )

        # Estimate lead time based on total and average mold capacity
        merged_df['totalEstimatedLeadtime'] = np.where(
            merged_df["totalItemCapacity"] > 0,
            merged_df['accumulatedQuantity'] / merged_df["totalItemCapacity"] / HOURS_PER_DAY,  # Convert hours to days
            np.nan
        )
        merged_df['avgEstimatedLeadtime'] = np.where(
            merged_df["avgItemCapacity"] > 0,
            merged_df['accumulatedQuantity'] / merged_df["avgItemCapacity"] / HOURS_PER_DAY,  # Convert hours to days
            np.nan
        )

        # Calculate Order-to-Delivery Time (OTD) and Remaining Lead Time (RLT)
        merged_df["poOTD"] = merged_df['poETA'] - merged_df['poReceivedDate']
        merged_df["poRLT"] = np.where(
            merged_df['poETA'] < analysis_timestamp,
            0, # Already past ETA → no remaining lead time
            merged_df['poETA'] - analysis_timestamp
        )

        # Calculate cumulative estimated lead time per mold
        # → Shows how total required production time builds up sequentially for each mold group
        merged_df['avgCumsumLT'] = grouped['avgEstimatedLeadtime'].transform('cumsum')
        merged_df['totalCumsumLT'] = grouped['totalEstimatedLeadtime'].transform('cumsum')

        # Determine whether mold capacity is exceeded
        merged_df['overTotalCapacity'] = np.where(
            (merged_df['totalCumsumLT'] > 0) & (merged_df["poRLT"].dt.days >= 0),
            pd.to_timedelta(merged_df['totalCumsumLT'], unit="D") > merged_df["poRLT"],
            False  # or np.nan for "unknown"
        )
        merged_df['overAvgCapacity'] = np.where(
            (merged_df['avgCumsumLT'] > 0) & (merged_df["poRLT"].dt.days>=0),
            pd.to_timedelta(merged_df['avgCumsumLT'], unit="D") > merged_df["poRLT"],
            False
        )

        # Convert estimated lead times from float (days) to timedelta
        merged_df['avgCumsumLT'] = pd.to_timedelta(merged_df['avgCumsumLT'], unit="D")
        merged_df['totalCumsumLT'] = pd.to_timedelta(merged_df['totalCumsumLT'], unit="D")

        # Flag overdue orders
        merged_df['is_overdue'] = (
            ((merged_df['poRLT'].dt.days == 0) | (merged_df['poRLT'] <= merged_df['avgCumsumLT'])) &
             (merged_df['itemRemainQuantity'] > 0))
        
        # Classify orders based on timeliness and completion status
        # --- Define condition flags ---
        is_in_progress = merged_df["poStatus"] == "in_progress"
        is_finished = merged_df["itemRemainQuantity"] == 0
        is_on_eta = merged_df["lastRecord"] <= merged_df["poETA"]
        is_within_eta = merged_df["avgCumsumLT"] < merged_df["poRLT"]

        # Evaluate ETA status
        merged_df["etaStatus"] = np.select(
            [
                is_in_progress & is_finished & is_on_eta,
                is_in_progress & is_finished & ~is_on_eta,
                is_in_progress & ~is_finished & is_within_eta,
                is_in_progress & ~is_finished & ~is_within_eta,
                ~is_in_progress & is_within_eta,
                ~is_in_progress & ~is_within_eta,
            ],
            [
                "ontime",
                "late",
                "ontime",
                "late",
                "expected_ontime",
                "late",
            ],
            default="unknown"
        )

        # Combine overcapacity flags into a unified warning
        merged_df['capacityWarning'] = (merged_df['overAvgCapacity'] | merged_df['overTotalCapacity'])

        # Categorize severity of capacity issues
        merged_df['capacitySeverity'] = np.select(
            [
                merged_df['overTotalCapacity'],   # Critical overcapacity
                merged_df['overAvgCapacity'],     # High utilization (may need support)
                ~merged_df['capacityWarning']     # Within capacity
            ],
            [
                'critical',    # Needs reschedule or outsourcing
                'high',        # Possibly requires additional molds or shifts
                'normal'       # Within acceptable range
            ],
            default='unknown'
        )

        # Add description columns (optional)
        merged_df['capacityExplanation'] = merged_df['capacitySeverity'].map({
            'normal': 'Within 1-mold capacity',
            'high': 'Need parallel molds',
            'critical': 'Exceeds max capacity'
        })

        # Convert estimated lead times from float (days) to timedelta
        merged_df['totalEstimatedLeadtime'] = pd.to_timedelta(merged_df['totalEstimatedLeadtime'], unit="D")
        merged_df['avgEstimatedLeadtime'] = pd.to_timedelta(merged_df['avgEstimatedLeadtime'], unit="D")


        return merged_df
    
    @staticmethod
    def _log_analysis_summary(record_month, 
                              analysis_timestamp, 
                              po_based_df, 
                              finished_df, 
                              unfinished_df):
        lines = []
        
        lines.append("=" * 60)
        lines.append(f"Analysis Results for {record_month}")
        lines.append(f"Analysis date: {analysis_timestamp.strftime('%Y-%m-%d')}")
        lines.append(f"Total Orders: {len(po_based_df)}")
        lines.append(f"Completed Orders Rate: {len(finished_df)}/{len(po_based_df)}")
        lines.append(f"Remaining Orders Rate: {len(unfinished_df)}/{len(po_based_df)}")
        lines.append(f"Orders with Capacity Warning: {unfinished_df['capacityWarning'].sum()}")
        lines.append(f"Capacity Severity Distribution: {unfinished_df['capacitySeverity'].value_counts().to_dict()}")
        
        backlog_df = po_based_df[po_based_df['is_backlog'] == True]
        backlog_count = len(backlog_df)
        backlog_pos = backlog_df['poNo'].tolist()
        lines.append(f"Backlog Orders: {backlog_count}-({backlog_pos})")
        
        lines.append("=" * 60)
        
        return "\n".join(lines)
    
    @staticmethod
    def _log_validation_summary(record_month,
                                original_analysis_date,
                                adjusted_record_month, 
                                analysis_timestamp):
        lines = []
        lines.append("=" * 60)
        lines.append("VALIDATION SUMMARY")
        lines.append("=" * 60)
        lines.append(f"Record month (requested): {pd.Period(record_month, freq='M')}")
        
        if adjusted_record_month != record_month:
            lines.append(f"Record month (adjusted): {adjusted_record_month}")
        
        lines.append(f"Analysis date (validated): {analysis_timestamp.date()}")
        
        if original_analysis_date != analysis_timestamp:
            lines.append(f"  └─ Adjusted from: {original_analysis_date.date()}")
        
        lines.append("=" * 60)
        
        return "\n".join(lines)