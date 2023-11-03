"""
These tests are for Generics that don't expose any generic parts to the schema.
"""

import sys

import pytest

import strawberry

pytestmark = pytest.mark.skipif(
    sys.version_info < (3, 12), reason="These are tests for Python 3.12+"
)


def test_does_not_create_a_new_type_when_no_generic_field_exposed():
    @strawberry.type
    class Edge[T]:
        cursor: strawberry.ID
        node_field: strawberry.Private[T]

    @strawberry.type
    class Query:
        @strawberry.field
        def example(self) -> Edge[int]:
            return Edge(cursor=strawberry.ID("1"), node_field=1)

    schema = strawberry.Schema(query=Query)

    query = """{
        example {
            __typename
            cursor
        }
    }"""

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data == {"example": {"__typename": "Edge", "cursor": "1"}}


def test_does_not_create_a_new_type_when_no_generic_field_exposed_argument():
    @strawberry.type
    class Edge[T]:
        cursor: strawberry.ID

        def something(input: T) -> T:
            return input

    @strawberry.type
    class Query:
        @strawberry.field
        def example(self) -> Edge[int]:
            return Edge(cursor=strawberry.ID("1"))

    schema = strawberry.Schema(query=Query)

    query = """{
        example {
            __typename
            cursor
        }
    }"""

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data == {"example": {"__typename": "Edge", "cursor": "1"}}
