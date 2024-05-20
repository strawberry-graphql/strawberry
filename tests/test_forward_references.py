# type: ignore
from __future__ import annotations

import sys
import textwrap
from typing import List
from typing_extensions import Annotated

import pytest

import strawberry
from strawberry.printer import print_schema
from strawberry.scalars import JSON
from strawberry.type import StrawberryList, StrawberryOptional
from tests.a import A


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


@pytest.mark.skipif(
    sys.version_info < (3, 9),
    reason="Python 3.8 and previous can't properly resolve this.",
)
def test_lazy_forward_reference():
    @strawberry.type
    class Query:
        @strawberry.field
        async def a(self) -> A:
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
      optionalA: A
      optionalA2: A
    }

    type Query {
      a: A!
    }
    """

    schema = strawberry.Schema(query=Query)
    assert print_schema(schema) == textwrap.dedent(expected_representation).strip()


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

    def get_users() -> List[User] | None:
        return []

    @strawberry.type
    class Query:
        users: List[User] | None = strawberry.field(resolver=get_users)

    definition = Query.__strawberry_definition__
    assert definition.name == "Query"

    [field] = definition.fields

    assert field.python_name == "users"
    assert isinstance(field.type, StrawberryOptional)
    assert isinstance(field.type.of_type, StrawberryList)
    assert field.type.of_type.of_type is User

    del User


@pytest.mark.skipif(
    sys.version_info < (3, 9),
    reason="generic type alias only available on python 3.9+",
)
def test_union_or_notation_generic_type_alias():
    global User

    @strawberry.type
    class User:
        name: str

    def get_users() -> list[User] | None:
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

    def get_users() -> List[User]:
        return []

    @strawberry.type
    class Query:
        users: Annotated[List[User], object()] = strawberry.field(resolver=get_users)

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

    def get_users() -> List[User] | None:
        return []

    @strawberry.type
    class Query:
        users: Annotated[List[User] | None, object()] = strawberry.field(
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


@pytest.mark.skipif(
    sys.version_info < (3, 9),
    reason="generic type alias only available on python 3.9+",
)
def test_annotated_or_notation_generic_type_alias():
    global User

    @strawberry.type
    class User:
        name: str

    def get_users() -> list[User]:
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
