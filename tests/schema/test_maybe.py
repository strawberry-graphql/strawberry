import sys
from textwrap import dedent

import pytest

import strawberry


def test_optional_argument_maybe() -> None:
    @strawberry.type
    class Query:
        @strawberry.field
        def hello(self, name: strawberry.Maybe[str] = None) -> str:
            if name:
                return "None" if name.value is None else name.value

            return "UNSET"

    schema = strawberry.Schema(query=Query)

    assert str(schema) == dedent(
        """\
        type Query {
          hello(name: String): String!
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
    assert result.data == {"hello": "UNSET"}
    result = schema.execute_sync(
        """
        query {
            hello(name: "bar")
        }
    """
    )
    assert not result.errors
    assert result.data == {"hello": "bar"}
    result = schema.execute_sync(
        """
        query {
            hello(name: null)
        }
    """
    )
    assert not result.errors
    assert result.data == {"hello": "None"}


@pytest.mark.skipif(sys.version_info < (3, 10), reason="Pattern matching is required")
def test_optional_argument_maybe_pattern_matching() -> None:
    @strawberry.type
    class Query:
        @strawberry.field
        def hello(self, name: strawberry.Maybe[str] = None) -> str:
            match name:
                case strawberry.Some(value=value):
                    return value if value is not None else "None"
                case None:
                    return "UNSET"

    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync(
        """
        query {
            hello
        }
        """
    )
    assert not result.errors
    assert result.data == {"hello": "UNSET"}
    result = schema.execute_sync(
        """
        query {
            hello(name: "bar")
        }
        """
    )
    assert not result.errors
    assert result.data == {"hello": "bar"}
    result = schema.execute_sync(
        """
        query {
            hello(name: null)
        }
        """
    )
    assert not result.errors
    assert result.data == {"hello": "None"}
