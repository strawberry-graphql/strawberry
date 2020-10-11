import pytest

from opentelemetry.trace import SpanKind

import strawberry
from strawberry.extensions.tracing.opentelemetry import (
    OpenTelemetryExtension,
    OpenTelemetryExtensionSync,
)


@pytest.fixture
def global_tracer_mock(mocker):
    return mocker.patch("strawberry.extensions.tracing.opentelemetry.trace.get_tracer")


@strawberry.type
class Person:
    name: str = "Jess"


@strawberry.type
class Query:
    @strawberry.field
    async def person(self, info) -> Person:
        return Person()


@pytest.mark.asyncio
async def test_opentelemetry_uses_global_tracer(global_tracer_mock):
    @strawberry.type
    class Person:
        name: str = "Jess"

    @strawberry.type
    class Query:
        @strawberry.field
        async def person(self, info) -> Person:
            return Person()

    schema = strawberry.Schema(query=Query, extensions=[OpenTelemetryExtension])

    query = """
        query {
            person {
                name
            }
        }
    """

    await schema.execute(query)

    global_tracer_mock.assert_called_once_with("strawberry")


@pytest.mark.asyncio
async def test_opentelemetry_Sync_uses_global_tracer(global_tracer_mock):
    @strawberry.type
    class Person:
        name: str = "Jess"

    @strawberry.type
    class Query:
        @strawberry.field
        async def person(self, info) -> Person:
            return Person()

    schema = strawberry.Schema(query=Query, extensions=[OpenTelemetryExtensionSync])

    query = """
        query {
            person {
                name
            }
        }
    """

    await schema.execute(query)

    global_tracer_mock.assert_called_once_with("strawberry")


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

    global_tracer_mock.return_value.start_span.assert_has_calls(
        [
            mocker.call("GraphQL Query", kind=SpanKind.SERVER),
            mocker.call().set_attribute("component", "graphql"),
            mocker.call().set_attribute("query", query),
            mocker.call("person", kind=SpanKind.SERVER),
            mocker.call().__enter__(),
            mocker.call().__enter__().set_attribute("component", "graphql"),
            mocker.call().__enter__().set_attribute("graphql.parentType", "Query"),
            mocker.call().__enter__().set_attribute("graphql.path", "person"),
            mocker.call().__exit__(None, None, None),
            mocker.call().end(),
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
            mocker.call("GraphQL Query: Example", kind=SpanKind.SERVER),
            mocker.call().set_attribute("component", "graphql"),
            mocker.call().set_attribute("query", query),
            mocker.call("person", kind=SpanKind.SERVER),
            mocker.call().__enter__(),
            mocker.call().__enter__().set_attribute("component", "graphql"),
            mocker.call().__enter__().set_attribute("graphql.parentType", "Query"),
            mocker.call().__enter__().set_attribute("graphql.path", "person"),
            mocker.call().__exit__(None, None, None),
            mocker.call().end(),
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

    global_tracer_mock.return_value.start_span.assert_has_calls(
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

    def extension():
        return OpenTelemetryExtension(arg_filter=arg_filter)

    @strawberry.type
    class Query:
        @strawberry.field
        def hi(self, name: str) -> str:
            return f"Hi {name}"

    schema = strawberry.Schema(query=Query, extensions=[extension])

    query = """
        query {
            hi(name: "Patrick")
        }
    """

    await schema.execute(query)

    global_tracer_mock.return_value.start_span.assert_has_calls(
        [
            mocker.call().__enter__().set_attribute("graphql.parentType", "Query"),
            mocker.call().__enter__().set_attribute("graphql.path", "hi"),
            mocker.call().__enter__().set_attribute("graphql.param.name", "[...]"),
        ]
    )
