import pytest


def test_can_import(mocker):
    # mocking sys.modules.ddtrace so we don't get an ImportError
    mocker.patch.dict("sys.modules", ddtrace=mocker.MagicMock())

    from strawberry.extensions.tracing import (  # noqa
        ApolloTracingExtension,
        ApolloTracingExtensionSync,
        DatadogTracingExtension,
        DatadogTracingExtensionSync,
        OpenTelemetryExtension,
        OpenTelemetryExtensionSync,
        apollo,
        datadog,
        opentelemetry,
    )
    from strawberry.extensions.tracing.apollo import (  # noqa
        ApolloTracingExtension,
        ApolloTracingExtensionSync,
    )
    from strawberry.extensions.tracing.datadog import (  # noqa
        DatadogTracingExtension,
        DatadogTracingExtensionSync,
    )
    from strawberry.extensions.tracing.opentelemetry import (  # noqa
        OpenTelemetryExtension,
        OpenTelemetryExtensionSync,
    )


def test_fails_if_import_is_not_found():
    with pytest.raises(ImportError):
        from strawberry.extensions.tracing import Blueberry  # noqa
