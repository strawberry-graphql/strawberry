from typing import List

import pytest

import strawberry
from strawberry.exceptions import InvalidDefaultFactoryError
from strawberry.field import StrawberryField
from strawberry.types.types import TypeDefinition


def test_type_add_type_definition_with_fields():
    @strawberry.type
    class Query:
        name: str
        age: int

    definition: TypeDefinition = Query.__strawberry_definition__

    assert definition.name == "Query"
    assert len(definition.fields) == 2

    assert definition.fields[0].python_name == "name"
    assert definition.fields[0].graphql_name is None
    assert definition.fields[0].type_annotation.resolve() == str

    assert definition.fields[1].python_name == "age"
    assert definition.fields[1].graphql_name is None
    assert definition.fields[1].type_annotation.resolve() == int


def test_passing_custom_names_to_fields():
    @strawberry.type
    class Query:
        x: str = strawberry.field(name="name")
        y: int = strawberry.field(name="age")

    definition: TypeDefinition = Query.__strawberry_definition__

    assert definition.name == "Query"
    assert len(definition.fields) == 2

    assert definition.fields[0].python_name == "x"
    assert definition.fields[0].graphql_name == "name"
    assert definition.fields[0].type_annotation.resolve() == str

    assert definition.fields[1].python_name == "y"
    assert definition.fields[1].graphql_name == "age"
    assert definition.fields[1].type_annotation.resolve() == int


def test_passing_nothing_to_fields():
    @strawberry.type
    class Query:
        name: str = strawberry.field()
        age: int = strawberry.field()

    definition: TypeDefinition = Query.__strawberry_definition__

    assert definition.name == "Query"
    assert len(definition.fields) == 2

    assert definition.fields[0].python_name == "name"
    assert definition.fields[0].graphql_name is None
    assert definition.fields[0].type_annotation.resolve() == str

    assert definition.fields[1].python_name == "age"
    assert definition.fields[1].graphql_name is None
    assert definition.fields[1].type_annotation.resolve() == int


def test_can_use_types_directly():
    @strawberry.type
    class User:
        username: str

        @strawberry.field
        def email(self) -> str:
            return self.username + "@somesite.com"

    user = User(username="abc")
    assert user.username == "abc"
    assert user.email() == "abc@somesite.com"


def test_graphql_name_unchanged():
    @strawberry.type
    class Query:
        the_field: int = strawberry.field(name="some_name")

    definition = Query.__strawberry_definition__

    assert definition.fields[0].python_name == "the_field"
    assert definition.fields[0].graphql_name == "some_name"


def test_field_with_default():
    @strawberry.type
    class Query:
        the_field: int = strawberry.field(default=3)

    instance = Query()
    assert instance.the_field == 3


def test_field_with_default_factory():
    @strawberry.type
    class Query:
        the_int: int = strawberry.field(default_factory=lambda: 3)
        the_list: List[str] = strawberry.field(default_factory=list)

    instance = Query()
    assert instance.the_int == 3
    assert instance.the_list == []
    fields: List[StrawberryField] = Query.__strawberry_definition__.fields
    assert [field.default_value for field in fields] == [3, []]

    with pytest.raises(InvalidDefaultFactoryError):

        @strawberry.type
        class ShouldRaiseHere:
            round_takes_arguments: int = strawberry.field(default_factory=round)
