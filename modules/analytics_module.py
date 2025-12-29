# modules/analytics_orchestrator_module.py

from pathlib import Path
from typing import Dict, List
from modules.base_module import BaseModule, ModuleResult
from loguru import logger

from agents.analyticsOrchestrator.analyticsConfigs.change_analyticflow_config import ChangeAnalyticflowConfig
from agents.analyticsOrchestrator.analyticsConfigs.performance_analyticflow_config import PerformanceAnalyticflowConfig
from agents.analyticsOrchestrator.analytics_orchestrator import AnalyticsOrchestratorConfig, AnalyticsOrchestrator

class AnalyticsModule(BaseModule):
    
    """
    Module wrapper for analyticsOrchestrator.
    
    Handles data analytics pipeline.
    """
    
    DEFAULT_CONFIG_PATH = 'configs/modules/analytics.yaml'

    @property
    def module_name(self) -> str:
        """Unique module name"""
        return "AnalyticsModule"
    
    @property
    def dependencies(self) -> List[str]:
        """No dependencies - this is typically the first module"""
        return []
    
    @property
    def context_outputs(self) -> List[str]:
        """Keys that this module writes to context"""
        return [
            'analytics_orchestrator_result',
            'analytics_orchestrator_log'
        ]
    
    def execute(self, context: Dict) -> ModuleResult:
        
        """Execute AnalyticsOrchestrator with auto-configuration logic
        
        Auto-propagation hierarchy:
        AnalyticsOrchestrator (parent)
          ├─> HardwareChangeAnalyzer
          └─> MultiLevelPerformanceAnalyzer
        
        """
        
        self.logger = logger.bind(class_="AnalyticsModule")

        try: 
            
            self.project_root = Path(self.config.get('project_root', '.'))
            self.analytics_config = self.config.get('analytics', {})

            self.logger.debug("Project root: {}", self.project_root)

            if not self.analytics_config:
                self.logger.debug("Cannot load AnalyticsModule config")
            
            # Extract parent enable flags to pass into nested builders
            parent_enable_flags = {
                'enable_hardware_change_analysis': self.analytics_config.get(
                    'enable_hardware_change_analysis', False
                ),
                'enable_hardware_change_machine_layout_tracker': self.analytics_config.get(
                    'enable_hardware_change_machine_layout_tracker', False
                ),
                'enable_hardware_change_machine_mold_pair_tracker': self.analytics_config.get(
                    'enable_hardware_change_machine_mold_pair_tracker', False
                ),
                'enable_multi_level_analysis': self.analytics_config.get(
                    'enable_multi_level_analysis', False
                ),
                'enable_multi_level_day_level_processor': self.analytics_config.get(
                    'enable_multi_level_day_level_processor', False
                ),
                'enable_multi_level_month_level_processor': self.analytics_config.get(
                    'enable_multi_level_month_level_processor', False
                ),
                'enable_multi_level_year_level_processor': self.analytics_config.get(
                    'enable_multi_level_year_level_processor', False
                ),
            }
            
            # Build nested configs with auto-propagation
            change_config = self._build_change_config(
                parent_enable_flags  # ← Pass parent flags
            )
            performance_config = self._build_performance_config(
                parent_enable_flags  # ← Pass parent flags
            )
            
            # Build orchestrator config
            orchestrator_config = self._build_orchestrator_config(
                change_config,
                performance_config
            )
            
            self.logger.info("AnalyticsOrchestrator configuration built:")
            self.logger.info(f"  - Hardware Change Analysis: {orchestrator_config.enable_hardware_change_analysis}")
            self.logger.info(f"    - Machine Layout Tracker: {change_config.enable_machine_layout_tracker}")
            self.logger.info(f"    - Machine-Mold Pair Tracker: {change_config.enable_machine_mold_pair_tracker}")
            self.logger.info(f"  - Multi-level Performance Analysis: {orchestrator_config.enable_multi_level_analysis}")
            
            # Execute orchestrator
            # NOTE: Agent's __init__ will call _apply_auto_configuration()
            # to apply one more time these auto-config rules
            orchestrator = AnalyticsOrchestrator(orchestrator_config)
            orchestrator_results, orchestrator_log_str = orchestrator.run_analytics()
            
            # Return success result
            return ModuleResult(
                status='success',
                data={
                    'orchestrator_results': orchestrator_results,
                    'orchestrator_log': orchestrator_log_str
                },
                message='AnalyticsOrchestrator completed successfully',
                context_updates={
                    'analytics_orchestrator_result': orchestrator_results,
                    'analytics_orchestrator_log': orchestrator_log_str
                }
            )
            
        except Exception as e:
            self.logger.error(f"AnalyticsOrchestrator failed: {e}", exc_info=True)
            return ModuleResult(
                status='failed', 
                data=None, 
                message=str(e), 
                errors=[str(e)]
            )
        
    def _build_change_config(self, 
                            parent_enable_flags: Dict) -> 'ChangeAnalyticflowConfig':
        """
        Build ChangeAnalyticflowConfig with auto-propagation from parent flags
        
        AUTO CONFIGURATION LOGIC:
        - If enable_hardware_change_analysis = True (parent)
          → auto enable all sub-trackers based on parent sub-flags
        - Nested config values from YAML are defaults
        - Parent flags with highest priority
        """
        change_config = self.analytics_config.get('change_analysis', {})

        if not change_config:
                self.logger.debug("Cannot load ChangeAnalytic config")

        # Get parent enable flags
        hardware_change_enabled = parent_enable_flags.get('enable_hardware_change_analysis', False)
        
        # AUTO-PROPAGATE: Parent enables → override nested enables
        if hardware_change_enabled:
            # If parent enabled, get sub-flags from parent level
            enable_machine_layout = parent_enable_flags.get(
                'enable_hardware_change_machine_layout_tracker',
                change_config.get('enable_machine_layout_tracker', False)
            )
            enable_machine_mold_pair = parent_enable_flags.get(
                'enable_hardware_change_machine_mold_pair_tracker',
                change_config.get('enable_machine_mold_pair_tracker', False)
            )
        else:
            # If parent disabled, force disable all sub-components
            enable_machine_layout = False
            enable_machine_mold_pair = False
        
        self.logger.info(
            f"Change Analysis Auto-Config: "
            f"parent={hardware_change_enabled}, "
            f"layout_tracker={enable_machine_layout}, "
            f"mold_pair_tracker={enable_machine_mold_pair}"
        )
        
        from agents.analyticsOrchestrator.analyticsConfigs.change_analyticflow_config import ChangeAnalyticflowConfig
        
        return ChangeAnalyticflowConfig(
            # AUTO-CONFIGURED enables
            enable_machine_layout_tracker=enable_machine_layout,
            enable_machine_mold_pair_tracker=enable_machine_mold_pair,
            
            # Other configs from YAML
            machine_layout_tracker_dir=str(self.project_root / change_config.get(
                'machine_layout_tracker_dir',
                'agents/shared_db/AnalyticsOrchestrator/HardwareChangeAnalyzer/MachineLayoutTracker' 
            )),
            machine_layout_tracker_change_log_name=change_config.get(
                'machine_layout_tracker_change_log_name',
                'change_log.txt'
            ),
            machine_mold_pair_tracker_dir=str(self.project_root / change_config.get(
                'machine_mold_pair_tracker_dir',
                'agents/shared_db/AnalyticsOrchestrator/HardwareChangeAnalyzer/MachineMoldPairTracker'
            )),
            machine_mold_pair_tracker_change_log_name=change_config.get(
                'machine_mold_pair_tracker_change_log_name',
                'change_log.txt'
            ),
            
            # Shared configs
            source_path=str(self.project_root / change_config.get(
                'source_path',
                self.config.get('data_loader_path', 'agents/shared_db/DataLoaderAgent/newest')
            )),
            annotation_name=change_config.get(
                'annotation_name',
                self.config.get('annotation_name', 'path_annotations.json')
            ),
            databaseSchemas_path=str(self.project_root / change_config.get(
                'databaseSchemas_path',
                self.config.get('database_schemas_path', 'database/databaseSchemas.json')
            )),
            save_hardware_change_analyzer_log=change_config.get(
                'save_hardware_change_analyzer_log',
                True
            ),
            hardware_change_analyzer_dir=str(self.project_root / change_config.get(
                'hardware_change_analyzer_dir',
                'agents/shared_db/AnalyticsOrchestrator/HardwareChangeAnalyzer'
            ))
        )
    
    def _build_performance_config(self,
                                 parent_enable_flags: Dict) -> 'PerformanceAnalyticflowConfig':
        """
        Build PerformanceAnalyticflowConfig với auto-propagation
        
        AUTO CONFIGURATION LOGIC:
        - enable_multi_level_analysis → controls all sub-processors
        """
        performance_config = self.analytics_config.get('performance_analysis', {})
        
        if not performance_config:
                self.logger.debug("Cannot load PerformanceAnalytic config")

        # Get parent enable flag
        multi_level_enabled = parent_enable_flags.get('enable_multi_level_analysis', False)
        
        # Note: Performance processors are typically controlled by data presence
        # (record_date, record_month, record_year not None)
        # But we can still respect parent flag
        
        if not multi_level_enabled:
            # Force disable if parent disabled
            self.logger.info("Multi-level analysis disabled by parent flag")
        
        from agents.analyticsOrchestrator.analyticsConfigs.performance_analyticflow_config import PerformanceAnalyticflowConfig
        
        return PerformanceAnalyticflowConfig(
            # Day Level
            record_date=performance_config.get('record_date') if multi_level_enabled else None,
            day_save_output=performance_config.get('day_save_output', False),
            
            # Month Level
            record_month=performance_config.get('record_month') if multi_level_enabled else None,
            month_analysis_date=performance_config.get('month_analysis_date'),
            month_save_output=performance_config.get('month_save_output', False),
            
            # Year Level
            record_year=performance_config.get('record_year') if multi_level_enabled else None,
            year_analysis_date=performance_config.get('year_analysis_date'),
            year_save_output=performance_config.get('year_save_output', False),
            
            # Shared configs
            source_path=str(self.project_root / performance_config.get(
                'source_path',
                self.config.get('data_loader_path', 'agents/shared_db/DataLoaderAgent/newest')
            )),
            annotation_name=performance_config.get(
                'annotation_name',
                self.config.get('annotation_name', 'path_annotations.json')
            ),
            databaseSchemas_path=str(self.project_root / performance_config.get(
                'databaseSchemas_path',
                self.config.get('database_schemas_path', 'database/databaseSchemas.json')
            )),
            save_multi_level_performance_analyzer_log=performance_config.get(
                'save_multi_level_performance_analyzer_log',
                True
            ),
            multi_level_performance_analyzer_dir=str(self.project_root / performance_config.get(
                'multi_level_performance_analyzer_dir',
                'agents/shared_db/AnalyticsOrchestrator/MultiLevelPerformanceAnalyzer'
            ))
        )
    
    def _build_orchestrator_config(self,
                                  change_config: 'ChangeAnalyticflowConfig',
                                  performance_config: 'PerformanceAnalyticflowConfig') -> 'AnalyticsOrchestratorConfig':
        """Build AnalyticsOrchestratorConfig với parent enable flags"""
        
        from agents.analyticsOrchestrator.analytics_orchestrator import AnalyticsOrchestratorConfig
        
        return AnalyticsOrchestratorConfig(
            # Parent enable flags
            enable_hardware_change_analysis=self.analytics_config.get(
                'enable_hardware_change_analysis',
                False
            ),
            enable_multi_level_analysis=self.analytics_config.get(
                'enable_multi_level_analysis',
                False
            ),
            
            # Sub-component flags
            # NOTE: Agent's _apply_auto_configuration() will auto override
            # these values based on parent flags, but I still pass it here
            # to control from YAML if required
            enable_hardware_change_machine_layout_tracker=self.analytics_config.get(
                'enable_hardware_change_machine_layout_tracker',
                False
            ),
            enable_hardware_change_machine_mold_pair_tracker=self.analytics_config.get(
                'enable_hardware_change_machine_mold_pair_tracker',
                False
            ),
            enable_multi_level_day_level_processor=self.analytics_config.get(
                'enable_multi_level_day_level_processor',
                False
            ),
            enable_multi_level_month_level_processor=self.analytics_config.get(
                'enable_multi_level_month_level_processor',
                False
            ),
            enable_multi_level_year_level_processor=self.analytics_config.get(
                'enable_multi_level_year_level_processor',
                False
            ),
            
            # General configs
            save_analytics_orchestrator_log=self.analytics_config.get(
                'save_analytics_orchestrator_log',
                True
            ),
            analytics_orchestrator_dir=str(self.project_root / self.analytics_config.get(
                'analytics_orchestrator_dir',
                'agents/shared_db/AnalyticsOrchestrator'
            )),
            
            # Nested configs (already built with auto-propagation)
            change_config=change_config,
            performance_config=performance_config
        )