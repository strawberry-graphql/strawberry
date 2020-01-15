import pytest

import strawberry
from graphql import DirectiveLocation
from strawberry.graphql import execute


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
