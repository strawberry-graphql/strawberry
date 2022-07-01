import importlib
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from .apollo import ApolloTracingExtension, ApolloTracingExtensionSync  # noqa
    from .opentelemetry import (  # noqa
        OpenTelemetryExtension,
        OpenTelemetryExtensionSync,
    )

__all__ = [
    "ApolloTracingExtension",
    "ApolloTracingExtensionSync",
    "OpenTelemetryExtension",
    "OpenTelemetryExtensionSync",
]


def __getattr__(name: str):
    if name in {"ApolloTracingExtension", "ApolloTracingExtensionSync"}:
        return getattr(importlib.import_module(".apollo", __name__), name)

    if name in {"OpenTelemetryExtension", "OpenTelemetryExtensionSync"}:
        return getattr(importlib.import_module(".opentelemetry", __name__), name)

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
