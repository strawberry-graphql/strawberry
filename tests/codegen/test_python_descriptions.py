import ast
import enum
from pathlib import Path

import strawberry
from strawberry.codegen import QueryCodegen
from strawberry.codegen.plugins.python import PythonPlugin
from strawberry.codegen.plugins.typescript import TypeScriptPlugin


def attribute_docstring(cls: ast.ClassDef, attribute: str) -> str:
    for index, node in enumerate(cls.body):
        if (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == attribute
        ):
            following = cls.body[index + 1]
            assert isinstance(following, ast.Expr)
            assert isinstance(following.value, ast.Constant)
            assert isinstance(following.value.value, str)
            return following.value.value
    raise AssertionError(f"Missing field: {attribute}")


def test_python_codegen_preserves_schema_descriptions_and_escapes_strings():
    input_description = 'Input with "quotes", backslash \\ and\na newline.'
    field_description = 'Title with """triple quotes""" and \\slashes.'

    @strawberry.input(description=input_description)
    class Input:
        title: str = strawberry.field(description=field_description)

    @strawberry.type(description="An output type.")
    class Item:
        title: str = strawberry.field(description="The item's title.")

    @strawberry.type
    class Query:
        @strawberry.field(description="Find an item.")
        def item(self, data: Input) -> Item:
            return Item(title=data.title)

    schema = strawberry.Schema(query=Query)
    query = "query Example($data: Input!) { item(data: $data) { alias: title } }"
    generated = QueryCodegen(schema, [PythonPlugin(Path("example.graphql"))]).run(query)
    code = generated.to_string()

    module = ast.parse(code)
    classes = {
        node.name: node for node in module.body if isinstance(node, ast.ClassDef)
    }
    assert ast.get_docstring(classes["Input"]) == input_description
    assert ast.get_docstring(classes["ExampleResultItem"]) == "An output type."

    assert attribute_docstring(classes["Input"], "title") == field_description
    assert (
        attribute_docstring(classes["ExampleResultItem"], "alias")
        == "The item's title."
    )
    assert attribute_docstring(classes["ExampleResult"], "item") == "Find an item."
    namespace: dict[str, object] = {}
    exec(compile(code, "example.py", "exec"), namespace)  # noqa: S102
    assert namespace["Input"].__doc__ == input_description


def test_typescript_codegen_does_not_emit_python_descriptions():
    @strawberry.type(description="An object description")
    class Query:
        message: str = strawberry.field(description="A field description")

    generated = QueryCodegen(
        strawberry.Schema(query=Query), [TypeScriptPlugin(Path("query.graphql"))]
    ).run("query Example { message }")
    assert "An object description" not in generated.to_string()
    assert "A field description" not in generated.to_string()


def test_inline_fragment_uses_concrete_type_description():
    @strawberry.interface
    class Node:
        name: str

    @strawberry.type(description="A concrete user.")
    class User(Node):
        age: int = strawberry.field(description="User age.")

    @strawberry.type
    class Query:
        node: Node

    schema = strawberry.Schema(query=Query, types=[User])
    query = "query Example { node { __typename ... on User { age } } }"
    code = QueryCodegen(schema, [PythonPlugin(Path("query.graphql"))]).run(query)
    classes = [
        node
        for node in ast.parse(code.to_string()).body
        if isinstance(node, ast.ClassDef)
    ]
    user = next(node for node in classes if node.name.endswith("User"))
    assert ast.get_docstring(user) == "A concrete user."
    assert attribute_docstring(user, "age") == "User age."


def test_python_codegen_preserves_enum_description():
    description = 'Status with "quotes", a backslash \\ and\na newline.'

    @strawberry.enum(description=description)
    class Status(enum.Enum):
        ACTIVE = "active"
        INACTIVE = "inactive"

    @strawberry.type
    class Query:
        status: Status

    schema = strawberry.Schema(query=Query)
    query = "query Example { status }"
    path = Path("query.graphql")
    python_code = QueryCodegen(schema, [PythonPlugin(path)]).run(query).to_string()
    enum_class = next(
        node
        for node in ast.parse(python_code).body
        if isinstance(node, ast.ClassDef) and node.name == "Status"
    )
    assert ast.get_docstring(enum_class) == description
    namespace: dict[str, object] = {}
    exec(compile(python_code, "query.py", "exec"), namespace)  # noqa: S102
    assert namespace["Status"].__doc__ == description
    typescript_code = (
        QueryCodegen(schema, [TypeScriptPlugin(path)]).run(query).to_string()
    )
    assert description not in typescript_code
