import textwrap
from enum import Enum
from typing import List, Optional

from typing_extensions import Annotated

import strawberry
from strawberry.printer import print_schema
from strawberry.schema.config import StrawberryConfig
from strawberry.schema_directive import Location
from strawberry.unset import UNSET


def test_print_simple_directive():
    @strawberry.schema_directive(locations=[Location.FIELD_DEFINITION])
    class Sensitive:
        reason: str

    @strawberry.type
    class Query:
        first_name: str = strawberry.field(directives=[Sensitive(reason="GDPR")])

    expected_output = """
    directive @sensitive(reason: String!) on FIELD_DEFINITION

    type Query {
      firstName: String! @sensitive(reason: "GDPR")
    }
    """

    schema = strawberry.Schema(query=Query)

    assert print_schema(schema) == textwrap.dedent(expected_output).strip()


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

    expected_output = """
    directive @sensitive(reason: String!) on FIELD_DEFINITION

    type Query {
      firstName: String! @sensitive(reason: "GDPR")
    }
    """

    schema = strawberry.Schema(query=Query)

    assert print_schema(schema) == textwrap.dedent(expected_output).strip()


def test_directive_on_types():
    @strawberry.input
    class SensitiveValue:
        key: str
        value: str

    @strawberry.schema_directive(locations=[Location.OBJECT, Location.FIELD_DEFINITION])
    class SensitiveData:
        reason: str
        meta: Optional[List[SensitiveValue]] = UNSET

    @strawberry.schema_directive(locations=[Location.INPUT_OBJECT])
    class SensitiveInput:
        reason: str
        meta: Optional[List[SensitiveValue]] = UNSET

    @strawberry.input(directives=[SensitiveInput(reason="GDPR")])
    class Input:
        first_name: str

    @strawberry.type(directives=[SensitiveData(reason="GDPR")])
    class User:
        first_name: str
        phone: str = strawberry.field(
            directives=[
                SensitiveData(
                    reason="PRIVATE",
                    meta=[
                        SensitiveValue(
                            key="can_share_field", value="phone_share_accepted"
                        )
                    ],
                )
            ]
        )
        phone_share_accepted: bool

    @strawberry.type
    class Query:
        @strawberry.field
        def user(self, input: Input) -> User:
            return User(
                first_name=input.first_name,
                phone="+551191551234",
                phone_share_accepted=False,
            )

    expected_output = """
    directive @sensitiveData(reason: String!, meta: [SensitiveValue!]) on OBJECT | FIELD_DEFINITION

    directive @sensitiveInput(reason: String!, meta: [SensitiveValue!]) on INPUT_OBJECT

    input Input @sensitiveInput(reason: "GDPR") {
      firstName: String!
    }

    type Query {
      user(input: Input!): User!
    }

    type User @sensitiveData(reason: "GDPR") {
      firstName: String!
      phone: String! @sensitiveData(reason: "PRIVATE", meta: [{key: "can_share_field", value: "phone_share_accepted"}])
      phoneShareAccepted: Boolean!
    }

    input SensitiveValue {
      key: String!
      value: String!
    }
    """  # noqa:E501

    schema = strawberry.Schema(query=Query)

    assert print_schema(schema) == textwrap.dedent(expected_output).strip()


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

    expected_output = """
    directive @sensitive(as: String!, realAge: String!, real_age: String!) on FIELD_DEFINITION

    type Query {
      firstName: String! @sensitive(as: "GDPR", realAge: "1", real_age: "2")
    }
    """  # noqa:E501

    schema = strawberry.Schema(query=Query)

    assert print_schema(schema) == textwrap.dedent(expected_output).strip()


def test_respects_schema_config_for_names():
    @strawberry.schema_directive(locations=[Location.FIELD_DEFINITION])
    class Sensitive:
        real_age: str

    @strawberry.type
    class Query:
        first_name: str = strawberry.field(directives=[Sensitive(real_age="42")])

    expected_output = """
    directive @Sensitive(real_age: String!) on FIELD_DEFINITION

    type Query {
      first_name: String! @Sensitive(real_age: "42")
    }
    """

    schema = strawberry.Schema(
        query=Query, config=StrawberryConfig(auto_camel_case=False)
    )

    assert print_schema(schema) == textwrap.dedent(expected_output).strip()


def test_respects_schema_parameter_types_for_arguments_int():
    @strawberry.schema_directive(locations=[Location.FIELD_DEFINITION])
    class Sensitive:
        real_age: int

    @strawberry.type
    class Query:
        first_name: str = strawberry.field(directives=[Sensitive(real_age=42)])

    expected_output = """
    directive @Sensitive(real_age: Int!) on FIELD_DEFINITION

    type Query {
      first_name: String! @Sensitive(real_age: 42)
    }
    """

    schema = strawberry.Schema(
        query=Query, config=StrawberryConfig(auto_camel_case=False)
    )

    assert print_schema(schema) == textwrap.dedent(expected_output).strip()


