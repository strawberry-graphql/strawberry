from __future__ import annotations

import textwrap

import strawberry
from tests.conftest import skip_if_gql_32

pytestmark = skip_if_gql_32("GraphQL 3.3.0 is required for incremental execution")


@strawberry.type
class Query:
    hello: str


def test_does_not_print_defer_and_stream_directives_when_experimental_execution_is_disabled():
    schema = strawberry.Schema(
        query=Query,
        config={"enable_experimental_incremental_execution": False},
    )

    expected_type = """
    type Query {
      hello: String!
    }
    """

    assert str(schema) == textwrap.dedent(expected_type).strip()


def test_prints_defer_and_stream_directives_when_experimental_execution_is_enabled():
    schema = strawberry.Schema(
        query=Query,
        config={"enable_experimental_incremental_execution": True},
    )

    expected_type = """
    directive @defer(if: Boolean, label: String) on FRAGMENT_SPREAD | INLINE_FRAGMENT

    directive @stream(if: Boolean, label: String, initialCount: Int = 0) on FIELD

    type Query {
      hello: String!
    }
    """

    assert str(schema) == textwrap.dedent(expected_type).strip()
