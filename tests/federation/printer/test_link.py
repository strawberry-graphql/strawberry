import textwrap

import strawberry
from strawberry.federation.schema_directives import Link
from tests.conftest import skip_if_gql_32


def test_link_directive():
    @strawberry.type
    class Query:
        hello: str

    schema = strawberry.federation.Schema(
        query=Query,
        schema_directives=[
            Link(
                url="https://specs.apollo.dev/link/v1.0",
            )
        ],
    )

    expected = """
        schema @link(url: "https://specs.apollo.dev/link/v1.0") {
          query: Query
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


@skip_if_gql_32("formatting is different in gql 3.2")
def test_link_directive_imports():
    @strawberry.type
    class Query:
        hello: str

    schema = strawberry.federation.Schema(
        query=Query,
        schema_directives=[
            Link(
                url="https://specs.apollo.dev/federation/v2.7",
                import_=[
                    "@key",
                    "@requires",
                    "@provides",
                    "@external",
                    {"name": "@tag", "as": "@mytag"},
                    "@extends",
                    "@shareable",
                    "@inaccessible",
                    "@override",
                ],
            )
        ],
    )

    expected = """
    schema @link(url: "https://specs.apollo.dev/federation/v2.7", import: [
      "@key"
      "@requires"
      "@provides"
      "@external"
      { name: "@tag", as: "@mytag" }
      "@extends"
      "@shareable"
      "@inaccessible"
      "@override"
    ]) {
      query: Query
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


def test_adds_link_directive_automatically():
    @strawberry.federation.type(keys=["id"])
    class User:
        id: strawberry.ID

    @strawberry.type
    class Query:
        user: User

    schema = strawberry.federation.Schema(query=Query, enable_federation_2=True)

    expected = """
        schema @link(url: "https://specs.apollo.dev/federation/v2.7", import: ["@key"]) {
          query: Query
        }

        type Query {
          _entities(representations: [_Any!]!): [_Entity]!
          _service: _Service!
          user: User!
        }

        type User @key(fields: "id") {
          id: ID!
        }

        scalar _Any

        union _Entity = User

        type _Service {
          sdl: String!
        }
    """

    assert schema.as_str() == textwrap.dedent(expected).strip()


def test_adds_link_directive_from_interface():
    @strawberry.federation.interface(keys=["id"])
    class SomeInterface:
        id: strawberry.ID

    @strawberry.type
    class User:
        id: strawberry.ID

    @strawberry.type
    class Query:
        user: User

    schema = strawberry.federation.Schema(
        query=Query, types=[SomeInterface], enable_federation_2=True
    )

    expected = """
        schema @link(url: "https://specs.apollo.dev/federation/v2.7", import: ["@key"]) {
          query: Query
        }

        type Query {
          _service: _Service!
          user: User!
        }

        interface SomeInterface @key(fields: "id") {
          id: ID!
        }

        type User {
          id: ID!
        }

        scalar _Any

        type _Service {
          sdl: String!
        }
    """

    assert schema.as_str() == textwrap.dedent(expected).strip()


def test_adds_link_directive_from_input_types():
    @strawberry.federation.input(inaccessible=True)
    class SomeInput:
        id: strawberry.ID

    @strawberry.type
    class User:
        id: strawberry.ID

    @strawberry.type
    class Query:
        user: User

    schema = strawberry.federation.Schema(
        query=Query, types=[SomeInput], enable_federation_2=True
    )

    expected = """
        schema @link(url: "https://specs.apollo.dev/federation/v2.7", import: ["@inaccessible"]) {
          query: Query
        }

        type Query {
          _service: _Service!
          user: User!
        }

        input SomeInput @inaccessible {
          id: ID!
        }

        type User {
          id: ID!
        }

        scalar _Any

        type _Service {
          sdl: String!
        }
    """

    assert schema.as_str() == textwrap.dedent(expected).strip()


def test_adds_link_directive_automatically_from_field():
    @strawberry.federation.type(keys=["id"])
    class User:
        id: strawberry.ID
        age: int = strawberry.federation.field(tags=["private"])

    @strawberry.type
    class Query:
        user: User

    schema = strawberry.federation.Schema(query=Query, enable_federation_2=True)

    expected = """
        schema @link(url: "https://specs.apollo.dev/federation/v2.7", import: ["@key", "@tag"]) {
          query: Query
        }

        type Query {
          _entities(representations: [_Any!]!): [_Entity]!
          _service: _Service!
          user: User!
        }

        type User @key(fields: "id") {
          id: ID!
          age: Int! @tag(name: "private")
        }

        scalar _Any

        union _Entity = User

        type _Service {
          sdl: String!
        }
    """

    assert schema.as_str() == textwrap.dedent(expected).strip()


def test_does_not_add_directive_link_if_federation_two_is_not_enabled():
    @strawberry.federation.type(keys=["id"])
    class User:
        id: strawberry.ID

    @strawberry.type
    class Query:
        user: User

    schema = strawberry.federation.Schema(query=Query, enable_federation_2=False)

    expected = """
        type Query {
          _entities(representations: [_Any!]!): [_Entity]!
          _service: _Service!
          user: User!
        }

        type User @key(fields: "id") {
          id: ID!
        }

        scalar _Any

        union _Entity = User

        type _Service {
          sdl: String!
        }
    """

    assert schema.as_str() == textwrap.dedent(expected).strip()


def test_adds_link_directive_automatically_from_scalar():
    # TODO: Federation scalar
    @strawberry.scalar
    class X:
        pass

    @strawberry.federation.type(keys=["id"])
    class User:
        id: strawberry.ID
        age: X

    @strawberry.type
    class Query:
        user: User

    schema = strawberry.federation.Schema(query=Query, enable_federation_2=True)

    expected = """
        schema @link(url: "https://specs.apollo.dev/federation/v2.7", import: ["@key"]) {
          query: Query
        }

        type Query {
          _entities(representations: [_Any!]!): [_Entity]!
          _service: _Service!
          user: User!
        }

        type User @key(fields: "id") {
          id: ID!
          age: X!
        }

        scalar X

        scalar _Any

        union _Entity = User

        type _Service {
          sdl: String!
        }
    """

    assert schema.as_str() == textwrap.dedent(expected).strip()
