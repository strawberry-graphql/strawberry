import textwrap
from enum import Enum
from typing import List

import strawberry


def test_field_tag_printed_correctly():
    @strawberry.interface
    class SomeInterface:
        id: strawberry.ID

    @strawberry.federation.type(keys=["upc"], extend=True)
    class Product(SomeInterface):
        upc: str = strawberry.federation.field(
            external=True, tags=["myTag", "anotherTag"]
        )

    @strawberry.federation.type
    class Query:
        @strawberry.field
        def top_products(self, first: int) -> List[Product]:
            return []

    schema = strawberry.federation.Schema(query=Query, enable_federation_2=True)

    expected = """
        schema @link(url: "https://specs.apollo.dev/federation/v2.0", import: ["@external", "@key", "@tag"]) {
          query: Query
        }

        extend type Product implements SomeInterface @key(fields: "upc") {
          id: ID!
          upc: String! @external @tag(name: "myTag") @tag(name: "anotherTag")
        }

        type Query {
          _service: _Service!
          _entities(representations: [_Any!]!): [_Entity]!
          topProducts(first: Int!): [Product!]!
        }

        interface SomeInterface {
          id: ID!
        }

        scalar _Any

        union _Entity = Product

        type _Service {
          sdl: String!
        }
    """

    assert schema.as_str() == textwrap.dedent(expected).strip()


def test_field_tag_printed_correctly_on_scalar():
    @strawberry.federation.scalar(tags=["myTag", "anotherTag"])
    class SomeScalar(str):
        ...

    @strawberry.federation.type
    class Query:
        hello: SomeScalar

    schema = strawberry.federation.Schema(query=Query, enable_federation_2=True)

    expected = """
        schema @link(url: "https://specs.apollo.dev/federation/v2.0", import: ["@tag"]) {
          query: Query
        }

        type Query {
          _service: _Service!
          hello: SomeScalar!
        }

        scalar SomeScalar @tag(name: "myTag") @tag(name: "anotherTag")

        scalar _Any

        type _Service {
          sdl: String!
        }
    """

    assert schema.as_str() == textwrap.dedent(expected).strip()


def test_field_tag_printed_correctly_on_enum():
    @strawberry.federation.enum(tags=["myTag", "anotherTag"])
    class SomeEnum(Enum):
        A = "A"

    @strawberry.federation.type
    class Query:
        hello: SomeEnum

    schema = strawberry.federation.Schema(query=Query, enable_federation_2=True)

    expected = """
        schema @link(url: "https://specs.apollo.dev/federation/v2.0", import: ["@tag"]) {
          query: Query
        }

        type Query {
          _service: _Service!
          hello: SomeEnum!
        }

        enum SomeEnum @tag(name: "myTag") @tag(name: "anotherTag") {
          A
        }

        scalar _Any

        type _Service {
          sdl: String!
        }
    """

    assert schema.as_str() == textwrap.dedent(expected).strip()


def test_field_tag_printed_correctly_on_enum_value():
    @strawberry.enum
    class SomeEnum(Enum):
        A = strawberry.federation.enum_value("A", tags=["myTag", "anotherTag"])

    @strawberry.federation.type
    class Query:
        hello: SomeEnum

    schema = strawberry.federation.Schema(query=Query, enable_federation_2=True)

    expected = """
        schema @link(url: "https://specs.apollo.dev/federation/v2.0", import: ["@tag"]) {
          query: Query
        }

        type Query {
          _service: _Service!
          hello: SomeEnum!
        }

        enum SomeEnum {
          A @tag(name: "myTag") @tag(name: "anotherTag")
        }

        scalar _Any

        type _Service {
          sdl: String!
        }
    """

    assert schema.as_str() == textwrap.dedent(expected).strip()


def test_field_tag_printed_correctly_on_union():
    @strawberry.type
    class A:
        a: str

    @strawberry.type
    class B:
        b: str

    Union = strawberry.federation.union("Union", (A, B), tags=["myTag", "anotherTag"])

    @strawberry.federation.type
    class Query:
        hello: Union

    schema = strawberry.federation.Schema(query=Query, enable_federation_2=True)

    expected = """
        schema @link(url: "https://specs.apollo.dev/federation/v2.0", import: ["@tag"]) {
          query: Query
        }

        type A {
          a: String!
        }

        type B {
          b: String!
        }

        type Query {
          _service: _Service!
          hello: Union!
        }

        union Union @tag(name: "myTag") @tag(name: "anotherTag") = A | B

        scalar _Any

        type _Service {
          sdl: String!
        }
    """

    assert schema.as_str() == textwrap.dedent(expected).strip()
