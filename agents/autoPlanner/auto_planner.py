from loguru import logger
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import List
from configs.shared.config_report_format import ConfigReportMixin
from configs.shared.dict_based_report_generator import DictBasedReportGenerator
from agents.autoPlanner.auto_planner_config import FeatureExtractorParams, InitialPlannerParams, AutoPlannerConfig

# Import agent report format components
from configs.shared.agent_report_format import (
    Executable,
    ExecutionResult,
    ExecutionStatus,
    PhaseSeverity,
    CompositeAgent,
    print_execution_summary,
    format_execution_tree,
    update_change_log,
    extract_export_metadata)

# Import unified ExecutableWrapper
from configs.shared.executable_wrapper import ExecutableWrapper

# ============================================
# AUTO PLANNER
# ============================================
class AutoPlanner(ConfigReportMixin):
    """
    Orchestrates multiple agents (HistoricalFeaturesExtractor, InitialPlanner) 
    using CompositeAgent pattern.
    
    Key difference from previous implementation:
    - Uses ExecutableWrapper to bridge analyzers into Executable interface
    - No more nested payload wrapping
    - Clean execution tree structure
    """

    REQUIRED_FIELDS = {
        'config': {
            'shared_source_config': {
                'databaseSchemas_path': str,
                'sharedDatabaseSchemas_path': str,
                'annotation_path': str,
                'progress_tracker_change_log_path': str,
                'mold_machine_weights_dir': str,
                'mold_machine_weights_hist_path': str,
                'mold_stability_index_dir': str,
                'mold_stability_index_change_log_path': str,
                'features_extractor_dir': str,
                'features_extractor_change_log_path': str,
                'features_extractor_constant_config_path': str,
                'initial_planner_dir': str,
                'initial_planner_change_log_path': str,
                'initial_planner_constant_config_path': str,
                'pending_processor_dir': str,
                'pending_processor_change_log_path': str,
                'producing_processor_dir': str,
                'producing_processor_change_log_path': str,
                'auto_planner_dir': str,
                'auto_planner_change_log_path': str
                },
            'efficiency': float,
            'loss': float,
            'feature_extractor': {
                'enabled': bool,
                'save_result': bool,
                'cavity_stability_threshold': float,
                'cycle_stability_threshold': float,
                'total_records_threshold': int,
                'scaling': str,
                'confidence_weight': float,
                'n_bootstrap': int,
                'confidence_level': float,
                'min_sample_size': int,
                'feature_weights': dict,
                'targets': dict
                },
            'initial_planner': {
                'enabled': bool,
                'save_result': bool,
                "priority_order": str,
                'max_load_threshold': int,
                'log_progress_interval': int
                },
            'save_orchestrator_log': bool
            }
        }

    def __init__(self, 
                 config: AutoPlannerConfig):
        
        """
        Initialize AutoPlanner with configuration.
        
        Args:        
            config: AutoPlannerConfig containing processing parameters, including:
                - shared_source_config: Paths for all sub-components
                - efficiency (float): Efficiency threshold [0-1] to classify good/bad records.
                - loss (float): Allowable production loss threshold [0-1].
                - feature_extractor (FeatureExtractorParams): HistoricalFeatureExtractor params
                - initial_planner (InitialPlannerParams): InitialPlanner params
                - save_planner_log (bool): Save planner change log
        """
        
        # Capture initialization arguments for reporting
        self._capture_init_args()

        # Initialize logger with class name for better tracking
        self.logger = logger.bind(class_="AutoPlanner")

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

    def run_scheduled_components(self) -> ExecutionResult:
        """
        Execute the complete auto planner pipeline.
        
        This method:
        1. Creates ExecutableWrappers for each enabled analyzer
        2. Uses CompositeAgent to execute them with automatic aggregation
        3. Saves pipeline log if requested
        4. Returns unified ExecutionResult
        
        Returns:
            ExecutionResult containing all sub-analyzer results
        """
        
        self.logger.info("Starting AutoPlanner ...")

        agent_id = self.__class__.__name__

        timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        config_header = self._generate_config_report(timestamp_str, required_only=True)
        
        # ============================================
        # BUILD EXECUTABLE LIST WITH WRAPPERS
        # ============================================
        executables: List[Executable] = []
        
        # 1. Historical Features Extractor (wrapped)
        if self.config.should_run_feature_extractor:
            def run_historical_features_extractor() -> ExecutionResult:
                """Factory function to create and run HistoricalFeaturesExtractor"""
                from agents.autoPlanner.featureExtractor.initial.historicalFeaturesExtractor.historical_features_extractor import (
                    HistoricalFeaturesExtractor)
                
                extractor = HistoricalFeaturesExtractor(
                    config=self.config.get_feature_extractor_config())
                
                if self.config.should_save_feature_extractor:
                    return extractor.run_extraction_and_save_results()
                else: 
                    return extractor.run_extraction()

            executables.append(
                ExecutableWrapper(
                    name="HistoricalFeaturesExtractor",
                    factory=run_historical_features_extractor,
                    on_error_severity=PhaseSeverity.ERROR.value  # Non-critical
                )
            )
            self.logger.info("✓ HistoricalFeaturesExtractor scheduled to run")

        # 2. Initial Planner (wrapped)
        if self.config.should_run_initial_planner:
            def run_initial_planner() -> ExecutionResult:
                """Factory function to create and run InitialPlanner"""
                from agents.autoPlanner.phases.initialPlanner.initial_planner import InitialPlanner
                
                planner = InitialPlanner(
                    config=self.config.get_initial_planner_config())

                if self.config.should_save_initial_planner:
                    return planner.run_planning_and_save_results()
                else: 
                    return planner.process_planning()
            
            executables.append(
                ExecutableWrapper(
                    name="InitialPlanner",
                    factory=run_initial_planner,
                    on_error_severity=PhaseSeverity.ERROR.value  # Non-critical
                )
            )
            self.logger.info("✓ InitialPlanner scheduled to run")
        
        # Check if any extractor or planner is scheduled to run
        if not executables:
            self.logger.warning("⚠️ No extractor or planner scheduled to run")
            return ExecutionResult(
                name="AutoPlanner",
                type="agent",
                status=ExecutionStatus.SKIPPED.value,
                duration=0.0,
                severity=PhaseSeverity.WARNING.value,
                skipped_reason="All extractor and planner skipped by configuration",
                metadata={
                    "should_run_feature_extractor": self.config.should_run_feature_extractor,
                    "should_run_initial_planner": self.config.should_run_initial_planner
                }
            )
        
        # ============================================
        # EXECUTE USING COMPOSITE AGENT
        # ============================================
        self.logger.info(f"🚀 Executing {len(executables)} scheduled component(s)...")
        
        agent = CompositeAgent("AutoPlanner", executables)
        result = agent.execute()
        
        # ============================================
        # SAVE PIPELINE LOG IF REQUESTED
        # ============================================
        if self.config.save_planner_log:
            try:
                # Generate summary report
                reporter = DictBasedReportGenerator(use_colors=False)
                summary = "\n".join(reporter.export_report(self.config.get_summary()))
                
                # Extract export metadata from all sub-results
                export_metadata_dict = extract_export_metadata(result)
                export_metadata = "\n".join(reporter.export_report(export_metadata_dict))
                
                # Save pipeline change log
                message = update_change_log(
                    agent_id, 
                    config_header, 
                    format_execution_tree(result), 
                    summary, 
                    export_metadata, 
                    Path(self.config.shared_source_config.auto_planner_change_log_path)
                )
                
                self.logger.info(f"📝 {message}")
                
            except Exception as e:
                self.logger.error(f"❌ Failed to save pipeline log: {e}")
                # Don't fail the entire pipeline just because log saving failed
                result.warnings.append({
                    "message": f"Failed to save pipeline log: {str(e)}",
                    "severity": PhaseSeverity.WARNING.value
                })

        # ============================================
        # PRINT EXECUTION TREE & ANALYSIS
        # ============================================
        self.logger.info(
            "✅ AutoPlanner completed in {:.2f}s! "
            "Status: {}",
            result.duration,
            result.status
        )
        
        # Print execution tree for visibility
        print_execution_summary(result)
        
        return result