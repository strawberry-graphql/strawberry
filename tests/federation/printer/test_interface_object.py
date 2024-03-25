import textwrap

import strawberry


def test_interface_object():
    @strawberry.federation.interface_object(keys=["id"])
    class SomeInterface:
        id: strawberry.ID

    schema = strawberry.federation.Schema(
        types=[SomeInterface], enable_federation_2=True
    )

    expected = """
        schema @link(url: "https://specs.apollo.dev/federation/v2.7", import: ["@interfaceObject", "@key"]) {
          query: Query
        }

        type Query {
          _entities(representations: [_Any!]!): [_Entity]!
          _service: _Service!
        }

        type SomeInterface @key(fields: "id") @interfaceObject {
          id: ID!
        }

        scalar _Any

        union _Entity = SomeInterface

        type _Service {
          sdl: String!
        }
    """

    assert schema.as_str() == textwrap.dedent(expected).strip()
