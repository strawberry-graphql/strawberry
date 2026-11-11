# - 1. test fragments
# - 2. test variables
# - 3. test input objects
# - 4. test mutations (raise?)
# - 5. test subscriptions (raise)

from pathlib import Path

import pytest
from graphql import GraphQLError
from pytest_snapshot.plugin import Snapshot

from strawberry.codegen import QueryCodegen, QueryCodegenPlugin
from strawberry.codegen.exceptions import (
    InvalidOperationError,
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
def test_codegen(  # noqa: PLR0917
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


@pytest.mark.parametrize("plugin_class", [PythonPlugin, TypeScriptPlugin])
def test_nested_fragment_spread_does_not_depend_on_definition_order(
    plugin_class: type[QueryCodegenPlugin], schema, tmp_path
):
    operation = "query OperationName { listLife { ...LifeFields } }"
    life_fields = (
        "fragment LifeFields on PersonAnimalLifeContainer"
        " { items1 { ...PersonFields } }"
    )
    person_fields = "fragment PersonFields on Person { name age }"
    query = tmp_path / "query.graphql"

    def generate(document: str) -> str:
        generator = QueryCodegen(schema, plugins=[plugin_class(query)])
        return generator.run(document).to_string()

    inner_first = generate(f"{operation}\n{person_fields}\n{life_fields}")
    inner_last = generate(f"{operation}\n{life_fields}\n{person_fields}")

    assert inner_last == inner_first
    assert "PersonFields" in inner_last


def test_fails_with_field_not_in_schema(schema, tmp_path):
    query = tmp_path / "query.graphql"
    data = "query OperationName {\n  integr\n}"
    with query.open("w") as f:
        f.write(data)

    generator = QueryCodegen(schema, plugins=[PythonPlugin(query)])

    with pytest.raises(InvalidOperationError) as exc_info:
        generator.run(data)

    assert exc_info.value.messages == [
        "2:3: Cannot query field 'integr' on type 'Query'. Did you mean 'integer'?"
    ]


def test_fails_with_unknown_fragment(schema, tmp_path):
    query = tmp_path / "query.graphql"
    data = "query OperationName { ...Missing }"
    with query.open("w") as f:
        f.write(data)

    generator = QueryCodegen(schema, plugins=[PythonPlugin(query)])

    with pytest.raises(InvalidOperationError, match="Unknown fragment 'Missing'"):
        generator.run(data)


def test_invalid_operation_error_without_location():
    error = InvalidOperationError([GraphQLError("Something is wrong.")])

    assert error.messages == ["Something is wrong."]
    assert str(error) == "Something is wrong."
