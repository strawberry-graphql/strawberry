# type: ignore
from __future__ import annotations

import textwrap
from typing import List

import strawberry
from strawberry.printer import print_schema


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
    assert len(definition.fields) == 1
    assert definition.fields[0].name == "users"
    assert definition.fields[0].is_list
    assert definition.fields[0].type is None
    assert definition.fields[0].is_optional is False
    assert definition.fields[0].child.is_optional is False

    del User
