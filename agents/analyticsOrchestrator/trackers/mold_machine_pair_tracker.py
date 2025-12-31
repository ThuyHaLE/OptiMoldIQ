from loguru import logger
from typing import Dict, Set, Tuple, List, Any
import pandas as pd
from datetime import datetime
from agents.decorators import validate_init_dataframes
from configs.shared.config_report_format import ConfigReportMixin
from configs.shared.dict_based_report_generator import DictBasedReportGenerator
from agents.analyticsOrchestrator.trackers.configs.tracker_config import TrackerResult

# Decorator to validate DataFrames are initialized with the correct schema
@validate_init_dataframes(lambda self: {
    "product_df": list(self.databaseSchemas_data['dynamicDB']['productRecords']['dtypes'].keys()),
    "mold_df": list(self.databaseSchemas_data['staticDB']['moldInfo']['dtypes'].keys()),
    "machine_df": list(self.databaseSchemas_data['staticDB']['machineInfo']['dtypes'].keys())
})
class MoldMachinePairTracker(ConfigReportMixin):
    """Class to track mold-machines pair changes over time"""

    def __init__(self,
                 productRecords_df: pd.DataFrame,
                 moldInfo_df: pd.DataFrame,
                 machineInfo_df: pd.DataFrame,
                 databaseSchemas_data: Dict,
                 mold_machines_dict: Dict = None):

        self.logger = logger.bind(class_="MoldMachinePairTracker")

        self.databaseSchemas_data = databaseSchemas_data

        self.product_df = productRecords_df[productRecords_df['moldNo'].notna()].copy()
        self.mold_df = moldInfo_df.copy()
        self.machine_df = machineInfo_df.copy()

        self.mold_machines_dict = mold_machines_dict

    def check_new_pairs(self, new_record_date: pd.Timestamp) -> TrackerResult:

        """Check for new mold-machines pairs"""

        self.logger.info("Starting MoldMachinePairTracker ...")

        # Generate config header
        start_time = datetime.now()
        timestamp_str = start_time.strftime("%Y-%m-%d %H:%M:%S")
        config_header = self._generate_config_report(timestamp_str)
        
        tracking_log_entries = [
            config_header,
            "--Processing Summary--\n",
            f"⤷ {self.__class__.__name__} results:\n"
        ]

        new_record_date_str = new_record_date.strftime("%Y-%m-%d")

        if new_record_date not in self.product_df['recordDate'].values:
            self.logger.error("Date {} not found in records", new_record_date)
            raise ValueError(f"Date {new_record_date} not found in records")

        try:
            # Prepare data
            self._prepare_data()

            # Case 1 & 2: No mold-machines pairs data or empty - detect all and mark as change
            if not self.mold_machines_dict:
                self.logger.info("No existing data. Detecting all changes...")
                self.mold_machines_dict = self.detect_all_mold_machines()
                changes_data = self._analyze_mold_machine_summary()

                tracking_summary = self._generate_analyzed_results_summary(changes_data,
                                                                           self.mold_machines_dict)

                tracking_log_entries.append(f"Initial change detection at {new_record_date.isoformat()}")
                tracking_log_entries.append(tracking_summary)

                return TrackerResult(
                    record_date=new_record_date_str,
                    has_change=True, # Always change at first time
                    changes_dict=self.mold_machines_dict,
                    changes_data=changes_data,
                    tracker_summary=tracking_summary,
                    log='\n'.join(tracking_log_entries)
                )

            # Get current mold-machines mapping
            current_mapping = self._get_mold_machines_at_date(new_record_date)

            # Get historical pairs
            historical_pairs = self._extract_latest_pairs(self.mold_machines_dict)

            # Get current pairs
            current_pairs = set()
            for mold, machines in current_mapping.items():
                for machine in machines:
                    current_pairs.add((mold, machine))

            # Find new pairs
            new_pairs = current_pairs - historical_pairs
            has_change = len(new_pairs) > 0
            changes_data = {}
            tracking_summary = ""
            
            if not has_change:
                self.logger.info("No new mold-machines pair changes detected!")
                tracking_log_entries.append("No new mold-machines pair changes detected!")

            else:
                new_date_str = new_record_date.isoformat()
                self.mold_machines_dict[new_date_str] = current_mapping

                self.logger.info(f"Found {len(new_pairs)} new pairs at {new_date_str}:")
                for mold, machine in new_pairs:
                    self.logger.info(f"  - {mold} -> {machine}")

                changes_data = self._analyze_mold_machine_summary()

                tracking_summary = self._generate_analyzed_results_summary(changes_data,
                                                                           self.mold_machines_dict)

                tracking_log_entries.append(tracking_summary)
                tracking_log_entries.append(f"New mold-machines pair changes detected at {new_record_date.isoformat()}")
                
            return TrackerResult(
                record_date=new_record_date_str,
                has_change=has_change,
                changes_dict=self.mold_machines_dict,
                changes_data=changes_data,
                tracker_summary=tracking_summary,
                log='\n'.join(tracking_log_entries)
            )
        
        except Exception as e:
            self.logger.error("❌ Tracker failed: {}", str(e))
            raise
    
    def _prepare_data(self):
        """Prepare dataframe"""
        if not pd.api.types.is_datetime64_any_dtype(self.product_df['recordDate']):
            self.product_df['recordDate'] = pd.to_datetime(self.product_df['recordDate'])

    def detect_all_mold_machines(self) -> Dict[str, Dict[str, List[str]]]:

        """Detect all mold-machine mappings from dataframe"""

        try:
            # Get dates when new mold-machine combinations appear
            change_dates = (
                self.product_df[['recordDate', 'machineCode', 'moldNo']]
                .sort_values('recordDate')
                .drop_duplicates(['machineCode', 'moldNo'], keep='first')
                ['recordDate']
                .unique()
            )

            mold_machines_dict = {}
            for date in sorted(change_dates):
                mapping = self._get_mold_machines_at_date(date)
                mold_machines_dict[date.isoformat()] = mapping

            self.logger.info(f"Detected {len(mold_machines_dict)} change dates")
            return mold_machines_dict

        except Exception as e:
            self.logger.error(f"Error detecting mold-machines: {str(e)}")
            raise

    def _get_mold_machines_at_date(self, 
                                   target_date: pd.Timestamp
                                   ) -> Dict[str, List[str]]:

        """Get mold->machines mapping at specific date"""

        df_filtered = self.product_df[self.product_df['recordDate'] <= target_date]
        mapping = df_filtered.groupby('moldNo')['machineCode'].apply(
            lambda x: sorted(list(x.unique()))
        ).to_dict()

        # Convert to string keys and values
        return {str(k): [str(v) for v in vals] for k, vals in mapping.items()}

    def _extract_latest_pairs(self,
                              mold_machines_dict: Dict[str, List[str]]
                              ) -> Set[Tuple[str, str]]:
        
        """Extract all mold-machines pairs from dict"""
        
        all_pairs = set()
        if not mold_machines_dict:
            return all_pairs
    
        # Get the latest date's mapping
        latest_date = max(mold_machines_dict.keys())
        latest_mapping = mold_machines_dict[latest_date]

        for mold, machines in latest_mapping.items():
            for machine in machines:
                all_pairs.add((mold, machine))
        return all_pairs
    
    def _analyze_mold_machine_summary(self) -> Dict[str, pd.DataFrame]:
        
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

        mold_machine_df.columns = ['recordDate', 'machineCode', 'moldNo',
                                   'suitedMachineTonnages', 'acquisitionDate', 'machineType']
        mold_machine_df['acquisitionDate'] = pd.to_datetime(mold_machine_df['acquisitionDate'])

        # Check tonnage matching
        # intentional for readability, optimize later if scale
        mold_machine_df['tonnageMatched'] = mold_machine_df.apply(
            lambda row: self._check_tonnage_match(row['machineCode'], row['suitedMachineTonnages']),
            axis=1)

        # Create summaries
        mold_tonnage_summary_df = self._create_mold_tonnage_summary(mold_machine_df)
        first_mold_usage_df = self._analyze_first_usage(mold_machine_df)
        first_paired_mold_machine_df = self._create_first_paired_data(mold_machine_df)

        self.logger.info("Data processing completed successfully")

        return {
                "mold_machine_df": mold_machine_df,
                "mold_tonnage_summary": mold_tonnage_summary_df,
                "first_mold_usage": first_mold_usage_df,
                "first_paired_mold_machine": first_paired_mold_machine_df
                }

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
    def _create_mold_tonnage_summary(mold_machine_df: pd.DataFrame) -> pd.DataFrame:

        """Create summary of tonnage types used for each mold."""

        summary_df = (mold_machine_df.groupby('moldNo', as_index=False)
                    .agg(usedMachineTonnage=('machineType', lambda x: x.unique().tolist()),
                        usedTonnageCount=('machineType', 'nunique')))

        return summary_df

    @staticmethod
    def _analyze_first_usage(mold_machine_df: pd.DataFrame) -> pd.DataFrame:

        """Analyze first use date and gap time for each mold."""

        first_use_df = mold_machine_df.groupby(
            ['moldNo', 'acquisitionDate'])['recordDate'].min().reset_index(name='firstDate')
        first_use_df['daysDifference'] = (first_use_df['firstDate'] - first_use_df['acquisitionDate']).dt.days

        return first_use_df

    @staticmethod
    def _create_first_paired_data(mold_machine_df: pd.DataFrame) -> pd.DataFrame:

        """Create paired mold-machines first use data."""

        paired_df = mold_machine_df.groupby(
            ['machineCode', 'moldNo', 'acquisitionDate']
        )['recordDate'].min().reset_index(name='firstDate')

        paired_df = paired_df[
            ['firstDate', 'machineCode', 'moldNo', 'acquisitionDate']
            ].sort_values('machineCode').reset_index(drop=True)

        return paired_df

    @staticmethod
    def _generate_analyzed_results_summary(changes_data: Dict,
                                           mold_machines_dict: Dict) -> str:
        """Generate analyzed results summary as formatted text string"""

        def get_summary_stats(mold_machines_dict: Dict[str, Dict[str, List[str]]]) -> pd.DataFrame:
            
            """Get summary statistics"""

            summary_data = []
            for date_str, mapping in mold_machines_dict.items():
                total_pairs = sum(len(machines) for machines in mapping.values())
                summary_data.append({
                    'date': pd.to_datetime(date_str),
                    'num_machines': len(mapping),
                    'total_pairs': total_pairs,
                    'avg_molds_per_machine': total_pairs / len(mapping) if mapping else 0
                })

            return pd.DataFrame(summary_data).sort_values('date')
    
        mold_machine_df = changes_data.get("mold_machine_df", pd.DataFrame())
        mold_tonnage_summary_df = changes_data.get("mold_tonnage_summary", pd.DataFrame())
        first_mold_usage_df = changes_data.get("first_mold_usage", pd.DataFrame())
        first_paired_mold_machine_df = changes_data.get("first_paired_mold_machine", pd.DataFrame())

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

        # Create pivot version
        machine_mold_pivot = (
            first_paired_mold_machine_df
                .pivot(index='machineCode', columns='moldNo', values='firstDate')
                .reset_index()
                )
        mold_machine_pivot = (
            first_paired_mold_machine_df
                .pivot(index='moldNo', columns='machineCode', values='firstDate')
                .reset_index()
                )

        machine_mold_pivot.columns.name = None
        mold_machine_pivot.columns.name = None

        reporter = DictBasedReportGenerator(use_colors=False)
        tracking_summary = "\n".join(reporter.export_report(
            {"mold_tonnage_unmatched": mold_machine_df[mold_machine_df['tonnageMatched'] == False],
             "machine_mold_first_run_pair": machine_mold_pivot,
             "mold_machine_first_run_pair": mold_machine_pivot,
             "first_paired_summary": get_summary_stats(mold_machines_dict)
            }))
        lines.append("3. TRACKING SUMMARY")
        lines.append(tracking_summary)
        lines.append("")

        # Check for data quality issues
        negative_gap = first_mold_usage_df[first_mold_usage_df['daysDifference'] < 0]
        if len(negative_gap) > 0:
            lines.append("4. DATA QUALITY WARNINGS")
            lines.append("-" * 80)
            mold_nums = len(negative_gap)
            info = ", ".join(negative_gap['moldNo'].tolist())
            lines.append(f"   WARNING: {mold_nums} mold(s) have negative gap (used before acquisition)")
            lines.append(f"   Affected Molds: {info}")
            lines.append("")
        
        lines.append("=" * 80)

        return "\n".join(lines)