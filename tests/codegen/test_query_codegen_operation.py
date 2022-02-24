from pathlib import Path
from typing import List

from strawberry.codegen import (
    CodegenPlugin,
    GraphQLOperation,
    GraphQLSelection,
    GraphQLType,
    QueryCodegen,
)


HERE = Path(__file__).parent


class PrintOperationNamePlugin(CodegenPlugin):
    def print(self, types: List[GraphQLType], operation: GraphQLOperation) -> str:
        return operation.name


def test_codegen_operation_name(schema):

    query = HERE / "queries" / "basic.graphql"

    generator = QueryCodegen(schema, plugins=[PrintOperationNamePlugin()])

    result = generator.codegen(query.read_text())

    assert result.strip() == "OperationName"


class PrintOperationPlugin(CodegenPlugin):
    def print(self, types: List[GraphQLType], operation: GraphQLOperation) -> str:
        return "\n".join(
            [
                f"{operation.kind} {operation.name} {{",
                self._print_selections(operation.selections),
                "}",
            ]
        )

    def _print_selection(self, selection: GraphQLSelection) -> str:
        if selection.selections:
            return f"{selection.field} {{\n{self._print_selections(selection.selections)}\n}}"

        return selection.field

    def _print_selections(self, selections: List[GraphQLSelection]) -> str:

        return "\n".join(
            [f"  {self._print_selection(selection)}" for selection in selections]
        )


def test_codegen_can_print_operation_again(schema):
    query = HERE / "queries" / "multiple_types.graphql"
    query_content = query.read_text()

    generator = QueryCodegen(schema, plugins=[PrintOperationPlugin()])

    result = generator.codegen(query_content)

    assert result == query_content
