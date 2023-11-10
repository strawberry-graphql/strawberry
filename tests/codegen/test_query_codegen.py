# - 1. test fragments
# - 2. test variables
# - 3. test input objects
# - 4. test mutations (raise?)
# - 5. test subscriptions (raise)

from pathlib import Path
from typing import Type

import pytest
from graphql.utilities import build_schema
from pytest_snapshot.plugin import Snapshot

from strawberry.codegen import QueryCodegen, QueryCodegenPlugin
from strawberry.codegen.exceptions import (
    MultipleOperationsProvidedError,
    NoOperationNameProvidedError,
    NoOperationProvidedError,
)
from strawberry.codegen.plugins.python import PythonPlugin
from strawberry.codegen.plugins.typescript import TypeScriptPlugin
from strawberry.codegen.schema_adapter import GraphQLSchemaWrapper
from strawberry.printer import print_schema

HERE = Path(__file__).parent
QUERIES = list(HERE.glob("queries/*.graphql"))


@pytest.mark.parametrize(
    ("plugin_class", "plugin_name", "extension"),
    [
        (PythonPlugin, "python", "py"),
        (TypeScriptPlugin, "typescript", "ts"),
    ],
    ids=["python", "typescript"],
)
@pytest.mark.parametrize("query", QUERIES, ids=[x.name for x in QUERIES])
def test_codegen(
    query: Path,
    plugin_class: Type[QueryCodegenPlugin],
    plugin_name: str,
    extension: str,
    snapshot: Snapshot,
    schema,
):
    generator = QueryCodegen(schema, plugins=[plugin_class(query)])

    result = generator.run(query.read_text())

    code = result.to_string()

    snapshot.snapshot_dir = HERE / "snapshots" / plugin_name
    snapshot.assert_match(code, f"{query.with_suffix('').stem}.{extension}")


@pytest.mark.parametrize(
    ("plugin_class", "plugin_name", "extension"),
    [
        (PythonPlugin, "python", "py"),
        (TypeScriptPlugin, "typescript", "ts"),
    ],
    ids=["python", "typescript"],
)
@pytest.mark.parametrize("query", QUERIES, ids=[x.name for x in QUERIES])
def test_codegen_from_schema_file(
    query: Path,
    plugin_class: Type[QueryCodegenPlugin],
    plugin_name: str,
    extension: str,
    snapshot: Snapshot,
    schema,
):
    schema_text = print_schema(schema)
    schema_wrapper = GraphQLSchemaWrapper(build_schema(schema_text))

    skip_snapshot_test = False
    if query.name == "custom_scalar.graphql":
        # The default plugins don't support custom types built this way
        # (because it doesn't know the python on Typscript types).
        # However, the query generator should still be able to handle the custom
        # types and user-custom plugins could still do something legitimate here.
        plugin = QueryCodegenPlugin(query)
        skip_snapshot_test = True
    else:
        plugin = plugin_class(query)

    generator = QueryCodegen(schema_wrapper, plugins=[plugin])

    result = generator.run(query.read_text())

    code = result.to_string()

    if skip_snapshot_test:
        return

    snapshot.snapshot_dir = HERE / "snapshots" / "from_graphql_schema" / plugin_name
    snapshot.assert_match(code, f"{query.with_suffix('').stem}.{extension}")


def test_codegen_fails_if_no_operation_name(schema, tmp_path):
    query = tmp_path / "query.graphql"
    data = "query { hello }"
    with query.open("w") as f:
        f.write(data)

    generator = QueryCodegen(schema, plugins=[PythonPlugin(query)])

    with pytest.raises(NoOperationNameProvidedError):
        generator.run(data)


def test_codegen_fails_if_no_operation(schema, tmp_path):
    query = tmp_path / "query.graphql"
    data = "type X { hello: String }"
    with query.open("w") as f:
        f.write(data)

    generator = QueryCodegen(schema, plugins=[PythonPlugin(query)])

    with pytest.raises(NoOperationProvidedError):
        generator.run(data)


def test_fails_with_multiple_operations(schema, tmp_path):
    query = tmp_path / "query.graphql"
    data = "query { hello } query { world }"
    with query.open("w") as f:
        f.write(data)

    generator = QueryCodegen(schema, plugins=[PythonPlugin(query)])

    with pytest.raises(MultipleOperationsProvidedError):
        generator.run(data)
