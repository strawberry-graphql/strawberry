import dataclasses
import json
from typing import Annotated, Optional

import pytest

import strawberry
from strawberry.types.base import StrawberryOptional
from strawberry.types.nodes import FragmentSpread, InlineFragment, SelectedField
from strawberry.types.unset import UNSET


def test_info_has_the_correct_shape():
    my_context = "123"
    root_value = "ABC"

    @strawberry.type
    class Result:
        field_name: str
        python_name: str
        selected_field: str
        operation: str
        path: str
        variable_values: str
        context_equal: bool
        root_equal: bool
        return_type: str
        schema_print: str

    @strawberry.type
    class Query:
        @strawberry.field
        def hello_world(self, info: strawberry.Info[str, str]) -> Result:
            return Result(
                path="".join([str(p) for p in info.path.as_list()]),
                operation=str(info.operation),
                field_name=info.field_name,
                python_name=info.python_name,
                selected_field=json.dumps(dataclasses.asdict(*info.selected_fields)),
                variable_values=str(info.variable_values),
                context_equal=info.context == my_context,
                root_equal=info.root_value == root_value,
                return_type=str(info.return_type),
                schema_print=info.schema.as_str(),
            )

    schema = strawberry.Schema(query=Query)

    query = """{
        helloWorld {
            fieldName
            pythonName
            selectedField
            contextEqual
            operation
            path
            rootEqual
            variableValues
            returnType
            schemaPrint
        }
    }"""

    result = schema.execute_sync(query, context_value=my_context, root_value=root_value)

    assert not result.errors
    assert result.data
    info = result.data["helloWorld"]
    assert info.pop("operation").startswith("OperationDefinitionNode at")
    field = json.loads(info.pop("selectedField"))
    selections = {selection["name"] for selection in field.pop("selections")}
    assert selections == {
        "selectedField",
        "path",
        "rootEqual",
        "operation",
        "contextEqual",
        "variableValues",
        "returnType",
        "fieldName",
        "pythonName",
        "schemaPrint",
    }
    assert field == {
        "name": "helloWorld",
        "directives": {},
        "alias": None,
        "arguments": {},
    }
    assert info == {
        "fieldName": "helloWorld",
        "pythonName": "hello_world",
        "path": "helloWorld",
        "contextEqual": True,
        "rootEqual": True,
        "variableValues": "{}",
        "returnType": "<class 'tests.schema.test_info.test_info_has_the_correct_shape.<locals>.Result'>",
        "schemaPrint": schema.as_str(),
    }


def test_info_field_fragments():
    @strawberry.type
    class Result:
        ok: bool

    selected_fields = None

    @strawberry.type
    class Query:
        @strawberry.field
        def hello(self, info: strawberry.Info[str, str]) -> Result:
            nonlocal selected_fields
            selected_fields = info.selected_fields
            return Result(ok=True)

    schema = strawberry.Schema(query=Query)
    query = """{
        hello {
            ... on Result {
                k: ok @include(if: true)
            }
            ...frag
        }
    }

    fragment frag on Result {
        ok
    }
    """
    result = schema.execute_sync(query)

    assert not result.errors
    assert selected_fields == [
        SelectedField(
            name="hello",
            directives={},
            alias=None,
            arguments={},
            selections=[
                InlineFragment(
                    type_condition="Result",
                    directives={},
                    selections=[
                        SelectedField(
                            name="ok",
                            alias="k",
                            arguments={},
                            directives={
                                "include": {
                                    "if": True,
                                },
                            },
                            selections=[],
                        )
                    ],
                ),
                FragmentSpread(
                    name="frag",
                    directives={},
                    type_condition="Result",
                    selections=[
                        SelectedField(
                            name="ok",
                            directives={},
                            arguments={},
                            selections=[],
                        )
                    ],
                ),
            ],
        )
    ]


