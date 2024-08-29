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


@strawberry.type
class SimpleGreeter:
    @strawberry.field
    def hi(self) -> str:
        return "Hi"


@strawberry.type
class ComplexGreeter:
    @strawberry.field
    def hi(self, name: str = "world") -> str:
        return f"Hello, {name}!"

    @strawberry.field
    def bye(self, name: str = "world") -> str:
        return f"Bye, {name}!"


def test_custom_name():
    """The resulting type should have a custom name is one is specified"""
    custom_name = "SuperQuery"
    ComboQuery = merge_types(custom_name, (ComplexGreeter, Person))
    assert ComboQuery.__name__ == custom_name


def test_inheritance():
    """It should merge multiple types following the regular inheritance rules"""
    ComboQuery = merge_types("SuperType", (ComplexGreeter, Person))

    definition = ComboQuery.__strawberry_definition__
    assert len(definition.fields) == 4

    actuals = [(field.python_name, field.type) for field in definition.fields]
    expected = [("hi", str), ("bye", str), ("name", str), ("age", int)]
    assert actuals == expected


def test_empty_list():
    """It should raise when the `types` argument is empty"""
    with pytest.raises(ValueError):
        merge_types("EmptyType", ())


def test_schema():
    """It should create a valid, usable schema based on a merged query"""
    ComboQuery = merge_types("SuperSchema", (ComplexGreeter, Person))
    schema = strawberry.Schema(query=ComboQuery)

    sdl = """
        schema {
          query: SuperSchema
        }

        type SuperSchema {
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


def test_fields_override():
    """It should warn when merging results in overriding fields"""
    with pytest.warns(Warning):
        merge_types("FieldsOverride", (ComplexGreeter, SimpleGreeter))
