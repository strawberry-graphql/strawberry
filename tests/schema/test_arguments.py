from textwrap import dedent
from typing import Optional

from typing_extensions import Annotated

import strawberry
from strawberry.unset import UNSET


def test_argument_descriptions():
    @strawberry.type
    class Query:
        @strawberry.field
        def hello(  # type: ignore
            name: Annotated[
                str, strawberry.argument(description="Your name")  # noqa: F722
            ] = "Patrick"
        ) -> str:
            return f"Hi {name}"

    schema = strawberry.Schema(query=Query)

    assert str(schema) == dedent(
        '''\
        type Query {
          hello(
            """Your name"""
            name: String! = "Patrick"
          ): String!
        }'''
    )


def test_argument_deprecation_reason():
    @strawberry.type
    class Query:
        @strawberry.field
        def hello(  # type: ignore
            name: Annotated[
                str, strawberry.argument(deprecation_reason="Your reason")  # noqa: F722
            ] = "Patrick"
        ) -> str:
            return f"Hi {name}"

    schema = strawberry.Schema(query=Query)

    assert str(schema) == dedent(
        """\
        type Query {
          hello(name: String! = "Patrick" @deprecated(reason: "Your reason")): String!
        }"""
    )


def test_argument_names():
    @strawberry.input
    class HelloInput:
        name: str = strawberry.field(default="Patrick", description="Your name")

    @strawberry.type
    class Query:
        @strawberry.field
        def hello(
            self, input_: Annotated[HelloInput, strawberry.argument(name="input")]
        ) -> str:
            return f"Hi {input_.name}"

    schema = strawberry.Schema(query=Query)

    assert str(schema) == dedent(
        '''\
        input HelloInput {
          """Your name"""
          name: String! = "Patrick"
        }

        type Query {
          hello(input: HelloInput!): String!
        }'''
    )


def test_argument_with_default_value_none():
    @strawberry.type
    class Query:
        @strawberry.field
        def hello(self, name: Optional[str] = None) -> str:
            return f"Hi {name}"

    schema = strawberry.Schema(query=Query)

    assert str(schema) == dedent(
        """\
        type Query {
          hello(name: String = null): String!
        }"""
    )


def test_optional_argument_unset():
    @strawberry.type
    class Query:
        @strawberry.field
        def hello(self, name: Optional[str] = UNSET, age: Optional[int] = UNSET) -> str:
            if name is UNSET:
                return "Hi there"
            return f"Hi {name}"

    schema = strawberry.Schema(query=Query)

    assert str(schema) == dedent(
        """\
        type Query {
          hello(name: String, age: Int): String!
        }"""
    )

    result = schema.execute_sync(
        """
        query {
            hello
        }
    """
    )
    assert not result.errors
    assert result.data == {"hello": "Hi there"}


def test_optional_input_field_unset():
    @strawberry.input
    class TestInput:
        name: Optional[str] = UNSET
        age: Optional[int] = UNSET

    @strawberry.type
    class Query:
        @strawberry.field
        def hello(self, input: TestInput) -> str:
            if input.name is UNSET:
                return "Hi there"
            return f"Hi {input.name}"

    schema = strawberry.Schema(query=Query)

    assert (
        str(schema)
        == dedent(
            """
        type Query {
          hello(input: TestInput!): String!
        }

        input TestInput {
          name: String
          age: Int
        }
        """
        ).strip()
    )

    result = schema.execute_sync(
        """
        query {
            hello(input: {})
        }
    """
    )
    assert not result.errors
    assert result.data == {"hello": "Hi there"}
