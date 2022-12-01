import pytest
from freezegun import freeze_time
from graphql.utilities import get_introspection_query

import strawberry
from strawberry.extensions.tracing.apollo import (
    ApolloTracingExtension,
    ApolloTracingExtensionSync,
)


@freeze_time("20120114 12:00:01")
def test_tracing_sync(mocker):
    mocker.patch(
        "strawberry.extensions.tracing.apollo.time.perf_counter_ns", return_value=0
    )

    @strawberry.type
    class Person:
        name: str = "Jess"

    @strawberry.type
    class Query:
        @strawberry.field
        def person(self) -> Person:
            return Person()

    schema = strawberry.Schema(query=Query, extensions=[ApolloTracingExtensionSync])

    query = """
        query {
            person {
                name
            }
        }
    """

    result = schema.execute_sync(query)

    assert not result.errors

    assert result.extensions == {
        "tracing": {
            "version": 1,
            "startTime": "2012-01-14T12:00:01.000000Z",
            "endTime": "2012-01-14T12:00:01.000000Z",
            "duration": 0,
            "execution": {
                "resolvers": [
                    {
                        "path": ["person"],
                        "field_name": "person",
                        "parentType": "Query",
                        "returnType": "Person!",
                        "startOffset": 0,
                        "duration": 0,
                    },
                ]
            },
            "validation": {"startOffset": 0, "duration": 0},
            "parsing": {"startOffset": 0, "duration": 0},
        }
    }


@pytest.mark.asyncio
@freeze_time("20120114 12:00:01")
async def test_tracing_async(mocker):
    mocker.patch(
        "strawberry.extensions.tracing.apollo.time.perf_counter_ns", return_value=0
    )

    @strawberry.type
    class Person:
        name: str = "Jess"

    @strawberry.type
    class Query:
        @strawberry.field
        def example(self) -> str:
            return "Hi"

        @strawberry.field
        async def person(self) -> Person:
            return Person()

    schema = strawberry.Schema(query=Query, extensions=[ApolloTracingExtension])

    query = """
        query {
            example
            person {
                name
            }
        }
    """

    result = await schema.execute(query)

    assert not result.errors

    assert result.extensions == {
        "tracing": {
            "version": 1,
            "startTime": "2012-01-14T12:00:01.000000Z",
            "endTime": "2012-01-14T12:00:01.000000Z",
            "duration": 0,
            "execution": {
                "resolvers": [
                    {
                        "duration": 0,
                        "field_name": "example",
                        "parentType": "Query",
                        "path": ["example"],
                        "returnType": "String!",
                        "startOffset": 0,
                    },
                    {
                        "path": ["person"],
                        "field_name": "person",
                        "parentType": "Query",
                        "returnType": "Person!",
                        "startOffset": 0,
                        "duration": 0,
                    },
                ]
            },
            "validation": {"startOffset": 0, "duration": 0},
            "parsing": {"startOffset": 0, "duration": 0},
        }
    }


@freeze_time("20120114 12:00:01")
def test_should_not_trace_introspection_sync_queries(mocker):
    mocker.patch(
        "strawberry.extensions.tracing.apollo.time.perf_counter_ns", return_value=0
    )

    @strawberry.type
    class Person:
        name: str = "Jess"

    @strawberry.type
    class Query:
        @strawberry.field
        def person(self) -> Person:
            return Person()

    schema = strawberry.Schema(query=Query, extensions=[ApolloTracingExtensionSync])

    result = schema.execute_sync(get_introspection_query())

    assert not result.errors
    assert result.extensions == {
        "tracing": {
            "version": 1,
            "startTime": "2012-01-14T12:00:01.000000Z",
            "endTime": "2012-01-14T12:00:01.000000Z",
            "duration": 0,
            "execution": {"resolvers": []},
            "validation": {"startOffset": 0, "duration": 0},
            "parsing": {"startOffset": 0, "duration": 0},
        }
    }


@pytest.mark.asyncio
@freeze_time("20120114 12:00:01")
async def test_should_not_trace_introspection_async_queries(mocker):
    mocker.patch(
        "strawberry.extensions.tracing.apollo.time.perf_counter_ns", return_value=0
    )

    @strawberry.type
    class Person:
        name: str = "Jess"

    @strawberry.type
    class Query:
        @strawberry.field
        async def person(self) -> Person:
            return Person()

    schema = strawberry.Schema(query=Query, extensions=[ApolloTracingExtension])

    result = await schema.execute(get_introspection_query())

    assert not result.errors
    assert result.extensions == {
        "tracing": {
            "version": 1,
            "startTime": "2012-01-14T12:00:01.000000Z",
            "endTime": "2012-01-14T12:00:01.000000Z",
            "duration": 0,
            "execution": {"resolvers": []},
            "validation": {"startOffset": 0, "duration": 0},
            "parsing": {"startOffset": 0, "duration": 0},
        }
    }
