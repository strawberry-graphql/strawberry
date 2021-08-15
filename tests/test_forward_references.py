# type: ignore

from __future__ import annotations

import textwrap
from typing import List

import strawberry
from strawberry.printer import print_schema
from strawberry.type import StrawberryList


def test_forward_reference():
    global MyType

    @strawberry.type
    class Query:
        me: MyType = strawberry.field(name="myself")

    @strawberry.type
    class MyType:
        id: strawberry.ID

    expected_representation = """
    type MyType {
      id: ID!
    }

    type Query {
      myself: MyType!
    }
    """

    schema = strawberry.Schema(Query)

    assert print_schema(schema) == textwrap.dedent(expected_representation).strip()

    del MyType


def test_with_resolver():
    global User

    @strawberry.type
    class User:
        name: str

    def get_users() -> List[User]:
        return []

    @strawberry.type
    class Query:
        users: List[User] = strawberry.field(resolver=get_users)

    definition = Query._type_definition
    assert definition.name == "Query"

    [field] = definition.fields

    assert field.python_name == "users"
    assert isinstance(field.type, StrawberryList)
    assert field.type.of_type is User

    del User
