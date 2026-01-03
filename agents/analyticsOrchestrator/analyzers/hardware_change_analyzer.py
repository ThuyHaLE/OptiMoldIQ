from loguru import logger
import pandas as pd
from pathlib import Path
import os
from datetime import datetime
from typing import Dict, Any, Optional, List, NoReturn
from configs.shared.config_report_format import ConfigReportMixin
from agents.utils import load_annotation_path, load_json, read_change_log
from agents.analyticsOrchestrator.analyzers.configs.change_analyzer_config import ChangeAnalyzerConfig
from configs.shared.dict_based_report_generator import DictBasedReportGenerator
from agents.analyticsOrchestrator.analyzers.configs.save_output_formatter import save_machine_layout, save_mold_machine_pair

# Import agent report format components
from configs.shared.agent_report_format import (
    Executable,
    ExecutionResult,
    AtomicPhase,
    CompositeAgent,
    save_result,
    print_execution_summary,
    format_execution_tree,
    update_change_log,
    format_export_logs)

# ============================================
# DATA LOADING PHASE
# ============================================
class DataLoadingPhase(AtomicPhase):
    """Phase for loading all required data files"""
    
    RECOVERABLE_ERRORS = (FileNotFoundError, pd.errors.EmptyDataError, KeyError)
    CRITICAL_ERRORS = (MemoryError, KeyboardInterrupt)
    FALLBACK_FAILURE_IS_CRITICAL = True  # ⭐ Data loading is critical!

    def __init__(self, 
                 config: ChangeAnalyzerConfig,
                 data_container: Dict[str, Any]):
        super().__init__("DataLoading")
        self.config = config.shared_source_config
        self.data_container = data_container
    
    def _execute_impl(self) -> Dict[str, Any]:
        """Load all required data"""
        logger.info("📂 Loading database schemas and path annotations...")
        
        # Load database schemas
        try:
            databaseSchemas_data = load_annotation_path(
                Path(self.config.databaseSchemas_path).parent,
                Path(self.config.databaseSchemas_path).name
            )
        except Exception as e:
            raise FileNotFoundError(f"Failed to load databaseSchemas: {e}")

        # Load path annotations
        try:
            path_annotation = load_annotation_path(
                Path(self.config.annotation_path).parent,
                Path(self.config.annotation_path).name
            )
        except Exception as e:
            raise FileNotFoundError(f"Failed to load path_annotation: {e}")
        
        logger.info("📊 Loading DataFrames from parquet files...")
        
        # Define dataframes to load
        dataframes_to_load = [
            ('productRecords', 'productRecords_df'),
            ('machineInfo', 'machineInfo_df'),
            ('moldInfo', 'moldInfo_df')
        ]

        loaded_dfs = {}
        missing_files = []
        failed_loads = []
        
        for path_key, attr_name in dataframes_to_load:
            path = path_annotation.get(path_key)
            
            if not path:
                missing_files.append(f"{path_key}: path not found in annotation")
                continue
            
            if not os.path.exists(path):
                missing_files.append(f"{path_key}: file not found at {path}")
                continue
            
            try:
                df = pd.read_parquet(path)
                loaded_dfs[attr_name] = df
                logger.debug("{}: {} - {}", path_key, df.shape, list(df.columns))
            except Exception as e:
                failed_loads.append(f"{path_key}: {str(e)}")
        
        # Check if we have critical failures
        if missing_files or failed_loads:
            error_msg = []
            if missing_files:
                error_msg.append("Missing files:\n  - " + "\n  - ".join(missing_files))
            if failed_loads:
                error_msg.append("Failed to load:\n  - " + "\n  - ".join(failed_loads))
            
            raise FileNotFoundError("\n".join(error_msg))
        
        self.data_container.update({
            'databaseSchemas_data': databaseSchemas_data,
            'path_annotation': path_annotation,
            'dataframes': loaded_dfs
        })

        logger.info("✓ All data loaded successfully ({} DataFrames)", len(loaded_dfs))
        
        return {
            'databaseSchemas_data': databaseSchemas_data,
            'path_annotation': path_annotation,
            'dataframes': loaded_dfs
        }

    def _fallback(self) -> NoReturn:
        """
        No valid fallback for data loading.
        Raise to ensure CRITICAL severity is applied.
        """
        logger.error("DataLoading cannot fallback - missing data files")
        
        raise FileNotFoundError(
            "Cannot proceed without required data files. "
            "Please check paths in configuration."
        )

