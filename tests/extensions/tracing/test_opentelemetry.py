from unittest.mock import Mock

import pytest
from opentelemetry.trace import TracerProvider

from strawberry.extensions.tracing.opentelemetry import (
    OpenTelemetryExtension,
    OpenTelemetryExtensionSync,
    _opentelemetry_state_var,
)


def test_no_per_request_state_on_instance():
    """Per-request span state lives in a context variable, not on the
    instance — so a freshly-built extension has none of it, and concurrent
    requests sharing one instance don't see each other's spans."""
    extension = OpenTelemetryExtension()
    assert not hasattr(extension, "_span_holder")
    assert _opentelemetry_state_var.get() is None


def test_no_per_request_state_on_instance_sync():
    extension = OpenTelemetryExtensionSync()
    assert not hasattr(extension, "_span_holder")
    assert _opentelemetry_state_var.get() is None


def test_tracer_provider_is_used():
    tracer_provider = Mock(spec=TracerProvider)
    OpenTelemetryExtension(tracer_provider=tracer_provider)
    assert tracer_provider.get_tracer.called


def test_on_validate_outside_operation_raises():
    """``_get_state`` must raise when ``on_validate`` is invoked without
    a preceding ``on_operation`` initialising the state ContextVar."""
    extension = OpenTelemetryExtension()
    gen = extension.on_validate()
    with pytest.raises(RuntimeError, match="on_operation"):
        next(gen)


def test_on_parse_outside_operation_raises():
    """Same contract for ``on_parse``."""
    extension = OpenTelemetryExtension()
    gen = extension.on_parse()
    with pytest.raises(RuntimeError, match="on_operation"):
        next(gen)
