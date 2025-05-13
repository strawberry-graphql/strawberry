# type: ignore
from __future__ import annotations

import textwrap
from typing import Annotated

import strawberry
from strawberry.printer import print_schema
from strawberry.scalars import JSON
from strawberry.types.base import StrawberryList, StrawberryOptional
from tests.a import A
from tests.d import D


def test_forward_reference():
    global MyType

    @strawberry.type
    class Query:
        me: MyType = strawberry.field(name="myself")

    @strawberry.type
    class MyType:
        id: strawberry.ID
        scalar: JSON
        optional_scalar: JSON | None

    expected_representation = '''
    """
    The `JSON` scalar type represents JSON values as specified by [ECMA-404](https://ecma-international.org/wp-content/uploads/ECMA-404_2nd_edition_december_2017.pdf).
    """
    scalar JSON @specifiedBy(url: "https://ecma-international.org/wp-content/uploads/ECMA-404_2nd_edition_december_2017.pdf")

    type MyType {
      id: ID!
      scalar: JSON!
      optionalScalar: JSON
    }

    type Query {
      myself: MyType!
    }
    '''

    schema = strawberry.Schema(Query)

    assert print_schema(schema) == textwrap.dedent(expected_representation).strip()

    del MyType


def test_lazy_forward_reference():
    @strawberry.type
    class Query:
        @strawberry.field
        async def a(self) -> A:  # pragma: no cover
            return A(id=strawberry.ID("1"))

    expected_representation = """
    type A {
      id: ID!
      b: B!
      optionalB: B
      optionalB2: B
    }

    type B {
      id: ID!
      a: A!
      aList: [A!]!
      optionalA: A
      optionalA2: A
    }

    type Query {
      a: A!
    }
    """

    schema = strawberry.Schema(query=Query)
    assert print_schema(schema) == textwrap.dedent(expected_representation).strip()


def test_lazy_forward_reference_schema_with_a_list_only():
    @strawberry.type
    class Query:
        @strawberry.field
        async def d(self) -> D:  # pragma: no cover
            return D(id=strawberry.ID("1"))

    expected_representation = """
    type C {
      id: ID!
    }

    type D {
      id: ID!
      cList: [C!]!
    }

    type Query {
      d: D!
    }
    """

    schema = strawberry.Schema(query=Query)
    assert print_schema(schema) == textwrap.dedent(expected_representation).strip()


def test_with_resolver():
    global User

    @strawberry.type
    class User:
        name: str

    def get_users() -> list[User]:  # pragma: no cover
        return []

    @strawberry.type
    class Query:
        users: list[User] = strawberry.field(resolver=get_users)

    definition = Query.__strawberry_definition__
    assert definition.name == "Query"

    [field] = definition.fields

    assert field.python_name == "users"
    assert isinstance(field.type, StrawberryList)
    assert field.type.of_type is User

    del User


def test_union_or_notation():
    global User

    @strawberry.type
    class User:
        name: str

    def get_users() -> list[User] | None:  # pragma: no cover
        return []

    @strawberry.type
    class Query:
        users: list[User] | None = strawberry.field(resolver=get_users)

    definition = Query.__strawberry_definition__
    assert definition.name == "Query"

    [field] = definition.fields

    assert field.python_name == "users"
    assert isinstance(field.type, StrawberryOptional)
    assert isinstance(field.type.of_type, StrawberryList)
    assert field.type.of_type.of_type is User

    del User


def test_union_or_notation_generic_type_alias():
    global User

    @strawberry.type
    class User:
        name: str

    def get_users() -> list[User] | None:  # pragma: no cover
        return []

    @strawberry.type
    class Query:
        users: list[User] | None = strawberry.field(resolver=get_users)

    definition = Query.__strawberry_definition__
    assert definition.name == "Query"

    [field] = definition.fields

    assert field.python_name == "users"
    assert isinstance(field.type, StrawberryOptional)
    assert isinstance(field.type.of_type, StrawberryList)
    assert field.type.of_type.of_type is User

    del User


def test_annotated():
    global User

    @strawberry.type
    class User:
        name: str

    def get_users() -> list[User]:  # pragma: no cover
        return []

    @strawberry.type
    class Query:
        users: Annotated[list[User], object()] = strawberry.field(resolver=get_users)

    definition = Query.__strawberry_definition__
    assert definition.name == "Query"

    [field] = definition.fields

    assert field.python_name == "users"
    assert isinstance(field.type, StrawberryList)
    assert field.type.of_type is User

    del User


def test_annotated_or_notation():
    global User

    @strawberry.type
    class User:
        name: str

    def get_users() -> list[User] | None:  # pragma: no cover
        return []

    @strawberry.type
    class Query:
        users: Annotated[list[User] | None, object()] = strawberry.field(
            resolver=get_users
        )

    definition = Query.__strawberry_definition__
    assert definition.name == "Query"

    [field] = definition.fields

    assert field.python_name == "users"
    assert isinstance(field.type, StrawberryOptional)
    assert isinstance(field.type.of_type, StrawberryList)
    assert field.type.of_type.of_type is User

    del User


def test_annotated_or_notation_generic_type_alias():
    global User

    @strawberry.type
    class User:
        name: str

    def get_users() -> list[User]:  # pragma: no cover
        return []

    @strawberry.type
    class Query:
        users: Annotated[list[User] | None, object()] = strawberry.field(
            resolver=get_users
        )

    definition = Query.__strawberry_definition__
    assert definition.name == "Query"

    [field] = definition.fields

    assert field.python_name == "users"
    assert isinstance(field.type, StrawberryOptional)
    assert isinstance(field.type.of_type, StrawberryList)
    assert field.type.of_type.of_type is User

    del User
