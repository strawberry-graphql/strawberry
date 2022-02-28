import textwrap
from typing import List

from strawberry.codegen import (
    CodegenPlugin,
    GraphQLArgument,
    GraphQLArgumentValue,
    GraphQLDirective,
    GraphQLFieldSelection,
    GraphQLInlineFragment,
    GraphQLIntValue,
    GraphQLOperation,
    GraphQLSelection,
    GraphQLStringValue,
    GraphQLType,
)


class PrintOperationPlugin(CodegenPlugin):
    def print(self, types: List[GraphQLType], operation: GraphQLOperation) -> str:
        return "\n".join(
            [
                f"{operation.kind} {operation.name}{self._print_directives(operation.directives)} {{",  # noqa: E501
                self._print_selections(operation.selections),
                "}",
            ]
        )

    def _print_argument_value(self, value: GraphQLArgumentValue) -> str:
        if isinstance(value, GraphQLStringValue):
            return f'"{value.value}"'

        if isinstance(value, GraphQLIntValue):
            return str(value.value)

        raise ValueError(f"not supported: {type(value)}")

    def _print_arguments(self, arguments: List[GraphQLArgument]) -> str:
        if not arguments:
            return ""

        return (
            "("
            + ", ".join(
                [
                    f"{argument.name}: {self._print_argument_value(argument.value)}"
                    for argument in arguments
                ]
            )
            + ")"
        )

    def _print_directives(self, directives: List[GraphQLDirective]) -> str:
        if not directives:
            return ""

        return " " + " ".join(
            [
                f"@{directive.name}{self._print_arguments(directive.arguments)}"
                for directive in directives
            ]
        )

    def _print_field_selection(self, selection: GraphQLFieldSelection) -> str:
        field = f"{selection.field}{self._print_directives(selection.directives)}"

        if selection.selections:
            return field + f" {{\n{self._print_selections(selection.selections)}\n}}"

        return field

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
