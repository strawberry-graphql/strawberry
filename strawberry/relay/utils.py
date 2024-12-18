import warnings
from typing import Any

from strawberry.pagination.utils import (
    SliceMetadata,
    from_base64,
    should_resolve_list_connection_edges,
    to_base64,
)

_DEPRECATIONS = {
    "SliceMetadata": SliceMetadata,
    "from_base64": from_base64,
    "should_resolve_list_connection_edges": should_resolve_list_connection_edges,
    "to_base64": to_base64,
}


def __getattr__(name: str) -> Any:
    if name in _DEPRECATIONS:
        warnings.warn(
            f"{name} should be imported from strawberry.pagination.utils",
            DeprecationWarning,
            stacklevel=2,
        )
        return _DEPRECATIONS[name]

    raise AttributeError(f"module {__name__} has no attribute {name}")
