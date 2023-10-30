# - 1. test fragments
# - 2. test variables
# - 3. test input objects
# - 4. test mutations (raise?)
# - 5. test subscriptions (raise)

import dataclasses
import textwrap
from pathlib import Path
from typing import Dict, List, Optional, Type

import pytest
from graphql.language.ast import FieldNode, InlineFragmentNode, OperationDefinitionNode
from pytest_snapshot.plugin import Snapshot

from strawberry.codegen import CodegenFile, QueryCodegen, QueryCodegenPlugin
from strawberry.codegen.exceptions import (
    MultipleOperationsProvidedError,
    NoOperationNameProvidedError,
    NoOperationProvidedError,
)
from strawberry.codegen.plugins.python import PythonPlugin
from strawberry.codegen.plugins.typescript import TypeScriptPlugin
from strawberry.codegen.types import GraphQLOperation, GraphQLType
from strawberry.types.types import StrawberryObjectDefinition

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


def test_codegen_augments_class_and_fields_with_source_objects(
    schema, conftest_globals, tmp_path
):
    class CustomPythonPlugin(PythonPlugin):
        types_by_name: Optional[Dict[str, GraphQLType]] = None

        def generate_code(
            self, types: List[GraphQLType], operation: GraphQLOperation
        ) -> List[CodegenFile]:
            self.types_by_name = {t.name: t for t in types}
            return super().generate_code(types, operation)

    query = tmp_path / "query.graphql"
    data = textwrap.dedent(
        """\
        query Operation {
            getPersonOrAnimal {
                ... on Person {
                    age
                }
            }
        }
        """
    )
    with query.open("w") as f:
        f.write(data)

    plugin = CustomPythonPlugin(query)
    generator = QueryCodegen(schema, plugins=[plugin])
    generator.run(data)

    assert plugin.types_by_name is not None
    types_by_name = plugin.types_by_name

    assert set(types_by_name) == {
        "Int",
        "OperationResultGetPersonOrAnimalPerson",
        "OperationResult",
    }

    person_type = types_by_name["OperationResultGetPersonOrAnimalPerson"]
    assert isinstance(person_type.graphql_type, StrawberryObjectDefinition)
    assert person_type.graphql_type.origin is conftest_globals["Person"]

    assert isinstance(person_type.graphql_node, InlineFragmentNode)

    name_field = next((fld for fld in person_type.fields if fld.name == "age"), None)

    assert name_field is not None
    # Check that we got the `dataclasses.Field` from the upstream ``Person`` type.
    assert isinstance(name_field.strawberry_field, dataclasses.Field)
    assert name_field.strawberry_field.default == 7
    # Check that we got the GraphQL AST node that defined this field in the graphql AST.
    assert isinstance(name_field.graphql_node, FieldNode)
    assert name_field.graphql_node.name.value == "age"

    result_type = types_by_name["OperationResult"]
    assert result_type.graphql_type is not None
    assert result_type.graphql_type.origin is conftest_globals["Query"]
    assert isinstance(result_type.graphql_node, OperationDefinitionNode)


def test_codegen_augments_class_and_fields_with_source_objects_when_inputs(
    schema, conftest_globals, tmp_path
):
    class CustomPythonPlugin(PythonPlugin):
        types_by_name: Optional[Dict[str, GraphQLType]] = None

        def generate_code(
            self, types: List[GraphQLType], operation: GraphQLOperation
        ) -> List[CodegenFile]:
            self.types_by_name = {t.name: t for t in types}
            return super().generate_code(types, operation)

    query = tmp_path / "query.graphql"
    data = textwrap.dedent(
        """\
        query Operation($name: String!, $age: Int!) {
            getPersonWithInputs(name: $name, age: $age) {
                name
                age
            }
        }
        """
    )
    with query.open("w") as f:
        f.write(data)

    plugin = CustomPythonPlugin(query)
    generator = QueryCodegen(schema, plugins=[plugin])
    generator.run(data)

    assert plugin.types_by_name is not None
    types_by_name = plugin.types_by_name

    assert set(types_by_name) == {
        "Int",
        "String",
        "OperationResult",
        "OperationResultGetPersonWithInputs",
        "OperationVariables",
    }

    # The special "Result" and "Variables" types hold references to the
    # overarching graphql Query/Mutation/Subscription types.
    query_type = types_by_name["OperationResult"]
    assert isinstance(query_type.graphql_type, StrawberryObjectDefinition)
    assert isinstance(query_type.graphql_node, OperationDefinitionNode)
    assert query_type.graphql_type is not None
    assert query_type.graphql_type.origin is conftest_globals["Query"]

    variables_type = types_by_name["OperationVariables"]
    assert isinstance(variables_type.graphql_type, StrawberryObjectDefinition)
    assert isinstance(variables_type.graphql_node, OperationDefinitionNode)
    assert variables_type.graphql_type is not None
    assert variables_type.graphql_type.origin is conftest_globals["Query"]

    person_type = types_by_name["OperationResultGetPersonWithInputs"]
    assert isinstance(person_type.graphql_type, StrawberryObjectDefinition)
    assert person_type.graphql_type is not None
    assert person_type.graphql_type.origin is conftest_globals["Person"]
