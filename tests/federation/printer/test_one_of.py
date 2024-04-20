import textwrap
from typing import Optional

import strawberry


def test_prints_one_of_directive():
    @strawberry.federation.input(one_of=True, tags=["myTag", "anotherTag"])
    class Input:
        a: Optional[str] = strawberry.UNSET
        b: Optional[int] = strawberry.UNSET

    @strawberry.federation.type
    class Query:
        hello: str

    schema = strawberry.federation.Schema(
        query=Query, types=[Input], enable_federation_2=True
    )

    expected = """
        directive @oneOf on INPUT_OBJECT

        schema @link(url: "https://specs.apollo.dev/federation/v2.7", import: ["@tag"]) {
          query: Query
        }

        input Input @tag(name: "myTag") @tag(name: "anotherTag") @oneOf {
          a: String
          b: Int
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
