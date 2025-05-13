import textwrap
from textwrap import dedent
from typing import Annotated, Optional

import strawberry
from strawberry.types.unset import UNSET


def test_argument_descriptions():
    @strawberry.type
    class Query:
        @strawberry.field
        def hello(  # type: ignore
            name: Annotated[
                str, strawberry.argument(description="Your name")
            ] = "Patrick",
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
                str, strawberry.argument(deprecation_reason="Your reason")
            ] = "Patrick",
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


def test_setting_metadata_on_argument():
    field_definition = None

    @strawberry.type
    class Query:
        @strawberry.field
        def hello(
            self,
            info: strawberry.Info,
            input: Annotated[str, strawberry.argument(metadata={"test": "foo"})],
        ) -> str:
            nonlocal field_definition
            field_definition = info._field
            return f"Hi {input}"

    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync(
        """
        query {
            hello(input: "there")
        }
    """
    )
    assert not result.errors
    assert result.data == {"hello": "Hi there"}

    assert field_definition
    assert field_definition.arguments[0].metadata == {
        "test": "foo",
    }


def test_argument_parse_order():
    """Check early early exit from argument parsing due to finding ``info``.

    Reserved argument parsing, which interally also resolves annotations, exits early
    after detecting the ``info`` argumnent. As a result, the annotation of the ``id_``
    argument in `tests.schema.test_annotated.type_a.Query` is never resolved. This
    results in `StrawberryArgument` not being able to detect that ``id_`` makes use of
    `typing.Annotated` and `strawberry.argument`.

    This behavior is fixed by by ensuring that `StrawberryArgument` makes use of the new
    `StrawberryAnnotation.evaluate` method instead of consuming the raw annotation.

    An added benefit of this fix is that by removing annotation resolving code from
    `StrawberryResolver` and making it a part of `StrawberryAnnotation`, it makes it
    possible for `StrawberryArgument` and `StrawberryResolver` to share the same type
    evaluation cache.

    Refer to: https://github.com/strawberry-graphql/strawberry/issues/2855
    """
    from tests.schema.test_annotated import type_a, type_b

    expected = """
    type Query {
      getTesting(id: UUID!): String
    }

    scalar UUID
    """

    schema_a = strawberry.Schema(type_a.Query)
    schema_b = strawberry.Schema(type_b.Query)

    assert str(schema_a) == str(schema_b)
    assert str(schema_a) == textwrap.dedent(expected).strip()
