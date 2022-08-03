import textwrap

import strawberry
from strawberry.apollo.schema_directives import CacheControl
from strawberry.printer import print_schema


def test_print_simple_cache_control():
    @strawberry.type
    class Query:
        first_name: str = strawberry.field(directives=[CacheControl(max_age=10)])

    expected_type = """
        directive @cacheControl(maxAge: Int, scope: CacheControlScope = PUBLIC, inhereditMaxAge: Boolean = false) on FIELD_DEFINITION | OBJECT | INTERFACE | UNION

        type Query {
          firstName: String! @cacheControl(maxAge: 10, scope: PUBLIC, inhereditMaxAge: false)
        }
    """
    schema = strawberry.Schema(query=Query)

    assert print_schema(schema) == textwrap.dedent(expected_type).strip()
