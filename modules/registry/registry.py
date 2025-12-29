# modules/registry/registry.py

from modules import AVAILABLE_MODULES

class ModuleRegistry:
    def __init__(self):
        self._modules = AVAILABLE_MODULES

    def get_module(self, name: str):
        if name not in self._modules:
            raise KeyError(
                f"Module '{name}' not found. "
                f"Available: {list(self._modules.keys())}"
            )
        return self._modules[name]

    def list_modules(self):
        return list(self._modules.keys())
