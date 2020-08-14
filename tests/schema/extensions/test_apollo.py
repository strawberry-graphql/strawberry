import pytest

import strawberry
from freezegun import freeze_time
from strawberry.extensions.tracing.apollo import ApolloTracingExtension


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
        def person(self, info) -> Person:
            return Person()

    schema = strawberry.Schema(query=Query, extensions=[ApolloTracingExtension()])

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
                    {
                        "path": ["person", "name"],
                        "field_name": "name",
                        "parentType": "Person",
                        "returnType": "String!",
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
        def person(self, info) -> Person:
            return Person()

    schema = strawberry.Schema(query=Query, extensions=[ApolloTracingExtension()])

    query = """
        query {
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
                        "path": ["person"],
                        "field_name": "person",
                        "parentType": "Query",
                        "returnType": "Person!",
                        "startOffset": 0,
                        "duration": 0,
                    },
                    {
                        "path": ["person", "name"],
                        "field_name": "name",
                        "parentType": "Person",
                        "returnType": "String!",
                        "startOffset": 0,
                        "duration": 0,
                    },
                ]
            },
            "validation": {"startOffset": 0, "duration": 0},
            "parsing": {"startOffset": 0, "duration": 0},
        }
    }
