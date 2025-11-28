import json
import os
from loguru import logger
from typing import Dict, Set, Tuple, Optional, List, Any
import pandas as pd
from pathlib import Path
from datetime import datetime
from agents.decorators import validate_init_dataframes
from agents.utils import read_change_log, load_annotation_path
import shutil

# Decorator to validate DataFrames are initialized with the correct schema
@validate_init_dataframes(lambda self: {
    "product_df": list(self.databaseSchemas_data['dynamicDB']['productRecords']['dtypes'].keys()),
    "mold_df": list(self.databaseSchemas_data['staticDB']['moldInfo']['dtypes'].keys()),
    "machine_df": list(self.databaseSchemas_data['staticDB']['machineInfo']['dtypes'].keys())
})

class MachineMoldPairTracker:
    """Class to track machine-mold pair changes over time"""

    def __init__(self,
                 productRecords_df: pd.DataFrame,
                 moldInfo_df: pd.DataFrame,
                 machineInfo_df: pd.DataFrame,
                 databaseSchemas_path: str = 'database/databaseSchemas.json',
                 output_dir: str = 'agents/shared_db/HardwareChangeAnalyzer/MachineMoldPairTracker',
                 change_log_name: str = 'change_log.txt'):

        self.logger = logger.bind(class_="MachineMoldPairTracker")

        # Load database schema and database paths annotation
        self.databaseSchemas_data = load_annotation_path(Path(databaseSchemas_path).parent,
                                                         Path(databaseSchemas_path).name)

        self.product_df = productRecords_df[productRecords_df['moldNo'].notna()].copy()
        self.mold_df = moldInfo_df.copy()
        self.machine_df = machineInfo_df.copy()

        self.filename_prefix = 'mold_machine_pairing'

        self.output_dir = Path(output_dir)
        self.change_log_name = change_log_name

    def data_process(self,
                     record_date: pd.Timestamp):

        self.logger.info("Start processing...")
        new_record_date, has_change, new_changes, machine_molds_dict = self.check_new_pairs(record_date)

        if has_change:
            self.logger.info("New machine-mold pair changes detected.")
            # Setup directories and timestamps
            timestamp_now = datetime.now()
            timestamp_str = timestamp_now.strftime("%Y-%m-%d %H:%M:%S")
            timestamp_file = timestamp_now.strftime("%Y%m%d_%H%M")

            newest_dir = self.output_dir / "newest"
            newest_dir.mkdir(parents=True, exist_ok=True)

            historical_dir = self.output_dir / "historical_db"
            historical_dir.mkdir(parents=True, exist_ok=True)

            pair_change_dir = newest_dir / "pair_changes"
            pair_change_dir.mkdir(parents=True, exist_ok=True)

            log_entries = [f"[{timestamp_str}] Saving new version...\n"]

            (mold_machine_df, mold_tonnage_summary_df,
            first_mold_usage_df, first_paired_mold_machine_df) = self._analyze_mold_machined_summary()

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
                elif f.is_dir():
                    try:
                        dest_folder = historical_dir / f.name
                        dest_folder.mkdir(parents=True, exist_ok=True)
                        sub_count = sum(1 for sub in f.iterdir() if sub.is_file())
                        for sub in f.iterdir():
                            if sub.is_file():
                                dest_file = dest_folder / sub.name
                                shutil.move(str(sub), dest_file)
                        log_entries.append(f"  ⤷ Moved {sub_count} files in folder {str(f)} → {dest_folder}\n")
                        self.logger.info("Moved {} files in folder {} to {}", 
                                         sub_count, str(f), dest_folder)
                  
                    except Exception as e:
                        self.logger.error("Failed to move {} files from folder {} to {}: {}", 
                                          sub_count, str(f), dest_folder, e)
                        raise OSError(f"Failed to move folder {f.name}: {e}")

            # Save layout changes
            try:
                for time_str in machine_molds_dict.keys():
                    timestamp = datetime.fromisoformat(time_str).strftime("%Y-%m-%d")
                    json_filepath = pair_change_dir / f"{timestamp}_{self.filename_prefix}_{new_record_date}.json"

                    with open(json_filepath, 'w', encoding='utf-8') as f:
                        json.dump(machine_molds_dict[time_str], f, ensure_ascii=False, indent=2)

                    log_entries.append(f"  ⤷ Saved new file: {json_filepath}\n")
                
                self.logger.info(f"Machine-mold pair changes saved to {pair_change_dir}, total {len(machine_molds_dict)} files")

            except Exception as e:
                self.logger.error("Failed to analyze machine-mold pair changes: {}", e)
                raise OSError(f"Failed to analyze machine-mold pair changes: {e}")

            # Save machine layout historical change
            try:
                excel_file_name = f"{timestamp_file}_{self.filename_prefix}_{new_record_date}.xlsx"
                excel_file_path = newest_dir / excel_file_name

                # Create pivot tables
                pivot_machine_mold = first_paired_mold_machine_df.pivot(
                    index='machineCode',
                    columns='moldNo',
                    values='firstDate'
                )
                pivot_mold_machine = first_paired_mold_machine_df.pivot(
                    index='moldNo',
                    columns='machineCode',
                    values='firstDate'
                    )

                excel_data = {
                    "moldTonageUnmatched": mold_machine_df[mold_machine_df['tonnageMatched'] == False],
                    "machineMoldFirstRunPair": pivot_machine_mold,
                    "moldMachineFirstRunPair": pivot_mold_machine
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
                analysis_summary_name = f"{timestamp_file}_{self.filename_prefix}_summary_{new_record_date}.txt"
                analysis_summary_path = newest_dir / analysis_summary_name

                analyzed_results_summary = self._generate_analyzed_results_summary(
                mold_tonnage_summary_df, first_mold_usage_df)

                with open(analysis_summary_path, "w", encoding="utf-8") as log_file:
                    log_file.writelines(analyzed_results_summary)
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

            return has_change, mold_tonnage_summary_df, first_mold_usage_df, first_paired_mold_machine_df, log_entries

        self.logger.info("No new machine-mold pair changes detected.")

        return has_change, None, None, None, None

    def check_new_pairs(self,
                        new_record_date: pd.Timestamp) -> Tuple[str, bool, Set[Tuple[str, str]], Dict[str, Dict[str, List[str]]]]:
        """
        Check for new machine-mold pairs

        Returns:
            tuple: (has_new_pairs, new_pairs_set, all_data)
        """
        # Load existing data
        machine_molds_dict = self.load_machine_molds()

        new_record_date_str = new_record_date.strftime("%Y-%m-%d")

        if not machine_molds_dict:
            self.logger.info("No existing data. Detecting all...")
            machine_molds_dict = self.detect_all_machine_molds()
            # Return all pairs as "new"
            all_pairs = self._extract_all_pairs(machine_molds_dict)
            return new_record_date_str, True, all_pairs, machine_molds_dict

        # Get current machine-molds mapping
        current_mapping = self._get_machine_molds_at_date(new_record_date)

        # Get historical pairs
        historical_pairs = self._extract_latest_pairs(machine_molds_dict)

        # Get current pairs
        current_pairs = set()
        for machine, molds in current_mapping.items():
            for mold in molds:
                current_pairs.add((machine, mold))

        # Find new pairs
        new_pairs = current_pairs - historical_pairs

        if new_pairs:
            new_date_str = new_record_date.isoformat()
            machine_molds_dict[new_date_str] = current_mapping

            self.logger.info(f"Found {len(new_pairs)} new pairs at {new_date_str}:")
            for machine, mold in new_pairs:
                self.logger.info(f"  - {machine} -> {mold}")

        return new_record_date_str, len(new_pairs) > 0, new_pairs, machine_molds_dict

    def _prepare_data(self):
        """Prepare dataframe"""
        if not pd.api.types.is_datetime64_any_dtype(self.product_df['recordDate']):
            self.product_df['recordDate'] = pd.to_datetime(self.product_df['recordDate'])

    def detect_all_machine_molds(self) -> Dict[str, Dict[str, List[str]]]:
        """Detect all machine-mold mappings from dataframe"""
        try:
            # Prepare data
            self._prepare_data()

            # Get dates when new machine-mold combinations appear
            change_dates = (
                self.product_df[['recordDate', 'machineCode', 'moldNo']]
                .sort_values('recordDate')
                .drop_duplicates(['machineCode', 'moldNo'], keep='first')
                ['recordDate']
                .unique()
            )

            machine_molds_dict = {}
            for date in sorted(change_dates):
                mapping = self._get_machine_molds_at_date(date)
                machine_molds_dict[date.isoformat()] = mapping

            self.logger.info(f"Detected {len(machine_molds_dict)} change dates")
            return machine_molds_dict

        except Exception as e:
            self.logger.error(f"Error detecting machine-molds: {str(e)}")
            raise

    def _get_machine_molds_at_date(self, target_date: pd.Timestamp) -> Dict[str, List[str]]:
        """Get machine->molds mapping at specific date"""
        df_filtered = self.product_df[self.product_df['recordDate'] <= target_date]
        mapping = df_filtered.groupby('moldNo')['machineCode'].apply(
            lambda x: sorted(list(x.unique()))
        ).to_dict()

        # Convert to string keys and values
        return {str(k): [str(v) for v in vals] for k, vals in mapping.items()}

    def load_machine_molds(self) -> Optional[Dict[str, Dict[str, List[str]]]]:
        """Load from JSON file"""

        try:
            stored_path = read_change_log(self.output_dir, self.change_log_name)

            latest_path = max(
                (Path(p) for p in stored_path),
                key=lambda p: datetime.strptime(p.name.split("_")[0], "%Y-%m-%d")
            )

            if not os.path.exists(latest_path):
                self.logger.warning(f"File not found: {latest_path}")
                return None

            self.logger.info('Loading machine-mold pair changes from {}', latest_path)
            with open(latest_path, 'r', encoding='utf-8') as f:
                return json.load(f)

        except Exception as e:
            self.logger.error(f"Error loading: {str(e)}")
            return None

    def _extract_all_pairs(self, machine_molds_dict: Dict[str, Dict[str, List[str]]]) -> Set[Tuple[str, str]]:
        """Extract all machine-mold pairs from dict"""
        all_pairs = set()
        for date_mapping in machine_molds_dict.values():
            for mold, machines in date_mapping.items():
                for machine in machines:
                    all_pairs.add((mold, machine))
        return all_pairs

    def _extract_latest_pairs(self, machine_molds_dict: Dict[str, List[str]]) -> Set[Tuple[str, str]]:
        """Extract all machine-mold pairs from dict"""
        all_pairs = set()
        for mold, machines in machine_molds_dict.items():
            for machine in machines:
                all_pairs.add((mold, machine))
        return all_pairs

    def get_latest_mapping(self, machine_molds_dict: Dict[str, Dict[str, List[str]]]) -> Dict[str, List[str]]:
        """Get latest machine->molds mapping"""
        if not machine_molds_dict:
            return {}

        latest_date = max(machine_molds_dict.keys())
        return machine_molds_dict[latest_date]

    def get_summary(self, machine_molds_dict: Dict[str, Dict[str, List[str]]]) -> pd.DataFrame:
        """Get summary statistics"""
        summary_data = []
        for date_str, mapping in machine_molds_dict.items():
            total_pairs = sum(len(machines) for machines in mapping.values())
            summary_data.append({
                'date': pd.to_datetime(date_str),
                'num_machines': len(mapping),
                'total_pairs': total_pairs,
                'avg_molds_per_machine': total_pairs / len(mapping) if mapping else 0
            })

        return pd.DataFrame(summary_data).sort_values('date')

    def _analyze_mold_machined_summary(self, **kwargs) -> None:
        """Process and analyze mold-machine data."""
        self.logger.info("Data processing...")

        # Merge data
        mold_machine_df = pd.merge(
            pd.merge(
                self.product_df[['recordDate', 'machineCode', 'moldNo']],
                self.mold_df[['moldNo', 'machineTonnage', 'acquisitionDate']],
                on='moldNo'
            ),
            self.machine_df[['machineCode', 'machineName']].drop_duplicates().reset_index(drop=True),
            on='machineCode'
        )

        mold_machine_df.columns = [
            'recordDate', 'machineCode', 'moldNo',
            'suitedMachineTonnages', 'acquisitionDate', 'machineType'
        ]
        mold_machine_df['acquisitionDate'] = pd.to_datetime(mold_machine_df['acquisitionDate'])

        # Check tonnage matching
        mold_machine_df['tonnageMatched'] = mold_machine_df.apply(
            lambda row: self._check_tonnage_match(row['machineCode'], row['suitedMachineTonnages']),
            axis=1
        )

        # Create summaries
        mold_tonnage_summary_df = self._create_mold_tonnage_summary(mold_machine_df)
        first_mold_usage_df = self._analyze_first_usage(mold_machine_df)
        first_paired_mold_machine_df = self._create_first_paired_data(mold_machine_df)

        self.logger.info("Data processing completed successfully")

        return mold_machine_df, mold_tonnage_summary_df, first_mold_usage_df, first_paired_mold_machine_df

    @staticmethod
    def _check_tonnage_match(machineCode: str,
                            suitedMachineTonnages: Any) -> bool:
        """Check if mold tonnage matches machine tonnage."""
        try:
            ton_list = suitedMachineTonnages.split('/')
        except:
            ton_list = [str(suitedMachineTonnages)]
        return any(ton in str(machineCode) for ton in ton_list)

    @staticmethod
    def _generate_analyzed_results_summary(mold_tonnage_summary_df: pd.DataFrame,
                                        first_mold_usage_df: pd.DataFrame):
        """Generate analyzed results summary as formatted text string"""

        lines = []
        lines.append("=" * 80)
        lines.append("MOLD ANALYSIS SUMMARY REPORT")
        lines.append("=" * 80)
        lines.append("")

        # Mold Tonnage Summary Statistics
        lines.append("1. MOLD TONNAGE SUMMARY STATISTICS")
        lines.append("-" * 80)
        lines.append(f"   Total Molds: {len(mold_tonnage_summary_df):,}")
        lines.append(f"   Average Tonnage Types per Mold: {mold_tonnage_summary_df['usedTonnageCount'].mean():.2f}")
        lines.append(f"   Max Tonnage Types: {mold_tonnage_summary_df['usedTonnageCount'].max()}")
        lines.append(f"   Min Tonnage Types: {mold_tonnage_summary_df['usedTonnageCount'].min()}")
        lines.append(f"   Median Tonnage Types: {mold_tonnage_summary_df['usedTonnageCount'].median():.2f}")
        lines.append(f"   Standard Deviation: {mold_tonnage_summary_df['usedTonnageCount'].std():.2f}")
        lines.append("")

        # First Use Analysis Statistics
        lines.append("2. FIRST USE ANALYSIS STATISTICS")
        lines.append("-" * 80)
        lines.append(f"   Total Molds Analyzed: {len(first_mold_usage_df):,}")
        lines.append(f"   Average Days Between Acquisition and First Use: {first_mold_usage_df['daysDifference'].mean():.2f}")
        lines.append(f"   Median Days Between Acquisition and First Use: {first_mold_usage_df['daysDifference'].median():.2f}")
        lines.append(f"   Standard Deviation: {first_mold_usage_df['daysDifference'].std():.2f}")
        lines.append(f"   Min Gap (days): {first_mold_usage_df['daysDifference'].min():.2f}")
        lines.append(f"   Max Gap (days): {first_mold_usage_df['daysDifference'].max():.2f}")
        lines.append("")

        # Check for data quality issues
        negative_gap = first_mold_usage_df[first_mold_usage_df['daysDifference'] < 0]
        if len(negative_gap) > 0:
            lines.append("3. DATA QUALITY WARNINGS")
            lines.append("-" * 80)
            mold_nums = len(negative_gap)
            info = ", ".join(negative_gap['moldNo'].tolist())
            lines.append(f"   WARNING: {mold_nums} mold(s) have negative gap (used before acquisition)")
            lines.append(f"   Affected Molds: {info}")
            lines.append("")

        lines.append("=" * 80)

        return "\n".join(lines)

    @staticmethod
    def _create_mold_tonnage_summary(mold_machine_df: pd.DataFrame) -> pd.DataFrame:
        """Create summary of tonnage types used for each mold."""
        summary_df = (mold_machine_df.groupby('moldNo', as_index=False)
                    .agg(usedMachineTonnage=('machineType', lambda x: x.unique().tolist()),
                        usedTonnageCount=('machineType', 'nunique')))

        return summary_df

    @staticmethod
    def _analyze_first_usage(mold_machine_df: pd.DataFrame) -> pd.DataFrame:
        """Analyze first use date and gap time for each mold."""
        first_use_df = mold_machine_df.groupby(['moldNo', 'acquisitionDate'])['recordDate'].min().reset_index(name='firstDate')
        first_use_df['daysDifference'] = (first_use_df['firstDate'] - first_use_df['acquisitionDate']).dt.days

        return first_use_df

    @staticmethod
    def _create_first_paired_data(mold_machine_df: pd.DataFrame) -> pd.DataFrame:
        """Create paired machine-mold first use data."""
        paired_df = mold_machine_df.groupby(
            ['machineCode', 'moldNo', 'acquisitionDate']
        )['recordDate'].min().reset_index(name='firstDate')

        paired_df = paired_df[['firstDate', 'machineCode', 'moldNo', 'acquisitionDate']].sort_values('machineCode').reset_index(drop=True)

        return paired_df