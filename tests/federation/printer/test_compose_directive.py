import textwrap

import strawberry
from strawberry.schema_directive import Location


def test_schema_directives_and_compose_schema():
    @strawberry.federation.schema_directive(
        locations=[Location.OBJECT],
        name="cacheControl",
        compose=True,
    )
    class CacheControl:
        max_age: int

    @strawberry.federation.schema_directive(
        locations=[Location.OBJECT], name="sensitive"
    )
    class Sensitive:
        reason: str

    @strawberry.federation.type(
        keys=["id"],
        shareable=True,
        extend=True,
        directives=[CacheControl(max_age=42), Sensitive(reason="example")],
    )
    class FederatedType:
        id: strawberry.ID

    @strawberry.type
    class Query:
        federatedType: FederatedType  # noqa: N815

    expected_type = """
    directive @cacheControl(maxAge: Int!) on OBJECT

    directive @sensitive(reason: String!) on OBJECT

    schema @composeDirective(name: "@cacheControl") @link(url: "https://directives.strawberry.rocks/cacheControl/v0.1", import: ["@cacheControl"]) @link(url: "https://specs.apollo.dev/federation/v2.7", import: ["@composeDirective", "@key", "@shareable"]) {
      query: Query
    }

    extend type FederatedType @cacheControl(maxAge: 42) @sensitive(reason: "example") @key(fields: "id") @shareable {
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


def test_schema_directives_and_compose_schema_custom_import_url():
    @strawberry.federation.schema_directive(
        locations=[Location.OBJECT],
        name="cacheControl",
        compose=True,
        import_url="https://f.strawberry.rocks/cacheControl/v1.0",
    )
    class CacheControl:
        max_age: int

    @strawberry.federation.schema_directive(
        locations=[Location.OBJECT], name="sensitive"
    )
    class Sensitive:
        reason: str

    @strawberry.federation.type(
        keys=["id"],
        shareable=True,
        extend=True,
        directives=[CacheControl(max_age=42), Sensitive(reason="example")],
    )
    class FederatedType:
        id: strawberry.ID

    @strawberry.type
    class Query:
        federatedType: FederatedType  # noqa: N815

    expected_type = """
    directive @cacheControl(maxAge: Int!) on OBJECT

    directive @sensitive(reason: String!) on OBJECT

    schema @composeDirective(name: "@cacheControl") @link(url: "https://f.strawberry.rocks/cacheControl/v1.0", import: ["@cacheControl"]) @link(url: "https://specs.apollo.dev/federation/v2.7", import: ["@composeDirective", "@key", "@shareable"]) {
      query: Query
    }

    extend type FederatedType @cacheControl(maxAge: 42) @sensitive(reason: "example") @key(fields: "id") @shareable {
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
