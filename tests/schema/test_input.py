from textwrap import dedent
from typing import Optional, Union

import strawberry
from strawberry.arguments import UNSET


def test_default_unset():
    @strawberry.input
    class UserInput:
        name: Union[Optional[str], UNSET]

    @strawberry.type
    class Query:
        @strawberry.field
        def hello(self, data: UserInput) -> str:
            if data.name is UNSET:
                return "Hello stranger"

            if data.name is None:
                return "Hello anonymous"

            return f"Hello {data.name}"

    schema = strawberry.Schema(Query)

    assert str(schema) == dedent(
        """\
        type Query {
          hello(data: UserInput!): String!
        }

        input UserInput {
          name: String
        }"""
    )

    result = schema.execute_sync("{ hello(data: {}) }")
    assert not result.errors
    assert result.data == {"hello": "Hello stranger"}

    result = schema.execute_sync("{ hello(data: { name: null }) }")
    assert not result.errors
    assert result.data == {"hello": "Hello anonymous"}

    result = schema.execute_sync('{ hello(data: { name: "jkimbo" }) }')
    assert not result.errors
    assert result.data == {"hello": "Hello jkimbo"}


def test_optional_value():
    @strawberry.input
    class UserInput:
        name: Optional[str]

    @strawberry.type
    class Query:
        @strawberry.field
        def hello(self, data: UserInput) -> str:
            if data.name is None:
                return "Hello anonymous"

            return f"Hello {data.name}"

    schema = strawberry.Schema(Query)

    assert str(schema) == dedent(
        """\
        type Query {
          hello(data: UserInput!): String!
        }

        input UserInput {
          name: String
        }"""
    )

    result = schema.execute_sync("{ hello(data: {}) }")
    assert not result.errors
    assert result.data == {"hello": "Hello anonymous"}

    result = schema.execute_sync("{ hello(data: { name: null }) }")
    assert not result.errors
    assert result.data == {"hello": "Hello anonymous"}

    result = schema.execute_sync('{ hello(data: { name: "jkimbo" }) }')
    assert not result.errors
    assert result.data == {"hello": "Hello jkimbo"}
