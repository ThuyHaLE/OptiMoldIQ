# modules/registry.py

import importlib
from pathlib import Path
import inspect

class ModuleRegistry:

    def __init__(self, module_folder="modules"):
        self.module_folder = Path(module_folder)
        self.modules = {}   # module_name → class

    def load_modules(self):
        """
        Scan folder for modules, load classes that define attribute `module_name`
        """
        for file in self.module_folder.glob("*.py"):
            if file.stem.startswith("_"):
                continue  # skip __init__, private files

            module = importlib.import_module(f"modules.{file.stem}")

            for attr in dir(module):
                obj = getattr(module, attr)

                # Only accept classes (not functions, not instances)
                if inspect.isclass(obj) and hasattr(obj, "module_name"):
                    class_name = obj.module_name  # e.g. "DataPipelineModule"
                    self.modules[class_name] = obj  # store CLASS, NOT INSTANCE

        return self.modules

    def list_modules(self):
        return list(self.modules.keys())

    def has_module(self, name: str) -> bool:
        return name in self.modules

    def get_module(self, name: str):
        """
        Returns the class (not instance)
        """
        if name not in self.modules:
            raise KeyError(f"Module not found: {name}")
        return self.modules[name]
