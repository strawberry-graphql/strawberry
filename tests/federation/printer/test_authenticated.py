import textwrap
from enum import Enum
from typing import Annotated

import strawberry


def test_field_authenticated_printed_correctly():
    @strawberry.federation.interface(authenticated=True)
    class SomeInterface:
        id: strawberry.ID

    @strawberry.federation.type(authenticated=True)
    class Product(SomeInterface):
        upc: str = strawberry.federation.field(authenticated=True)

    @strawberry.federation.type
    class Query:
        @strawberry.federation.field(authenticated=True)
        def top_products(
            self, first: Annotated[int, strawberry.federation.argument()]
        ) -> list[Product]:  # pragma: no cover
            return []

    schema = strawberry.federation.Schema(query=Query, enable_federation_2=True)

    expected = """
        schema @link(url: "https://specs.apollo.dev/federation/v2.7", import: ["@authenticated"]) {
          query: Query
        }

        type Product implements SomeInterface @authenticated {
          id: ID!
          upc: String! @authenticated
        }

        type Query {
          _service: _Service!
          topProducts(first: Int!): [Product!]! @authenticated
        }

        interface SomeInterface @authenticated {
          id: ID!
        }

        scalar _Any

        type _Service {
          sdl: String!
        }
    """

    assert schema.as_str() == textwrap.dedent(expected).strip()


def test_field_authenticated_printed_correctly_on_scalar():
    @strawberry.federation.scalar(authenticated=True)
    class SomeScalar(str):
        __slots__ = ()

    @strawberry.federation.type
    class Query:
        hello: SomeScalar

    schema = strawberry.federation.Schema(query=Query, enable_federation_2=True)

    expected = """
        schema @link(url: "https://specs.apollo.dev/federation/v2.7", import: ["@authenticated"]) {
          query: Query
        }

        type Query {
          _service: _Service!
          hello: SomeScalar!
        }

        scalar SomeScalar @authenticated

        scalar _Any

        type _Service {
          sdl: String!
        }
    """

    assert schema.as_str() == textwrap.dedent(expected).strip()


def test_field_authenticated_printed_correctly_on_enum():
    @strawberry.federation.enum(authenticated=True)
    class SomeEnum(Enum):
        A = "A"

    @strawberry.federation.type
    class Query:
        hello: SomeEnum

    schema = strawberry.federation.Schema(query=Query, enable_federation_2=True)

    expected = """
        schema @link(url: "https://specs.apollo.dev/federation/v2.7", import: ["@authenticated"]) {
          query: Query
        }

        type Query {
          _service: _Service!
          hello: SomeEnum!
        }

        enum SomeEnum @authenticated {
          A
        }

        scalar _Any

        type _Service {
          sdl: String!
        }
    """

    assert schema.as_str() == textwrap.dedent(expected).strip()
