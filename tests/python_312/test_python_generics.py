"""These tests are for Generics that don't expose any generic parts to the schema."""

import sys
import textwrap

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


def test_with_interface():
    @strawberry.interface
    class GenericInterface[T]:
        data: strawberry.Private[T]

        @strawberry.field
        def value(self) -> str:
            raise NotImplementedError

    @strawberry.type
    class ImplementationOne(GenericInterface[str]):
        @strawberry.field
        def value(self) -> str:
            return self.data

    @strawberry.type
    class ImplementationTwo(GenericInterface[bool]):
        @strawberry.field
        def value(self) -> str:
            if self.data is True:
                return "true"
            return "false"

    @strawberry.type
    class Query:
        @strawberry.field
        @staticmethod
        async def generic_field() -> GenericInterface:  # type: ignore
            return ImplementationOne(data="foo")

    schema = strawberry.Schema(
        query=Query, types=[ImplementationOne, ImplementationTwo]
    )

    expected_schema = textwrap.dedent(
        """
        interface GenericInterface {
          value: String!
        }

        type ImplementationOne implements GenericInterface {
          value: String!
        }

        type ImplementationTwo implements GenericInterface {
          value: String!
        }

        type Query {
          genericField: GenericInterface!
        }
        """
    ).strip()

    assert str(schema) == expected_schema


def test_with_interface_and_type():
    @strawberry.interface
    class GenericInterface[T]:
        data: strawberry.Private[T]

        @strawberry.field
        def value(self) -> str:
            raise NotImplementedError

    @strawberry.type
    class ImplementationOne(GenericInterface[str]):
        @strawberry.field
        def value(self) -> str:
            return self.data

    @strawberry.type
    class ImplementationTwo(GenericInterface[bool]):
        @strawberry.field
        def value(self) -> str:
            if self.data is True:
                return "true"
            return "false"

    @strawberry.type
    class Query:
        @strawberry.field
        @staticmethod
        async def generic_field() -> GenericInterface[str | bool]:
            return ImplementationOne(data="foo")

    schema = strawberry.Schema(
        query=Query, types=[ImplementationOne, ImplementationTwo]
    )

    expected_schema = textwrap.dedent(
        """
        interface GenericInterface {
          value: String!
        }

        type ImplementationOne implements GenericInterface {
          value: String!
        }

        type ImplementationTwo implements GenericInterface {
          value: String!
        }

        type Query {
          genericField: GenericInterface!
        }
        """
    ).strip()

    assert str(schema) == expected_schema
