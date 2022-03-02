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
    GraphQLList,
    GraphQLOperation,
    GraphQLOptional,
    GraphQLSelection,
    GraphQLStringValue,
    GraphQLType,
    GraphQLVariableReference,
)


class PrintOperationPlugin(CodegenPlugin):
    def print(self, types: List[GraphQLType], operation: GraphQLOperation) -> str:
        return "\n".join(
            [
                (
                    f"{operation.kind} {operation.name}"
                    f"{self._print_operation_variables(operation)}"
                    f"{self._print_directives(operation.directives)} {{"
                ),
                self._print_selections(operation.selections),
                "}",
            ]
        )

    def _print_operation_variables(self, operation: GraphQLOperation) -> str:
        if not operation.variables:
            return ""

        variables = ", ".join(
            f"${v.name}: {self._print_graphql_type(v.type)}"
            for v in operation.variables
        )

        return f"({variables})"

    def _print_graphql_type(self, type: GraphQLType) -> str:
        if isinstance(type, GraphQLList):
            return f"[{self._print_graphql_type(type.of_type)}]"

        if isinstance(type, GraphQLOptional):
            if hasattr(type.of_type, "name"):
                return type.of_type.name

            return self._print_graphql_type(type.of_type)

        return f"{type.name}!"

    def _print_argument_value(self, value: GraphQLArgumentValue) -> str:
        if isinstance(value, GraphQLStringValue):
            return f'"{value.value}"'

        if isinstance(value, GraphQLIntValue):
            return str(value.value)

        if isinstance(value, GraphQLVariableReference):
            return f"${value.value}"

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
        field = (
            f"{selection.field}"
            f"{self._print_arguments(selection.arguments)}"
            f"{self._print_directives(selection.directives)}"
        )

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
