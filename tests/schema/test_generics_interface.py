import textwrap
from typing import Any, Generic, TypeVar

import strawberry


def test_supports_generic_interface():
    T = TypeVar("T")

    @strawberry.interface
    class Example(Generic[T]):
        cursor: strawberry.ID
        field: T

    @strawberry.type
    class User(Example[str]):
        ...

    @strawberry.type
    class Query:
        # TODO: do an example where we are returning a generic interface
        @strawberry.field
        def example(self) -> User:
            return User(cursor=strawberry.ID("1"), field="abc")

    schema = strawberry.Schema(query=Query)

    query = """{
        example {
            __typename
            cursor
            field
        }
    }"""

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data == {
        "example": {"__typename": "User", "cursor": "1", "field": "abc"}
    }

    expected_schema = textwrap.dedent(
        """
        type Query {
          example: User!
        }

        interface StrExample {
          cursor: ID!
          field: String!
        }

        type User implements StrExample {
          cursor: ID!
          field: String!
        }
        """
    ).strip()

    assert str(schema) == expected_schema


def test_generic_interfaces_without_generic_fields_do_not_create_new_types():
    T = TypeVar("T")

    # NOTE: Example here is generic, but none of the exposed fields are generic
    @strawberry.interface
    class Example(Generic[T]):
        cursor: strawberry.ID
        field: strawberry.Private[T]

        @classmethod
        def resolve_type(cls, obj: Any, *args: Any, **kwargs: Any) -> str:
            return "User"

    @strawberry.type
    class User(Example[str]):
        ...

    @strawberry.type
    class Query:
        @strawberry.field
        def example(self) -> Example[str]:
            return User(cursor=strawberry.ID("1"), field="abc")

    schema = strawberry.Schema(query=Query, types=[User])

    expected_schema = textwrap.dedent(
        """
        interface Example {
          cursor: ID!
        }

        type Query {
          example: Example!
        }

        type User implements Example {
          cursor: ID!
        }
        """
    ).strip()

    assert str(schema) == expected_schema

    query = """{
        example {
            __typename
            cursor
        }
    }"""

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data == {"example": {"__typename": "User", "cursor": "1"}}
