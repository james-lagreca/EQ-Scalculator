# scaling_models/__init__.py
"""
Package that hosts individual scaling-relation modules.

Any Python file in this folder (except tests) is considered a model.
"""

import importlib, pkgutil, pathlib

__all__ = []

for module_info in pkgutil.iter_modules([pathlib.Path(__file__).parent]):
    name = module_info.name
    if name.startswith("test"):
        continue        # skip test modules
    importlib.import_module(f"{__name__}.{name}")   # register side-effects
    __all__.append(name)
