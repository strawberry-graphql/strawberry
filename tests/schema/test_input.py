import re
import textwrap
import typing

import pytest

import strawberry
from strawberry.exceptions import InvalidSuperclassInterfaceError
from strawberry.printer import print_schema
from strawberry.types.execution import ExecutionResult
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


def test_nullable_input_field_without_default():
    @strawberry.type
    class Query:
        hello: str = "Hello"

    @strawberry.input
    class TestInput:
        union_expression: str | None
        string_union_expression: "float | None"
        typing_union: typing.Union[int | None]
        optional: typing.Optional[bool]

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def test(self, input: TestInput) -> strawberry.scalars.JSON:
            return {
                "union_expression": input.union_expression,
                "string_union_expression": input.string_union_expression,
                "typing_union": input.typing_union,
                "optional": input.optional,
            }

    schema = strawberry.Schema(query=Query, mutation=Mutation)
    result = schema.execute_sync("mutation { test(input: {}) }")

    assert result == ExecutionResult(
        data={
            "test": {
                "union_expression": None,
                "string_union_expression": None,
                "typing_union": None,
                "optional": None,
            },
        },
        errors=None,
        extensions={},
    )
