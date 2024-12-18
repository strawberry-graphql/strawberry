# - 1. test fragments
# - 2. test variables
# - 3. test input objects
# - 4. test mutations (raise?)
# - 5. test subscriptions (raise)

from pathlib import Path

import pytest
from pytest_snapshot.plugin import Snapshot

from strawberry.codegen import QueryCodegen, QueryCodegenPlugin
from strawberry.codegen.exceptions import (
    MultipleOperationsProvidedError,
    NoOperationNameProvidedError,
    NoOperationProvidedError,
)
from strawberry.codegen.plugins.python import PythonPlugin
from strawberry.codegen.plugins.typescript import TypeScriptPlugin

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
    plugin_class: type[QueryCodegenPlugin],
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
