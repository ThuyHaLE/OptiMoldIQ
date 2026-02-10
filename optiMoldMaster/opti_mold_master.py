# optiMoldMaster/optim_mold_master.py

from pathlib import Path
from typing import Dict, Any, List
from loguru import logger
import json

from optiMoldMaster.workflows.registry.registry import ModuleRegistry
from optiMoldMaster.workflows.executor import WorkflowExecutor, WorkflowExecutorResult
from optiMoldMaster.workflows.dependency_policies.factory import DependencyPolicyFactory

class OptiMoldIQ:
    """
    Master orchestrator orchestrate multiple workflows.
    
    Features:
    - Auto-discover workflows from definitions/
    - Lazy load workflow executor
    - Support workflow chaining
    - Centralized workflow management
    """
    
    def __init__(
        self,
        module_registry: ModuleRegistry,
        workflows_dir: str = "optiMoldMaster/workflows/definitions"
    ):
        self.module_registry = module_registry
        self.workflows_dir = Path(workflows_dir)
        
        # Cache executors (1 executor per workflow type)
        self._executors: Dict[str, WorkflowExecutor] = {}
        
        # Discover available workflows
        self._available_workflows = self._discover_workflows()
        
        logger.info(f"📋 Orchestrator initialized with {len(self._available_workflows)} workflows")
    
    # ------------------------------------------------------------------
    # Workflow Discovery
    # ------------------------------------------------------------------
    def _discover_workflows(self) -> Dict[str, Path]:
        """Auto-discover workflows with schema validation."""
        workflows = {}
        
        for json_file in self.workflows_dir.glob("*.json"):
            workflow_name = json_file.stem
            
            try:
                # Load JSON
                with open(json_file, 'r') as f:
                    workflow_def = json.load(f)
                
                # Validate workflow
                self._validate_workflow_definition(workflow_def, workflow_name)
                
                workflows[workflow_name] = json_file
                logger.info(f"✅ Loaded workflow: {workflow_name}")
                
            except Exception as e:
                logger.error(f"❌ Failed to load workflow '{workflow_name}': {e}")
                # Continue discovering other workflows
        
        return workflows
    
    def _validate_workflow_definition(self, 
                                      workflow_def: Dict, 
                                      workflow_name: str):
        """
        Validate workflow definition including dependency policies.
        Raises ValueError if invalid.
        """
        errors = []
        
        # Check basic structure
        if "modules" not in workflow_def:
            errors.append("Missing 'modules' field")
        
        # Validate each module's dependency_policy
        for idx, module_cfg in enumerate(workflow_def.get("modules", [])):
            module_name = module_cfg.get("module", f"module_{idx}")
            
            if "module" not in module_cfg:
                errors.append(f"Module {idx}: Missing 'module' field")
                continue
            
            # Validate dependency_policy if present
            policy_cfg = module_cfg.get("dependency_policy")
            if policy_cfg is not None:
                try:
                    # This will validate against schema
                    DependencyPolicyFactory.create(policy_cfg)
                except (ValueError, TypeError) as e:
                    errors.append(f"Module '{module_name}': {e}")
        
        # Raise if any errors
        if errors:
            error_msg = f"Invalid workflow '{workflow_name}':\n" + \
                       "\n".join(f"  - {e}" for e in errors)
            raise ValueError(error_msg)
        
    def list_workflows(self) -> List[str]:
        """Get list of available workflow names."""
        return list(self._available_workflows.keys())
    
    def get_workflow_info(self, workflow_name: str) -> Dict[str, Any]:
        """Get workflow definition without executing."""
        executor = self._get_or_create_executor(workflow_name)
        return executor.get_workflow_info(workflow_name)
    
    # ------------------------------------------------------------------
    # Executor Management (Lazy Loading)
    # ------------------------------------------------------------------
    def _get_or_create_executor(self, workflow_name: str) -> WorkflowExecutor:
        """
        Get or create executor for workflow.
        Cache to reuse execution_cache if using same workflow type.
        """
        if workflow_name not in self._available_workflows:
            raise ValueError(
                f"Workflow '{workflow_name}' not found. "
                f"Available: {list(self._available_workflows.keys())}"
            )
        
        # Cache executor per workflow (reuse execution cache)
        if workflow_name not in self._executors:
            logger.debug(f"Creating new executor for: {workflow_name}")
            self._executors[workflow_name] = WorkflowExecutor(
                registry=self.module_registry,
                workflows_dir=str(self.workflows_dir)
            )
        
        return self._executors[workflow_name]
    
    # ------------------------------------------------------------------
    # Workflow Execution
    # ------------------------------------------------------------------
    def execute(self,
                workflow_name: str,
                clear_cache: bool = False) -> WorkflowExecutorResult:
        """
        Execute a workflow by name.
        
        Args:
            workflow_name: Name of workflow (e.g., 'update_database')
            clear_cache: Clear execution cache before running
            
        Returns:
            Workflow execution result
        """
        logger.info(f"🎬 Orchestrator executing workflow: {workflow_name}")
        
        executor = self._get_or_create_executor(workflow_name)
        
        # Optionally clear cache
        if clear_cache:
            logger.info(f"🗑️  Clearing execution cache for: {workflow_name}")
            executor._execution_cache.clear()
        
        return executor.execute(workflow_name=workflow_name)
    
    # ------------------------------------------------------------------
    # Workflow Chaining
    # ------------------------------------------------------------------
    def execute_chain(
        self,
        workflow_names: List[str],
        stop_on_failure: bool = True
    ) -> Dict[str, Dict[str, Any]]:
        """
        Execute multiple workflows in sequence.
        
        Args:
            workflow_names: List of workflows to execute in order
            stop_on_failure: Stop chain if any workflow fails
            
        Returns:
            Dict mapping workflow_name -> execution result
        """
        logger.info(f"⛓️  Executing workflow chain: {' → '.join(workflow_names)}")
        
        results = {}
        
        for workflow_name in workflow_names:
            logger.info(f"▶️  Chain step: {workflow_name}")
            
            result = self.execute(workflow_name)
            results[workflow_name] = result
            
            # Check failure
            if stop_on_failure and result.get("status") == "failed":
                logger.error(f"❌ Chain stopped at: {workflow_name}")
                break
        
        return results
    
    # ------------------------------------------------------------------
    # Cache Management
    # ------------------------------------------------------------------
    def clear_all_caches(self):
        """Clear execution cache for all workflows."""
        for workflow_name, executor in self._executors.items():
            logger.info(f"🗑️  Clearing cache for: {workflow_name}")
            executor._execution_cache.clear()
    
    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics for all workflows."""
        stats = {}
        for workflow_name, executor in self._executors.items():
            stats[workflow_name] = len(executor._execution_cache)
        return stats