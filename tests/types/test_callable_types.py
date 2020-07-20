# type: ignore

import importlib
from typing import TYPE_CHECKING, List, Optional

import strawberry


def test_basic_types():
    @strawberry.type
    class Query:
        name: None = strawberry.field(type=lambda: str)
        age: None = strawberry.field(type=lambda: int)

    definition = Query._type_definition

    assert definition.name == "Query"
    assert len(definition.fields) == 2

    assert definition.fields[0].name == "name"
    assert definition.fields[0].type == str

    assert definition.fields[1].name == "age"
    assert definition.fields[1].type == int


def test_optional():
    @strawberry.type
    class Query:
        name: None = strawberry.field(type=lambda: Optional[str])
        age: None = strawberry.field(type=lambda: Optional[int])

    definition = Query._type_definition

    assert definition.name == "Query"
    assert len(definition.fields) == 2

    assert definition.fields[0].name == "name"
    assert definition.fields[0].type == str
    assert definition.fields[0].is_optional

    assert definition.fields[1].name == "age"
    assert definition.fields[1].type == int
    assert definition.fields[1].is_optional


def test_basic_list():
    @strawberry.type
    class Query:
        names: None = strawberry.field(type=lambda: List[str])

    definition = Query._type_definition

    assert definition.name == "Query"
    assert len(definition.fields) == 1

    assert definition.fields[0].name == "names"
    assert definition.fields[0].is_list
    assert definition.fields[0].type is None
    assert definition.fields[0].is_optional is False
    assert definition.fields[0].child.type == str
    assert definition.fields[0].child.is_optional is False


def test_list_of_types():
    @strawberry.type
    class User:
        name: str

    @strawberry.type
    class Query:
        users: None = strawberry.field(type=lambda: List[User])

    definition = Query._type_definition

    assert definition.name == "Query"
    assert len(definition.fields) == 1

    assert definition.fields[0].name == "users"
    assert definition.fields[0].is_list
    assert definition.fields[0].type is None
    assert definition.fields[0].is_optional is False
    assert definition.fields[0].child.type == User
    assert definition.fields[0].child.is_optional is False


def test_can_import_types_in_lambda():
    if TYPE_CHECKING:
        from .example import Example

    @strawberry.type
    class User:
        name: str

    @strawberry.type
    class Query:
        example: "Optional[Example]" = strawberry.field(
            type=lambda: Optional[
                importlib.import_module("tests.types.example").Example  # noqa
            ]
        )

    definition = Query._type_definition

    assert definition.name == "Query"
    assert len(definition.fields) == 1

    assert definition.fields[0].name == "example"
    assert definition.fields[0].is_optional
    assert definition.fields[0].type._type_definition.name == "Example"


def test_can_import_types_in_lambda_resolvers():
    if TYPE_CHECKING:
        from .example import Example

    @strawberry.type
    class User:
        name: str

    @strawberry.type
    class Query:
        @strawberry.field(
            type=lambda: Optional[
                importlib.import_module("tests.types.example").Example  # noqa
            ]
        )
        def example(self) -> "Optional[Example]":
            return None

    definition = Query._type_definition

    assert definition.name == "Query"
    assert len(definition.fields) == 1

    assert definition.fields[0].name == "example"
    assert definition.fields[0].is_optional
    assert definition.fields[0].type._type_definition.name == "Example"
