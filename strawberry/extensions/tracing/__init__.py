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
    if name in __all__:
        return importlib.import_module(f".{name}", __name__)

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
