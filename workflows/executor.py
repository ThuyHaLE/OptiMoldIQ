# workflows/executor.py

from pathlib import Path
from typing import Dict, Any
import json
import uuid
from loguru import logger
from dataclasses import dataclass, field

from modules.base_module import ModuleResult
from workflows.dependency_policies.factory import DependencyPolicyFactory
from workflows.registry.registry import ModuleRegistry

@dataclass
class WorkflowExecutorResult:
    """Standardized result format returned by executor"""
    execution_id: str
    workflow_name: str
    status: str  # 'success' | 'failed' | 'skipped'
    message: str
    results: Dict = field(default_factory=dict)
    execution_context: Dict = field(default_factory=dict)
    def is_success(self) -> bool:
        return self.status == 'success'
    def is_skipped(self) -> bool:
        return self.status == 'skipped'
    def is_failed(self) -> bool:
        return self.status == 'failed'
    
class WorkflowExecutor:
    """
    Production Workflow Executor
    - Execute modules
    - Manage context, cache, retry, required logic

    for module in execution_order:
    1. build dependency_policy
    2. validate_dependencies()
       → failed? STOP / SKIP
    3. safe_execute()
    4. update context
    """

    def __init__(
        self,
        registry: ModuleRegistry,
        workflows_dir: str,
    ):
        self.registry = registry
        self.workflows_dir = Path(workflows_dir)

        # Cache execution results across workflow run
        self._execution_cache: Dict[str, ModuleResult] = {}

    # ------------------------------------------------------------------
    # Workflow loading
    # ------------------------------------------------------------------
    def _load_workflow(self, workflow_name: str) -> Dict[str, Any]:
        path = self.workflows_dir / f"{workflow_name}.json"
        if not path.exists():
            raise FileNotFoundError(f"Workflow file not found: {path}")

        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def get_workflow_info(self, workflow_name: str) -> Dict[str, Any]:
        return self._load_workflow(workflow_name)

    # ------------------------------------------------------------------
    # Core execution
    # ------------------------------------------------------------------
    def execute(
        self,
        workflow_name: str) -> WorkflowExecutorResult:

        workflow = self._load_workflow(workflow_name)
        workflow_modules = workflow["modules"]
        requested_modules = [m["module"] for m in workflow_modules]

        results: Dict[str, ModuleResult] = {}

        execution_id = uuid.uuid4().hex[:8]
        logger.info(f"[{execution_id}] ▶️ Executing workflow: {workflow_name}")

        # --------------------------------------------------------------
        # Execute modules
        # --------------------------------------------------------------
        for module in workflow_modules:
            module_name = module.get("module")
            module_config_path = module.get("config_file", None)
            module_dependency_policy = module.get("dependency_policy")
            module_required = module.get("required", False)

            if module_name in self._execution_cache:
                logger.info(f"[{execution_id}] ♻️ Reusing cached result: {module_name}")
                result = self._execution_cache[module_name]
                results[module_name] = result
                continue

            # 🔹 Instantiate FIRST
            logger.info(f"[{execution_id}] 🚀 Executing module: {module_name}")
            module_instance = self.registry.get_module_instance(module_name, module_config_path)
            
            dependency_policy = DependencyPolicyFactory.create(module_dependency_policy)

            # 🔹 Validate dependency BEFORE execution
            dep_result = self.validate_dependencies(
                module_instance=module_instance,
                requested_modules=requested_modules,
                dependency_policy=dependency_policy
            )

            if not dep_result.valid:
                logger.error(
                    f"[{execution_id}] Dependency validation failed for {module_name}: "
                    f"{dep_result.summary()}"
                )

                if module_required:
                    return self._build_response(
                        workflow_name,
                        execution_id,
                        status="failed",
                        message=f"Dependency validation failed: {module_name}",
                        results=results
                    )

                skip_result = ModuleResult(
                    status="skipped",
                    data=None,
                    message=f"Dependencies not met: {dep_result.summary()}",
                    errors=[issue.to_dict() for issue in dep_result.errors.values()]
                )
                results[module_name] = skip_result
                continue

            # 🔹 Execute
            result = module_instance.safe_execute()

            self._execution_cache[module_name] = result
            results[module_name] = result

            if module_required and result.is_failed():
                logger.error(f"[{execution_id}] ❌ Required module failed: {module_name}")
                return self._build_response(
                    workflow_name,
                    execution_id,
                    status="failed",
                    message=f"Module {module_name} failed",
                    results=results
                )

        # Add success return
        logger.info(f"[{execution_id}] ✅ Workflow completed successfully: {workflow_name}")
        return self._build_response(
            workflow_name,
            execution_id,
            status="success",
            message="Workflow completed successfully",
            results=results
        )

    # ------------------------------------------------------------------
    # Dependency validation
    # ------------------------------------------------------------------
    def validate_dependencies(
        self,
        module_instance,
        requested_modules,
        dependency_policy=None
    ):
        if dependency_policy is None:
            # StrictWorkflowPolicy use as default
            from workflows.dependency_policies.strict import StrictWorkflowPolicy
            dependency_policy = StrictWorkflowPolicy()

        return dependency_policy.validate(
            module_instance.dependencies,
            requested_modules
        )
    
    # ------------------------------------------------------------------
    # Response builder
    # ------------------------------------------------------------------
    def _build_response(
        self,
        workflow_name: str,
        execution_id: str,
        status: str,
        message: str,
        results: Dict[str, ModuleResult]
    ) -> WorkflowExecutorResult:

        return WorkflowExecutorResult(
            execution_id=execution_id,
            workflow_name=workflow_name,
            status=status,
            message=message,
            results={
                name: {
                    "status": r.status,
                    "message": r.message,
                    "data": r.data,
                    "errors": r.errors,
                }
                for name, r in results.items()
            },
            execution_context={
                "cached_modules": list(self._execution_cache.keys()),
                "total_modules": len(results)
            }
        )