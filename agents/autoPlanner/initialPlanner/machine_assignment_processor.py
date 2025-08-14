import pandas as pd
import re
import ast
from collections import defaultdict
from typing import Dict, List, Tuple
from loguru import logger

class MachineAssignmentProcessor:

    """
    A class to handle manufacturing assignment processing with optimized methods.
    """

    def __init__(self,
                 assigned_matrix: pd.DataFrame,
                 mold_lead_times: pd.DataFrame,
                 pending_data: pd.DataFrame,
                 machine_info_df: pd.DataFrame,
                 producing_mold_list: List,
                 producing_info_list: List):

        self.logger = logger.bind(class_="MachineAssignmentProcessor")

        self.assigned_matrix = assigned_matrix
        self.mold_lead_times = mold_lead_times
        self.pending_data = pending_data
        self.machine_info_df = machine_info_df
        self.producing_mold_list = producing_mold_list
        self.producing_info_list = producing_info_list

        # Cache frequently used mappings
        self._item_to_po_mapping = None
        self._lead_time_mapping = None
        self._machine_info_mapping = None

    @property
    def item_to_po_mapping(self) -> Dict[str, List[Tuple]]:

        """Cached mapping from itemCode to PO info."""

        if self._item_to_po_mapping is None:
            self._item_to_po_mapping = (
                self.pending_data
                .assign(poInfo=lambda df: list(zip(df['poNo'], df['itemQuantity'], df['poETA'])))
                .groupby('itemCode')['poInfo']
                .apply(list)
                .to_dict()
            )
        return self._item_to_po_mapping

    @property
    def lead_time_mapping(self) -> Dict[str, float]:

        """Cached mapping from moldNo to moldLeadTime."""

        if self._lead_time_mapping is None:
            lead_times_unique = self.mold_lead_times.drop_duplicates(subset=['moldNo', 'itemCode'])
            if len(lead_times_unique) < len(self.mold_lead_times):
                self.logger.warning("Found {} duplicate moldNo entries in lead_times. Using first occurrence.",
                                    len(self.mold_lead_times) - len(lead_times_unique))
            self._lead_time_mapping = lead_times_unique.set_index('moldNo')['moldLeadTime'].to_dict()
        return self._lead_time_mapping

    @property
    def machine_info_mapping(self) -> Dict[str, str]:

        """Cached mapping from machineCode to machineNo."""

        if self._machine_info_mapping is None:
            self._machine_info_mapping = self.machine_info_df.set_index('machineCode')['machineNo'].to_dict()
        return self._machine_info_mapping

    def get_assignment_summary(self) -> pd.DataFrame:

        """
        Convert detailed assignment matrix into readable summary format.
        Optimized with vectorized operations.
        """

        self.logger.info("Generating assignment summary...")

        # Handle duplicate moldNo in lead_times by taking first occurrence
        lead_times_unique = self.mold_lead_times[['itemCode', 'moldNo']].drop_duplicates(subset=['itemCode', 'moldNo'])

        # Check if there are still duplicates and warn
        if len(lead_times_unique) < len(self.mold_lead_times[['itemCode', 'moldNo']]):
            self.logger.warning("Found duplicate moldNo in lead_times. Using first occurrence for each moldNo.")

        # Merge without validation first, then check manually if needed
        df = (self.assigned_matrix
              .reset_index()
              .merge(lead_times_unique,
                    how='left', on='moldNo'))

        # Vectorized string operations
        df['pairItemMold'] = '(' + df['moldNo'] + ',' + df['itemCode'] + ')'
        df = df.drop(columns=['moldNo', 'itemCode']).set_index('pairItemMold')

        # Transpose and generate assignments in one go
        df.columns.name = 'machineCode'
        df_t = df.T

        # Optimized assignment generation using list comprehension
        df_t['assignedMolds'] = [
            ','.join(col for col in df_t.columns if df_t.loc[idx, col] != 0)
            for idx in df_t.index
        ]

        result = df_t.reset_index()[['machineCode', 'assignedMolds']]
        result.columns.name = None

        self.logger.info("Generated summary for {} machines", len(result))
        return result

    def convert_itemcode_to_pono(self, assignment_df: pd.DataFrame) -> pd.DataFrame:

        """
        Convert assignedMolds from (moldNo,itemCode) to (moldNo,(poNo,quantity,ETA)).
        Optimized with compiled regex and better error handling.
        """

        self.logger.info("Converting item codes to PO numbers...")

        # Compile regex pattern once for better performance
        pair_pattern = re.compile(r'\(([^,]+),([^)]+)\)')

        def convert_mold_string(mold_string: str) -> str:
            if pd.isna(mold_string) or not mold_string.strip():
                return ''

            pairs = pair_pattern.findall(mold_string)
            converted = []

            for mold_no, item_code in pairs:
                mold_no, item_code = mold_no.strip(), item_code.strip()
                po_infos = self.item_to_po_mapping.get(item_code)

                if po_infos:
                    converted.extend(f"('{mold_no}',{po})" for po in po_infos)
                else:
                    converted.append(f"('{mold_no}','{item_code}')")

            return ','.join(converted)

        def parse_assigned_molds(converted_str: str) -> Dict[str, List[Tuple]]:
            if not converted_str.strip():
                return {}

            try:
                molds = ast.literal_eval(f"[{converted_str}]")
                result = defaultdict(list)
                for mold_no, po_info in molds:
                    result[mold_no].append(tuple(po_info))
                return dict(result)
            except (ValueError, SyntaxError) as e:
                logger.warning("Failed to parse: {}... Error: {}",
                                    converted_str[:50], e)
                return {}

        # Use vectorized operations where possible
        df = assignment_df.copy()
        df['assignedMolds'] = (
            df['assignedMolds']
            .fillna('')
            .apply(convert_mold_string)
            .apply(parse_assigned_molds)
        )

        self.logger.info("Conversion completed")
        return df

    def flatten_assignments(self, df: pd.DataFrame) -> pd.DataFrame:

        """
        Flatten assignment data with optimized list comprehension.
        """

        self.logger.info("Flattening assignment data...")

        rows = []
        for _, row in df.iterrows():
            machine = row['machineCode']
            molds = row['assignedMolds']

            if not molds:
                rows.append({
                    'machineCode': machine,
                    'moldNo': None,
                    'itemCode': None,
                    'itemQuantity': None,
                    'poETA': None,
                    'moldLeadTime': None
                })
            else:
                for mold_no, items in molds.items():
                    mold_lead_time = self.lead_time_mapping.get(mold_no)
                    rows.extend([
                        {
                            'machineCode': machine,
                            'moldNo': mold_no,
                            'itemCode': item_code,
                            'itemQuantity': quantity,
                            'poETA': date,
                            'moldLeadTime': mold_lead_time
                        }
                        for item_code, quantity, date in items
                    ])

        result = pd.DataFrame(rows)
        self.logger.info("Flattened to {} rows", len(result))
        return result

    def prioritize_by_machine(self,
                              flattened_df: pd.DataFrame) -> pd.DataFrame:

        """
        Optimized prioritization with proper date handling.
        Priority order:
        1. Producing molds (moldNo in producing_mold_list) - highest priority
        2. Earliest ETA → Shortest moldLeadTime → Smallest itemQuantity
        Machines without assignments will be given priority 0.
        """

        self.logger.info("Prioritizing assignments by machine...")

        # Convert dates and numeric values once with proper error handling
        df = flattened_df.copy()
        df['poETA'] = pd.to_datetime(df['poETA'], errors='coerce')
        df['itemQuantity'] = pd.to_numeric(df['itemQuantity'], errors='coerce').fillna(0)
        df['moldLeadTime'] = pd.to_numeric(df['moldLeadTime'], errors='coerce').fillna(0).astype('Int64')

        # Create producing mold priority flag (0 for producing molds, 1 for others)
        # This will be used as the first sort key to give producing molds highest priority
        if self.producing_mold_list is not None:
            self.logger.info('There are some molds in producing list, they will be the first priorities. Details: {}', self.producing_mold_list)
            df['is_producing'] = df['moldNo'].isin(self.producing_mold_list).map({True: 0, False: 1})
        else:
            df['is_producing'] = 1  # All get same priority if no producing list provided

        # Sort with multiple keys efficiently
        # Priority: Producing molds first (0) → Earliest ETA (ascending) → Shortest moldLeadTime (ascending) → Smallest itemQuantity (ascending)
        df_sorted = df.sort_values(
            by=['machineCode', 'is_producing', 'poETA', 'moldLeadTime', 'itemQuantity'],
            ascending=[True, True, True, True, True],
            na_position='last'  # Handle NaT dates and NaN values properly
        )

        # Create a mask for rows with actual assignments (i.e., moldNo is not null)
        has_assignment = df_sorted['moldNo'].notna()

        # Initialize priority rank to 0 for all rows
        df_sorted['priorityRank'] = 0

        # Assign priority ranks (starting from 1) only to rows with valid assignments
        df_sorted.loc[has_assignment, 'priorityRank'] = (
            df_sorted[has_assignment].groupby('machineCode').cumcount() + 1
        )

        # Drop the temporary helper column
        df_sorted = df_sorted.drop('is_producing', axis=1)

        self.logger.info("Prioritization completed with producing molds → ETA → moldLeadTime → itemQuantity priority")
        return df_sorted.reset_index(drop=True)

    def optimize_mold_assignment(self, df: pd.DataFrame):
        """
        Optimize mold assignment to machines to avoid unnecessary transfers.
        Move ALL jobs with the same mold to the target machine for efficiency.
        Jobs in producing_info_list get highest priority.

        Args:
            df: DataFrame containing machine and mold information
            self.producing_info_list: List of [Machine No., Mold Code] requested for production

        Returns:
            Optimized DataFrame and information about the changes made
        """

        # Create a copy to avoid modifying the original data
        df_optimized = df.copy()

        for machine_code, requested_mold in self.producing_info_list:
            self.logger.info("\nProcessing request: Machine {} requires mold {}",
                            machine_code, requested_mold)

            # Find the requested machine
            target_machine_rows = df_optimized[df_optimized['machineCode'] == machine_code]

            if target_machine_rows.empty:
                self.logger.warning("Machine {} not found", machine_code)
                continue

            # Check if the mold is already on the target machine
            mold_on_target = target_machine_rows[target_machine_rows['moldNo'] == requested_mold]

            if not mold_on_target.empty:
                self.logger.info("Mold {} is already on machine {} - No change needed",
                              requested_mold, machine_code)
                continue

            # Find ALL jobs with this mold (regardless of which machine they're on)
            jobs_with_mold = df_optimized[df_optimized['moldNo'] == requested_mold].copy()

            if jobs_with_mold.empty:
                self.logger.warning("Mold {} does not exist in the system", requested_mold)
                continue

            # Get existing jobs on target machine (excluding empty rows)
            existing_jobs_on_target = df_optimized[
                (df_optimized['machineCode'] == machine_code) &
                (~pd.isna(df_optimized['moldNo'])) &
                (df_optimized['moldNo'] != '') &
                (~pd.isna(df_optimized['itemCode'])) &
                (df_optimized['itemCode'] != '') &
                (df_optimized['itemQuantity'] > 0)
            ].copy()

            # Remove empty rows from target machine
            empty_rows = df_optimized[
                (df_optimized['machineCode'] == machine_code) &
                ((pd.isna(df_optimized['moldNo']) | (df_optimized['moldNo'] == '')) |
                (pd.isna(df_optimized['itemCode']) | (df_optimized['itemCode'] == '')) |
                (df_optimized['itemQuantity'] == 0) | pd.isna(df_optimized['itemQuantity']))
            ]

            if not empty_rows.empty:
                df_optimized = df_optimized.drop(empty_rows.index).reset_index(drop=True)
                self.logger.info("Removed {} empty rows from machine {}",
                              len(empty_rows), machine_code)

            # Get jobs to move (exclude jobs already on target machine)
            jobs_to_move = df_optimized[
                (df_optimized['moldNo'] == requested_mold) &
                (df_optimized['machineCode'] != machine_code)
            ].copy()

            moved_jobs = []

            # Move all jobs with the requested mold to target machine
            for idx in jobs_to_move.index:
                current_machine = df_optimized.loc[idx, 'machineCode']
                df_optimized.loc[idx, 'machineCode'] = machine_code
                moved_jobs.append({
                    'itemCode': df_optimized.loc[idx, 'itemCode'],
                    'from_machine': current_machine,
                    'quantity': df_optimized.loc[idx, 'itemQuantity'],
                    'original_priority': df_optimized.loc[idx, 'priorityRank']
                })

            # Re-prioritize jobs on target machine
            # Get all jobs now on target machine (including moved ones)
            all_jobs_on_target = df_optimized[df_optimized['machineCode'] == machine_code].copy()

            # Separate moved jobs (with requested mold) from existing jobs
            moved_job_indices = []
            existing_job_indices = []

            for idx in all_jobs_on_target.index:
                if df_optimized.loc[idx, 'moldNo'] == requested_mold:
                    moved_job_indices.append(idx)
                else:
                    existing_job_indices.append(idx)

            # Sort moved jobs by their original priority (maintain relative order)
            moved_jobs_data = [(idx, df_optimized.loc[idx, 'priorityRank']) for idx in moved_job_indices]
            moved_jobs_data.sort(key=lambda x: x[1])  # Sort by original priority

            # Assign priorities: moved jobs get priority 1, 2, 3...
            new_priority = 1
            for idx, _ in moved_jobs_data:
                df_optimized.loc[idx, 'priorityRank'] = new_priority
                new_priority += 1

            # If there were existing jobs on target machine, push their priorities down
            if existing_job_indices:
                num_moved_jobs = len(moved_job_indices)

                # Sort existing jobs by their current priority
                existing_jobs_data = [(idx, df_optimized.loc[idx, 'priorityRank']) for idx in existing_job_indices]
                existing_jobs_data.sort(key=lambda x: x[1])

                # Assign new priorities starting after moved jobs
                for idx, _ in existing_jobs_data:
                    df_optimized.loc[idx, 'priorityRank'] = new_priority
                    new_priority += 1

            # Update priorities on source machines (re-sequence after job removal)
            source_machines = set(job['from_machine'] for job in moved_jobs)

            for source_machine in source_machines:
                source_jobs = df_optimized[df_optimized['machineCode'] == source_machine]

                if source_jobs.empty:
                    # Create empty row for the now-empty machine
                    empty_row = pd.DataFrame({
                        'machineCode': [source_machine],
                        'moldNo': [None],
                        'itemCode': [None],
                        'itemQuantity': [0],
                        'poETA': [pd.NaT],
                        'moldLeadTime': [None],
                        'priorityRank': [0]
                    })

                    df_optimized = pd.concat([df_optimized, empty_row], ignore_index=True)

                    self.logger.info("Machine {} is now empty, added default empty row with priority 0",
                                  source_machine)
                else:
                    # Sort by current priority and re-assign starting from 1
                    source_jobs_sorted = source_jobs.sort_values('priorityRank')
                    for new_priority, idx in enumerate(source_jobs_sorted.index, 1):
                        df_optimized.loc[idx, 'priorityRank'] = new_priority

            # Log the transfer details
            total_moved = len(moved_jobs)
            total_quantity = sum(job['quantity'] for job in moved_jobs if pd.notna(job['quantity']))

            self.logger.info("Moved {} jobs with mold {} to machine {} (Total quantity: {})",
                            total_moved, requested_mold, machine_code, total_quantity)

            for job in moved_jobs:
                self.logger.info("  - Job {} (Qty: {}, Original Priority: {}) from machine {}",
                              job['itemCode'], job['quantity'], job['original_priority'], job['from_machine'])

            # Log final priority structure on target machine
            final_target_jobs = df_optimized[df_optimized['machineCode'] == machine_code].sort_values('priorityRank')
            self.logger.info("Final priority on machine {}:", machine_code)
            for _, row in final_target_jobs.iterrows():
                self.logger.info("  Priority {}: {} - {}",
                              row['priorityRank'], row['moldNo'], row['itemCode'])

        return df_optimized

    @staticmethod
    def sort_by_machine_number(df: pd.DataFrame) -> pd.DataFrame:

        """
        Optimized machine number sorting with better error handling.
        After sorting by machine number, also sort by priority if available.
        """

        if 'machineNo' not in df.columns:
            logger.warning("machineNo column not found, skipping sort")
            return df

        df_sorted = df.copy()

        # Extract numeric part with error handling
        numeric_extract = df_sorted['machineNo'].str.extract(r'NO\.?(\d+)', expand=False)
        df_sorted['machineNo_numeric'] = pd.to_numeric(numeric_extract, errors='coerce')

        # Build sort keys
        sort_keys = ['machineNo_numeric']
        if 'priorityRank' in df.columns:
            sort_keys.append('priorityRank')

        # Sort and clean up
        df_sorted = (
            df_sorted
            .sort_values(by=sort_keys, na_position='last')
            .drop(columns='machineNo_numeric')
            .reset_index(drop=True)
        )

        return df_sorted

    def beautify_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:

        """
        Enhanced beautification with better formatting and column organization.
        """

        self.logger.info("Beautifying dataframe...")

        beautified = df.copy()

        # Enhanced date formatting
        if 'poETA' in beautified.columns:
            beautified['poETA'] = pd.to_datetime(beautified['poETA'], errors='coerce')

        # Better numeric formatting
        if 'itemQuantity' in beautified.columns:
            beautified['itemQuantity'] = (
                pd.to_numeric(beautified['itemQuantity'], errors='coerce')
                .fillna(0)
                .astype('Int64')  # Nullable integer type
            )

        # Add machine info if not present
        if 'machineNo' not in beautified.columns and 'machineCode' in beautified.columns:
            beautified['machineNo'] = beautified['machineCode'].map(self.machine_info_mapping)

        # Sort by machine number
        beautified = self.sort_by_machine_number(beautified)

        # Rename columns for clarity
        column_mapping = {
            'machineCode': 'Machine Code',
            'machineNo': 'Machine No.',
            'moldNo': 'Assigned Mold',
            'itemCode': 'Item Code',
            'itemQuantity': 'PO Quantity',
            'poETA': 'ETA (PO Date)',
            'priorityRank': 'Priority in Machine',
            'moldLeadTime': 'Mold Lead Time'
        }

        beautified = beautified.rename(columns=column_mapping)

        # Reorder columns logically
        preferred_order = [
            'Machine No.', 'Machine Code', 'Assigned Mold', 'Item Code',
            'PO Quantity', 'ETA (PO Date)', 'Mold Lead Time', 'Priority in Machine'
        ]

        # Only include columns that exist
        available_cols = [col for col in preferred_order if col in beautified.columns]
        beautified = beautified[available_cols]

        self.logger.info("Beautification completed")
        return beautified

    def process_all(self) -> pd.DataFrame:

        """
        Execute the complete processing pipeline with error handling.
        """

        try:
            self.logger.info("Starting complete assignment processing pipeline...")

            # Step 1: Generate assignment summary
            assignment_summary = self.get_assignment_summary()

            # Step 2: Convert item codes to PO numbers
            converted_df = self.convert_itemcode_to_pono(assignment_summary)
            self.logger.info("Convert item codes to PO numbers: {} - {}", len(converted_df), converted_df.columns)

            # Step 3: Flatten the data
            flattened_df = self.flatten_assignments(converted_df)
            self.logger.info("Flatten the data: {} - {}", len(flattened_df), flattened_df.columns)

            # Step 4: Prioritize by machine
            prioritized_df = self.prioritize_by_machine(flattened_df)
            self.logger.info("Prioritize by machine: {} - {}", len(prioritized_df), prioritized_df.columns)

            # Step 5: Optimize and beautify the final result
            optimized_df = self.optimize_mold_assignment(prioritized_df)
            final_result = self.beautify_dataframe(optimized_df)
            self.logger.info("Pipeline completed successfully. Final result: {} - ", len(final_result), final_result.columns)

            return final_result

        except Exception as e:
            self.logger.error("Error in processing pipeline: {}", e)
            raise