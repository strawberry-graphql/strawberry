import dataclasses
import json
from typing import List, Optional

import pytest

import strawberry
from strawberry.types import Info
from strawberry.types.nodes import SelectedField, InlineFragment, FragmentSpread


def test_info_has_the_correct_shape():
    my_context = "123"
    root_value = "ABC"

    @strawberry.type
    class Result:
        field_name: str
        selected_field: str
        operation: str
        path: str
        variable_values: str
        context_equal: bool
        root_equal: bool
        return_type: str

    @strawberry.type
    class Query:
        @strawberry.field
        def hello(self, info: Info[str, str]) -> Result:
            return Result(
                path="".join([str(p) for p in info.path.as_list()]),
                operation=str(info.operation),
                field_name=info.field_name,
                selected_field=json.dumps(dataclasses.asdict(*info.selected_fields)),
                variable_values=str(info.variable_values),
                context_equal=info.context == my_context,
                root_equal=info.root_value == root_value,
                return_type=str(info.return_type),
            )

    schema = strawberry.Schema(query=Query)

    query = """{
        hello {
            fieldName
            selectedField
            contextEqual
            operation
            path
            rootEqual
            variableValues
            returnType
        }
    }"""

    result = schema.execute_sync(query, context_value=my_context, root_value=root_value)

    assert not result.errors
    info = result.data["hello"]
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
    }
    assert field == {"name": "hello", "directives": {}, "alias": None, "arguments": {}}
    assert info == {
        "fieldName": "hello",
        "path": "hello",
        "contextEqual": True,
        "rootEqual": True,
        "variableValues": "{}",
        "returnType": "<class 'tests.schema.test_info.test_info_has_the_correct_shape.<locals>.Result'>",  # noqa
    }


def test_info_field_fragments():
    @strawberry.type
    class Result:
        ok: bool

    selected_fields = None

    @strawberry.type
    class Query:
        @strawberry.field
        def hello(self, info: Info[str, str]) -> Result:
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
                    ]
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
                )
            ],
        )
    ]


@pytest.mark.parametrize(
    "return_type,return_value",
    [
        (str, "text"),
        (List[str], ["text"]),
        (Optional[List[int]], None),
    ],
)
def test_return_type_from_resolver(return_type, return_value):
    @strawberry.type
    class Query:
        @strawberry.field
        def field(self, info: Info) -> return_type:
            assert info.return_type == return_type
            return return_value

    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync("{ field }")

    assert not result.errors
    assert result.data["field"] == return_value


def test_return_type_from_field():
    def resolver(info):
        assert info.return_type == int
        return 0

    @strawberry.type
    class Query:
        field: int = strawberry.field(resolver=resolver)

    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync("{ field }")

    assert not result.errors
    assert result.data["field"] == 0


def test_field_nodes_deprecation():
    def resolver(info):
        info.field_nodes
        return 0

    @strawberry.type
    class Query:
        field: int = strawberry.field(resolver=resolver)

    schema = strawberry.Schema(query=Query)

    with pytest.deprecated_call():
        result = schema.execute_sync("{ field }")

    assert not result.errors
    assert result.data["field"] == 0
