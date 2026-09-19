import re
import textwrap
from enum import Enum

import pytest

import strawberry
from strawberry.exceptions import InvalidSuperclassInterfaceError
from strawberry.printer import print_schema
from strawberry.utils import IS_GQL_32
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


@strawberry.enum
class Color(Enum):
    RED = "red"
    BLUE = "blue"


@strawberry.input
class Pagination:
    limit: int = 10
    offset: int = 0


@strawberry.input
class Options:
    color: Color
    pagination: Pagination = strawberry.field(default_factory=Pagination)
    label: strawberry.Maybe[str | None] = None
    note: str | None = None


@strawberry.type
class QueryWithInstanceDefaults:
    @strawberry.field
    def options(
        self, options: Options = Options(color=Color.RED, label=strawberry.Some(None))
    ) -> str:
        options.pagination.offset += 1
        return repr(options)

    @strawberry.field
    def required_options(self, options: Options) -> str:
        return repr(options)


@strawberry.input
class Renamed:
    some_value: int = 0


@strawberry.type
class QueryWithNestedInstanceDefaults:
    @strawberry.field
    def nullable_options(
        self, options: Options | None = Options(color=Color.BLUE)
    ) -> str:
        return repr(options)

    @strawberry.field
    def pages(self, pages: list[Pagination] = [Pagination(limit=1)]) -> str:  # noqa: B006
        return repr(pages)

    @strawberry.field
    def options_from_dict(
        self,
        options: Options = {"color": Color.RED, "pagination": Pagination(limit=2)},  # noqa: B006
    ) -> str:
        return repr(options)

    @strawberry.field
    def renamed(self, value: Renamed = {"some_value": 5}) -> str:  # noqa: B006
        return repr(value)


def test_input_instance_as_argument_default():
    schema = strawberry.Schema(query=QueryWithInstanceDefaults)

    result = schema.execute_sync("{ options }")

    assert not result.errors
    assert result.data == {
        "options": (
            "Options(color=<Color.RED: 'red'>, "
            "pagination=Pagination(limit=10, offset=1), label=Some(None), note=None)"
        )
    }


def test_input_instance_as_argument_default_is_fresh_per_execution():
    schema = strawberry.Schema(query=QueryWithInstanceDefaults)

    first = schema.execute_sync("{ options }")
    second = schema.execute_sync("{ options }")

    assert not first.errors
    assert not second.errors
    assert first.data == second.data


def test_input_instance_as_field_default_applies_when_field_is_omitted():
    schema = strawberry.Schema(query=QueryWithInstanceDefaults)

    result = schema.execute_sync("{ requiredOptions(options: { color: BLUE }) }")

    assert not result.errors
    assert result.data == {
        "requiredOptions": (
            "Options(color=<Color.BLUE: 'blue'>, "
            "pagination=Pagination(limit=10, offset=0), label=None, note=None)"
        )
    }


def test_input_instance_as_nullable_argument_default():
    schema = strawberry.Schema(query=QueryWithNestedInstanceDefaults)

    result = schema.execute_sync("{ nullableOptions }")

    assert not result.errors
    assert result.data == {
        "nullableOptions": (
            "Options(color=<Color.BLUE: 'blue'>, "
            "pagination=Pagination(limit=10, offset=0), label=None, note=None)"
        )
    }


def test_input_instances_nested_in_list_and_dict_defaults():
    schema = strawberry.Schema(query=QueryWithNestedInstanceDefaults)

    result = schema.execute_sync("{ pages optionsFromDict renamed }")

    assert not result.errors
    assert result.data == {
        "pages": "[Pagination(limit=1, offset=0)]",
        "optionsFromDict": (
            "Options(color=<Color.RED: 'red'>, "
            "pagination=Pagination(limit=2, offset=0), label=None, note=None)"
        ),
        "renamed": "Renamed(some_value=5)",
    }


def test_input_instance_default_is_exposed_in_introspection():
    schema = strawberry.Schema(query=QueryWithInstanceDefaults)

    result = schema.execute_sync(
        """
        {
          query: __type(name: "QueryWithInstanceDefaults") {
            fields { name args { name defaultValue } }
          }
          options: __type(name: "Options") {
            inputFields { name defaultValue }
          }
        }
        """
    )

    assert not result.errors
    assert result.data == {
        "query": {
            "fields": [
                {
                    "name": "options",
                    "args": [
                        {
                            "name": "options",
                            "defaultValue": (
                                "{color: RED, pagination: {limit: 10, offset: 0}, "
                                "label: null, note: null}"
                                if IS_GQL_32
                                else "{ color: RED, pagination: { limit: 10, offset: 0 }, "
                                "label: null, note: null }"
                            ),
                        }
                    ],
                },
                {
                    "name": "requiredOptions",
                    "args": [{"name": "options", "defaultValue": None}],
                },
            ]
        },
        "options": {
            "inputFields": [
                {"name": "color", "defaultValue": None},
                {
                    "name": "pagination",
                    "defaultValue": (
                        "{limit: 10, offset: 0}"
                        if IS_GQL_32
                        else "{ limit: 10, offset: 0 }"
                    ),
                },
                {"name": "label", "defaultValue": None},
                {"name": "note", "defaultValue": "null"},
            ]
        },
    }


def test_input_instance_default_is_printed_in_schema():
    schema = strawberry.Schema(query=QueryWithInstanceDefaults)

    default = (
        "{color: RED, pagination: {limit: 10, offset: 0}, label: null}"
        if IS_GQL_32
        else "{ color: RED, pagination: { limit: 10, offset: 0 }, label: null }"
    )
    expected = f"""
    type QueryWithInstanceDefaults {{
      options(options: Options! = {default}): String!
      requiredOptions(options: Options!): String!
    }}
    """

    assert textwrap.dedent(expected).strip() in print_schema(schema)
