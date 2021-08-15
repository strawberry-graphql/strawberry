import textwrap
from typing import Optional
from uuid import UUID

import strawberry
from strawberry.arguments import UNSET
from strawberry.printer import print_schema
from strawberry.schema.config import StrawberryConfig


def test_simple_required_types():
    @strawberry.type
    class Query:
        s: str
        i: int
        b: bool
        f: float
        id: strawberry.ID
        uid: UUID

    expected_type = """
    type Query {
      s: String!
      i: Int!
      b: Boolean!
      f: Float!
      id: ID!
      uid: UUID!
    }

    scalar UUID
    """

    schema = strawberry.Schema(query=Query)

    assert print_schema(schema) == textwrap.dedent(expected_type).strip()


def test_printer_with_camel_case_on():
    @strawberry.type
    class Query:
        hello_world: str

    expected_type = """
    type Query {
      helloWorld: String!
    }
    """

    schema = strawberry.Schema(
        query=Query, config=StrawberryConfig(auto_camel_case=True)
    )

    assert print_schema(schema) == textwrap.dedent(expected_type).strip()


def test_printer_with_camel_case_off():
    @strawberry.type
    class Query:
        hello_world: str

    expected_type = """
    type Query {
      hello_world: String!
    }
    """

    schema = strawberry.Schema(
        query=Query, config=StrawberryConfig(auto_camel_case=False)
    )

    assert print_schema(schema) == textwrap.dedent(expected_type).strip()


def test_optional():
    @strawberry.type
    class Query:
        s: Optional[str]

    expected_type = """
    type Query {
      s: String
    }
    """

    schema = strawberry.Schema(query=Query)

    assert print_schema(schema) == textwrap.dedent(expected_type).strip()


def test_input_simple_required_types():
    @strawberry.input
    class MyInput:
        s: str
        i: int
        b: bool
        f: float
        id: strawberry.ID
        uid: UUID

    @strawberry.type
    class Query:
        @strawberry.field
        def search(self, input: MyInput) -> str:
            return input.s

    expected_type = """
    input MyInput {
      s: String!
      i: Int!
      b: Boolean!
      f: Float!
      id: ID!
      uid: UUID!
    }

    type Query {
      search(input: MyInput!): String!
    }

    scalar UUID
    """

    schema = strawberry.Schema(query=Query)

    assert print_schema(schema) == textwrap.dedent(expected_type).strip()


def test_input_defaults():
    @strawberry.input
    class MyInput:
        s: Optional[str] = None
        i: int = 0
        x: Optional[int] = UNSET

    @strawberry.type
    class Query:
        @strawberry.field
        def search(self, input: MyInput) -> int:
            return input.i

    expected_type = """
    input MyInput {
      s: String = null
      i: Int! = 0
      x: Int
    }

    type Query {
      search(input: MyInput!): Int!
    }
    """

    schema = strawberry.Schema(query=Query)

    assert print_schema(schema) == textwrap.dedent(expected_type).strip()


def test_interface():
    @strawberry.interface
    class Node:
        id: strawberry.ID

    @strawberry.type
    class User(Node):
        name: str

    @strawberry.type
    class Query:
        user: User

    expected_type = """
    interface Node {
      id: ID!
    }

    type Query {
      user: User!
    }

    type User implements Node {
      id: ID!
      name: String!
    }
    """

    schema = strawberry.Schema(query=Query)

    assert print_schema(schema) == textwrap.dedent(expected_type).strip()
