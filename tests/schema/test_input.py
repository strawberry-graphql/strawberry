import re
import textwrap

import pytest

import strawberry
from strawberry.exceptions import (
    InvalidSuperclassInterfaceError,
    ResolverFieldOnInputError,
)
from strawberry.printer import print_schema


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
    ResolverFieldOnInputError,
    match=re.escape(
        "Field `upper_name` on input type `UserInput` can't have a resolver"
    ),
)
def test_input_fields_cannot_have_a_resolver():
    @strawberry.input
    class UserInput:
        name: str

        # it would be a required input field, whose resolver never runs
        @strawberry.field
        def upper_name(self) -> str:
            return self.name.upper()


@pytest.mark.raises_strawberry_exception(
    ResolverFieldOnInputError,
    match=re.escape(
        "Field `upper_name` on input type `UserInput` can't have a resolver"
    ),
)
def test_input_fields_cannot_have_a_resolver_passed_to_field():
    def get_upper_name() -> str:
        return "ADA"

    @strawberry.input
    class UserInput:
        name: str
        upper_name: str = strawberry.field(resolver=get_upper_name)


@pytest.mark.raises_strawberry_exception(
    ResolverFieldOnInputError,
    match=re.escape(
        "Field `upper_name` on input type `UserInput`, inherited from `User`, "
        "can't have a resolver"
    ),
)
def test_input_cannot_inherit_fields_with_a_resolver():
    @strawberry.type
    class User:
        name: str

        @strawberry.field
        def upper_name(self) -> str:
            return self.name.upper()

    @strawberry.input
    class UserInput(User):
        pass


def test_error_for_a_lambda_resolver_points_at_the_field():
    with pytest.raises(ResolverFieldOnInputError) as exc_info:

        @strawberry.input
        class UserInput:
            name: str
            upper_name: str = strawberry.field(resolver=lambda: "ADA")

    source = exc_info.value.exception_source

    assert source is not None
    assert "upper_name" in source.code.splitlines()[source.error_line - 1]


def test_inherited_resolver_fields_hidden_with_private_are_allowed():
    @strawberry.type
    class User:
        name: str

        @strawberry.field
        def upper_name(self) -> str | None:
            return self.name.upper()

    @strawberry.input
    class UserInput(User):
        upper_name: strawberry.Private[str | None] = None

    @strawberry.type
    class Query:
        @strawberry.field
        def hello(self, input: UserInput) -> str:
            return f"{input.name}/{input.upper_name}"

    schema = strawberry.Schema(query=Query)

    assert schema.execute_sync('{ hello(input: {name: "ada"}) }').data == {
        "hello": "ada/None"
    }


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


@pytest.mark.parametrize(
    ("query", "variables", "expected_error"),
    [
        (
            "query { test(input: {}) }",
            None,
            "Expected value of type 'TestInput' to include required field 'required', found: {  }.",
        ),
        (
            "query($input: TestInput!) { test(input: $input) }",
            None,
            "Variable '$input' has invalid value: Expected a value of non-null type 'TestInput!' to be provided.",
        ),
        (
            "query($input: TestInput!) { test(input: $input) }",
            {"input": {}},
            "Variable '$input' has invalid value: Expected value of type 'TestInput' to include required field 'required', found: {}.",
        ),
    ],
)
def test_non_nullable_input_fields_must_be_specified(query, variables, expected_error):
    @strawberry.input
    class TestInput:
        required: str

    @strawberry.type
    class Query:
        @strawberry.field
        def test(self, input: TestInput) -> str:
            return input.required

    schema = strawberry.Schema(query=Query)
    result = schema.execute_sync(query, variables)

    assert not result.data
    assert result.errors
    assert [error.message for error in result.errors] == [expected_error]


@pytest.mark.parametrize(
    ("query", "variables"),
    [
        ("query { test(input: {}) }", None),
        ("query { test(input: {optional: null}) }", None),
        ("query($input: TestInput!) { test(input: $input) }", {"input": {}}),
        (
            "query($input: TestInput!) { test(input: $input) }",
            {"input": {"optional": None}},
        ),
    ],
)
def test_nullable_input_field_without_default(query, variables):
    @strawberry.input
    class TestInput:
        optional: str | None

    @strawberry.type
    class Query:
        @strawberry.field
        def test(self, input: TestInput) -> str | None:
            return input.optional

    schema = strawberry.Schema(query=Query)
    result = schema.execute_sync(query, variables)

    assert not result.errors
    assert result.data == {"test": None}
