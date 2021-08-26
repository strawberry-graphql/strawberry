import textwrap
from typing import List

import pytest

import strawberry
from strawberry.directive import DirectiveLocation
from strawberry.extensions import Extension
from strawberry.utils.await_maybe import await_maybe


def test_supports_default_directives():
    @strawberry.type
    class Person:
        name: str = "Jess"
        points: int = 2000

    @strawberry.type
    class Query:
        @strawberry.field
        def person(self) -> Person:
            return Person()

    query = """query ($includePoints: Boolean!){
        person {
            name
            points @include(if: $includePoints)
        }
    }"""

    schema = strawberry.Schema(query=Query)
    result = schema.execute_sync(query, variable_values={"includePoints": False})

    assert not result.errors
    assert result.data["person"] == {"name": "Jess"}

    query = """query ($skipPoints: Boolean!){
        person {
            name
            points @skip(if: $skipPoints)
        }
    }"""

    schema = strawberry.Schema(query=Query)
    result = schema.execute_sync(query, variable_values={"skipPoints": False})

    assert not result.errors
    assert result.data["person"] == {"name": "Jess", "points": 2000}


def test_can_declare_directives():
    @strawberry.type
    class Query:
        cake: str = "made_in_switzerland"

    @strawberry.directive(
        locations=[DirectiveLocation.FIELD], description="Make string uppercase"
    )
    def uppercase(value: str, example: str):
        return value.upper()

    schema = strawberry.Schema(query=Query, directives=[uppercase])

    expected_schema = '''
    """Make string uppercase"""
    directive @uppercase(example: String!) on FIELD

    type Query {
      cake: String!
    }
    '''

    assert schema.as_str() == textwrap.dedent(expected_schema).strip()


def test_runs_directives():
    @strawberry.type
    class Person:
        name: str = "Jess"

    @strawberry.type
    class Query:
        @strawberry.field
        def person(self) -> Person:
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

    result = schema.execute_sync(query, variable_values={"identified": False})

    assert not result.errors
    assert result.data["person"]["name"] == "JESS"
    assert result.data["jess"]["name"] == "Jessica"
    assert result.data["johnDoe"].get("name") is None


@pytest.mark.asyncio
async def test_runs_directives_async():
    @strawberry.type
    class Person:
        name: str = "Jess"

    @strawberry.type
    class Query:
        @strawberry.field
        def person(self) -> Person:
            return Person()

    @strawberry.directive(
        locations=[DirectiveLocation.FIELD], description="Make string uppercase"
    )
    async def uppercase(value: str):
        return value.upper()

    schema = strawberry.Schema(query=Query, directives=[uppercase])

    query = """{
        person {
            name @uppercase
        }
    }"""

    result = await schema.execute(query, variable_values={"identified": False})

    assert not result.errors
    assert result.data
    assert result.data["person"]["name"] == "JESS"


@pytest.mark.xfail
def test_runs_directives_with_list_params():
    @strawberry.type
    class Person:
        name: str = "Jess"

    @strawberry.type
    class Query:
        @strawberry.field
        def person(self) -> Person:
            return Person()

    @strawberry.directive(locations=[DirectiveLocation.FIELD])
    def replace(value: str, old_list: List[str], new: str):
        for old in old_list:
            value = value.replace(old, new)

        return value

    schema = strawberry.Schema(query=Query, directives=[replace])

    query = """query People {
        person {
            name @replace(oldList: ["J", "e", "s", "s"], new: "John")
        }
    }"""

    result = schema.execute_sync(query, variable_values={"identified": False})

    assert not result.errors
    assert result.data["person"]["name"] == "JESS"


def test_runs_directives_with_extensions():
    @strawberry.type
    class Person:
        name: str = "Jess"

    @strawberry.type
    class Query:
        @strawberry.field
        def person(self) -> Person:
            return Person()

    @strawberry.directive(
        locations=[DirectiveLocation.FIELD], description="Make string uppercase"
    )
    def uppercase(value: str):
        return value.upper()

    class ExampleExtension(Extension):
        def resolve(self, _next, root, info, *args, **kwargs):
            return _next(root, info, *args, **kwargs)

    schema = strawberry.Schema(
        query=Query, directives=[uppercase], extensions=[ExampleExtension]
    )

    query = """query {
        person {
            name @uppercase
        }
    }"""

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data
    assert result.data["person"]["name"] == "JESS"


@pytest.mark.asyncio
async def test_runs_directives_with_extensions_async():
    @strawberry.type
    class Person:
        name: str = "Jess"

    @strawberry.type
    class Query:
        @strawberry.field
        async def person(self) -> Person:
            return Person()

    @strawberry.directive(
        locations=[DirectiveLocation.FIELD], description="Make string uppercase"
    )
    def uppercase(value: str):
        return value.upper()

    class ExampleExtension(Extension):
        async def resolve(self, _next, root, info, *args, **kwargs):
            return await await_maybe(_next(root, info, *args, **kwargs))

    schema = strawberry.Schema(
        query=Query, directives=[uppercase], extensions=[ExampleExtension]
    )

    query = """query {
        person {
            name @uppercase
        }
    }"""

    result = await schema.execute(query)

    assert not result.errors
    assert result.data
    assert result.data["person"]["name"] == "JESS"
