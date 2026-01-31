from pathlib import Path
from loguru import logger
from datetime import datetime
import pandas as pd
from typing import Dict, Any, NoReturn, List
from configs.shared.config_report_format import ConfigReportMixin
from configs.shared.shared_source_config import SharedSourceConfig
from configs.shared.dict_based_report_generator import DictBasedReportGenerator
from agents.dataPipelineOrchestrator.configs.save_output_formatter import save_collected_data

# Import agent report format components
from configs.shared.agent_report_format import (
    Executable,
    ExecutionResult,
    AtomicPhase,
    CompositeAgent,
    print_execution_summary,
    format_execution_tree,
    update_change_log,
    save_result,
    format_export_logs)

# ============================================
# PHASE 1: DATABASE COLLECTING
# ============================================
class DatabaseCollectingPhase(AtomicPhase):
    """Phase for running the actual database collecting logic"""
    
    RECOVERABLE_ERRORS = (KeyError, ValueError, pd.errors.MergeError)
    CRITICAL_ERRORS = (MemoryError, KeyboardInterrupt)
    FALLBACK_FAILURE_IS_CRITICAL = True  # Can return partial results
    
    def __init__(self, 
                 config: SharedSourceConfig):
        super().__init__("DataPipelineProcessor")
        self.config = config
    
    def _execute_impl(self) -> Dict[str, Any]:
        """Run database collecting logic"""
        logger.info("🔄 Running database collecting...")
        
        # Import DataPipelineProcessor
        from agents.dataPipelineOrchestrator.processors.data_pipeline_processor import DataPipelineProcessor
        from agents.dataPipelineOrchestrator.configs.output_formats import ProcessingStatus

        # Initialize and run processsor
        processsor = DataPipelineProcessor(config = self.config)
        processsor_result = processsor.run_pipeline()
        
        logger.info("✓ Progress collector completed")
        
        return {
                "payload": {
                    "collected_data": processsor_result.collected_data,
                    "path_annotation": processsor_result.path_annotation,
                    "log_str": processsor_result.metadata['log']
                },
                "savable": processsor_result.status == ProcessingStatus.SUCCESS
            }
        
    def _fallback(self) -> NoReturn:
        """
        No valid fallback for database collecting.
        Raise to ensure CRITICAL severity is applied.
        """
        logger.error("DataPipelineProcessor cannot fallback - error database collecting")
        
        raise RuntimeError(
            "Error database collecting."
            "DataPipelineProcessor cannot fallback."
        )

# ============================================
# MAIN AGENT: DATA PIPELINE ORCHESTRATOR
# ============================================

class DataPipelineOrchestrator(ConfigReportMixin):
    """
    Data Pipeline Orchestrator Agent
    
    Orchestrates the complete database collecting workflow using
    the standardized agent report format.
    """
    
    REQUIRED_FIELDS = {
        'annotation_path': str,
        'databaseSchemas_path': str,
        'shared_database_dir': str,
        'manual_review_notifications_dir': str,
        'data_pipeline_change_log_path': str
    }
    
    def __init__(self, config: SharedSourceConfig):
        """
        Initialize the DataPipelineOrchestrator agent
        
        Args:        
            config: SharedSourceConfig containing processing parameters, including:
                - annotation_path (str): Path to the JSON file containing database path annotations.
                - databaseSchemas_path (str): Path to database schema for validation.
                - shared_database_dir (str): Default directory for output and temporary files.
                - manual_review_notifications_dir (str): Default directory for healing notifications (if any)
                - data_pipeline_change_log_path (str): Path to the DataPipelineOrchestrator change log.
        """
        
        # Capture initialization arguments for reporting
        self._capture_init_args()
        
        # Initialize logger
        self.logger = logger.bind(class_="DataPipelineOrchestrator")
        
        # Validate required configs
        is_valid, errors = config.validate_requirements(self.REQUIRED_FIELDS)
        if not is_valid:
            raise ValueError(
                f"{self.__class__.__name__} config validation failed:\n" +
                "\n".join(f"  - {e}" for e in errors)
            )
        self.logger.info("✓ Validation for config requirements: PASSED!")
        
        # Store config
        self.config = config

        self.save_routing = {
            "DataPipelineProcessor": {
                "enabled": True,
                "save_fn": save_collected_data,
                "save_paths": {
                    "output_dir": f"{self.config.shared_database_dir}",
                    "change_log_path": self.config.annotation_path
                }
            }
        }

    def run_collecting(self, **kwargs) -> ExecutionResult:
        """
        Main execution method using agent report format
        
        Returns:
            ExecutionResult: Hierarchical execution report
        """

        self.logger.info("Starting DataPipelineOrchestrator ...")

        # ============================================
        # BUILD PHASE LIST WITH SHARED CONFIG
        # ============================================
        phases: List[Executable] = [DatabaseCollectingPhase(self.config)]
        
        # ============================================
        # EXECUTE USING COMPOSITE AGENT
        # ============================================
        agent = CompositeAgent("DataPipelineOrchestrator", phases)
        result = agent.execute()
        
        # ============================================
        # PRINT EXECUTION TREE & ANALYSIS
        # ============================================
        self.logger.info("✅ DataPipelineOrchestrator completed in {:.2f}s!", result.duration)
        
        # Print execution tree for visibility
        print_execution_summary(result)
        
        return result
                
    def run_collecting_and_save_results(self, **kwargs) -> ExecutionResult:
        """
        Execute collecting and save results to Excel files.
        
        Returns:
            ExecutionResult: Hierarchical execution result with saved data
        """

        agent_id = self.__class__.__name__

        timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        config_header = self._generate_config_report(timestamp_str, required_only=True)

        try:
            # Execute collecting
            result = self.run_collecting(**kwargs)

            # Process save routing and collect metadata
            save_routing, export_metadata = save_result(self.save_routing, result)

            # Log any export failures (optional, doesn't affect execution status)
            for phase_name, phase_export in export_metadata.items():
                if phase_export and phase_export.get('metadata'):
                    phase_metadata = phase_export['metadata']
                    if phase_metadata.get('status') == 'failed':
                        self.logger.warning(
                            "⤷ Phase {}: ⚠️ Excel export failed: {}",
                            phase_name,
                            phase_metadata.get('export_log')
                        )

            # Update result metadata
            result.metadata.update({
                'save_routing': save_routing,
                'export_metadata': export_metadata
            })
            
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
                Path(self.config.data_pipeline_change_log_path)
            )

            self.logger.info(f"Pipeline log saved: {message}")

            return result

        except Exception as e:
            self.logger.error("❌ Failed to save results: {}", str(e))
            raise