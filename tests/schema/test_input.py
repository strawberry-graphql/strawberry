import re
import textwrap

import pytest

import strawberry
from strawberry.exceptions import InvalidSuperclassInterfaceError
from strawberry.printer import print_schema
from tests.conftest import skip_if_gql_32


def test_renaming_input_fields():
    @strawberry.input
    class FilterInput:
        in_: str | None = strawberry.field(name="in", default=strawberry.UNSET)

    @strawberry.type
    class Query:
        hello: str = "Hello"

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def filter(self, input: FilterInput) -> str:
            return f"Hello {input.in_ or 'nope'}"

    schema = strawberry.Schema(query=Query, mutation=Mutation)

    query = "mutation { filter(input: {}) }"

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data
    assert result.data["filter"] == "Hello nope"


def test_input_extension_prints_extend_input():
    @strawberry.input(name="UserInput", extend=True)
    class UserInputExtension:
        extra: str

    @strawberry.type
    class Query:
        @strawberry.field
        def echo(self, data: UserInputExtension) -> str:
            return data.extra

    schema = strawberry.Schema(query=Query)

    expected = """
    type Query {
      echo(data: UserInput!): String!
    }

    extend input UserInput {
      extra: String!
    }
    """

    assert print_schema(schema) == textwrap.dedent(expected).strip()


def test_input_extension_can_extend_existing_input():
    @strawberry.input(name="UserInput")
    class UserInput:
        name: str

    @strawberry.input(name="UserInput", extend=True)
    class UserInputExtension:
        extra: str

    @strawberry.type
    class Query:
        @strawberry.field
        def echo(self, data: UserInput) -> str:
            return f"{data.name} {data.extra}"

    schema = strawberry.Schema(query=Query, types=[UserInputExtension])

    expected = """
    type Query {
      echo(data: UserInput!): String!
    }

    input UserInput {
      name: String!
    }

    extend input UserInput {
      extra: String!
    }
    """

    assert print_schema(schema) == textwrap.dedent(expected).strip()

    result = schema.execute_sync('{ echo(data: { name: "Ada", extra: "Lovelace" }) }')

    assert not result.errors
    assert result.data == {"echo": "Ada Lovelace"}


def test_input_extension_conversion_is_schema_local():
    @strawberry.input(name="UserInput")
    class UserInput:
        name: str

    @strawberry.input(name="UserInput", extend=True)
    class FirstUserInputExtension:
        first: str

    @strawberry.input(name="UserInput", extend=True)
    class SecondUserInputExtension:
        second: str

    @strawberry.type
    class FirstQuery:
        @strawberry.field
        def echo(self, data: UserInput) -> str:
            return f"{data.name} {data.first}"

    @strawberry.type
    class SecondQuery:
        @strawberry.field
        def echo(self, data: UserInput) -> str:
            return f"{data.name} {data.second}"

    first_schema = strawberry.Schema(query=FirstQuery, types=[FirstUserInputExtension])
    second_schema = strawberry.Schema(
        query=SecondQuery, types=[SecondUserInputExtension]
    )

    first_result = first_schema.execute_sync(
        '{ echo(data: { name: "Ada", first: "Lovelace" }) }'
    )
    second_result = second_schema.execute_sync(
        '{ echo(data: { name: "Grace", second: "Hopper" }) }'
    )

    assert not first_result.errors
    assert first_result.data == {"echo": "Ada Lovelace"}
    assert not second_result.errors
    assert second_result.data == {"echo": "Grace Hopper"}


@skip_if_gql_32("formatting is different in gql 3.2")
def test_input_with_nonscalar_field_default():
    @strawberry.input
    class NonScalarField:
        id: int = 10
        nullable_field: int | None = None

    @strawberry.input
    class Input:
        non_scalar_field: NonScalarField = strawberry.field(
            default_factory=NonScalarField
        )
        id: int = 10

    @strawberry.type
    class ExampleOutput:
        input_id: int
        non_scalar_id: int
        non_scalar_nullable_field: int | None

    @strawberry.type
    class Query:
        @strawberry.field
        def example(self, data: Input) -> ExampleOutput:
            return ExampleOutput(
                input_id=data.id,
                non_scalar_id=data.non_scalar_field.id,
                non_scalar_nullable_field=data.non_scalar_field.nullable_field,
            )

    schema = strawberry.Schema(query=Query)

    expected = """
    type ExampleOutput {
      inputId: Int!
      nonScalarId: Int!
      nonScalarNullableField: Int
    }

    input Input {
      nonScalarField: NonScalarField! = { id: 10 }
      id: Int! = 10
    }

    input NonScalarField {
      id: Int! = 10
      nullableField: Int = null
    }

    type Query {
      example(data: Input!): ExampleOutput!
    }
    """
    assert print_schema(schema) == textwrap.dedent(expected).strip()

    query = """
    query($input_data: Input!)
    {
        example(data: $input_data) {
            inputId nonScalarId nonScalarNullableField
        }
    }
    """
    result = schema.execute_sync(
        query, variable_values={"input_data": {"nonScalarField": {}}}
    )

    assert not result.errors
    expected_result = {"inputId": 10, "nonScalarId": 10, "nonScalarNullableField": None}
    assert result.data["example"] == expected_result


@pytest.mark.raises_strawberry_exception(
    InvalidSuperclassInterfaceError,
    match=re.escape(
        "Input class 'SomeInput' cannot inherit from interface(s): SomeInterface"
    ),
)
def test_input_cannot_inherit_from_interface():
    @strawberry.interface
    class SomeInterface:
        some_arg: str

    @strawberry.input
    class SomeInput(SomeInterface):
        another_arg: str


@pytest.mark.raises_strawberry_exception(
    InvalidSuperclassInterfaceError,
    match=re.escape(
        "Input class 'SomeOtherInput' cannot inherit from interface(s): SomeInterface, SomeOtherInterface"
    ),
)
def test_input_cannot_inherit_from_interfaces():
    @strawberry.interface
    class SomeInterface:
        some_arg: str

    @strawberry.interface
    class SomeOtherInterface:
        some_other_arg: str

    @strawberry.input
    class SomeOtherInput(SomeInterface, SomeOtherInterface):
        another_arg: str