# ============================================
# PHASE: MACHINE LAYOUT TRACKING
# ============================================
class  MachineLayoutTrackingPhase(AtomicPhase):
    """Phase for running the actual machine layout tracker logic"""
    
    RECOVERABLE_ERRORS = (KeyError, ValueError, pd.errors.MergeError)
    CRITICAL_ERRORS = (MemoryError, KeyboardInterrupt)
    FALLBACK_FAILURE_IS_CRITICAL = False
    
    def __init__(self, 
                 config: ChangeAnalyzerConfig,
                 data_container: Dict[str, Any]):
        super().__init__("MachineLayoutTracker")

        self.config = config
        self.loaded_data = data_container

    @staticmethod
    def _load_layout_changes(layout_tracker_change_log_path
                             ) -> Optional[Dict[str, Dict[str, str]]]:
        
        """Load layout changes from JSON file with error handling"""

        try:
            layout_changes_path = read_change_log(
                Path(layout_tracker_change_log_path).parent,
                Path(layout_tracker_change_log_path).name,
                pattern=r'Saved new json file:\s*(.+)'
            )      
            return load_json(str(layout_changes_path))
        
        except Exception as e:
            logger.error(f"Error loading layout changes: {str(e)}")
            return None
        
    def _execute_impl(self) -> Dict[str, Any]:
        """Run machine layout tracker logic"""
        logger.info("🔄 Running machine layout tracker...")

        productRecords_df = self.loaded_data['dataframes']["productRecords_df"]
        databaseSchemas_data = self.loaded_data['databaseSchemas_data']
        layout_changes_dict = self._load_layout_changes(self.config.shared_source_config.machine_layout_tracker_change_log_path)

        # Initialize layout tracker
        from agents.analyticsOrchestrator.trackers.machine_layout_tracker import MachineLayoutTracker
        tracker = MachineLayoutTracker( 
            productRecords_df=productRecords_df, 
            databaseSchemas_data=databaseSchemas_data,
            layout_changes_dict = layout_changes_dict
            )
        
        # Check for new layout changes
        latest_record_date = productRecords_df['recordDate'].max()
        tracker_result = tracker.check_new_layout_change(latest_record_date)
        
        return {
            "payload": tracker_result.to_dict(),
            "savable": True
        }

    def _fallback(self) -> Dict[str, Any]:
        """Fallback: return empty tracking results"""
        logger.warning("Using fallback for MachineLayoutTrackingPhase - returning empty results")
        return {
            "payload": None,
            "savable": False
        }
    
