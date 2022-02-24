import textwrap
from pathlib import Path
from typing import List

import pytest

from strawberry.codegen import (
    CodegenPlugin,
    GraphQLFieldSelection,
    GraphQLInlineFragment,
    GraphQLOperation,
    GraphQLSelection,
    GraphQLType,
    QueryCodegen,
)


HERE = Path(__file__).parent
QUERIES = list(HERE.glob("queries/*.graphql"))


class PrintOperationPlugin(CodegenPlugin):
    def print(self, types: List[GraphQLType], operation: GraphQLOperation) -> str:
        return "\n".join(
            [
                f"{operation.kind} {operation.name} {{",
                self._print_selections(operation.selections),
                "}",
            ]
        )

    def _print_field_selection(self, selection: GraphQLFieldSelection) -> str:
        if selection.selections:
            return (
                f"{selection.field} "
                f"{{\n{self._print_selections(selection.selections)}\n}}"
            )

        return selection.field

    def _print_inline_fragment(self, fragment: GraphQLInlineFragment) -> str:
        return "\n".join(
            [
                f"... on {fragment.type_condition} {{",
                self._print_selections(fragment.selections),
                "}",
            ]
        )

    def _print_selection(self, selection: GraphQLSelection) -> str:
        if isinstance(selection, GraphQLFieldSelection):
            return self._print_field_selection(selection)

        if isinstance(selection, GraphQLInlineFragment):
            return self._print_inline_fragment(selection)

    def _print_selections(self, selections: List[GraphQLSelection]) -> str:
        selections_text = "\n".join(
            [self._print_selection(selection) for selection in selections]
        )

        return textwrap.indent(selections_text, " " * 2)


@pytest.mark.parametrize("query", QUERIES, ids=[x.name for x in QUERIES])
def test_codegen(
    query: Path,
    schema,
):
    generator = QueryCodegen(schema, plugins=[PrintOperationPlugin()])
    query_content = query.read_text()

    result = generator.codegen(query_content)

    assert result == query_content
