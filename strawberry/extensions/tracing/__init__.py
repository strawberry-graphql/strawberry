import importlib
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from . import apollo, opentelemetry
    from .apollo import ApolloTracingExtension, ApolloTracingExtensionSync  # noqa
    from .opentelemetry import (  # noqa
        OpenTelemetryExtension,
        OpenTelemetryExtensionSync,
    )

__all__ = [
    "opentelemetry",
    "apollo",
    "ApolloTracingExtension",
    "ApolloTracingExtensionSync",
    "OpenTelemetryExtension",
    "OpenTelemetryExtensionSync",
]


def __getattr__(name):
    if name in {"apollo", "opentelemetry"}:
        return importlib.import_module(f".{name}", __name__)

    if name in {"ApolloTracingExtension", "ApolloTracingExtensionSync"}:
        return getattr(importlib.import_module(".apollo", __name__), name)

    if name in {"OpenTelemetryExtension", "OpenTelemetryExtensionSync"}:
        return getattr(importlib.import_module(".opentelemetry", __name__), name)

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
