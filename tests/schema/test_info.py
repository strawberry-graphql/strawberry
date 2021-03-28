import strawberry
from strawberry.types import Info


def test_info_has_the_correct_shape():
    my_context = "123"
    root_value = "ABC"

    @strawberry.type
    class Result:
        field_name: str
        field_nodes: str
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
                field_nodes=str(info.field_nodes),
                variable_values=str(info.variable_values),
                context_equal=info.context == my_context,
                root_equal=info.root_value == root_value,
                return_type=str(info.return_type),
            )

    schema = strawberry.Schema(query=Query)

    query = """{
        hello {
            fieldName
            fieldNodes
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
    assert info.pop("fieldNodes").startswith("[FieldNode at")
    assert info == {
        # TODO: abstract this (in future)
        "fieldName": "hello",
        "path": "hello",
        "contextEqual": True,
        "rootEqual": True,
        "variableValues": "{}",
        "returnType": "<class 'tests.schema.test_info.test_info_has_the_correct_shape.<locals>.Result'>",  # noqa
    }
