import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .apollo import ApolloTracingExtension, ApolloTracingExtensionSync
    from .datadog import DatadogTracingExtension, DatadogTracingExtensionSync
    from .opentelemetry import (
        OpenTelemetryExtension,
        OpenTelemetryExtensionSync,
    )

__all__ = [
    "ApolloTracingExtension",
    "ApolloTracingExtensionSync",
    "DatadogTracingExtension",
    "DatadogTracingExtensionSync",
    "OpenTelemetryExtension",
    "OpenTelemetryExtensionSync",
]


def __getattr__(name: str) -> Any:
    if name in {"DatadogTracingExtension", "DatadogTracingExtensionSync"}:
        return getattr(importlib.import_module(".datadog", __name__), name)

    if name in {"ApolloTracingExtension", "ApolloTracingExtensionSync"}:
        return getattr(importlib.import_module(".apollo", __name__), name)

    if name in {"OpenTelemetryExtension", "OpenTelemetryExtensionSync"}:
        return getattr(importlib.import_module(".opentelemetry", __name__), name)

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
