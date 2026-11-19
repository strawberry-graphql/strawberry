from typing import Any
from unittest.mock import MagicMock

import pytest
from opentelemetry.sdk.trace import TracerProvider as SdkTracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.trace import SpanKind, StatusCode
from pytest_mock import MockerFixture

import strawberry
from strawberry.exceptions import StrawberryGraphQLError
from strawberry.extensions.tracing.opentelemetry import (
    OpenTelemetryExtension,
    OpenTelemetryExtensionSync,
)
from strawberry.permission import BasePermission


@pytest.fixture
def global_tracer_mock(mocker: MockerFixture) -> MagicMock:
    return mocker.patch("strawberry.extensions.tracing.opentelemetry.trace.get_tracer")


@strawberry.type
class Person:
    name: str = "Duck"


@strawberry.type
class Query:
    @strawberry.field
    async def person(self) -> Person:
        return Person()


@pytest.mark.asyncio
async def test_opentelemetry_uses_global_tracer(global_tracer_mock):
    schema = strawberry.Schema(query=Query, extensions=[OpenTelemetryExtension])

    query = """
        query {
            person {
                name
            }
        }
    """

    await schema.execute(query)

    global_tracer_mock.assert_called_once_with("strawberry", tracer_provider=None)


@pytest.mark.asyncio
async def test_opentelemetry_sync_uses_global_tracer(global_tracer_mock):
    schema = strawberry.Schema(query=Query, extensions=[OpenTelemetryExtensionSync])

    query = """
        query {
            person {
                name
            }
        }
    """

    await schema.execute(query)

    global_tracer_mock.assert_called_once_with("strawberry", tracer_provider=None)


def _instrumentation_stages(mocker, query):
    return [
        mocker.call("GraphQL Query", kind=SpanKind.SERVER),
        mocker.call().set_attribute("component", "graphql"),
        mocker.call().set_attribute("query", query),
        mocker.call("GraphQL Parsing", context=mocker.ANY),
        mocker.call().end(),
        mocker.call("GraphQL Validation", context=mocker.ANY),
        mocker.call().end(),
        mocker.call().end(),
    ]


@pytest.mark.asyncio
async def test_open_tracing(global_tracer_mock, mocker):
    schema = strawberry.Schema(query=Query, extensions=[OpenTelemetryExtension])
    query = """
        query {
            person {
                name
            }
        }
    """

    await schema.execute(query)

    # start_span is called by the Extension framework to instrument
    # phases of pre-request handling logic; parsing, validation, etc
    global_tracer_mock.return_value.start_span.assert_has_calls(
        _instrumentation_stages(mocker, query)
    )

    # start_as_current_span is called at the very start of request handling
    # it is a context manager, all other spans are a child of this
    global_tracer_mock.return_value.start_as_current_span.assert_has_calls(
        [
            mocker.call(
                "GraphQL Resolving: person",
                context=mocker.ANY,
                record_exception=False,
                set_status_on_exception=False,
            ),
            mocker.call().__enter__(),
            mocker.call().__enter__().set_attribute("component", "graphql"),
            mocker.call().__enter__().set_attribute("graphql.parentType", "Query"),
            mocker.call().__enter__().set_attribute("graphql.path", "person"),
            mocker.call().__exit__(None, None, None),
        ]
    )


@pytest.mark.asyncio
async def test_open_tracing_uses_operation_name(global_tracer_mock, mocker):
    schema = strawberry.Schema(query=Query, extensions=[OpenTelemetryExtension])
    query = """
        query Example {
            person {
                name
            }
        }
    """

    await schema.execute(query, operation_name="Example")

    global_tracer_mock.return_value.start_span.assert_has_calls(
        [
            # if operation_name is supplied it is added to this span's tag
            mocker.call("GraphQL Query: Example", kind=SpanKind.SERVER),
            *_instrumentation_stages(mocker, query)[1:],
        ]
    )


@pytest.mark.asyncio
async def test_open_tracing_gets_operation_name(global_tracer_mock, mocker):
    schema = strawberry.Schema(query=Query, extensions=[OpenTelemetryExtension])
    query = """
        query Example {
            person {
                name
            }
        }
    """

    tracers = []

    def generate_trace(*args: str, **kwargs: Any):
        nonlocal tracers
        tracer = mocker.Mock()
        tracers.append(tracer)
        return tracer

    global_tracer_mock.return_value.start_span.side_effect = generate_trace

    await schema.execute(query)

    tracers[0].update_name.assert_has_calls(
        [
            # if operation_name is supplied it is added to this span's tag
            mocker.call("GraphQL Query: Example"),
        ]
    )


