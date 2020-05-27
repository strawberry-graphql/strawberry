import pytest

import strawberry
from freezegun import freeze_time
from graphql import DirectiveLocation
from strawberry.extensions.tracing import ApolloTracingExtension
from strawberry.graphql import execute, execute_sync


@pytest.mark.asyncio
async def test_handles_async_resolvers():
    @strawberry.type
    class Query:
        @strawberry.field
        async def async_field(self, info) -> str:
            return "async result"

    schema = strawberry.Schema(Query)

    result = await execute(schema, "{ asyncField }")

    assert not result.errors
    assert result.data["asyncField"] == "async result"


@pytest.mark.asyncio
async def test_runs_directives():
    @strawberry.type
    class Person:
        name: str = "Jess"

    @strawberry.type
    class Query:
        @strawberry.field
        def person(self, info) -> Person:
            return Person()

    @strawberry.directive(
        locations=[DirectiveLocation.FIELD], description="Make string uppercase"
    )
    def uppercase(value: str):
        return value.upper()

    @strawberry.directive(locations=[DirectiveLocation.FIELD])
    def replace(value: str, old: str, new: str):
        return value.replace(old, new)

    schema = strawberry.Schema(query=Query, directives=[uppercase, replace])

    query = """query People($identified: Boolean!){
        person {
            name @uppercase
        }
        jess: person {
            name @replace(old: "Jess", new: "Jessica")
        }
        johnDoe: person {
            name @replace(old: "Jess", new: "John") @include(if: $identified)
        }
    }"""

    result = await execute(schema, query, variable_values={"identified": False})

    assert not result.errors
    assert result.data["person"]["name"] == "JESS"
    assert result.data["jess"]["name"] == "Jessica"
    assert result.data["johnDoe"].get("name") is None


@freeze_time("2012-01-14 12:00:01")
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

    result = execute_sync(schema, query)

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
@freeze_time("2012-01-14 12:00:01")
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

    result = await execute(schema, query)

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
