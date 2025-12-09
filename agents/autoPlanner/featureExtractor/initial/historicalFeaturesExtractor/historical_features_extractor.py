from pathlib import Path
from typing import Dict, Any
from loguru import logger
from datetime import datetime
import shutil

from agents.utils import ConfigReportMixin
from agents.orderProgressTracker.order_progress_tracker import OrderProgressTracker

from agents.autoPlanner.featureExtractor.initial.historicalFeaturesExtractor.configs.features_extractor_config import FeaturesExtractorConfig
from agents.autoPlanner.featureExtractor.initial.historicalFeaturesExtractor.mold_machine_feature_weight_calculator import MoldMachineFeatureWeightCalculator
from agents.autoPlanner.featureExtractor.initial.historicalFeaturesExtractor.mold_stability_index_calculator import MoldStabilityIndexCalculator
from agents.autoPlanner.reportFormatters.dict_based_report_generator import DictBasedReportGenerator


class HistoricalFeaturesExtractor(ConfigReportMixin):
    """
    Main orchestrator class that coordinates the historical features extraction pipeline.
    
    This class manages a three-phase extraction pipeline:
    1. Mold Stability Calculation: Calculate stability indices for molds
    2. Order Progress Tracking: Track progress of manufacturing orders
    3. Feature Weight Calculation: Calculate feature weights for mold-machine combinations
    
    The orchestrator includes error handling and comprehensive reporting.
    """

    REQUIRED_FIELDS = {
        'config': {
            'shared_source_config': {
                'databaseSchemas_path': str,
                'sharedDatabaseSchemas_path': str,
                'annotation_path': str,
                'progress_tracker_change_log_path': str,
                'mold_stability_index_change_log_path': str,
                'mold_machine_weights_dir': str,
                'mold_stability_index_dir': str,
                'features_extractor_dir': str
                },
            'feature_weight_config': {
                'efficiency': float,
                'loss': float,
                'scaling': str,
                'confidence_weight': float,
                'n_bootstrap': int,
                'confidence_level': float,
                'min_sample_size': int,
                'feature_weights': dict,
                'targets': dict
                },
            'mold_stability_config': {
                'efficiency': float,
                'loss': float,
                'cavity_stability_threshold': float,
                'cycle_stability_threshold': float,
                'total_records_threshold': int
                }
            }
    }
    
    def __init__(self, config: FeaturesExtractorConfig):
        """
        Initialize HistoricalFeaturesExtractor with configuration.
        
        Args:
            config: FeaturesExtractorConfig containing processing parameters
        """
        self._capture_init_args()
        
        # Initialize logger with class-specific binding
        self.logger = logger.bind(class_="HistoricalFeaturesExtractor")

        # Validate required configs
        is_valid, errors = shared_source_config.validate_requirements(self.REQUIRED_FIELDS['config']['shared_source_config'])
        if not is_valid:
            raise ValueError(
                f"{self.__class__.__name__} config validation failed:\n" +
                "\n".join(f"  - {e}" for e in errors)
            )
        self.logger.info("✓ Validation for shared_source_config requirements: PASSED!")
        
        # Store configuration
        self.config = config

        # Set up output configuration for saving results
        self.output_dir = Path(self.config.shared_source_config.features_extractor_dir)
        
        # Initialize report collection
        self.report_collection = {}

    def save_report(self) -> str:
        """
        Save the report to a file and return the log entries.
        
        Returns:
            str: Log entries describing the save operation
        """
        timestamp_now = datetime.now()
        timestamp_str = timestamp_now.strftime("%Y-%m-%d %H:%M:%S")
        timestamp_file = timestamp_now.strftime("%Y%m%d_%H%M")
        log_entries = [f"[{timestamp_str}] Saving new version...\n"]

        newest_dir = self.output_dir / "newest"
        newest_dir.mkdir(parents=True, exist_ok=True)
        historical_dir = self.output_dir / "historical_db"
        historical_dir.mkdir(parents=True, exist_ok=True)

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

        # Save phase reports
        for agent_id, info in self.report_collection.items():
            for prefix_name, message in info.items():
                filename = f"{timestamp_file}_{agent_id}_{prefix_name}.txt"
                output_path = Path(newest_dir / filename)

                try:
                    # Convert message to string if it's not already
                    if isinstance(message, str):
                        content = message
                    else:
                        reporter = DictBasedReportGenerator(use_colors=False)
                        content = "\n".join(reporter.export_report(
                            message, 
                            title=f"{agent_id} - {prefix_name} Report"))
                    
                    with open(output_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    log_entries.append(f"  ⤷ Saved new file: {output_path}\n")
                    self.logger.info("Saved new file: {}", output_path)
                except Exception as e:
                    self.logger.error("Failed to save file {}: {}", output_path, e)
                    raise OSError(f"Failed to save file {output_path}: {e}")
        
        return "".join(log_entries)

    def run_extraction(self) -> tuple[Dict[str, Any], str]:
        """
        Execute the complete historical features extraction pipeline.
        
        This is the main entry point that orchestrates the entire pipeline:
        1. Runs MoldStabilityIndexCalculator (Phase 1)
        2. Runs OrderProgressTracker (Phase 2)
        3. Runs MoldMachineFeatureWeightCalculator (Phase 3)
        4. Returns comprehensive pipeline results
        
        Returns:
            tuple[Dict[str, Any], str]: Pipeline execution results and log string
        """
        agent_id = "HistoricalFeaturesExtractor"
        self.logger.info("🚀 Starting {}...", agent_id)

        # Generate config header using mixin
        timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        config_header = self._generate_config_report(timestamp_str, required_only=True)

        pipeline_log_lines = [config_header]
        pipeline_log_lines.append("--Processing Summary--\n")
        pipeline_log_lines.append(f"⤷ {self.__class__.__name__} results:\n")

        # Phase 1: Mold Stability Index Calculation
        stability_result = self._run_mold_stability_calculator()

        # Phase 2: Order Progress Tracking
        progress_result = self._run_order_progress_tracker()

        # Phase 3: Feature Weight Calculation
        weight_result = self._run_feature_weight_calculator()

        # Create comprehensive pipeline result summary
        pipeline_result = self._create_pipeline_result(
            stability_result, 
            progress_result, 
            weight_result
        )

        self.logger.info("✅ {} completed", agent_id)

        # Save final report
        final_report = {
            'Agent ID': agent_id,
            'Timestamp': self._get_timestamp(),
            'Content': pipeline_result
        }
        
        self.report_collection[agent_id] = {'final_report': final_report}
        
        # Export reports to files
        output_exporting_log = self.save_report()
        pipeline_log_lines.append(f"{output_exporting_log}\n")

        # Append detailed phase logs
        pipeline_log_lines.append("--Details--\n")
        
        if stability_result:
            stability_log = stability_result.get('log_entries', 'No log available')
            pipeline_log_lines.append("⤷ Phase 1: Mold Stability Index Calculation\n")
            pipeline_log_lines.append(f"{stability_log}\n")
        
        if progress_result:
            progress_log = progress_result.get('log_entries', 'No log available')
            pipeline_log_lines.append("⤷ Phase 2: Order Progress Tracking\n")
            pipeline_log_lines.append(f"{progress_log}\n")
        
        if weight_result:
            weight_log = weight_result.get('log_entries', 'No log available')
            pipeline_log_lines.append("⤷ Phase 3: Feature Weight Calculation\n")
            pipeline_log_lines.append(f"{weight_log}\n")

        pipeline_log_str = "\n".join(pipeline_log_lines)
        
        # Save change log
        try:
            log_path = self.output_dir / "change_log.txt"
            with open(log_path, "a", encoding="utf-8") as log_file:
                log_file.write(pipeline_log_str)
            self.logger.info("✓ Updated and saved change log: {}", log_path)
        except Exception as e:
            self.logger.error("✗ Failed to save change log {}: {}", log_path, e)

        self.logger.info("✅ All reports saved successfully")

        return pipeline_result, pipeline_log_str

    def _run_mold_stability_calculator(self) -> Dict[str, Any]:
        """
        Execute Phase 1: MoldStabilityIndexCalculator.
        
        Returns:
            Dict[str, Any]: Calculation result with status and details
        """
        agent_id = 'MoldStabilityIndexCalculator'
        self.logger.info("📊 Phase 1: Running {}...", agent_id)
        
        try:
            calculator = MoldStabilityIndexCalculator(
                shared_source_config = self.config.shared_source_config, 
                mold_stability_config = self.config.mold_stability_config)
            results, log_str = calculator.process(save_results = True)
            self.logger.info("✅ Phase 1: {} completed successfully", agent_id)
            
            success_report = {
                'Agent ID': agent_id,
                'Timestamp': self._get_timestamp(),
                'Content': results,
                'log_entries': log_str
            }
            self.report_collection[agent_id] = {'success_report': success_report}
            
            return success_report
            
        except Exception as e:
            self.logger.error("❌ Phase 1: {} error: {}", agent_id, str(e))
            error_result = self._create_error_result(agent_id, str(e))
            self.report_collection[agent_id] = {'error_report': error_result}
            return error_result

    def _run_order_progress_tracker(self) -> Dict[str, Any]:
        """
        Execute Phase 2: OrderProgressTracker.
        
        Returns:
            Dict[str, Any]: Tracking result with status and details
        """
        agent_id = 'OrderProgressTracker'
        self.logger.info("📋 Phase 2: Running {}...", agent_id)
        
        try:
            tracker = OrderProgressTracker(config = self.config.shared_source_config)
            results, log_str = tracker.pro_status()
            self.logger.info("✅ Phase 2: {} completed successfully", agent_id)
            
            success_report = {
                'Agent ID': agent_id,
                'Timestamp': self._get_timestamp(),
                'Content': results,
                'log_entries': log_str
            }
            self.report_collection[agent_id] = {'success_report': success_report}
            
            return success_report
            
        except Exception as e:
            self.logger.error("❌ Phase 2: {} error: {}", agent_id, str(e))
            error_result = self._create_error_result(agent_id, str(e))
            self.report_collection[agent_id] = {'error_report': error_result}
            return error_result

    def _run_feature_weight_calculator(self) -> Dict[str, Any]:
        """
        Execute Phase 3: MoldMachineFeatureWeightCalculator.
        
        Returns:
            Dict[str, Any]: Calculation result with status and details
        """
        agent_id = 'MoldMachineFeatureWeightCalculator'
        self.logger.info("🔢 Phase 3: Running {}...", agent_id)
        
        try:
            calculator = MoldMachineFeatureWeightCalculator(
                shared_source_config = self.config.shared_source_config, 
                feature_weight_config = self.config.feature_weight_config)
            results, log_str = calculator.process(save_results = True)
            self.logger.info("✅ Phase 3: {} completed successfully", agent_id)
            
            success_report = {
                'Agent ID': agent_id,
                'Timestamp': self._get_timestamp(),
                'Content': results,
                'log_entries': log_str
            }
            self.report_collection[agent_id] = {'success_report': success_report}
            
            return success_report
            
        except Exception as e:
            self.logger.error("❌ Phase 3: {} error: {}", agent_id, str(e))
            error_result = self._create_error_result(agent_id, str(e))
            self.report_collection[agent_id] = {'error_report': error_result}
            return error_result

    def _create_error_result(self, component: str, error_message: str) -> Dict[str, Any]:
        """
        Create a standardized error result object.
        
        Args:
            component: Name of the component that failed
            error_message: Description of the error
            
        Returns:
            Dict[str, Any]: Standardized error result
        """
        return {
            'Agent ID': component,
            'Timestamp': self._get_timestamp(),
            'status': 'error',
            'error_message': error_message,
            'log_entries': f"Error in {component}: {error_message}"
        }

    def _create_pipeline_result(self, 
                                stability_result: Dict[str, Any],
                                progress_result: Dict[str, Any],
                                weight_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create comprehensive pipeline result summary.
        
        Args:
            stability_result: Results from Phase 1
            progress_result: Results from Phase 2
            weight_result: Results from Phase 3
            
        Returns:
            Dict[str, Any]: Complete pipeline result summary
        """
        # Determine overall status
        phase_statuses = []
        
        if stability_result:
            phase_statuses.append(stability_result.get('status', 'success'))
        if progress_result:
            phase_statuses.append(progress_result.get('status', 'success'))
        if weight_result:
            phase_statuses.append(weight_result.get('status', 'success'))
        
        # Overall status logic
        if all(status == 'success' for status in phase_statuses):
            overall_status = 'success'
        elif any(status == 'success' for status in phase_statuses):
            overall_status = 'partial_success'
        else:
            overall_status = 'failed'
        
        return {
            'overall_status': overall_status,
            'stability_result': stability_result,
            'progress_result': progress_result,
            'weight_result': weight_result,
            'timestamp': self._get_timestamp()
        }

    def _get_timestamp(self) -> str:
        """
        Get current timestamp in ISO format.
        
        Returns:
            str: Current timestamp (YYYY-MM-DD HH:MM:SS)
        """
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")