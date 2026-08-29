import textwrap

import strawberry
import strawberry.schema.schema as schema_module
from strawberry.schema_directive import Location


def test_schema_directives_and_compose_schema(monkeypatch):
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

    schema @composeDirective(name: "@cacheControl") @link(url: "https://directives.strawberry.rocks/cacheControl/v0.1", import: ["@cacheControl"]) @link(url: "https://specs.apollo.dev/federation/v2.11", import: ["@composeDirective", "@key", "@shareable"]) {
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

    graphql_schema_calls = 0
    graphql_schema = schema_module.GraphQLSchema
    validated_schemas: list[object] = []
    validate_schema = schema_module.validate_schema

    def counting_graphql_schema(*args: object, **kwargs: object):
        nonlocal graphql_schema_calls
        graphql_schema_calls += 1
        return graphql_schema(*args, **kwargs)

    def tracking_validate_schema(schema: object):
        validated_schemas.append(schema)
        return validate_schema(schema)

    monkeypatch.setattr(schema_module, "GraphQLSchema", counting_graphql_schema)
    monkeypatch.setattr(schema_module, "validate_schema", tracking_validate_schema)

    schema = strawberry.federation.Schema(
        query=Query,
    )

    assert graphql_schema_calls == 1
    assert validated_schemas == [schema._schema]
    assert schema.as_str() == textwrap.dedent(expected_type).strip()

    result = schema.execute_sync(
        """
        {
          __schema {
            directives {
              name
            }
          }
        }
        """
    )

    assert result.errors is None
    directive_names = {
        directive["name"] for directive in result.data["__schema"]["directives"]
    }
    assert {
        "cacheControl",
        "sensitive",
        "key",
        "shareable",
        "composeDirective",
        "link",
    } <= directive_names


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

    schema @composeDirective(name: "@cacheControl") @link(url: "https://f.strawberry.rocks/cacheControl/v1.0", import: ["@cacheControl"]) @link(url: "https://specs.apollo.dev/federation/v2.11", import: ["@composeDirective", "@key", "@shareable"]) {
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
    )

    assert schema.as_str() == textwrap.dedent(expected_type).strip()
