from dataclasses import dataclass
from typing import Optional, Dict, Any
from enum import Enum
import pandas as pd
from configs.shared.dict_based_report_generator import DictBasedReportGenerator

class ProcessorLevel(Enum):
    """Enum to identify processor level"""
    DAY = "day"
    MONTH = "month"
    YEAR = "year"

@dataclass
class ProcessorResult:
    """
    Result from data processors with auto-adjustment capability.
    """
    
    # ============ PROCESSOR IDENTITY ============
    processor_level: ProcessorLevel
    
    # ============ ORIGINAL INPUT ============
    record_date: Optional[str] = None
    record_month: Optional[str] = None
    record_year: Optional[str] = None
    analysis_date: Optional[str] = None
    
    # ============ VALIDATED/ADJUSTED OUTPUT ============
    adjusted_record_date: Optional[str] = None
    adjusted_record_month: Optional[str] = None
    adjusted_record_year: Optional[str] = None
    analysis_timestamp: Optional[pd.Timestamp] = None  # Changed to pd.Timestamp
    
    # ============ VALIDATION METADATA ============
    was_adjusted: bool = False

    # ============ ANALYSIS RESULTS ============
    processed_data: Optional[Dict] = None
    analysis_summary: Optional[str] = None
    log: str = ""
    
    # ============ SUMMARY GENERATION ============
    def __post_init__(self):
        """Apply default values for None fields"""
        self.analysis_summary = self.get_processor_summary()

    def _log_processor_summary(self) -> str: 
        if not self.processed_data:
            return "No processor summary available"

        reporter = DictBasedReportGenerator(use_colors=False)
        return "\n".join(reporter.export_report(self.processed_data))
    
    def _update_log(self, processor_summary):
        """Update log with new processor summary"""
        self.log = self.log + "\n\n" + processor_summary
    
    def get_processor_summary(self) -> str:
        """Generate summary based on processor level"""

        validation_summary = "No validation summary available"
        analysis_summary = "No analysis summary available"
        processor_summary = self._log_processor_summary()

        self._update_log(processor_summary)
        
        if self.processor_level == ProcessorLevel.DAY:
            validation_summary = self._log_day_validation_summary()
            analysis_summary = self._log_day_analysis_summary()

        elif self.processor_level == ProcessorLevel.MONTH:
            validation_summary = self._log_month_validation_summary()
            analysis_summary = self._log_month_analysis_summary()

        elif self.processor_level == ProcessorLevel.YEAR:
            validation_summary = self._log_year_validation_summary()
            analysis_summary = self._log_year_analysis_summary()
        
        # Build parts list
        parts = [validation_summary, analysis_summary, processor_summary]

        # Return final summary
        return "\n\n".join(parts) + "\n"
        
    def get_temporal_context(self) -> Dict[str, Any]:
        """Helper to extract temporal info"""
        return {
            'processor_level': self.processor_level.value,
            'original': {
                'date': self.record_date,
                'month': self.record_month,
                'year': self.record_year,
                'analysis_date': self.analysis_date
            },
            'adjusted': {
                'date': self.adjusted_record_date,
                'month': self.adjusted_record_month,
                'year': self.adjusted_record_year,
                'analysis_timestamp': str(self.analysis_timestamp) if self.analysis_timestamp else None
            },
            'was_adjusted': self.was_adjusted,
            'processed_data': self.processed_data,
            'analysis_summary': self.analysis_summary,
            'log': self.log
        }

    # ============ DAY LEVEL SUMMARIES (Placeholder) ============  
    def _log_day_validation_summary(self) -> str:
        """Generate validation summary for day-level processing"""
        if self.record_date is None:
            return ""
            
        lines = []
        lines.append("=" * 60)
        lines.append("VALIDATION SUMMARY")
        lines.append("=" * 60)
        
        # Convert string to Timestamp for display
        requested_date = pd.Timestamp(self.record_date) if isinstance(self.record_date, str) else self.record_date
        lines.append(f"Record date (requested): {requested_date.date()}")
        
        # Check if adjusted
        if self.adjusted_record_date:
            adjusted_date = pd.Timestamp(self.adjusted_record_date) if isinstance(self.adjusted_record_date, str) else self.adjusted_record_date
            
            # Compare timestamps (normalize to ignore time component)
            if adjusted_date.normalize() != requested_date.normalize():
                lines.append(f"Record date (adjusted): {adjusted_date.date()}")
        
        lines.append("=" * 60)
        
        return "\n".join(lines)
    
    def _log_day_analysis_summary(self) -> str:
        """Generate analysis summary for day-level processing"""
        if not self.processed_data:
            return ""

        stats = self.processed_data.get("summaryStatics", pd.DataFrame())

        lines = []
        lines.append("=" * 60)
        lines.append("DATA SUMMARY REPORT")
        lines.append("=" * 60)

        # Basic info
        lines.append(f"Record date: {stats.get('record_date')}")
        lines.append(f"Total records: {stats.get('total_records', 0)}")
        lines.append(f"Active jobs: {stats.get('active_jobs', 0)}")

        # Optional: Only show detailed stats if active_jobs > 0
        if stats.get('active_jobs', 0) > 0:

            # Working shifts & machines
            if 'working_shifts' in stats:
                lines.append(f"Working shifts: {stats['working_shifts']}")

            if 'machines' in stats:
                lines.append(f"Machines: {stats['machines']}")

            if 'purchase_orders' in stats:
                lines.append(f"Purchase orders: {stats['purchase_orders']}")

            # Products
            if 'products' in stats:
                lines.append(f"Products: {stats['products']}")

            # Molds
            if 'molds' in stats:
                lines.append(f"Molds: {stats['molds']}")

            # Late status report
            if 'late_pos' in stats and 'total_pos_with_eta' in stats:
                late = stats['late_pos']
                total = stats['total_pos_with_eta']
                lines.append(f"POs delayed vs ETA: {late}/{total}")

            # Change type distribution
            if 'change_type_distribution' in stats:
                lines.append("Change type distribution:")
                for change_type, count in stats['change_type_distribution'].items():
                    lines.append(f"  └─ {change_type}: {count}")
        else:
            lines.append("No active job data found!")

        lines.append("=" * 60)
        return "\n".join(lines)
        
    # ============ MONTH LEVEL SUMMARIES ============
    def _log_month_validation_summary(self) -> str:
        """Generate validation summary for month-level processing"""
        if not self.record_month:
            return ""
            
        lines = []
        lines.append("=" * 60)
        lines.append("VALIDATION SUMMARY")
        lines.append("=" * 60)
        lines.append(f"Record month (requested): {pd.Period(self.record_month, freq='M')}")
        
        if self.adjusted_record_month and self.adjusted_record_month != self.record_month:
            lines.append(f"Record month (adjusted): {pd.Period(self.adjusted_record_month, freq='M')}")
        
        # Show if analysis_date was provided or auto-generated
        if self.analysis_date is None:
            lines.append(f"Analysis date (auto-generated): {self.analysis_timestamp.date()}")
            lines.append(f"  └─ Default: end of record_month")
        else:
            lines.append(f"Analysis date (provided): {self.analysis_date}")
            original_ts = pd.Timestamp(self.analysis_date).normalize()
            if original_ts != self.analysis_timestamp:
                lines.append(f"Analysis date (adjusted): {self.analysis_timestamp.date()}")
                lines.append(f"  └─ Reason: beyond available data")
            else:
                lines.append(f"Analysis date (validated): {self.analysis_timestamp.date()}")
        
        lines.append("=" * 60)
        
        return "\n".join(lines)
    
    def _log_month_analysis_summary(self) -> str:
        """Generate analysis summary for month-level processing"""
        if not self.processed_data:
            return ""
            
        po_based_df = self.processed_data.get("filteredRecords", pd.DataFrame())
        finished_df = self.processed_data.get("finishedRecords", pd.DataFrame())
        unfinished_df = self.processed_data.get("unfinishedRecords", pd.DataFrame())

        lines = []
        
        lines.append("=" * 60)
        lines.append(f"ANALYSIS RESULTS FOR {self.adjusted_record_month or self.record_month}")
        lines.append("=" * 60)
        lines.append(f"Analysis date: {self.analysis_timestamp.strftime('%Y-%m-%d')}")
        lines.append(f"Total Orders: {len(po_based_df)}")
        lines.append(f"Completed Orders Rate: {len(finished_df)}/{len(po_based_df)}")
        lines.append(f"Remaining Orders Rate: {len(unfinished_df)}/{len(po_based_df)}")
        
        if not unfinished_df.empty:
            lines.append(f"Orders with Capacity Warning: {unfinished_df['capacityWarning'].sum()}")
            severity_dist = unfinished_df['capacitySeverity'].value_counts().to_dict()
            lines.append(f"Capacity Severity Distribution: {severity_dist}")
        
        backlog_df = po_based_df[po_based_df['is_backlog'] == True]
        backlog_count = len(backlog_df)
        if backlog_count > 0:
            backlog_pos = backlog_df['poNo'].tolist()
            lines.append(f"Backlog Orders: {backlog_count} - ({', '.join(map(str, backlog_pos))})")
        else:
            lines.append(f"Backlog Orders: 0")
        
        lines.append("=" * 60)
        
        return "\n".join(lines)

    # ============ YEAR LEVEL SUMMARIES ============
    def _log_year_validation_summary(self) -> str:
        """Generate validation summary for year-level processing"""
        if not self.record_year:
            return ""
            
        lines = []
        lines.append("=" * 60)
        lines.append("VALIDATION SUMMARY")
        lines.append("=" * 60)
        lines.append(f"Record year (requested): {pd.Period(self.record_year, freq='Y')}")
        
        if self.adjusted_record_year and self.adjusted_record_year != self.record_year:
            lines.append(f"Record year (adjusted): {pd.Period(self.adjusted_record_year, freq='Y')}")
        
        # Show if analysis_date was provided or auto-generated
        if self.analysis_date is None:
            lines.append(f"Analysis date (auto-generated): {self.analysis_timestamp.date()}")
            lines.append(f"  └─ Default: end of record_year")
        else:
            lines.append(f"Analysis date (provided): {self.analysis_date}")
            original_ts = pd.Timestamp(self.analysis_date).normalize()
            if original_ts != self.analysis_timestamp:
                lines.append(f"Analysis date (adjusted): {self.analysis_timestamp.date()}")
                lines.append(f"  └─ Reason: beyond available data")
            else:
                lines.append(f"Analysis date (validated): {self.analysis_timestamp.date()}")
        
        lines.append("=" * 60)
        
        return "\n".join(lines)
    
    def _log_year_analysis_summary(self) -> str:
        """Generate analysis summary for year-level processing"""
        if not self.processed_data:
            return ""
            
        df = self.processed_data.get("filteredRecords", pd.DataFrame())

        lines = []
        
        lines.append("=" * 60)
        lines.append("ANALYSIS SUMMARY")
        lines.append("=" * 60)
        lines.append(f"Record year (requested): {self.adjusted_record_year}")
        lines.append(f"Analysis date (validated): {self.analysis_timestamp.date()}")
        
        lines.append("-" * 30)
        lines.append("TOTAL PRODUCTION PROGRESS")
        
        total_good = df["itemGoodQuantity"].sum()
        total_qty = df["itemQuantity"].sum()
        total_rate = round(total_good / total_qty * 100, 2) if total_qty > 0 else 0
        lines.append(f"Production progress: {total_good:,} / {total_qty:,} ({total_rate:.2f}%)")
        
        # --- PO status summary ---
        for status in df['poStatus'].unique().tolist():
            count = len(df[df['poStatus'] == status])
            total = len(df)
            rate = count / total * 100 if total else 0
            lines.append(f"{status.capitalize()} POs: {count}/{total} ({rate:.2f}%)")
        
        lines.append("-" * 30)
        lines.append(f"Unique months in poReceivedDate: {sorted(df['poReceivedDate'].dt.strftime('%Y-%m').unique().tolist())}")
        lines.append(f"Unique months in poETA: {df['poETA'].dt.strftime('%Y-%m').unique().tolist()}")
        
        lines.append("-" * 30)
        lines.append("MONTHLY PRODUCTION PROGRESS")
        
        for m_info, m_df in df.groupby(df['poETA'].dt.strftime('%Y-%m')):
            month_good = m_df["itemGoodQuantity"].sum()
            month_qty = m_df["itemQuantity"].sum()
            month_rate = round(month_good / month_qty * 100, 2) if month_qty > 0 else 0
            backlog_flag = " (BACKLOG)" if m_df['is_backlog'].any() else ""
            
            lines.append(f"- ETA period: {m_info}{backlog_flag}: Production progress: {month_good:,}/{month_qty:,} ({month_rate:.2f}%)")
            
            # --- PO status summary ---
            lines.extend(self.get_po_status_summary(m_df))
        
        lines.append("=" * 60)
        
        return "\n".join(lines)
    
    @staticmethod
    def get_po_status_summary(df):
        lines = []
        total = len(df)
        for status, label in {
            'finished': 'Finished',
            'in_progress': 'In-progress',
            'not_started': 'Not-start'
        }.items():
            count = len(df[df['poStatus'] == status])
            rate = count / total * 100 if total else 0
            lines.append(f"{label} POs: {count}/{total} ({rate:.2f}%)")
        return lines