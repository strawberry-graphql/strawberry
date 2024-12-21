import textwrap
from enum import Enum
from typing import Annotated

import strawberry


def test_field_requires_scopes_printed_correctly():
    @strawberry.federation.interface(
        requires_scopes=[["client", "poweruser"], ["admin"], ["productowner"]]
    )
    class SomeInterface:
        id: strawberry.ID

    @strawberry.federation.type(
        requires_scopes=[["client", "poweruser"], ["admin"], ["productowner"]]
    )
    class Product(SomeInterface):
        upc: str = strawberry.federation.field(requires_scopes=[["productowner"]])

    @strawberry.federation.type
    class Query:
        @strawberry.federation.field(
            requires_scopes=[["client", "poweruser"], ["admin"], ["productowner"]]
        )
        def top_products(
            self, first: Annotated[int, strawberry.federation.argument()]
        ) -> list[Product]:  # pragma: no cover
            return []

    schema = strawberry.federation.Schema(query=Query, enable_federation_2=True)

    expected = """
        schema @link(url: "https://specs.apollo.dev/federation/v2.7", import: ["@requiresScopes"]) {
          query: Query
        }

        type Product implements SomeInterface @requiresScopes(scopes: [["client", "poweruser"], ["admin"], ["productowner"]]) {
          id: ID!
          upc: String! @requiresScopes(scopes: [["productowner"]])
        }

        type Query {
          _service: _Service!
          topProducts(first: Int!): [Product!]! @requiresScopes(scopes: [["client", "poweruser"], ["admin"], ["productowner"]])
        }

        interface SomeInterface @requiresScopes(scopes: [["client", "poweruser"], ["admin"], ["productowner"]]) {
          id: ID!
        }

        scalar _Any

        type _Service {
          sdl: String!
        }
    """

    assert schema.as_str() == textwrap.dedent(expected).strip()


def test_field_requires_scopes_printed_correctly_on_scalar():
    @strawberry.federation.scalar(
        requires_scopes=[["client", "poweruser"], ["admin"], ["productowner"]]
    )
    class SomeScalar(str):
        __slots__ = ()

    @strawberry.federation.type
    class Query:
        hello: SomeScalar

    schema = strawberry.federation.Schema(query=Query, enable_federation_2=True)

    expected = """
        schema @link(url: "https://specs.apollo.dev/federation/v2.7", import: ["@requiresScopes"]) {
          query: Query
        }

        type Query {
          _service: _Service!
          hello: SomeScalar!
        }

        scalar SomeScalar @requiresScopes(scopes: [["client", "poweruser"], ["admin"], ["productowner"]])

        scalar _Any

        type _Service {
          sdl: String!
        }
    """

    assert schema.as_str() == textwrap.dedent(expected).strip()


def test_field_requires_scopes_printed_correctly_on_enum():
    @strawberry.federation.enum(
        requires_scopes=[["client", "poweruser"], ["admin"], ["productowner"]]
    )
    class SomeEnum(Enum):
        A = "A"

    @strawberry.federation.type
    class Query:
        hello: SomeEnum

    schema = strawberry.federation.Schema(query=Query, enable_federation_2=True)

    expected = """
        schema @link(url: "https://specs.apollo.dev/federation/v2.7", import: ["@requiresScopes"]) {
          query: Query
        }

        type Query {
          _service: _Service!
          hello: SomeEnum!
        }

        enum SomeEnum @requiresScopes(scopes: [["client", "poweruser"], ["admin"], ["productowner"]]) {
          A
        }

        scalar _Any

        type _Service {
          sdl: String!
        }
    """

    assert schema.as_str() == textwrap.dedent(expected).strip()
