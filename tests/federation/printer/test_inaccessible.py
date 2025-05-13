import textwrap
from enum import Enum
from typing import Annotated, Union

import strawberry


def test_field_inaccessible_printed_correctly():
    @strawberry.federation.interface(inaccessible=True)
    class AnInterface:
        id: strawberry.ID

    @strawberry.interface
    class SomeInterface:
        id: strawberry.ID
        a_field: str = strawberry.federation.field(inaccessible=True)

    @strawberry.federation.type(keys=["upc"], extend=True)
    class Product(SomeInterface):
        upc: str = strawberry.federation.field(external=True, inaccessible=True)

    @strawberry.federation.input(inaccessible=True)
    class AnInput:
        id: strawberry.ID = strawberry.federation.field(inaccessible=True)

    @strawberry.federation.type(inaccessible=True)
    class AnInaccessibleType:
        id: strawberry.ID

    @strawberry.federation.type
    class Query:
        @strawberry.field
        def top_products(
            self,
            first: Annotated[int, strawberry.federation.argument(inaccessible=True)],
        ) -> list[Product]:  # pragma: no cover
            return []

    schema = strawberry.federation.Schema(
        query=Query,
        types=[AnInterface, AnInput, AnInaccessibleType],
        enable_federation_2=True,
    )

    expected = """
        schema @link(url: "https://specs.apollo.dev/federation/v2.7", import: ["@external", "@inaccessible", "@key"]) {
          query: Query
        }

        type AnInaccessibleType @inaccessible {
          id: ID!
        }

        input AnInput @inaccessible {
          id: ID! @inaccessible
        }

        interface AnInterface @inaccessible {
          id: ID!
        }

        extend type Product implements SomeInterface @key(fields: "upc") {
          id: ID!
          aField: String! @inaccessible
          upc: String! @external @inaccessible
        }

        type Query {
          _entities(representations: [_Any!]!): [_Entity]!
          _service: _Service!
          topProducts(first: Int! @inaccessible): [Product!]!
        }

        interface SomeInterface {
          id: ID!
          aField: String! @inaccessible
        }

        scalar _Any

        union _Entity = Product

        type _Service {
          sdl: String!
        }
    """

    assert schema.as_str() == textwrap.dedent(expected).strip()


def test_inaccessible_on_mutation():
    @strawberry.type
    class Query:
        hello: str

    @strawberry.type
    class Mutation:
        @strawberry.federation.mutation(inaccessible=True)
        def hello(self) -> str:  # pragma: no cover
            return "Hello"

    schema = strawberry.federation.Schema(
        query=Query,
        mutation=Mutation,
        enable_federation_2=True,
    )

    expected = """
        schema @link(url: "https://specs.apollo.dev/federation/v2.7", import: ["@inaccessible"]) {
          query: Query
          mutation: Mutation
        }

        type Mutation {
          hello: String! @inaccessible
        }

        type Query {
          _service: _Service!
          hello: String!
        }

        scalar _Any

        type _Service {
          sdl: String!
        }
    """

    assert schema.as_str() == textwrap.dedent(expected).strip()


def test_inaccessible_on_scalar():
    SomeScalar = strawberry.federation.scalar(str, name="SomeScalar", inaccessible=True)

    @strawberry.type
    class Query:
        hello: SomeScalar

    schema = strawberry.federation.Schema(
        query=Query,
        enable_federation_2=True,
    )

    expected = """
        schema @link(url: "https://specs.apollo.dev/federation/v2.7", import: ["@inaccessible"]) {
          query: Query
        }

        type Query {
          _service: _Service!
          hello: SomeScalar!
        }

        scalar SomeScalar @inaccessible

        scalar _Any

        type _Service {
          sdl: String!
        }
    """

    assert schema.as_str() == textwrap.dedent(expected).strip()


def test_inaccessible_on_enum():
    @strawberry.federation.enum(inaccessible=True)
    class SomeEnum(Enum):
        A = "A"

    @strawberry.type
    class Query:
        hello: SomeEnum

    schema = strawberry.federation.Schema(
        query=Query,
        enable_federation_2=True,
    )

    expected = """
        schema @link(url: "https://specs.apollo.dev/federation/v2.7", import: ["@inaccessible"]) {
          query: Query
        }

        type Query {
          _service: _Service!
          hello: SomeEnum!
        }

        enum SomeEnum @inaccessible {
          A
        }

        scalar _Any

        type _Service {
          sdl: String!
        }
    """

    assert schema.as_str() == textwrap.dedent(expected).strip()


def test_inaccessible_on_enum_value():
    @strawberry.enum
    class SomeEnum(Enum):
        A = strawberry.federation.enum_value("A", inaccessible=True)

    @strawberry.type
    class Query:
        hello: SomeEnum

    schema = strawberry.federation.Schema(
        query=Query,
        enable_federation_2=True,
    )

    expected = """
        schema @link(url: "https://specs.apollo.dev/federation/v2.7", import: ["@inaccessible"]) {
          query: Query
        }

        type Query {
          _service: _Service!
          hello: SomeEnum!
        }

        enum SomeEnum {
          A @inaccessible
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

    MyUnion = Annotated[
        Union[A, B], strawberry.federation.union("Union", inaccessible=True)
    ]

    @strawberry.federation.type
    class Query:
        hello: MyUnion

    schema = strawberry.federation.Schema(query=Query, enable_federation_2=True)

    expected = """
        schema @link(url: "https://specs.apollo.dev/federation/v2.7", import: ["@inaccessible"]) {
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

        union Union @inaccessible = A | B

        scalar _Any

        type _Service {
          sdl: String!
        }
    """

    assert schema.as_str() == textwrap.dedent(expected).strip()
