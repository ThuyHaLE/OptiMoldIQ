# optiMoldMaster/optim_mold_master.py

from pathlib import Path
from typing import Dict, Any, List, Optional
from loguru import logger
import json
import time
import ast
import numpy as np
import pandas as pd

from workflows.registry.registry import ModuleRegistry
from workflows.executor import WorkflowExecutor, WorkflowExecutorResult
from workflows.dependency_policies.factory import DependencyPolicyFactory

import uuid
import threading
from dataclasses import dataclass

@dataclass
class WorkflowRunRecord:
    execution_id: str
    workflow_name: str
    status: str
    timestamp: float
    duration: float
    summary: Dict[str, Any]
    viz_data: Optional[Dict[str, Any]]
    def is_success(self) -> bool:
        return self.status == 'success'
    def is_failed(self) -> bool:
        return self.status == 'failed'
    def to_dict(self) -> Dict[str, Any]:
        return {
            "execution_id": self.execution_id,
            "workflow_name": self.workflow_name,
            "status": self.status,
            "timestamp": self.timestamp,
            "duration": self.duration,
            "summary": self._safe_convert(self.summary),
            "viz_data": self._safe_convert(self.viz_data),
        }

    def _safe_convert(self, obj):
        if obj is None:
            return None
        if isinstance(obj, dict):
            return {k: self._safe_convert(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [self._safe_convert(v) for v in obj]
        if isinstance(obj, (np.integer, np.floating)):
            return obj.item()
        if isinstance(obj, pd.Timestamp):
            return obj.isoformat()
        if isinstance(obj, pd.DataFrame):
            return obj.where(pd.notna(obj), None).to_dict(orient="records")
        if isinstance(obj, pd.Series):
            return obj.where(pd.notna(obj), None).to_dict()
        return obj

# ------------------------------------------------------------------
# Default params (override via __init__ if needed)
# ------------------------------------------------------------------
_DEFAULT_CHANGE_LOG_PARAMS = {
    "ProgressTrackingModule": {
        "r_var": "tracking_result",
        "a_name": "ProgressTracker"
    },
    "AnalyticsModule": {
        "r_var": "orchestrator_result",
        "a_name": {
            "HardwareChangeAnalyzer":        ["MachineLayoutTracker", "MoldMachinePairTracker"],
            "MultiLevelPerformanceAnalyzer": ["DayLevelDataProcessor", "MonthLevelDataProcessor", "YearLevelDataProcessor"]
        }
    },
    "InitialPlanningModule": {
        "r_var": "planning_result",
        "a_name": {
            "InitialPlanner": ["ProducingOrderPlanner", "PendingOrderPlanner"]
        }
    }
}

_DEFAULT_SHEET_NAME_PARAMS = {
    "AnalyticsModule": {
        "MachineLayoutTracker":            ["machineLayoutChange"],
        "MoldMachinePairTracker":          ["machineMoldFirstRunPair", "moldMachineFirstRunPair"],
        "DayLevelDataProcessor":           ["moldBasedRecords", "itemBasedRecords"],
        "MonthLevelDataProcessor":         ["finishedRecords", "unfinishedRecords"],
        "YearLevelDataProcessor":          ["finishedRecords", "unfinishedRecords"],
    },
    "ProgressTrackingModule": {
        "ProgressTracker": ["productionStatus"]
    },
    "InitialPlanningModule": {
        "ProducingOrderPlanner": ["producing_pro_plan", "producing_mold_plan", "producing_plastic_plan"],
        "PendingOrderPlanner":   ["initial_plan"]
    }
}


class OptiMoldIQ:
    """
    Master orchestrator for multiple workflows.

    Features:
    - Auto-discover workflows from definitions/
    - Lazy load workflow executor
    - Support workflow chaining
    - Centralized workflow management
    - Viz cache: processed Excel data snapshots for control panel display
    """

    def __init__(
        self,
        module_registry: ModuleRegistry,
        workflows_dir: str = "workflows/definitions",
        change_log_params: Optional[Dict] = None,
        sheet_name_params: Optional[Dict] = None,
    ):
        self.module_registry = module_registry
        self.workflows_dir = Path(workflows_dir)

        # Viz params — use defaults if not provided via constructor
        self._change_log_params = change_log_params or _DEFAULT_CHANGE_LOG_PARAMS
        self._sheet_name_params = sheet_name_params or _DEFAULT_SHEET_NAME_PARAMS

        # Cache executors (1 executor per workflow type)
        self._executors: Dict[str, WorkflowExecutor] = {}

        # Viz cache: processed viz data per workflow (None if extraction failed)
        self._viz_cache: Dict[str, Optional[Dict[str, Any]]] = {}

        self._available_workflows = self._discover_workflows()
        logger.info(f"📋 Orchestrator initialized with {len(self._available_workflows)} workflows")

        self._run_lock = threading.Lock()
        self._run_records: Dict[str, WorkflowRunRecord] = {}
        self._latest_run_per_workflow: Dict[str, str] = {}

    def _generate_execution_id(self) -> str:
        return uuid.uuid4().hex[:8]

    def _build_summary(self, result: WorkflowExecutorResult) -> Dict[str, Any]:
        modules = {
            name: r.get("status")
            for name, r in result.results.items()
        }

        first_failed = next(
            (m for m, s in modules.items() if s == "failed"),
            None
        )

        success = sum(1 for s in modules.values() if s == "success")
        failed  = sum(1 for s in modules.values() if s == "failed")
        total   = len(modules)

        return {
            "total": total,
            "success": success,
            "failed": failed,
            "skipped": total - success - failed,
            "modules": modules,
            "first_failed": first_failed
        }

    def _execute_internal(
            self,
            workflow_name: str,
            execution_id: str,
            clear_cache: bool = False
        ) -> WorkflowExecutorResult:

        logger.info(f"🎬 Executing workflow: {workflow_name} | run={execution_id}")

        executor = self._get_or_create_executor(workflow_name)

        if clear_cache:
            logger.info(f"🗑️  Clearing execution cache for: {workflow_name}")
            executor._execution_cache.clear()

        result = executor.execute(workflow_name=workflow_name)

        #-------------------------------------------#
        # Future work: healing mechanism to attempt recovery and viz extraction even if initial execution failed.
        # For now, we skip viz extraction on failed runs
        # to mirror notebook logic and avoid complications of partial/failed executions.
        #-------------------------------------------#
        # if result.is_failed():
        #     healed = self._attempt_healing(workflow_name, executor, result)
        #     if healed:
        #         result = executor.execute(workflow_name=workflow_name)
        #-------------------------------------------#

        viz_data = None

        #-------------------------------------------#
        # Only extract viz if final result succeeded —
        # mirrors notebook logic and avoids complications of partial/failed executions.
        #-------------------------------------------#
        if not result.is_failed():
            try:
                viz_data_paths = self._get_data_paths(workflow_name, result)
                viz_data = self._process_viz_data(workflow_name, viz_data_paths)
            except Exception as e:
                logger.warning(f"⚠️ Viz extraction failed for '{workflow_name}' | run={execution_id}: {e}")

        #-------------------------------------------#
        # Always write cache once — atomic lifecycle
        #-------------------------------------------#
        with self._run_lock:
            self._viz_cache[execution_id] = viz_data

        return result

    def execute(
        self,
        workflow_name: str,
        clear_cache: bool = False
    ) -> WorkflowRunRecord:

        execution_id = self._generate_execution_id()
        start_time = time.time()

        result = self._execute_internal(workflow_name, execution_id, clear_cache)

        end_time = time.time()

        summary = self._build_summary(result)
        status = "failed" if result.is_failed() else "success"

        with self._run_lock:
            viz_data = self._viz_cache.get(execution_id)

        record = WorkflowRunRecord(
            execution_id=execution_id,
            workflow_name=workflow_name,
            status=status,
            timestamp=end_time,
            duration=round(end_time - start_time, 3),
            summary=summary,
            viz_data=viz_data
        )

        with self._run_lock:
            self._run_records[execution_id] = record
            self._latest_run_per_workflow[workflow_name] = execution_id

        return record

    def execute_chain(
        self,
        workflow_names: List[str],
        stop_on_failure: bool = True
    ) -> Dict[str, WorkflowRunRecord]:

        logger.info(f"⛓️ Executing chain: {' → '.join(workflow_names)}")

        results = {}

        for workflow_name in workflow_names:
            run = self.execute(workflow_name)
            results[workflow_name] = run

            if stop_on_failure and run.status == "failed":
                logger.error(f"❌ Chain stopped at: {workflow_name}")
                break

        return results

    # ------------------------------------------------------------------
    # Workflow Discovery
    # ------------------------------------------------------------------
    def _discover_workflows(self) -> Dict[str, Path]:
        """Auto-discover and validate workflows from the definitions directory."""
        workflows = {}
        for json_file in self.workflows_dir.glob("*.json"):
            workflow_name = json_file.stem
            try:
                with open(json_file, "r") as f:
                    workflow_def = json.load(f)
                self._validate_workflow_definition(workflow_def, workflow_name)
                workflows[workflow_name] = json_file
                logger.info(f"✅ Loaded workflow: {workflow_name}")
            except Exception as e:
                logger.error(f"❌ Failed to load workflow '{workflow_name}': {e}")
        return workflows

    def _validate_workflow_definition(self, workflow_def: Dict, workflow_name: str):
        """
        Validate workflow definition structure and dependency policies.
        Raises ValueError if any validation errors are found.
        """
        errors = []
        if "modules" not in workflow_def:
            errors.append("Missing 'modules' field")
        for idx, module_cfg in enumerate(workflow_def.get("modules", [])):
            module_name = module_cfg.get("module", f"module_{idx}")
            if "module" not in module_cfg:
                errors.append(f"Module {idx}: Missing 'module' field")
                continue
            policy_cfg = module_cfg.get("dependency_policy")
            if policy_cfg is not None:
                try:
                    DependencyPolicyFactory.create(policy_cfg)
                except (ValueError, TypeError) as e:
                    errors.append(f"Module '{module_name}': {e}")
        if errors:
            raise ValueError(
                f"Invalid workflow '{workflow_name}':\n" +
                "\n".join(f"  - {e}" for e in errors)
            )

    def list_workflows(self) -> List[str]:
        """Return list of available workflow names."""
        return list(self._available_workflows.keys())

    def get_workflow_info(self, workflow_name: str) -> Dict[str, Any]:
        """Return workflow definition without executing."""
        executor = self._get_or_create_executor(workflow_name)
        return executor.get_workflow_info(workflow_name)

    # ------------------------------------------------------------------
    # Executor Management (Lazy Loading)
    # ------------------------------------------------------------------
    def _get_or_create_executor(self, workflow_name: str) -> WorkflowExecutor:
        """
        Get or create a cached executor for the given workflow.
        Reuses execution cache across calls for the same workflow type.
        """
        if workflow_name not in self._available_workflows:
            raise ValueError(
                f"Workflow '{workflow_name}' not found. "
                f"Available: {list(self._available_workflows.keys())}"
            )
        if workflow_name not in self._executors:
            logger.debug(f"Creating new executor for: {workflow_name}")
            self._executors[workflow_name] = WorkflowExecutor(
                registry=self.module_registry,
                workflows_dir=str(self.workflows_dir)
            )
        return self._executors[workflow_name]

    # ------------------------------------------------------------------
    # Viz — Data Path Resolution
    # ------------------------------------------------------------------
    def _get_newest_path(self, change_log_path: str) -> Path:
        """Resolve the newest data file path from a change log."""
        from agents.utils import read_change_log
        return read_change_log(
            Path(change_log_path).parent,
            Path(change_log_path).name
        )

    def _get_data_paths(
        self,
        workflow_name: str,
        result: WorkflowExecutorResult
    ) -> Dict[str, Any]:
        """
        Resolve Excel file paths for the last module in the workflow result,
        mirroring the original notebook behavior.

        Returns:
            Dict mapping sub_name -> Path (multi-agent)
                    or module_name -> Path (single agent)
        """
        # Only process the last module — same as notebook
        last_module_name = list(result.results.keys())[-1]

        if last_module_name not in self._change_log_params:
            raise KeyError(f"Module '{last_module_name}' not found in change_log_params")

        params   = self._change_log_params[last_module_name]
        r_var    = params["r_var"]
        a_name   = params["a_name"]
        m_result = result.results[last_module_name]["data"][r_var]

        data_paths = {}

        if isinstance(a_name, str):
            change_log_path = m_result.metadata["save_routing"][a_name]["save_paths"]["change_log_path"]
            data_paths[last_module_name] = self._get_newest_path(change_log_path)

        elif isinstance(a_name, dict):
            data_paths[last_module_name] = {}
            sub_result = m_result.sub_results

            for agent, subs in a_name.items():
                a_result = [r for r in sub_result if r.name == agent][0].metadata["save_routing"]

                if isinstance(subs, str):
                    change_log_path = a_result[subs]["save_paths"]["change_log_path"]
                    data_paths[last_module_name][subs] = self._get_newest_path(change_log_path)

                elif isinstance(subs, list):
                    for s in subs:
                        change_log_path = a_result[s]["save_paths"]["change_log_path"]
                        data_paths[last_module_name][s] = self._get_newest_path(change_log_path)

        return data_paths

    # ------------------------------------------------------------------
    # Viz Cache — Access
    # ------------------------------------------------------------------
    def get_viz_data(self, workflow_name: str) -> Optional[Dict[str, Any]]:
        """
        Return viz data from the latest run of a workflow.

        Does NOT trigger execution.
        """

        latest_run = self.get_latest_run(workflow_name)

        if not latest_run:
            logger.warning(f"⚠️  No runs found for '{workflow_name}'")
            return None

        viz = self._viz_cache.get(latest_run.execution_id)

        if viz is None:
            logger.warning(f"⚠️  Viz data missing in cache for run '{latest_run.execution_id}'")
            viz = latest_run.viz_data

        return viz

    def get_all_viz_data(self) -> Dict[str, Optional[Dict[str, Any]]]:
        """
        Return latest viz snapshot per workflow.
        """
        output = {}

        for workflow_name in self._latest_run_per_workflow:
            latest = self.get_latest_run(workflow_name)
            if not latest:
                output[workflow_name] = None
                continue

            viz = self._viz_cache.get(latest.execution_id)

            if viz is None:
                viz = latest.viz_data

            output[workflow_name] = viz

        return output

    def get_viz_data_by_run(self, execution_id: str) -> Optional[Dict[str, Any]]:
        return self._viz_cache.get(execution_id)

    # ------------------------------------------------------------------
    # Cache Management
    # ------------------------------------------------------------------
    def get_run(self, execution_id: str) -> Optional[WorkflowRunRecord]:
        return self._run_records.get(execution_id)

    def get_latest_run(self, workflow_name: str) -> Optional[WorkflowRunRecord]:
        run_id = self._latest_run_per_workflow.get(workflow_name)
        if not run_id:
            return None

        record = self._run_records.get(run_id)
        if record:
            return record

        # fallback scan (future async-safe)
        runs = self.list_runs(workflow_name)
        return runs[0] if runs else None

    def list_runs(self, workflow_name: Optional[str] = None, limit: Optional[int] = None) -> List[WorkflowRunRecord]:
        runs = (
            self._run_records.values()
            if workflow_name is None
            else [r for r in self._run_records.values() if r.workflow_name == workflow_name]
        )
        sorted_runs = sorted(runs, key=lambda r: r.timestamp, reverse=True)
        return sorted_runs[:limit] if limit else sorted_runs

    def get_cache_stats(self) -> Dict[str, Any]:
        return {
            "execution": {
                name: len(executor._execution_cache)
                for name, executor in self._executors.items()
            },
            "viz": {
                wf: (
                    "ok" if self.get_viz_data(wf) is not None else "failed/empty"
                )
                for wf in self._latest_run_per_workflow
            },
            "runs": len(self._run_records)
        }

    def clear_all_caches(self):
        """Clear execution cache, viz cache and run history."""
        for workflow_name, executor in self._executors.items():
            logger.info(f"🗑️  Clearing execution cache: {workflow_name}")
            executor._execution_cache.clear()

        with self._run_lock:
            self._viz_cache.clear()
            self._run_records.clear()
            self._latest_run_per_workflow.clear()

        logger.info("🗑️  All caches cleared")

    # ------------------------------------------------------------------
    # Viz — Data Processing
    # ------------------------------------------------------------------
    @staticmethod
    def _safe_mean(x) -> Optional[float]:
        """Return mean of x, handling NaN and string-encoded lists."""
        if pd.isna(x):
            return None
        if isinstance(x, str):
            x = ast.literal_eval(x)
        return float(np.mean(x))

    def _process_tracker_result(self, tracker_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Process the productionStatus sheet into two display-ready datasets:
        - daily_data:    latest snapshot across all active POs
        - tracking_data: full production tracking records with parsed maps/lists
        """
        tracker_df["progress"] = round(
            (tracker_df["itemQuantity"] - tracker_df["itemRemain"]) * 100
            / tracker_df["itemQuantity"], 2
        )
        tracker_df["avg_cavity"]         = tracker_df["moldCavity"].apply(self._safe_mean)
        tracker_df["estimatedCapacity"]  = round(
            (tracker_df["totalMoldShot"] / tracker_df["totalDay"]) * tracker_df["avg_cavity"], 2
        )

        # Daily snapshot — latest record only
        daily_df = tracker_df[
            tracker_df["lastestRecordTime"] == tracker_df["lastestRecordTime"].max()
        ].copy()
        daily_df = daily_df[[
            "lastestMachineNo", "poNo", "itemName", "lastestMoldNo", "poETA",
            "progress", "startedDate", "actualFinishedDate", "itemQuantity",
            "estimatedCapacity", "totalDay", "itemRemain"
        ]]

        # Full tracking snapshot
        tracking_cols = [
            "poNo", "poReceivedDate", "itemCode", "itemName", "itemType", "poETA",
            "itemQuantity", "itemRemain", "startedDate", "actualFinishedDate",
            "proStatus", "progress", "etaStatus", "machineHist", "moldList",
            "moldHist", "moldCavity", "totalMoldShot", "totalDay", "totalShift",
            "moldShotMap", "machineQuantityMap", "dayQuantityMap",
            "shiftQuantityMap", "materialComponentMap", "lastestRecordTime",
            "lastestMachineNo", "lastestMoldNo", "warningNotes"
        ]
        tracking_df = tracker_df[tracking_cols].copy()

        # datetime → ISO string
        for col in tracking_df.select_dtypes(include=["datetime64[ns]"]).columns:
            tracking_df[col] = tracking_df[col].dt.strftime("%Y-%m-%d")

        # string-encoded dict → dict
        for col in ["moldShotMap", "machineQuantityMap", "dayQuantityMap",
                    "shiftQuantityMap", "materialComponentMap"]:
            tracking_df[col] = tracking_df[col].apply(
                lambda x: ast.literal_eval(x) if pd.notna(x) else None
            )

        # string-encoded list → list
        for col in ["machineHist", "moldHist", "moldCavity"]:
            if col in tracking_df.columns:
                tracking_df[col] = tracking_df[col].apply(
                    lambda x: ast.literal_eval(x) if isinstance(x, str) and x.startswith("[") else x
                )

        return {
            "daily_data":    daily_df.where(daily_df.notna(), None).to_dict(orient="records"),
            "tracking_data": tracking_df.where(tracking_df.notna(), None).to_dict(orient="records"),
        }

    def _process_viz_data(
        self,
        workflow_name: str,
        viz_data_paths: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Read Excel files from resolved paths and process each sheet
        into a display-ready dict. Only processes modules present in
        sheet_name_params.

        Returns:
            Nested dict: { sub_name: { sheet_name: records } }
        """
        viz_data = {}

        # viz_data_paths = { last_module_name: Path | { sub_name: Path } }
        module_name, module_paths = list(viz_data_paths.items())[0]
        sheet_params = self._sheet_name_params.get(module_name, {})

        if isinstance(module_paths, Path):
            # Single agent — e.g. ProgressTracker
            agent_key   = next(iter(sheet_params))
            sheet_names = sheet_params[agent_key]
            viz_data[agent_key] = {}
            for sheet_name in sheet_names:
                self._read_sheet_into(viz_data[agent_key], module_name, module_paths, sheet_name)

        else:
            # Multi-agent: module_paths = { sub_name: Path }
            for sub_name, newest_path in module_paths.items():
                sheet_names = sheet_params.get(sub_name, [])
                viz_data[sub_name] = {}
                for sheet_name in sheet_names:
                    self._read_sheet_into(viz_data[sub_name], module_name, newest_path, sheet_name)

        return viz_data

    def _read_sheet_into(
        self,
        target: Dict,
        module_name: str,
        path: Path,
        sheet_name: str
    ):
        """
        Read a single Excel sheet, apply module-specific processing if needed,
        and store the result in the target dict keyed by sheet_name.
        """
        df = pd.read_excel(path, sheet_name=sheet_name)

        if module_name == "ProgressTrackingModule" and sheet_name == "productionStatus":
            target[sheet_name] = self._process_tracker_result(df)
        else:
            for col in df.select_dtypes(include=["datetime64[ns]", "datetime64"]).columns:
                df[col] = df[col].astype(str)
            target[sheet_name] = df.where(df.notna(), None).to_dict(orient="records")