# ============================================
# PHASE: MOLD MACHINE PAIR TRACKER
# ============================================
class  MoldMachinePairTrackingPhase(AtomicPhase):
    """Phase for running the actual mold machine pair tracker logic"""
    
    RECOVERABLE_ERRORS = (KeyError, ValueError, pd.errors.MergeError)
    CRITICAL_ERRORS = (MemoryError, KeyboardInterrupt)
    FALLBACK_FAILURE_IS_CRITICAL = False
    
    def __init__(self, 
                 config: ChangeAnalyzerConfig,
                 data_container: Dict[str, Any]):
        super().__init__("MoldMachinePairTracker")

        self.config = config
        self.loaded_data = data_container

    @staticmethod
    def _load_mold_machine_dict(pair_tracker_change_log_path
                                ) -> Optional[Dict[str, Dict[str, List[str]]]]:
        
        """Load mold-machine pair changes from JSON file (uses latest dated file)"""
        
        try:
            stored_paths = read_change_log(
                Path(pair_tracker_change_log_path).parent,
                Path(pair_tracker_change_log_path).name, 
                pattern=r'Saved new json file:\s*(.+)'
            )       

            if not stored_paths:
                logger.warning(f"Mold-machine pair change collection not found: {stored_paths}")
                return None
        
            latest_path = max(
                (Path(p) for p in stored_paths),
                key=lambda p: datetime.strptime(p.name.split("_")[0], "%Y-%m-%d")
            )
            return load_json(str(latest_path))
        
        except Exception as e:
            logger.error(f"Error loading mold-machine dict: {str(e)}")
            return None
        
    def _execute_impl(self) -> Dict[str, Any]:
        """Run mold machine pair tracker logic"""
        logger.info("🔄 Running mold machine pair tracker...")

        productRecords_df = self.loaded_data['dataframes']["productRecords_df"]
        moldInfo_df = self.loaded_data['dataframes']["moldInfo_df"]
        machineInfo_df = self.loaded_data['dataframes']["machineInfo_df"]
        databaseSchemas_data = self.loaded_data['databaseSchemas_data']
        mold_machines_dict = self._load_mold_machine_dict(self.config.shared_source_config.mold_machine_pair_tracker_change_log_path)

        # Initialize machine-mold pair tracker
        from agents.analyticsOrchestrator.trackers.mold_machine_pair_tracker import MoldMachinePairTracker
        tracker = MoldMachinePairTracker(
                 productRecords_df = productRecords_df, 
                 moldInfo_df = moldInfo_df,
                 machineInfo_df = machineInfo_df,
                 databaseSchemas_data = databaseSchemas_data,
                 mold_machines_dict = mold_machines_dict)

        # Check for new mold-machine pair changes
        latest_record_date = productRecords_df['recordDate'].max()
        tracker_result = tracker.check_new_pairs(latest_record_date)

        return {
            "payload": tracker_result.to_dict(),
            "savable": True
        }

    def _fallback(self) -> Dict[str, Any]:
        """Fallback: return empty tracking results"""
        logger.warning("Using fallback for MoldMachinePairTrackingPhase - returning empty results")
        return {
            "payload": None,
            "savable": False
        }

