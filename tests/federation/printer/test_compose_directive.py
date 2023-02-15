import textwrap

import strawberry
from strawberry.schema_directive import Location


def test_schema_directives_and_compose_schema():
    @strawberry.federation.schema_directive(
        locations=[Location.OBJECT], name="cacheControl"
    )
    class CacheControl:
        max_age: int

    @strawberry.federation.type(
        keys=["id"], shareable=True, extend=True, directives=[CacheControl(max_age=42)]
    )
    class FederatedType:
        id: strawberry.ID

    @strawberry.type
    class Query:
        federatedType: FederatedType

    expected_type = """
    directive @cacheControl(maxAge: Int!) on OBJECT

    schema @composeDirective(name: "cacheControl") @link(url: "https://specs.apollo.dev/federation/v2.3", import: ["@composeDirective", "@key", "@shareable"]) {
      query: Query
    }

    extend type FederatedType @cacheControl(maxAge: 42) @key(fields: "id") @shareable {
      id: ID!
    }

    type Query {
      _entities(representations: [_Any!]!): [_Entity]!
      _service: _Service!
      federatedType: FederatedType!
    }

    scalar _Any

    union _Entity = FederatedType

    type _Service {
      sdl: String!
    }
    """

    schema = strawberry.federation.Schema(
        query=Query,
        enable_federation_2=True,
    )

    assert schema.as_str() == textwrap.dedent(expected_type).strip()
