import re
import textwrap
from unittest.mock import Mock, call

import pytest

import strawberry
from strawberry.dataloader import DataLoader
from strawberry.exceptions import InvalidSuperclassInterfaceError
from strawberry.printer import print_schema
from strawberry.schema import schema_converter
from strawberry.types import Info
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


def test_input_clean_runs_after_coercion_and_before_resolver():
    hooks = Mock()

    @strawberry.input
    class ChildInput:
        value: str

        def clean(self, info: Info) -> None:
            hooks.child_clean(info.context["prefix"], self.value)
            self.value = self.value.upper()

    @strawberry.input
    class ParentInput:
        child: ChildInput
        children: list[ChildInput]

        def clean(self, info: Info) -> None:
            hooks.parent_clean(self.child.value, self.children[0].value)

    @strawberry.type
    class Query:
        @strawberry.field
        def values(self, data: ParentInput) -> str:
            hooks.resolver(data.child.value, data.children[0].value)
            return f"{data.child.value},{data.children[0].value}"

    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync(
        """
        query {
            values(data: { child: { value: "one" }, children: [{ value: "two" }] })
        }
        """,
        context_value={"prefix": "request"},
    )

    assert result.errors is None
    assert result.data == {"values": "ONE,TWO"}
    assert hooks.mock_calls == [
        call.child_clean("request", "one"),
        call.child_clean("request", "two"),
        call.parent_clean("ONE", "TWO"),
        call.resolver("ONE", "TWO"),
    ]


def test_input_without_clean_skips_input_clean_traversal(
    monkeypatch: pytest.MonkeyPatch,
):
    run_input_clean_methods = Mock(wraps=schema_converter.run_input_clean_methods)
    monkeypatch.setattr(
        schema_converter, "run_input_clean_methods", run_input_clean_methods
    )

    @strawberry.input
    class Input:
        value: str

    @strawberry.type
    class Query:
        @strawberry.field
        def value(self, data: Input) -> str:
            return data.value

    schema = strawberry.Schema(query=Query)
    result = schema.execute_sync('query { value(data: { value: "project" }) }')

    assert result.errors is None
    assert result.data == {"value": "project"}
    run_input_clean_methods.assert_not_called()


async def test_input_async_clean_runs_before_containing_clean_and_resolver():
    hooks = Mock()

    @strawberry.input
    class ChildInput:
        value: str

        async def clean(self, info: Info) -> None:
            hooks.child_clean(info.context["suffix"], self.value)
            self.value += info.context["suffix"]

    @strawberry.input
    class ParentInput:
        child: ChildInput

        def clean(self, info: Info) -> None:
            hooks.parent_clean(self.child.value)
            self.child.value = self.child.value.upper()

    @strawberry.type
    class Query:
        @strawberry.field
        def value(self, data: ParentInput) -> str:
            hooks.resolver(data.child.value)
            return data.child.value

    schema = strawberry.Schema(query=Query)

    result = await schema.execute(
        'query { value(data: { child: { value: "project" } }) }',
        context_value={"suffix": "-1"},
    )

    assert result.errors is None
    assert result.data == {"value": "PROJECT-1"}
    assert hooks.mock_calls == [
        call.child_clean("-1", "project"),
        call.parent_clean("project-1"),
        call.resolver("PROJECT-1"),
    ]


async def test_input_async_clean_runs_after_contained_clean():
    hooks = Mock()

    @strawberry.input
    class ChildInput:
        value: str

        def clean(self, info: Info) -> None:
            hooks.child_clean(self.value)
            self.value = self.value.upper()

    @strawberry.input
    class ParentInput:
        child: ChildInput

        async def clean(self, info: Info) -> None:
            hooks.parent_clean(self.child.value)
            self.child.value += info.context["suffix"]

    @strawberry.type
    class Query:
        @strawberry.field
        def value(self, data: ParentInput) -> str:
            hooks.resolver(data.child.value)
            return data.child.value

    schema = strawberry.Schema(query=Query)

    result = await schema.execute(
        'query { value(data: { child: { value: "project" } }) }',
        context_value={"suffix": "-1"},
    )

    assert result.errors is None
    assert result.data == {"value": "PROJECT-1"}
    assert hooks.mock_calls == [
        call.child_clean("project"),
        call.parent_clean("PROJECT"),
        call.resolver("PROJECT-1"),
    ]


def test_input_clean_error_prevents_resolver_execution():
    resolver = Mock()

    @strawberry.input
    class Input:
        value: str

        def clean(self, info: Info) -> None:
            raise ValueError("Invalid input")

    @strawberry.type
    class Query:
        @strawberry.field
        def value(self, data: Input) -> str:
            resolver(data)
            return data.value

    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync('query { value(data: { value: "project" }) }')

    assert result.data is None
    assert result.errors is not None
    assert result.errors[0].message == "Invalid input"
    resolver.assert_not_called()


async def test_input_clean_can_use_dataloader():
    async def load_projects(keys: list[str]) -> list[str]:
        return [f"project:{key}" for key in keys]

    project_loader = Mock(side_effect=load_projects)

    @strawberry.input
    class ProjectInput:
        project_id: strawberry.ID
        project: strawberry.Private[str | None] = None

        async def clean(self, info: Info) -> None:
            self.project = await info.context["project_loader"].load(self.project_id)

    @strawberry.type
    class Query:
        @strawberry.field
        def project(self, data: ProjectInput) -> str:
            assert data.project is not None
            return data.project

    schema = strawberry.Schema(query=Query)
    loader = DataLoader(load_fn=project_loader)

    result = await schema.execute(
        'query { project(data: { projectId: "one" }) }',
        context_value={"project_loader": loader},
    )

    assert result.errors is None
    assert result.data == {"project": "project:one"}
    project_loader.assert_called_once_with(["one"])


async def test_input_clean_preserves_mutation_field_order():
    hooks = Mock()

    @strawberry.input
    class Input:
        value: str

        async def clean(self, info: Info) -> None:
            hooks.clean(self.value)

    @strawberry.type
    class Query:
        value: str = "query"

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        async def first(self, data: Input) -> str:
            hooks.resolver("first", data.value)
            return data.value

        @strawberry.mutation
        async def second(self, data: Input) -> str:
            hooks.resolver("second", data.value)
            return data.value

    schema = strawberry.Schema(query=Query, mutation=Mutation)

    result = await schema.execute(
        'mutation { first(data: { value: "one" }) second(data: { value: "two" }) }'
    )

    assert result.errors is None
    assert result.data == {"first": "one", "second": "two"}
    assert hooks.mock_calls == [
        call.clean("one"),
        call.resolver("first", "one"),
        call.clean("two"),
        call.resolver("second", "two"),
    ]
