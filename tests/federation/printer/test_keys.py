# type: ignore

import textwrap

import strawberry
from strawberry.federation.schema_directives import Key


def test_keys_federation_2():
    global Review

    @strawberry.federation.type
    class User:
        username: str

    @strawberry.federation.type(keys=[Key(fields="upc", resolvable=True)], extend=True)
    class Product:
        upc: str = strawberry.federation.field(external=True)
        reviews: list["Review"]

    @strawberry.federation.type(keys=["body"])
    class Review:
        body: str
        author: User
        product: Product

    @strawberry.federation.type
    class Query:
        @strawberry.field
        def top_products(self, first: int) -> list[Product]:  # pragma: no cover
            return []

    schema = strawberry.federation.Schema(query=Query)

    expected = """
        schema @link(url: "https://specs.apollo.dev/federation/v2.11", import: ["@external", "@key"]) {
          query: Query
        }

        extend type Product @key(fields: "upc", resolvable: true) {
          upc: String! @external
          reviews: [Review!]!
        }

        type Query {
          _entities(representations: [_Any!]!): [_Entity]!
          _service: _Service!
          topProducts(first: Int!): [Product!]!
        }

        type Review @key(fields: "body") {
          body: String!
          author: User!
          product: Product!
        }

        type User {
          username: String!
        }

        scalar _Any

        union _Entity = Product | Review

        type _Service {
          sdl: String!
        }
    """

    assert schema.as_str() == textwrap.dedent(expected).strip()

    del Review


def test_keys_use_the_name_converter_for_field_names():
    # https://github.com/strawberry-graphql/strawberry/issues/591
    # `fields` on `@key` is a plain string, so it isn't renamed the same way
    # a real field is; without running it through the name converter, the
    # printed directive references a field name (`my_key`) that doesn't
    # match the one actually printed for the field (`myKey`).
    @strawberry.federation.type(keys=["my_key"])
    class Product:
        my_key: str

    @strawberry.federation.type
    class Query:
        @strawberry.field
        def product(self) -> Product:  # pragma: no cover
            return Product(my_key="1")

    schema = strawberry.federation.Schema(query=Query)

    expected = """
        schema @link(url: "https://specs.apollo.dev/federation/v2.11", import: ["@key"]) {
          query: Query
        }

        type Product @key(fields: "myKey") {
          myKey: String!
        }

        type Query {
          _entities(representations: [_Any!]!): [_Entity]!
          _service: _Service!
          product: Product!
        }

        scalar _Any

        union _Entity = Product

        type _Service {
          sdl: String!
        }
    """

    assert schema.as_str() == textwrap.dedent(expected).strip()


def test_keys_use_the_name_converter_for_nested_field_names():
    @strawberry.federation.type(keys=["org_id"])
    class Organization:
        org_id: str

    @strawberry.federation.type(keys=["my_key organization { org_id }"])
    class Product:
        my_key: str
        organization: Organization

    @strawberry.federation.type
    class Query:
        @strawberry.field
        def product(self) -> Product:  # pragma: no cover
            return Product(my_key="1", organization=Organization(org_id="1"))

    schema = strawberry.federation.Schema(query=Query)

    expected = """
        schema @link(url: "https://specs.apollo.dev/federation/v2.11", import: ["@key"]) {
          query: Query
        }

        type Organization @key(fields: "orgId") {
          orgId: String!
        }

        type Product @key(fields: "myKey organization { orgId }") {
          myKey: String!
          organization: Organization!
        }

        type Query {
          _entities(representations: [_Any!]!): [_Entity]!
          _service: _Service!
          product: Product!
        }

        scalar _Any

        union _Entity = Organization | Product

        type _Service {
          sdl: String!
        }
    """

    assert schema.as_str() == textwrap.dedent(expected).strip()


def test_keys_are_not_renamed_when_auto_camel_case_is_off():
    from strawberry.schema.config import StrawberryConfig

    @strawberry.federation.type(keys=["my_key"])
    class Product:
        my_key: str

    @strawberry.federation.type
    class Query:
        @strawberry.field
        def product(self) -> Product:  # pragma: no cover
            return Product(my_key="1")

    schema = strawberry.federation.Schema(
        query=Query, config=StrawberryConfig(auto_camel_case=False)
    )

    expected = """
        schema @link(url: "https://specs.apollo.dev/federation/v2.11", import: ["@key"]) {
          query: Query
        }

        type Product @key(fields: "my_key") {
          my_key: String!
        }

        type Query {
          _entities(representations: [_Any!]!): [_Entity]!
          _service: _Service!
          product: Product!
        }

        scalar _Any

        union _Entity = Product

        type _Service {
          sdl: String!
        }
    """

    assert schema.as_str() == textwrap.dedent(expected).strip()
