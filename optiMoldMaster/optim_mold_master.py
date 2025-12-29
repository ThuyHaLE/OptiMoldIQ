# agents/optiMoldMaster/optim_mold_master.py 

from pathlib import Path
from typing import Dict, Any, Optional, List
from loguru import logger
from datetime import datetime

from modules.registry.registry import ModuleRegistry
from workflows.executor import WorkflowExecutor

class OptiMoldMaster:
    """
    OptiMold Master Agent - Main orchestrator for manufacturing optimization workflows.
    
    Manages and executes various workflows for data pipeline, planning, dashboards, and sync operations.
    """
    
    def __init__(
        self, 
        modules_folder: str = "modules",
        workflows_dir: str = "workflows/definitions",
        log_dir: str = "logs"
    ):
        """
        Initialize OptiMold Master Agent
        
        Args:
            modules_folder: Path to modules directory
            workflows_dir: Path to workflow definition files
            log_dir: Path to log directory
        """
        self.modules_folder = modules_folder
        self.workflows_dir = Path(workflows_dir)
        self.log_dir = Path(log_dir)
        
        # Setup logging
        self._setup_logging()
        
        # Initialize registry and executor
        logger.info("🚀 Initializing OptiMoldMaster Agent...")
        self.registry = ModuleRegistry(module_folder=modules_folder)
        self.registry.load_modules()
        logger.info(f"✅ Loaded {len(self.registry.list_modules())} modules: {self.registry.list_modules()}")
        
        self.executor = WorkflowExecutor(
            registry=self.registry,
            workflows_dir=workflows_dir
        )
        
        # Workflow execution history
        self.execution_history: List[Dict] = []
        
    def _setup_logging(self):
        """Setup logging configuration"""
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        log_file = self.log_dir / f"optim_mold_master_{datetime.now().strftime('%Y%m%d')}.log"
        
        logger.add(
            log_file,
            rotation="500 MB",
            retention="30 days",
            level="INFO",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
        )
    
    def list_available_workflows(self) -> List[str]:
        """
        List all available workflow files
        
        Returns:
            List of workflow names (without .json extension)
        """
        workflows = []
        for file in self.workflows_dir.glob("*.json"):
            workflows.append(file.stem)
        
        logger.info(f"📋 Available workflows: {workflows}")
        return workflows
    
    def get_workflow_details(self, workflow_name: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific workflow
        
        Args:
            workflow_name: Name of the workflow
            
        Returns:
            Workflow configuration dictionary
        """
        try:
            workflow_info = self.executor.get_workflow_info(workflow_name)
            logger.info(f"📖 Workflow '{workflow_name}' details retrieved")
            return workflow_info
        except Exception as e:
            logger.error(f"❌ Failed to get workflow details: {e}")
            raise
    
    def execute_workflow(self, 
                         workflow_name: str, 
                         config_overrides: Optional[Dict[str, Dict]] = None
                         ) -> Dict[str, Any]:
        """
        Execute a specific workflow
        
        Args:
            workflow_name: Name of the workflow to execute
            config_overrides: Optional configuration overrides per module
                              Format: {"ModuleName": {"param": "value"}}
        
        Returns:
            Workflow execution result dictionary
        """
        logger.info(f"▶️  Starting workflow execution: {workflow_name}")
        start_time = datetime.now()
        
        try:
            result = self.executor.execute(
                workflow_name=workflow_name,
                config_overrides=config_overrides
            )
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # Add execution metadata
            result["execution_time"] = duration
            result["start_time"] = start_time.isoformat()
            result["end_time"] = end_time.isoformat()
            
            # Store in history
            self.execution_history.append({
                "workflow_name": workflow_name,
                "timestamp": start_time.isoformat(),
                "duration": duration,
                "status": result["status"],
                "message": result["message"]
            })
            
            if result["status"] == "success":
                logger.info(f"✅ Workflow '{workflow_name}' completed successfully in {duration:.2f}s")
            else:
                logger.error(f"❌ Workflow '{workflow_name}' failed: {result['message']}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Workflow execution error: {e}")
            return {
                "status": "error",
                "workflow": workflow_name,
                "message": str(e),
                "execution_time": (datetime.now() - start_time).total_seconds()
            }
    
    def execute_multiple_workflows(
        self, 
        workflow_names: List[str],
        stop_on_failure: bool = True
    ) -> Dict[str, Any]:
        """
        Execute multiple workflows sequentially
        
        Args:
            workflow_names: List of workflow names to execute
            stop_on_failure: Stop execution if a workflow fails
            
        Returns:
            Combined execution results
        """
        logger.info(f"🔄 Executing {len(workflow_names)} workflows sequentially")
        
        results = []
        overall_status = "success"
        
        for workflow_name in workflow_names:
            result = self.execute_workflow(workflow_name)
            results.append(result)
            
            if result["status"] != "success":
                overall_status = "failed"
                if stop_on_failure:
                    logger.warning(f"⚠️  Stopping execution due to failure in '{workflow_name}'")
                    break
        
        return {
            "status": overall_status,
            "total_workflows": len(workflow_names),
            "executed_workflows": len(results),
            "results": results
        }
    
    def get_execution_history(self, limit: Optional[int] = None) -> List[Dict]:
        """
        Get workflow execution history
        
        Args:
            limit: Maximum number of records to return (most recent first)
            
        Returns:
            List of execution history records
        """
        history = sorted(
            self.execution_history, 
            key=lambda x: x["timestamp"], 
            reverse=True
        )
        
        if limit:
            history = history[:limit]
        
        return history
    
    def get_execution_summary(self) -> Dict[str, Any]:
        """
        Get summary statistics of workflow executions
        
        Returns:
            Summary statistics dictionary
        """
        if not self.execution_history:
            return {
                "total_executions": 0,
                "successful": 0,
                "failed": 0,
                "average_duration": 0
            }
        
        total = len(self.execution_history)
        successful = sum(1 for h in self.execution_history if h["status"] == "success")
        failed = total - successful
        avg_duration = sum(h["duration"] for h in self.execution_history) / total
        
        return {
            "total_executions": total,
            "successful": successful,
            "failed": failed,
            "success_rate": f"{(successful/total)*100:.1f}%",
            "average_duration": f"{avg_duration:.2f}s"
        }
    
    def run_update_database_workflow(self) -> Dict[str, Any]:
        """
        Convenience method to run the update_database workflow
        """
        return self.execute_workflow("update_database")
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check health status of the agent and its components
        
        Returns:
            Health status dictionary
        """
        logger.info("🏥 Performing health check...")
        
        health = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "modules_loaded": len(self.registry.list_modules()),
            "available_workflows": len(self.list_available_workflows()),
            "execution_history_size": len(self.execution_history)
        }
        
        return health