@pytest.mark.asyncio
async def test_tracing_add_kwargs(global_tracer_mock, mocker):
    @strawberry.type
    class Query:
        @strawberry.field
        def hi(self, name: str) -> str:
            return f"Hi {name}"

    schema = strawberry.Schema(query=Query, extensions=[OpenTelemetryExtension])

    query = """
        query {
            hi(name: "Patrick")
        }
    """

    await schema.execute(query)

    global_tracer_mock.return_value.start_as_current_span.assert_has_calls(
        [
            mocker.call().__enter__().set_attribute("graphql.parentType", "Query"),
            mocker.call().__enter__().set_attribute("graphql.path", "hi"),
            mocker.call().__enter__().set_attribute("graphql.param.name", "Patrick"),
        ]
    )


@pytest.mark.asyncio
async def test_tracing_filter_kwargs(global_tracer_mock, mocker):
    def arg_filter(kwargs, info):
        return {"name": "[...]"}

    @strawberry.type
    class Query:
        @strawberry.field
        def hi(self, name: str) -> str:
            return f"Hi {name}"

    schema = strawberry.Schema(
        query=Query,
        extensions=[lambda: OpenTelemetryExtension(arg_filter=arg_filter)],
    )

    query = """
        query {
            hi(name: "Patrick")
        }
    """

    await schema.execute(query)

    global_tracer_mock.return_value.start_as_current_span.assert_has_calls(
        [
            mocker.call().__enter__().set_attribute("graphql.parentType", "Query"),
            mocker.call().__enter__().set_attribute("graphql.path", "hi"),
            mocker.call().__enter__().set_attribute("graphql.param.name", "[...]"),
        ]
    )


class DenyAll(BasePermission):
    message = "Not allowed"

    def has_permission(self, source: Any, info: strawberry.Info, **kwargs: Any) -> bool:
        return False


@strawberry.type
class ErrorQuery:
    @strawberry.field(permission_classes=[DenyAll])
    async def secret(self) -> str:
        return "secret"

    @strawberry.field
    async def broken(self) -> str:
        raise ValueError("boom")


@strawberry.type
class SyncErrorQuery:
    @strawberry.field(permission_classes=[DenyAll])
    def secret(self) -> str:
        return "secret"

    @strawberry.field
    def broken(self) -> str:
        raise ValueError("boom")


def skip_permission_errors(error: Exception) -> bool:
    return not isinstance(error, StrawberryGraphQLError)


def make_exporter() -> tuple[SdkTracerProvider, InMemorySpanExporter]:
    exporter = InMemorySpanExporter()
    provider = SdkTracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    return provider, exporter


def resolver_span(exporter: InMemorySpanExporter, field: str):
    return next(
        span
        for span in exporter.get_finished_spans()
        if span.name == f"GraphQL Resolving: {field}"
    )


@pytest.mark.parametrize(
    ("field", "record_exception_filter", "expected_status", "expected_events"),
    [
        ("secret", None, StatusCode.ERROR, ["exception"]),
        ("secret", skip_permission_errors, StatusCode.UNSET, []),
        ("broken", skip_permission_errors, StatusCode.ERROR, ["exception"]),
    ],
)
@pytest.mark.asyncio
async def test_record_exception_filter(
    field, record_exception_filter, expected_status, expected_events
):
    provider, exporter = make_exporter()
    schema = strawberry.Schema(
        query=ErrorQuery,
        extensions=[
            lambda: OpenTelemetryExtension(
                tracer_provider=provider,
                record_exception_filter=record_exception_filter,
            )
        ],
    )

    result = await schema.execute(f"{{ {field} }}")

    assert result.errors
    span = resolver_span(exporter, field)
    assert span.status.status_code == expected_status
    assert [event.name for event in span.events] == expected_events


@pytest.mark.parametrize(
    ("field", "record_exception_filter", "expected_status", "expected_events"),
    [
        ("secret", None, StatusCode.ERROR, ["exception"]),
        ("secret", skip_permission_errors, StatusCode.UNSET, []),
        ("broken", skip_permission_errors, StatusCode.ERROR, ["exception"]),
    ],
)
def test_record_exception_filter_sync(
    field, record_exception_filter, expected_status, expected_events
):
    provider, exporter = make_exporter()
    schema = strawberry.Schema(
        query=SyncErrorQuery,
        extensions=[
            lambda: OpenTelemetryExtensionSync(
                tracer_provider=provider,
                record_exception_filter=record_exception_filter,
            )
        ],
    )

    result = schema.execute_sync(f"{{ {field} }}")

    assert result.errors
    span = resolver_span(exporter, field)
    assert span.status.status_code == expected_status
    assert [event.name for event in span.events] == expected_events
