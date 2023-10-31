import textwrap
from typing import Generic, TypeVar

import strawberry


def test_supports_generic_interface():
    T = TypeVar("T")

    @strawberry.interface
    class Example(Generic[T]):
        cursor: strawberry.ID
        field: T

        # TODO: add this to the interface class when they are generic
        def __class_getitem__(cls, params):
            params = params if isinstance(params, tuple) else (params,)
            type_vars = (p.__name__ for p in cls.__parameters__)

            type_var_map = dict(zip(type_vars, params))

            return cls.__strawberry_definition__.copy_with(type_var_map=type_var_map)

    @strawberry.type
    class User(Example[str]):
        ...

    @strawberry.type
    class Query:
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
