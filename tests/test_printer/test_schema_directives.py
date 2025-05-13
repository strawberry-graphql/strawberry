import textwrap
from enum import Enum
from typing import Annotated, Any, Optional, Union

import strawberry
from strawberry import BasePermission, Info
from strawberry.permission import PermissionExtension
from strawberry.printer import print_schema
from strawberry.schema.config import StrawberryConfig
from strawberry.schema_directive import Location
from strawberry.types.unset import UNSET
from tests.conftest import skip_if_gql_32


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


@skip_if_gql_32("formatting is different in gql 3.2")
def test_directive_on_types():
    @strawberry.input
    class SensitiveValue:
        key: str
        value: str

    @strawberry.schema_directive(locations=[Location.OBJECT, Location.FIELD_DEFINITION])
    class SensitiveData:
        reason: str
        meta: Optional[list[SensitiveValue]] = UNSET

    @strawberry.schema_directive(locations=[Location.INPUT_OBJECT])
    class SensitiveInput:
        reason: str
        meta: Optional[list[SensitiveValue]] = UNSET

    @strawberry.schema_directive(locations=[Location.INPUT_FIELD_DEFINITION])
    class RangeInput:
        min: int
        max: int

    @strawberry.input(directives=[SensitiveInput(reason="GDPR")])
    class Input:
        first_name: str
        age: int = strawberry.field(directives=[RangeInput(min=1, max=100)])

    @strawberry.type(directives=[SensitiveData(reason="GDPR")])
    class User:
        first_name: str
        age: int
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
                age=input.age,
                phone="+551191551234",
                phone_share_accepted=False,
            )

    expected_output = """
    directive @rangeInput(min: Int!, max: Int!) on INPUT_FIELD_DEFINITION

    directive @sensitiveData(reason: String!, meta: [SensitiveValue!]) on OBJECT | FIELD_DEFINITION

    directive @sensitiveInput(reason: String!, meta: [SensitiveValue!]) on INPUT_OBJECT

    input Input @sensitiveInput(reason: "GDPR") {
      firstName: String!
      age: Int! @rangeInput(min: 1, max: 100)
    }

    type Query {
      user(input: Input!): User!
    }

    type User @sensitiveData(reason: "GDPR") {
      firstName: String!
      age: Int!
      phone: String! @sensitiveData(reason: "PRIVATE", meta: [{ key: "can_share_field", value: "phone_share_accepted" }])
      phoneShareAccepted: Boolean!
    }

    input SensitiveValue {
      key: String!
      value: String!
    }
    """

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
    """

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
        real_age: list[int]

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
        real_age: list[str]

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


@skip_if_gql_32("formatting is different in gql 3.2")
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
      firstName: String! @sensitive(config: { reason: "example" })
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

        __slots__ = ()

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

        __slots__ = ()

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


def test_dedupe_multiple_equal_directives():
    class MemberRoleRequired(BasePermission):
        message = "Keine Rechte"

        def has_permission(self, source, info: Info, **kwargs: Any) -> bool:
            return True

    @strawberry.interface
    class MyInterface:
        id: strawberry.ID

        @strawberry.field(
            extensions=[PermissionExtension(permissions=[MemberRoleRequired()])]
        )
        def hello(self, info: Info) -> str:
            return "world"

    @strawberry.type
    class MyType1(MyInterface):
        name: str

    @strawberry.type
    class MyType2(MyInterface):
        age: int

    @strawberry.type
    class Query:
        @strawberry.field
        def my_type(self, info: Info) -> MyInterface:
            return MyType1(id=strawberry.ID("1"), name="Hello")

    expected_output = """
    directive @memberRoleRequired on FIELD_DEFINITION

    interface MyInterface {
      id: ID!
      hello: String! @memberRoleRequired
    }

    type MyType1 implements MyInterface {
      id: ID!
      hello: String! @memberRoleRequired
      name: String!
    }

    type MyType2 implements MyInterface {
      id: ID!
      hello: String! @memberRoleRequired
      age: Int!
    }

    type Query {
      myType: MyInterface!
    }
    """

    schema = strawberry.Schema(Query, types=[MyType1, MyType2])

    assert print_schema(schema) == textwrap.dedent(expected_output).strip()

    retval = schema.execute_sync("{ myType { id hello } }")
    assert retval.errors is None
    assert retval.data == {"myType": {"id": "1", "hello": "world"}}


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

    MyUnion = Annotated[
        Union[A, B],
        strawberry.union(name="MyUnion", directives=[Sensitive(reason="example")]),
    ]

    @strawberry.type
    class Query:
        example: MyUnion

    expected_output = """
    directive @sensitive(reason: String!) on SCALAR

    type A {
      a: Int!
    }

    type B {
      b: Int!
    }

    union MyUnion @sensitive(reason: "example") = A | B

    type Query {
      example: MyUnion!
    }
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


@skip_if_gql_32("formatting is different in gql 3.2")
def test_print_directive_with_unset_value():
    @strawberry.input
    class FooInput:
        a: Optional[str] = strawberry.UNSET
        b: Optional[str] = strawberry.UNSET

    @strawberry.schema_directive(locations=[Location.FIELD_DEFINITION])
    class FooDirective:
        input: FooInput
        optional_input: Optional[FooInput] = strawberry.UNSET

    @strawberry.type
    class Query:
        @strawberry.field(directives=[FooDirective(input=FooInput(a="something"))])
        def foo(self, info) -> str: ...

    schema = strawberry.Schema(query=Query)

    expected_output = """
    directive @fooDirective(input: FooInput!, optionalInput: FooInput) on FIELD_DEFINITION

    type Query {
      foo: String! @fooDirective(input: { a: "something" })
    }

    input FooInput {
      a: String
      b: String
    }
    """

    schema = strawberry.Schema(query=Query)

    assert print_schema(schema) == textwrap.dedent(expected_output).strip()


@skip_if_gql_32("formatting is different in gql 3.2")
def test_print_directive_with_snake_case_arguments():
    @strawberry.input
    class FooInput:
        hello: str
        hello_world: str

    @strawberry.schema_directive(locations=[Location.FIELD_DEFINITION])
    class FooDirective:
        input: FooInput
        optional_input: Optional[FooInput] = strawberry.UNSET

    @strawberry.type
    class Query:
        @strawberry.field(
            directives=[
                FooDirective(input=FooInput(hello="hello", hello_world="hello world"))
            ]
        )
        def foo(self, info) -> str: ...

    schema = strawberry.Schema(query=Query)

    expected_output = """
    directive @fooDirective(input: FooInput!, optionalInput: FooInput) on FIELD_DEFINITION

    type Query {
      foo: String! @fooDirective(input: { hello: "hello", helloWorld: "hello world" })
    }

    input FooInput {
      hello: String!
      helloWorld: String!
    }
    """

    schema = strawberry.Schema(query=Query)

    assert print_schema(schema) == textwrap.dedent(expected_output).strip()
