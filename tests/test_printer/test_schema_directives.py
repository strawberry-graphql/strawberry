import textwrap

import strawberry
from strawberry.printer import print_schema
from strawberry.schema.config import StrawberryConfig
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
    @strawberry.schema_directive(
        name="sensitive", locations=[Location.FIELD_DEFINITION]
    )
    class SensitiveDirective:
        reason: str

    @strawberry.type
    class Query:
        first_name: str = strawberry.field(
            directives=[SensitiveDirective(reason="GDPR")]
        )

    expected_type = """
    type Query {
      firstName: String! @sensitive(reason: "GDPR")
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


def test_using_different_names_for_directive_field():
    @strawberry.schema_directive(locations=[Location.FIELD_DEFINITION])
    class Sensitive:
        reason: str = strawberry.directive_field(name="as")
        real_age: str
        real_age_2: str = strawberry.directive_field(name="real_age")

    @strawberry.type
    class Query:
        first_name: str = strawberry.field(
            directives=[Sensitive(reason="GDPR", real_age="1", real_age_2="2")]
        )

    expected_type = """
    type Query {
      firstName: String! @sensitive(as: "GDPR", realAge: "1", real_age: "2")
    }
    """

    schema = strawberry.Schema(query=Query)

    assert print_schema(schema) == textwrap.dedent(expected_type).strip()


def test_respects_schema_config_for_names():
    @strawberry.schema_directive(locations=[Location.FIELD_DEFINITION])
    class Sensitive:
        real_age: str

    @strawberry.type
    class Query:
        first_name: str = strawberry.field(directives=[Sensitive(real_age="42")])

    expected_type = """
    type Query {
      first_name: String! @Sensitive(real_age: "42")
    }
    """

    schema = strawberry.Schema(
        query=Query, config=StrawberryConfig(auto_camel_case=False)
    )

    assert print_schema(schema) == textwrap.dedent(expected_type).strip()
