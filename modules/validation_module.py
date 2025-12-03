# modules/validation_module.py

from pathlib import Path
from typing import Dict, List
from modules.base_module import BaseModule, ModuleResult

from agents.validationOrchestrator.validation_orchestrator import ValidationOrchestrator
from agents.autoPlanner.reportFormatters.dict_based_report_generator import DictBasedReportGenerator

class ValidationModule(BaseModule):
    """
    Module wrapper for ValidationOrchestrator.
    
    Handles validation pipeline.
    """
    
    DEFAULT_CONFIG_PATH = 'configs/modules/validation.yaml'

    @property
    def module_name(self) -> str:
        """Unique module name"""
        return "ValidationModule"
    
    @property
    def dependencies(self) -> List[str]:
        """No dependencies - this is typically the first module"""
        return []
    
    @property
    def context_outputs(self) -> List[str]:
        """Keys that this module writes to context"""
        return [
            'validation_result',
            'validation_report',
            'dataschemas_path',
            'annotation_path'
        ]

    def execute(self, 
                context: Dict, 
                dependencies: Dict) -> ModuleResult:
        """
        Execute DataPipelineOrchestrator.
        
        Args:
            context: Shared context (empty for first module)
            self.config: Configuration containing:
                - project_root: Project root directory
                - data_pipeline:
                    - source_path: Main shared database (from DataPipeline) directory
                    - annotation_name: # Annotation name
                    - databaseSchemas_path: Path to database schemas
                    - default_dir: Default directory for outputs
                    - use_colored_report: Whether to use colored output (default: True)
            dependencies: Empty dict (no dependencies)
            
        Returns:
            ModuleResult with pipeline execution results
        """
        
        try:

            # Extract self.config
            project_root = Path(self.config.get('project_root', '.'))
            validation_config = self.config.get('validation_orchestrator', {})
            
            # Main shared database from DataPipeline
            source_path = str(project_root / validation_config.get(
                'source_path', 
                'agents/shared_db/DataLoaderAgent/newest'))
            annotation_name = validation_config.get(
                'annotation_name',
                'path_annotations.json')
            
            databaseSchemas_path = str(project_root / validation_config.get(
                'databaseSchemas_path',
                'database/databaseSchemas.json'
            ))
            
            default_dir = str(project_root / validation_config.get(
                'default_dir',
                'agents/shared_db' 
            ))
            
            self.logger.info("ValidationOrchestrator configuration:")
            self.logger.info(f"  - Annotation Path: {source_path}/{annotation_name}")
            self.logger.info(f"  - Database Schemas: {databaseSchemas_path}")
            self.logger.info(f"  - Default Dir: {default_dir}")
            
            # Create orchestrator
            orchestrator = ValidationOrchestrator(
                source_path = source_path,
                annotation_name = annotation_name,
                databaseSchemas_path = databaseSchemas_path,
                default_dir = default_dir)

            # Run validations
            self.logger.info("Running validations...")
            results = orchestrator.run_validations_and_save_results()
            
            # Generate report
            use_colored_report = validation_config.get('use_colored_report', True)
            reporter = DictBasedReportGenerator(use_colors=use_colored_report)
            report_lines = reporter.export_report(results)
            report_text = "\n".join(report_lines)

            # Log report
            self.logger.info("Validation execution completed:")
            for line in report_lines:
                self.logger.info(line)
            
            # Return success result
            return ModuleResult(
                status='success',
                data={
                    'validation_results': results,
                    'report': report_text,
                    'dataschemas_path': databaseSchemas_path,
                    'annotation_path': f"{source_path}/{annotation_name}"
                },
                message='Validation completed successfully',
                context_updates={
                    'validation_result': results,
                    'validation_report': report_text,
                    'dataschemas_path': databaseSchemas_path,
                    'annotation_path': f"{source_path}/{annotation_name}"
                }
            )
            
        except Exception as e:
            self.logger.error(f"Validation failed: {e}", exc_info=True)
            return ModuleResult(
                status='failed',
                data=None,
                message=f"Validation execution failed: {str(e)}",
                errors=[str(e)]
            )