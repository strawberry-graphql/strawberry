import pytest

import strawberry
from strawberry.extensions.tracing.opentracing import (
    OpenTracingExtension,
    OpenTracingExtensionSync,
)


@pytest.fixture
def global_tracer_mock(mocker):
    return mocker.patch("strawberry.extensions.tracing.opentracing.global_tracer")


@pytest.fixture
def active_span_mock(global_tracer_mock):
    return global_tracer_mock.return_value.start_active_span.return_value


@strawberry.type
class Person:
    name: str = "Jess"


@strawberry.type
class Query:
    @strawberry.field
    async def person(self, info) -> Person:
        return Person()


def test_tracing_sync(global_tracer_mock):
    @strawberry.type
    class Person:
        name: str = "Jess"

    @strawberry.type
    class Query:
        @strawberry.field
        def person(self, info) -> Person:
            return Person()

    schema = strawberry.Schema(query=Query, extensions=[OpenTracingExtensionSync])

    query = """
        query {
            person {
                name
            }
        }
    """

    result = schema.execute_sync(query)

    assert not result.errors


@pytest.mark.asyncio
async def test_tracing_async(global_tracer_mock):
    @strawberry.type
    class Person:
        name: str = "Jess"

    @strawberry.type
    class Query:
        @strawberry.field
        async def person(self, info) -> Person:
            return Person()

    schema = strawberry.Schema(query=Query, extensions=[OpenTracingExtension])

    query = """
        query {
            person {
                name
            }
        }
    """

    result = await schema.execute(query)

    assert not result.errors


@pytest.mark.asyncio
async def test_opentracing_uses_global_tracer(global_tracer_mock):
    @strawberry.type
    class Person:
        name: str = "Jess"

    @strawberry.type
    class Query:
        @strawberry.field
        async def person(self, info) -> Person:
            return Person()

    schema = strawberry.Schema(query=Query, extensions=[OpenTracingExtension])

    query = """
        query {
            person {
                name
            }
        }
    """

    await schema.execute(query)

    global_tracer_mock.assert_called_once()


@pytest.mark.asyncio
async def test_opentracing_Sync_uses_global_tracer(global_tracer_mock):
    @strawberry.type
    class Person:
        name: str = "Jess"

    @strawberry.type
    class Query:
        @strawberry.field
        async def person(self, info) -> Person:
            return Person()

    schema = strawberry.Schema(query=Query, extensions=[OpenTracingExtensionSync])

    query = """
        query {
            person {
                name
            }
        }
    """

    await schema.execute(query)

    global_tracer_mock.assert_called_once()


@pytest.mark.asyncio
async def test_open_tracing(global_tracer_mock, mocker):
    schema = strawberry.Schema(query=Query, extensions=[OpenTracingExtension])
    query = """
        query {
            person {
                name
            }
        }
    """

    await schema.execute(query)

    global_tracer_mock.return_value.start_active_span.assert_has_calls(
        [
            mocker.call("GraphQL Query"),
            mocker.call().span.set_tag("component", "graphql"),
            mocker.call().span.set_tag("query", query),
            mocker.call("person"),
            mocker.call().__enter__(),
            mocker.call().__enter__().span.set_tag("component", "graphql"),
            mocker.call().__enter__().span.set_tag("graphql.parentType", "Query"),
            mocker.call().__enter__().span.set_tag("graphql.path", "person"),
            mocker.call().__exit__(None, None, None),
            mocker.call().close(),
        ]
    )


@pytest.mark.asyncio
async def test_open_tracing_uses_operation_name(global_tracer_mock, mocker):
    schema = strawberry.Schema(query=Query, extensions=[OpenTracingExtension])
    query = """
        query Example {
            person {
                name
            }
        }
    """

    await schema.execute(query, operation_name="Example")

    global_tracer_mock.return_value.start_active_span.assert_has_calls(
        [
            mocker.call("GraphQL Query: Example"),
            mocker.call().span.set_tag("component", "graphql"),
            mocker.call().span.set_tag("query", query),
            mocker.call("person"),
            mocker.call().__enter__(),
            mocker.call().__enter__().span.set_tag("component", "graphql"),
            mocker.call().__enter__().span.set_tag("graphql.parentType", "Query"),
            mocker.call().__enter__().span.set_tag("graphql.path", "person"),
            mocker.call().__exit__(None, None, None),
            mocker.call().close(),
        ]
    )


@pytest.mark.asyncio
async def test_tracing_add_kwargs(active_span_mock, mocker):
    @strawberry.type
    class Query:
        @strawberry.field
        def hi(self, name: str) -> str:
            return f"Hi {name}"

    schema = strawberry.Schema(query=Query, extensions=[OpenTracingExtension])

    query = """
        query {
            hi(name: "Patrick")
        }
    """

    await schema.execute(query)

    span_mock = active_span_mock.__enter__.return_value.span
    span_mock.set_tag.assert_has_calls(
        [
            mocker.call("component", "graphql"),
            mocker.call("graphql.parentType", "Query"),
            mocker.call("graphql.path", "hi"),
            mocker.call("graphql.param.name", "Patrick"),
        ]
    )


@pytest.mark.asyncio
async def test_tracing_filter_kwargs(active_span_mock, mocker):
    def arg_filter(kwargs, info):
        return {"name": "[...]"}

    def extension():
        return OpenTracingExtension(arg_filter=arg_filter)

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

    span_mock = active_span_mock.__enter__.return_value.span
    span_mock.set_tag.assert_has_calls(
        [
            mocker.call("component", "graphql"),
            mocker.call("graphql.parentType", "Query"),
            mocker.call("graphql.path", "hi"),
            mocker.call("graphql.param.name", "[...]"),
        ]
    )
