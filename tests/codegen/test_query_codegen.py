# # TODO:
# # 2. test fragments
# # 3. test variables
# # 7. test input objects
# # 13. test mutations (raise?)
# # 14. test subscriptions (raise)

from pathlib import Path
from typing import Type

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
    "plugin_class,plugin_name,extension",
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
    generator = QueryCodegen(schema, plugins=[plugin_class()])

    result = generator.run(query.read_text())

    code = result.to_string()

    snapshot.snapshot_dir = HERE / "snapshots" / plugin_name
    snapshot.assert_match(code, f"{query.with_suffix('').stem}.{extension}")


def test_codegen_fails_if_no_operation_name(schema):
    generator = QueryCodegen(schema, plugins=[PythonPlugin()])

    with pytest.raises(NoOperationNameProvidedError):
        generator.run("query { hello }")


def test_codegen_fails_if_no_operation(schema):
    generator = QueryCodegen(schema, plugins=[PythonPlugin()])

    with pytest.raises(NoOperationProvidedError):
        generator.run("type X { hello: String }")


def test_fails_with_multiple_operations(schema):
    generator = QueryCodegen(schema, plugins=[PythonPlugin()])

    with pytest.raises(MultipleOperationsProvidedError):
        generator.run("query { hello } query { world }")