def test_info_arguments():
    @strawberry.input
    class TestInput:
        name: str
        age: Optional[int] = UNSET

    selected_fields = None

    @strawberry.type
    class Query:
        @strawberry.field
        def test_arg(
            self,
            info: strawberry.Info[str, str],
            input: TestInput,
            another_arg: bool = True,
        ) -> str:
            nonlocal selected_fields
            selected_fields = info.selected_fields
            return "Hi"

    schema = strawberry.Schema(query=Query)

    query = """{
        testArg(input: {name: "hi"})
    }
    """
    result = schema.execute_sync(query)

    assert not result.errors
    assert selected_fields == [
        SelectedField(
            name="testArg",
            directives={},
            arguments={
                "input": {
                    "name": "hi",
                },
            },
            selections=[],
        )
    ]

    query = """query TestQuery($input: TestInput!) {
        testArg(input: $input)
    }
    """
    result = schema.execute_sync(
        query,
        variable_values={
            "input": {
                "name": "hi",
                "age": 10,
            },
        },
    )
    assert not result.errors
    assert selected_fields == [
        SelectedField(
            name="testArg",
            directives={},
            arguments={
                "input": {
                    "name": "hi",
                    "age": 10,
                },
            },
            selections=[],
        )
    ]


def test_info_selected_fields_undefined_variable():
    @strawberry.type
    class Result:
        ok: bool

    selected_fields = None

    @strawberry.type
    class Query:
        @strawberry.field
        def hello(
            self, info: strawberry.Info[str, str], optional_input: Optional[str] = "hi"
        ) -> Result:
            nonlocal selected_fields
            selected_fields = info.selected_fields
            return Result(ok=True)

    schema = strawberry.Schema(query=Query)
    query = """
    query MyQuery($optionalInput: String) {
        hello(optionalInput: $optionalInput) {
            ok
        }
    }
    """
    result = schema.execute_sync(query, variable_values={})

    assert not result.errors
    assert selected_fields == [
        SelectedField(
            name="hello",
            directives={},
            alias=None,
            arguments={
                "optionalInput": None,
            },
            selections=[
                SelectedField(
                    name="ok",
                    alias=None,
                    arguments={},
                    directives={},
                    selections=[],
                )
            ],
        )
    ]


@pytest.mark.parametrize(
    ("return_type", "return_value"),
    [
        (str, "text"),
        (list[str], ["text"]),
        (Optional[list[int]], None),
    ],
)
def test_return_type_from_resolver(return_type, return_value):
    @strawberry.type
    class Query:
        @strawberry.field
        def field(self, info: strawberry.Info) -> return_type:
            assert info.return_type == return_type
            return return_value

    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync("{ field }")

    assert not result.errors
    assert result.data
    assert result.data["field"] == return_value


def test_return_type_from_field():
    def resolver(info: strawberry.Info):
        assert info.return_type is int
        return 0

    @strawberry.type
    class Query:
        field: int = strawberry.field(resolver=resolver)

    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync("{ field }")

    assert not result.errors
    assert result.data
    assert result.data["field"] == 0


def test_field_nodes_deprecation():
    def resolver(info: strawberry.Info):
        info.field_nodes
        return 0

    @strawberry.type
    class Query:
        field: int = strawberry.field(resolver=resolver)

    schema = strawberry.Schema(query=Query)

    with pytest.deprecated_call():
        result = schema.execute_sync("{ field }")

    assert not result.errors
    assert result.data
    assert result.data["field"] == 0


def test_get_argument_defintion_helper():
    @strawberry.input
    class TestInput:
        foo: str

    arg_1_def = None
    arg_2_def = None
    missing_arg_def = None

    @strawberry.type
    class Query:
        @strawberry.field
        def field(
            self,
            info: strawberry.Info,
            arg_1: Annotated[str, strawberry.argument(description="Some description")],
            arg_2: Optional[TestInput] = None,
        ) -> str:
            nonlocal arg_1_def, arg_2_def, missing_arg_def
            arg_1_def = info.get_argument_definition("arg_1")
            arg_2_def = info.get_argument_definition("arg_2")
            missing_arg_def = info.get_argument_definition("missing_arg_def")

            return "bar"

    schema = strawberry.Schema(query=Query)
    result = schema.execute_sync('{ field(arg1: "hi") }')

    assert not result.errors
    assert arg_1_def
    assert arg_1_def.type is str
    assert arg_1_def.python_name == "arg_1"
    assert arg_1_def.description == "Some description"

    assert arg_2_def
    assert arg_2_def.python_name == "arg_2"
    assert arg_2_def.default is None
    assert isinstance(arg_2_def.type, StrawberryOptional)
    assert arg_2_def.type.of_type is TestInput

    assert missing_arg_def is None
