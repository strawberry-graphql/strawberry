def test_can_import():
    from strawberry.extensions.tracing import (  # noqa
        ApolloTracingExtension,
        ApolloTracingExtensionSync,
        OpenTelemetryExtension,
        OpenTelemetryExtensionSync,
        apollo,
        opentelemetry,
    )
    from strawberry.extensions.tracing.apollo import (  # noqa
        ApolloTracingExtension,
        ApolloTracingExtensionSync,
    )
    from strawberry.extensions.tracing.opentelemetry import (  # noqa
        OpenTelemetryExtension,
        OpenTelemetryExtensionSync,
    )
