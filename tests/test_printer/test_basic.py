import textwrap
from typing import Optional
from uuid import UUID

import strawberry
from strawberry.printer import print_schema
from strawberry.scalars import JSON
from strawberry.schema.config import StrawberryConfig
from strawberry.types.unset import UNSET
from tests.conftest import skip_if_gql_32


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
        s2: str = None  # type: ignore - we do this for testing purposes

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
      s2: String!
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
        b: bool = False
        f: float = 0.0
        f2: float = 0.1
        id: strawberry.ID = strawberry.ID("some_id")
        id_number: strawberry.ID = strawberry.ID(123)  # type: ignore
        id_number_string: strawberry.ID = strawberry.ID("123")
        x: Optional[int] = UNSET
        l: list[str] = strawberry.field(default_factory=list)  # noqa: E741
        list_with_values: list[str] = strawberry.field(
            default_factory=lambda: ["a", "b"]
        )
        list_from_generator: list[str] = strawberry.field(
            default_factory=lambda: (x for x in ["a", "b"])
        )
        list_from_string: list[str] = "ab"  # type: ignore - we do this for testing purposes

    @strawberry.type
    class Query:
        @strawberry.field
        def search(self, input: MyInput) -> int:
            return input.i

    expected_type = """
    input MyInput {
      s: String = null
      i: Int! = 0
      b: Boolean! = false
      f: Float! = 0
      f2: Float! = 0.1
      id: ID! = "some_id"
      idNumber: ID! = 123
      idNumberString: ID! = 123
      x: Int
      l: [String!]! = []
      listWithValues: [String!]! = ["a", "b"]
      listFromGenerator: [String!]! = ["a", "b"]
      listFromString: [String!]! = "ab"
    }

    type Query {
      search(input: MyInput!): Int!
    }
    """

    schema = strawberry.Schema(query=Query)

    assert print_schema(schema) == textwrap.dedent(expected_type).strip()


@skip_if_gql_32("formatting is different in gql 3.2")
def test_input_other_inputs():
    @strawberry.input
    class Nested:
        s: str

    @strawberry.input
    class MyInput:
        nested: Nested
        nested2: Nested = strawberry.field(default_factory=lambda: Nested(s="a"))
        nested3: Nested = strawberry.field(default_factory=lambda: {"s": "a"})
        nested4: Nested = "abc"  # type: ignore - we do this for testing purposes

    @strawberry.type
    class Query:
        @strawberry.field
        def search(self, input: MyInput) -> str:
            return input.nested.s

    expected_type = """
    input MyInput {
      nested: Nested!
      nested2: Nested! = { s: "a" }
      nested3: Nested! = { s: "a" }
      nested4: Nested!
    }

    input Nested {
      s: String!
    }

    type Query {
      search(input: MyInput!): String!
    }
    """

    schema = strawberry.Schema(query=Query)

    assert print_schema(schema) == textwrap.dedent(expected_type).strip()


@skip_if_gql_32("formatting is different in gql 3.2")
def test_input_defaults_scalars():
    @strawberry.input
    class MyInput:
        j: JSON = strawberry.field(default_factory=dict)
        j2: JSON = strawberry.field(default_factory=lambda: {"hello": "world"})
        j3: JSON = strawberry.field(
            default_factory=lambda: {"hello": {"nice": "world"}}
        )

    @strawberry.type
    class Query:
        @strawberry.field
        def search(self, input: MyInput) -> JSON:
            return input.j

    expected_type = """
    \"\"\"
    The `JSON` scalar type represents JSON values as specified by [ECMA-404](https://ecma-international.org/wp-content/uploads/ECMA-404_2nd_edition_december_2017.pdf).
    \"\"\"
    scalar JSON @specifiedBy(url: "https://ecma-international.org/wp-content/uploads/ECMA-404_2nd_edition_december_2017.pdf")

    input MyInput {
      j: JSON! = {  }
      j2: JSON! = { hello: "world" }
      j3: JSON! = { hello: { nice: "world" } }
    }

    type Query {
      search(input: MyInput!): JSON!
    }
    """

    schema = strawberry.Schema(query=Query)

    assert print_schema(schema) == textwrap.dedent(expected_type).strip()


@skip_if_gql_32("formatting is different in gql 3.2")
def test_arguments_scalar():
    @strawberry.input
    class MyInput:
        j: JSON = strawberry.field(default_factory=dict)
        j2: JSON = strawberry.field(default_factory=lambda: {"hello": "world"})
        j3: JSON = strawberry.field(
            default_factory=lambda: {"hello": {"nice": "world"}}
        )

    @strawberry.type
    class Query:
        @strawberry.field
        def search(self, j: JSON = {}) -> JSON:  # noqa: B006
            return j

        @strawberry.field
        def search2(self, j: JSON = {"hello": "world"}) -> JSON:  # noqa: B006
            return j

        @strawberry.field
        def search3(self, j: JSON = {"hello": {"nice": "world"}}) -> JSON:  # noqa: B006
            return j

    expected_type = """
    \"\"\"
    The `JSON` scalar type represents JSON values as specified by [ECMA-404](https://ecma-international.org/wp-content/uploads/ECMA-404_2nd_edition_december_2017.pdf).
    \"\"\"
    scalar JSON @specifiedBy(url: "https://ecma-international.org/wp-content/uploads/ECMA-404_2nd_edition_december_2017.pdf")

    type Query {
      search(j: JSON! = {  }): JSON!
      search2(j: JSON! = { hello: "world" }): JSON!
      search3(j: JSON! = { hello: { nice: "world" } }): JSON!
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


def test_root_objects_with_different_names():
    @strawberry.type
    class Domanda:
        name: str

    @strawberry.type
    class Mutazione:
        name: str

    @strawberry.type
    class Abbonamento:
        name: str

    expected_type = """
    schema {
      query: Domanda
      mutation: Mutazione
      subscription: Abbonamento
    }

    type Abbonamento {
      name: String!
    }

    type Domanda {
      name: String!
    }

    type Mutazione {
      name: String!
    }
    """

    schema = strawberry.Schema(
        query=Domanda, mutation=Mutazione, subscription=Abbonamento
    )

    assert print_schema(schema) == textwrap.dedent(expected_type).strip()
