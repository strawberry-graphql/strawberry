from unittest.mock import Mock

from opentelemetry.trace import Span

from strawberry.extensions import LifecycleStep
from strawberry.extensions.tracing.opentelemetry import (
    OpenTelemetryExtension,
    OpenTelemetryExtensionSync,
)


def test_span_holder_initialization():
    extension = OpenTelemetryExtension()
    assert extension._span_holder == {}
    extension._span_holder[LifecycleStep.OPERATION] = Mock(spec=Span)
    extension = OpenTelemetryExtension()
    assert extension._span_holder == {}


def test_span_holder_initialization_sync():
    extension = OpenTelemetryExtensionSync()
    assert extension._span_holder == {}
    extension._span_holder[LifecycleStep.OPERATION] = Mock(spec=Span)
    extension = OpenTelemetryExtensionSync()
    assert extension._span_holder == {}
