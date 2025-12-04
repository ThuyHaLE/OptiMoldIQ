# modules/validation_module.py

from pathlib import Path
from typing import Dict, List
from modules.base_module import BaseModule, ModuleResult
from loguru import logger

from agents.validationOrchestrator.validation_orchestrator import ValidationOrchestrator

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
            'validation_orchestrator_result',
            'validation_orchestrator_log',
            'dataschemas_path',
            'annotation_path'
        ]

    def execute(self, 
                context: Dict, 
                dependencies: Dict) -> ModuleResult:
        """
        Execute ValidationOrchestrator.
        
        Args:
            context: Shared context (empty for first module)
            self.config: Configuration containing:
                - project_root: Project root directory
                - validation:
                    - source_path: Main shared database (from DataPipeline) directory
                    - annotation_name: # Annotation name
                    - databaseSchemas_path: Path to database schemas
                    - default_dir: Default directory for outputs
                    - use_colored_report: Whether to use colored output (default: True)
            dependencies: Empty dict (no dependencies)
            
        Returns:
            ModuleResult with pipeline execution results
        """
        
        self.logger = logger.bind(class_="ValidationModule")

        try:

            # Extract self.config
            project_root = Path(self.config.get('project_root', '.'))
            validation_config = self.config.get('validation', {})
            
            self.logger.debug("Project root: {}", project_root)
            
            if not validation_config:
                self.logger.debug("Cannot load ValidationOrchestrator config")

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
            results, log_str = orchestrator.run_validations_and_save_results()

            self.logger.info("Validation execution completed!")
 
            # Return success result
            return ModuleResult(
                status='success',
                data={
                    'validation_results': results,
                    'validation_log': log_str
                },
                message='Validation completed successfully',
                context_updates={
                    'validation_orchestrator_result': results,
                    'validation_orchestrator_log': log_str,
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