def test_respects_schema_parameter_types_for_arguments_list_of_ints():
    @strawberry.schema_directive(locations=[Location.FIELD_DEFINITION])
    class Sensitive:
        real_age: List[int]

    @strawberry.type
    class Query:
        first_name: str = strawberry.field(directives=[Sensitive(real_age=[42])])

    expected_output = """
    directive @Sensitive(real_age: [Int!]!) on FIELD_DEFINITION

    type Query {
      first_name: String! @Sensitive(real_age: [42])
    }
    """

    schema = strawberry.Schema(
        query=Query, config=StrawberryConfig(auto_camel_case=False)
    )

    assert print_schema(schema) == textwrap.dedent(expected_output).strip()


def test_respects_schema_parameter_types_for_arguments_list_of_strings():
    @strawberry.schema_directive(locations=[Location.FIELD_DEFINITION])
    class Sensitive:
        real_age: List[str]

    @strawberry.type
    class Query:
        first_name: str = strawberry.field(directives=[Sensitive(real_age=["42"])])

    expected_output = """
    directive @Sensitive(real_age: [String!]!) on FIELD_DEFINITION

    type Query {
      first_name: String! @Sensitive(real_age: ["42"])
    }
    """

    schema = strawberry.Schema(
        query=Query, config=StrawberryConfig(auto_camel_case=False)
    )

    assert print_schema(schema) == textwrap.dedent(expected_output).strip()


def test_prints_directive_on_schema():
    @strawberry.schema_directive(locations=[Location.SCHEMA])
    class Tag:
        name: str

    @strawberry.type
    class Query:
        first_name: str = strawberry.field(directives=[Tag(name="team-1")])

    schema = strawberry.Schema(query=Query, schema_directives=[Tag(name="team-1")])

    expected_output = """
    directive @tag(name: String!) on SCHEMA

    schema @tag(name: "team-1") {
      query: Query
    }

    type Query {
      firstName: String!
    }
    """

    assert print_schema(schema) == textwrap.dedent(expected_output).strip()


def test_prints_multiple_directives_on_schema():
    @strawberry.schema_directive(locations=[Location.SCHEMA])
    class Tag:
        name: str

    @strawberry.type
    class Query:
        first_name: str

    schema = strawberry.Schema(
        query=Query, schema_directives=[Tag(name="team-1"), Tag(name="team-2")]
    )

    expected_output = """
    directive @tag(name: String!) on SCHEMA

    schema @tag(name: "team-1") @tag(name: "team-2") {
      query: Query
    }

    type Query {
      firstName: String!
    }
    """

    assert print_schema(schema) == textwrap.dedent(expected_output).strip()


def test_prints_with_types():
    @strawberry.input
    class SensitiveConfiguration:
        reason: str

    @strawberry.schema_directive(locations=[Location.FIELD_DEFINITION])
    class Sensitive:
        config: SensitiveConfiguration

    @strawberry.type
    class Query:
        first_name: str = strawberry.field(
            directives=[Sensitive(config=SensitiveConfiguration(reason="example"))]
        )

    expected_output = """
    directive @sensitive(config: SensitiveConfiguration!) on FIELD_DEFINITION

    type Query {
      firstName: String! @sensitive(config: {reason: "example"})
    }

    input SensitiveConfiguration {
      reason: String!
    }
    """

    schema = strawberry.Schema(query=Query)

    assert print_schema(schema) == textwrap.dedent(expected_output).strip()


def test_prints_with_scalar():
    SensitiveConfiguration = strawberry.scalar(str, name="SensitiveConfiguration")

    @strawberry.schema_directive(locations=[Location.FIELD_DEFINITION])
    class Sensitive:
        config: SensitiveConfiguration

    @strawberry.type
    class Query:
        first_name: str = strawberry.field(directives=[Sensitive(config="Some config")])

    expected_output = """
    directive @sensitive(config: SensitiveConfiguration!) on FIELD_DEFINITION

    type Query {
      firstName: String! @sensitive(config: "Some config")
    }

    scalar SensitiveConfiguration
    """

    schema = strawberry.Schema(query=Query)

    assert print_schema(schema) == textwrap.dedent(expected_output).strip()


def test_prints_with_enum():
    @strawberry.enum
    class Reason(str, Enum):
        EXAMPLE = "example"

    @strawberry.schema_directive(locations=[Location.FIELD_DEFINITION])
    class Sensitive:
        reason: Reason

    @strawberry.type
    class Query:
        first_name: str = strawberry.field(
            directives=[Sensitive(reason=Reason.EXAMPLE)]
        )

    expected_output = """
    directive @sensitive(reason: Reason!) on FIELD_DEFINITION

    type Query {
      firstName: String! @sensitive(reason: EXAMPLE)
    }

    enum Reason {
      EXAMPLE
    }
    """

    schema = strawberry.Schema(query=Query)

    assert print_schema(schema) == textwrap.dedent(expected_output).strip()