class HardwareChangeAnalyzer(ConfigReportMixin):

    REQUIRED_FIELDS = {
        'config': {
            'shared_source_config': {
                'annotation_path': str,
                'databaseSchemas_path': str,
                'machine_layout_tracker_dir': str,
                'machine_layout_tracker_change_log_path': str,
                'mold_machine_pair_tracker_dir': str,
                'mold_machine_pair_tracker_change_log_path': str,
                'hardware_change_analyzer_log_path': str,
                },
            'enable_machine_layout_tracker': Optional[bool],
            'save_machine_layout_result': Optional[bool],
            'enable_mold_machine_pair_tracker': Optional[bool],
            'save_mold_machine_pair_result': Optional[bool],
            'save_hardware_change_analyzer_log': Optional[bool]
            }
        }

    def __init__(self, 
                 config: ChangeAnalyzerConfig):
        
        """
        Initialize HardwareChangeAnalyzer with configuration.
        
        Args:        
            config: ChangeAnalyzerConfig containing processing parameters, including:
                - shared_source_config:
                    - annotation_path (str): Path to the JSON file containing path annotations.
                    - databaseSchemas_path (str): Path to database schema for validation.
                    - machine_layout_tracker_dir (str): Base directory for storing reports.
                    - machine_layout_tracker_change_log_path (str): Path to the MachineLayoutTracker change log.
                    - mold_machine_pair_tracker_dir (str): Base directory for storing reports.
                    - mold_machine_pair_tracker_change_log_path (str): Path to the MoldMachinePairTracker change log.
                    - hardware_change_analyzer_log_path (str): Path to the HardwareChangeAnalyzer change log.

                - enable_machine_layout_tracker (bool): Enable MachineLayoutTracker
                - save_machine_layout_result (bool): Save MachineLayoutTracker result
                - enable_mold_machine_pair_tracker (bool): Enable MoldMachinePairTracker
                - save_mold_machine_pair_result (bool): Save MoldMachinePairTracker result
                - save_hardware_change_analyzer_log (bool): Save HardwareChangeAnalyzer change log
        """
        
        # Capture initialization arguments for reporting
        self._capture_init_args()

        # Initialize logger with class name for better tracking
        self.logger = logger.bind(class_="HardwareChangeAnalyzer")

        # Store configuration
        self.config = config

        # Validate required configs
        is_valid, errors = self.config.shared_source_config.validate_requirements(
            self.REQUIRED_FIELDS['config']['shared_source_config'])
        if not is_valid:
            raise ValueError(
                f"{self.__class__.__name__} config validation failed:\n" +
                "\n".join(f"  - {e}" for e in errors)
            )

        self.save_routing = {
            "MachineLayoutTracker": {
                "enabled": self.config.save_machine_layout_result,
                "save_fn": save_machine_layout,
                "save_paths": {
                    "output_dir": self.config.shared_source_config.machine_layout_tracker_dir,
                    "change_log_path": self.config.shared_source_config.machine_layout_tracker_change_log_path
                }
            },
            "MoldMachinePairTracker": {
                "enabled": self.config.save_mold_machine_pair_result,
                "save_fn": save_mold_machine_pair,
                "save_paths": {
                    "output_dir": self.config.shared_source_config.mold_machine_pair_tracker_dir,
                    "change_log_path": self.config.shared_source_config.mold_machine_pair_tracker_change_log_path
                }
            },
        }

    def run_analyzing(self) -> ExecutionResult:
        """Execute the complete hardware change analyzer pipeline."""
        
        self.logger.info("Starting HardwareChangeAnalyzer ...")

        agent_id = self.__class__.__name__

        timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        config_header = self._generate_config_report(timestamp_str, required_only=True)
        
        # ============================================
        # ✨ CREATE SHARED CONTAINER
        # ============================================
        shared_data = {}  # This will be populated by DataLoadingPhase
        
        # ============================================
        # BUILD PHASE LIST WITH SHARED CONTAINER
        # ============================================
        phases: List[Executable] = []
        
        # Phase 1: Data Loading (always required)
        phases.append(DataLoadingPhase(self.config, shared_data))
        
        # Phase 2: Machine Layout Tracking (optional)
        if self.config.enable_machine_layout_tracker:
            self.save_routing["MachineLayoutTracker"].update({
                "change_log_header": config_header
                })
            phases.append(MachineLayoutTrackingPhase(self.config, shared_data))
        
        # Phase 3: Mold-Machine Pair Tracking (optional)
        if self.config.enable_mold_machine_pair_tracker:
            phases.append(MoldMachinePairTrackingPhase(self.config, shared_data))
            self.save_routing["MoldMachinePairTracker"].update({
                "change_log_header": config_header
                })
        
        # ============================================
        # EXECUTE USING COMPOSITE AGENT
        # ============================================
        agent = CompositeAgent("HardwareChangeAnalyzer", phases)
        result = agent.execute()
        
        # Process save routing and collect metadata
        save_routing, export_metadata = save_result(self.save_routing, result)
        
        # Update result metadata
        result.metadata.update({
            'save_routing': save_routing,
            'export_metadata': export_metadata
        })

        # ============================================
        # SAVE PIPELINE LOG IF REQUESTED
        # ============================================
        if self.config.save_hardware_change_analyzer_log:

            # Generate summary report
            reporter = DictBasedReportGenerator(use_colors=False)
            summary = "\n".join(reporter.export_report(save_routing))
            
            # Save pipeline change log
            message = update_change_log(
                agent_id, 
                config_header, 
                format_execution_tree(result), 
                summary, 
                "\n".join(format_export_logs(export_metadata)), 
                Path(self.config.shared_source_config.hardware_change_analyzer_log_path)
            )
            
            self.logger.info(f"Pipeline log saved: {message}")

        # ============================================
        # PRINT EXECUTION TREE & ANALYSIS
        # ============================================
        self.logger.info("✅ HardwareChangeAnalyzer completed in {:.2f}s!", result.duration)
        
        # Print execution tree for visibility
        print_execution_summary(result)
        
        return result