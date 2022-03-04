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
    type Query {
      firstName: String! @sensitiveField(reason: "GDPR")
    }
    """

    schema = strawberry.Schema(query=Query)

    assert print_schema(schema) == textwrap.dedent(expected_type).strip()


def test_directive_on_types():
    @strawberry.schema_directive(locations=[Location.OBJECT])
    class SensitiveData:
        reason: str

    @strawberry.schema_directive(locations=[Location.INPUT_OBJECT])
    class SensitiveInput:
        reason: str

    @strawberry.input(directives=[SensitiveInput(reason="GDPR")])
    class Input:
        first_name: str

    @strawberry.type(directives=[SensitiveData(reason="GDPR")])
    class User:
        first_name: str

    @strawberry.type
    class Query:
        @strawberry.field
        def user(self, input: Input) -> User:
            return User(first_name=input.first_name)

    expected_type = """
    input Input @sensitiveInput(reason: "GDPR") {
      firstName: String!
    }

    type Query {
      user(input: Input!): User!
    }

    type User @sensitiveData(reason: "GDPR") {
      firstName: String!
    }
    """

    schema = strawberry.Schema(query=Query)

    assert print_schema(schema) == textwrap.dedent(expected_type).strip()