def test_does_not_print_definition():
    @strawberry.schema_directive(
        locations=[Location.FIELD_DEFINITION], print_definition=False
    )
    class Sensitive:
        reason: str

    @strawberry.type
    class Query:
        first_name: str = strawberry.field(directives=[Sensitive(reason="GDPR")])

    expected_output = """
    type Query {
      firstName: String! @sensitive(reason: "GDPR")
    }
    """

    schema = strawberry.Schema(query=Query)

    assert print_schema(schema) == textwrap.dedent(expected_output).strip()


def test_print_directive_on_scalar():
    @strawberry.schema_directive(locations=[Location.SCALAR])
    class Sensitive:
        reason: str

    SensitiveString = strawberry.scalar(
        str, name="SensitiveString", directives=[Sensitive(reason="example")]
    )

    @strawberry.type
    class Query:
        first_name: SensitiveString

    expected_output = """
    directive @sensitive(reason: String!) on SCALAR

    type Query {
      firstName: SensitiveString!
    }

    scalar SensitiveString @sensitive(reason: "example")
    """

    schema = strawberry.Schema(query=Query)

    assert print_schema(schema) == textwrap.dedent(expected_output).strip()


def test_print_directive_on_enum():
    @strawberry.schema_directive(locations=[Location.ENUM])
    class Sensitive:
        reason: str

    @strawberry.enum(directives=[Sensitive(reason="example")])
    class SomeEnum(str, Enum):
        EXAMPLE = "example"

    @strawberry.type
    class Query:
        first_name: SomeEnum

    expected_output = """
    directive @sensitive(reason: String!) on ENUM

    type Query {
      firstName: SomeEnum!
    }

    enum SomeEnum @sensitive(reason: "example") {
      EXAMPLE
    }
    """

    schema = strawberry.Schema(query=Query)

    assert print_schema(schema) == textwrap.dedent(expected_output).strip()


def test_print_directive_on_enum_value():
    @strawberry.schema_directive(locations=[Location.ENUM_VALUE])
    class Sensitive:
        reason: str

    @strawberry.enum
    class SomeEnum(Enum):
        EXAMPLE = strawberry.enum_value(
            "example", directives=[Sensitive(reason="example")]
        )

    @strawberry.type
    class Query:
        first_name: SomeEnum

    expected_output = """
    directive @sensitive(reason: String!) on ENUM_VALUE

    type Query {
      firstName: SomeEnum!
    }

    enum SomeEnum {
      EXAMPLE @sensitive(reason: "example")
    }
    """

    schema = strawberry.Schema(query=Query)

    assert print_schema(schema) == textwrap.dedent(expected_output).strip()


def test_print_directive_on_union():
    @strawberry.type
    class A:
        a: int

    @strawberry.type
    class B:
        b: int

    @strawberry.schema_directive(locations=[Location.SCALAR])
    class Sensitive:
        reason: str

    Union = strawberry.union("Union", (A, B), directives=[Sensitive(reason="example")])

    @strawberry.type
    class Query:
        example: Union

    expected_output = """
    directive @sensitive(reason: String!) on SCALAR

    type A {
      a: Int!
    }

    type B {
      b: Int!
    }

    type Query {
      example: Union!
    }

    union Union @sensitive(reason: "example") = A | B
    """

    schema = strawberry.Schema(query=Query)

    assert print_schema(schema) == textwrap.dedent(expected_output).strip()


def test_print_directive_on_argument():
    @strawberry.schema_directive(locations=[Location.ARGUMENT_DEFINITION])
    class Sensitive:
        reason: str

    @strawberry.type
    class Query:
        @strawberry.field
        def hello(
            self,
            name: Annotated[
                str, strawberry.argument(directives=[Sensitive(reason="example")])
            ],
            age: Annotated[
                str, strawberry.argument(directives=[Sensitive(reason="example")])
            ],
        ) -> str:
            return f"Hello {name} of {age}"

    expected_output = """
    directive @sensitive(reason: String!) on ARGUMENT_DEFINITION

    type Query {
      hello(name: String! @sensitive(reason: "example"), age: String! @sensitive(reason: "example")): String!
    }
    """

    schema = strawberry.Schema(query=Query)

    assert print_schema(schema) == textwrap.dedent(expected_output).strip()


def test_print_directive_on_argument_with_description():
    @strawberry.schema_directive(locations=[Location.ARGUMENT_DEFINITION])
    class Sensitive:
        reason: str

    @strawberry.type
    class Query:
        @strawberry.field
        def hello(
            self,
            name: Annotated[
                str,
                strawberry.argument(
                    description="Name", directives=[Sensitive(reason="example")]
                ),
            ],
            age: Annotated[
                str, strawberry.argument(directives=[Sensitive(reason="example")])
            ],
        ) -> str:
            return f"Hello {name} of {age}"

    expected_output = """
    directive @sensitive(reason: String!) on ARGUMENT_DEFINITION

    type Query {
      hello(
        \"\"\"Name\"\"\"
        name: String! @sensitive(reason: "example")
        age: String! @sensitive(reason: "example")
      ): String!
    }
    """

    schema = strawberry.Schema(query=Query)

    assert print_schema(schema) == textwrap.dedent(expected_output).strip()
