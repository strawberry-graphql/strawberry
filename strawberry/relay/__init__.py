import warnings
from typing import Any

from strawberry.pagination.fields import ConnectionExtension, connection
from strawberry.pagination.types import (
    Connection,
    Edge,
    ListConnection,
    NodeType,
    PageInfo,
)
from strawberry.pagination.utils import from_base64, to_base64

from .fields import NodeExtension, node
from .types import (
    GlobalID,
    GlobalIDValueError,
    Node,
    NodeID,
)

_DEPRECATIONS = {
    "Connection": Connection,
    "ConnectionExtension": ConnectionExtension,
    "Edge": Edge,
    "ListConnection": ListConnection,
    "NodeType": NodeType,
    "PageInfo": PageInfo,
    "connection": connection,
    "from_base64": from_base64,
    "to_base64": to_base64,
}


def __getattr__(name: str) -> Any:
    if name in _DEPRECATIONS:
        warnings.warn(
            f"{name} should be imported from strawberry.pagination",
            DeprecationWarning,
            stacklevel=2,
        )
        return _DEPRECATIONS[name]

    raise AttributeError(f"module {__name__} has no attribute {name}")


__all__ = [
    "GlobalID",
    "GlobalIDValueError",
    "Node",
    "NodeExtension",
    "NodeID",
    "node",
]
