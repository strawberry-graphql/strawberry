import warnings
from typing import Any

from .fields import NodeExtension, node
from .types import (
    GlobalID,
    GlobalIDValueError,
    Node,
    NodeID,
)

_DEPRECATED_IMPORTS = {
    "Connection": ("strawberry.pagination", "strawberry.pagination.types"),
    "ConnectionExtension": ("strawberry.pagination", "strawberry.pagination.fields"),
    "Edge": ("strawberry.pagination", "strawberry.pagination.types"),
    "ListConnection": ("strawberry.pagination", "strawberry.pagination.types"),
    "NodeType": ("strawberry.pagination", "strawberry.pagination.types"),
    "PageInfo": ("strawberry.pagination", "strawberry.pagination.types"),
    "connection": ("strawberry.pagination", "strawberry.pagination.fields"),
    "from_base64": ("strawberry.pagination", "strawberry.pagination.utils"),
    "to_base64": ("strawberry.pagination", "strawberry.pagination.utils"),
}


def __getattr__(name: str) -> Any:
    if name in _DEPRECATED_IMPORTS:
        package, module_path = _DEPRECATED_IMPORTS[name]
        warnings.warn(
            f"{name} should be imported from {package}",
            DeprecationWarning,
            stacklevel=2,
        )
        import importlib

        module = importlib.import_module(module_path)
        value = getattr(module, name)
        # Cache in module namespace to avoid repeated __getattr__ calls
        globals()[name] = value
        return value

    raise AttributeError(f"module {__name__} has no attribute {name}")


__all__ = [
    "GlobalID",
    "GlobalIDValueError",
    "Node",
    "NodeExtension",
    "NodeID",
    "node",
]
