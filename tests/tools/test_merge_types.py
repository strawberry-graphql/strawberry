from operator import attrgetter
from textwrap import dedent

import pytest

import strawberry
from strawberry.tools import merge_types


@strawberry.type
class Person:
    @strawberry.field
    def name(self) -> str:
        return "Eve"

    @strawberry.field
    def age(self) -> int:
        return 42

    @strawberry.field
    def hi(self) -> str:
        return "Hi"


@strawberry.type
class Greeter:
    @strawberry.field
    def hi(self, name: str = "world") -> str:
        return f"Hello, {name}!"

    @strawberry.field
    def bye(self, name: str = "world") -> str:
        return f"Bye, {name}!"


def test_inheritance():
    """It should merge multiple types following the regular inheritance rules"""

    ComboQuery = merge_types((Greeter, Person))

    definition = ComboQuery._type_definition
    assert len(definition.fields) == 4

    actuals = [attrgetter("python_name", "type")(f) for f in definition.fields]
    expected = [("hi", str), ("bye", str), ("name", str), ("age", int)]
    assert actuals == expected


def test_empty_list():
    """It should raise when the `types` argument is empty"""

    with pytest.raises(ValueError):
        merge_types(())


def test_schema():
    """It should create a valid, usable schema based on a merged query"""

    ComboQuery = merge_types((Greeter, Person))
    schema = strawberry.Schema(query=ComboQuery)

    sdl = """
    schema {
      query: MegaType
    }

    type MegaType {
      hi(name: String! = "world"): String!
      bye(name: String! = "world"): String!
      name: String!
      age: Int!
    }
    """
    assert dedent(sdl).strip() == str(schema)

    result = schema.execute_sync("query { hi }")
    assert not result.errors
    assert result.data == {"hi": "Hello, world!"}
