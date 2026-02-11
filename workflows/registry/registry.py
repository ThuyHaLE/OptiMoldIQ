# workflows/registry/registry.py

from pathlib import Path
from typing import Dict, Optional
import yaml
import modules as modules_package
from loguru import logger


class ModuleRegistry:
    """
    Registry manages:
    - Module availability (AVAILABLE_MODULES)
    - Module configurations (from YAML)
    - Module metadata
    """

    def __init__(self, registry_path: str = "configs/module_registry.yaml"):
        self.registry_path = registry_path
        self.module_registry = self._load_registry()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @property
    def available_modules(self) -> Dict:
        """
        Live view of the module catalogue.

        Reading through the package reference (rather than a cached copy)
        means that unittest.mock.patch('modules.AVAILABLE_MODULES', …) is
        always respected, whether it is applied before or after this object
        is constructed.
        """
        return modules_package.AVAILABLE_MODULES

    def _load_registry(self) -> Dict:
        """Load module registry from YAML"""
        registry_file = Path(self.registry_path)

        if not registry_file.exists():
            logger.warning(f"Registry not found: {self.registry_path}")
            logger.warning("Using empty config. Modules will use defaults.")
            return {}

        with open(registry_file, "r", encoding="utf-8") as f:
            registry = yaml.safe_load(f) or {}

        logger.info(f"✅ Loaded registry: {len(registry)} modules configured")
        return registry

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_module_instance(
        self,
        module_name: str,
        override_config_path: Optional[str] = None,
    ):
        """
        Get a module instance, optionally overriding the config path stored
        in the registry.

        Args:
            module_name: Module class name (e.g., "DataPipelineModule")
            override_config_path: Optional config path to override registry config

        Returns:
            Module instance
        """
        if module_name not in self.available_modules:
            available = ", ".join(self.available_modules.keys())
            raise ValueError(
                f"Module '{module_name}' not found. Available: {available}"
            )

        # Use the live factory so patches to modules.get_module are respected.
        module_class = modules_package.get_module(module_name)

        config_path = (
            override_config_path
            or self.module_registry.get(module_name, {}).get("config_path")
        )
        return module_class(config_path)

    def list_modules(self, enabled_only: bool = False) -> list:
        """List available modules"""
        if not enabled_only:
            return list(self.available_modules.keys())

        return [
            name
            for name, config in self.module_registry.items()
            if config.get("enabled", True)
        ]

    def get_module_info(self, module_name: str) -> dict:
        """Get module metadata from registry"""
        if module_name not in self.available_modules:
            raise ValueError(f"Module '{module_name}' not found")

        return self.module_registry.get(module_name, {})