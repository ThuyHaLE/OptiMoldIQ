# workflows/executor.py

from pathlib import Path
import yaml
import uuid
from loguru import logger
import importlib

class WorkflowExecutor:

    def __init__(self, registry, workflows_dir: str):
        self.registry = registry
        self.workflows_dir = Path(workflows_dir)

    def _load_workflow(self, workflow_name: str) -> dict:
        path = self.workflows_dir / f"{workflow_name}.json"
        if not path.exists():
            raise FileNotFoundError(f"Workflow file not found: {path}")

        import json
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def get_workflow_info(self, workflow_name: str):
        return self._load_workflow(workflow_name)

    def execute(self, workflow_name: str, config_overrides=None) -> dict:
        workflow = self._load_workflow(workflow_name)
        modules = workflow["modules"]

        context = {}
        results = []

        execution_id = uuid.uuid4().hex[:8]
        logger.info(f"[{execution_id}] Executing workflow: {workflow_name}")

        for m in modules:
            module_name = m["module"]
            config_file = m["config_file"]
            dependency_policy = m['dependency_policy']

            logger.info(f"[{execution_id}] → Running module: {module_name}")

            # --- 1️⃣ get module class from registry
            ModuleClass = self.registry.get_module(module_name)

            if ModuleClass is None:
                raise ValueError(f"Module not found in registry: {module_name}")

            # --- 2️⃣ create instance (the most importance)
            module_instance = ModuleClass(config_path=config_file)

            # --- 3️⃣ execute module
            if dependency_policy is None:
                policy_instance = None
            else:
                try:
                    module_path, class_name = dependency_policy.rsplit(".", 1)
                    mod = importlib.import_module(module_path)
                    PolicyClass = getattr(mod, class_name)
                    policy_instance = PolicyClass()
                except (ImportError, AttributeError) as e:
                    raise ValueError(f"Cannot load dependency policy '{dependency_policy}': {e}")

            result = module_instance.safe_execute(context=context, 
                                                  dependency_policy=policy_instance)

            results.append({
                "module": module_name,
                "required": m.get("required", True),
                "status": result.status,
                "message": result.message,
                "data": result.data,
            })

            # --- update context
            context[module_name] = result
            if result.context_updates:
                context.update(result.context_updates)

            # --- required fail → stop workflow
            if m.get("required", True) and result.is_failed():
                return {
                    "status": "failed",
                    "workflow": workflow_name,
                    "message": f"Module {module_name} failed",
                    "results": results,
                    "context": context
                }

        # --- OK → success
        return {
            "status": "success",
            "workflow": workflow_name,
            "message": "Workflow completed",
            "results": results,
            "context": context
        }