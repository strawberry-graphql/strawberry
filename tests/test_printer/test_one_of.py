from __future__ import annotations

import textwrap

import strawberry
from strawberry.schema_directives import OneOf


@strawberry.input(directives=[OneOf()])
class ExampleInputTagged:
    a: str | None
    b: int | None


@strawberry.type
class ExampleResult:
    a: str | None
    b: int | None


@strawberry.type
class Query:
    @strawberry.field
    def test(self, input: ExampleInputTagged) -> ExampleResult:  # pragma: no cover
        return input  # type: ignore


schema = strawberry.Schema(query=Query)


def test_prints_one_of_directive():
    expected_type = """
    directive @oneOf on INPUT_OBJECT

    input ExampleInputTagged @oneOf {
      a: String
      b: Int
    }

    type ExampleResult {
      a: String
      b: Int
    }

    type Query {
      test(input: ExampleInputTagged!): ExampleResult!
    }
    """

    assert str(schema) == textwrap.dedent(expected_type).strip()
