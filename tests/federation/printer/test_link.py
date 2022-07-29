import textwrap

import strawberry
from strawberry.federation.schema_directives import Link


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
        directive @link(url: String, as: String, for: link__Purpose, import: [link__Import]) repeatable on SCHEMA

        schema @link(url: "https://specs.apollo.dev/link/v1.0") {
          query: Query
        }

        type Query {
          _service: _Service!
          hello: String!
        }

        scalar _Any

        scalar _FieldSet

        type _Service {
          sdl: String!
        }
    """

    assert schema.as_str() == textwrap.dedent(expected).strip()


def test_link_directive_imports():
    @strawberry.type
    class Query:
        hello: str

    schema = strawberry.federation.Schema(
        query=Query,
        schema_directives=[
            Link(
                url="https://specs.apollo.dev/federation/v2.0",
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
        directive @link(url: String, as: String, for: link__Purpose, import: [link__Import]) repeatable on SCHEMA

        schema @link(url: "https://specs.apollo.dev/federation/v2.0", import: ["@key", "@requires", "@provides", "@external", {name: "@tag", as: "@mytag"}, "@extends", "@shareable", "@inaccessible", "@override"]) {
          query: Query
        }

        type Query {
          _service: _Service!
          hello: String!
        }

        scalar _Any

        scalar _FieldSet

        type _Service {
          sdl: String!
        }
    """

    assert schema.as_str() == textwrap.dedent(expected).strip()
