import textwrap

import strawberry
from strawberry.printer import print_schema
from strawberry.schema_directive import Location


def test_print_simple_directive():
    @strawberry.schema_directive(locations=[Location.FIELD_DEFINITION])
    class Sensitive:
        reason: str

    @strawberry.type
    class Query:
        first_name: str = strawberry.field(directives=[Sensitive(reason="GDPR")])

    expected_type = """
    directive @sensitive on FIELD_DEFINITION

    type Query {
      firstName: String! @sensitive(reason: "GDPR")
    }
    """

    schema = strawberry.Schema(query=Query)

    assert print_schema(schema) == textwrap.dedent(expected_type).strip()


def test_print_directive_with_name():
    @strawberry.schema_directive(locations=[Location.FIELD_DEFINITION])
    class SensitiveField:
        reason: str

    @strawberry.type
    class Query:
        first_name: str = strawberry.field(directives=[SensitiveField(reason="GDPR")])

    expected_type = """
    directive @sensitiveField on FIELD_DEFINITION

    type Query {
      firstName: String! @sensitiveField(reason: "GDPR")
    }
    """

    schema = strawberry.Schema(query=Query)

    assert print_schema(schema) == textwrap.dedent(expected_type).strip()
