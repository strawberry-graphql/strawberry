from __future__ import annotations

import textwrap
from typing import TYPE_CHECKING, List, Optional

from strawberry.codegen import CodegenFile, QueryCodegenPlugin
from strawberry.codegen.types import (
    GraphQLBoolValue,
    GraphQLEnumValue,
    GraphQLField,
    GraphQLFieldSelection,
    GraphQLFragmentSpread,
    GraphQLFragmentType,
    GraphQLInlineFragment,
    GraphQLIntValue,
    GraphQLList,
    GraphQLListValue,
    GraphQLObjectType,
    GraphQLObjectValue,
    GraphQLOptional,
    GraphQLStringValue,
    GraphQLVariableReference,
)

if TYPE_CHECKING:
    from strawberry.codegen.types import (
        GraphQLArgument,
        GraphQLArgumentValue,
        GraphQLDirective,
        GraphQLOperation,
        GraphQLSelection,
        GraphQLType,
    )


class PrintOperationPlugin(QueryCodegenPlugin):
    def generate_code(
        self, types: List[GraphQLType], operation: GraphQLOperation
    ) -> List[CodegenFile]:
        code_lines = []
        for t in types:
            if not isinstance(t, GraphQLFragmentType):
                continue
            code_lines.append(self._print_fragment(t))

        code = "\n".join(
            [
                *code_lines,
                (
                    f"{operation.kind} {operation.name}"
                    f"{self._print_operation_variables(operation)}"
                    f"{self._print_directives(operation.directives)} {{"
                ),
                self._print_selections(operation.selections),
                "}",
            ]
        )
        return [CodegenFile("query.graphql", code)]

    def _print_fragment_field(self, field: GraphQLField, indent: str = "") -> str:
        code_lines = []
        if isinstance(field.type, GraphQLObjectType):
            code_lines.append(f"{indent}{field.name} {{")
            for subfield in field.type.fields:
                code_lines.append(  # noqa: PERF401
                    self._print_fragment_field(subfield, indent=indent + "  ")
                )
            code_lines.append(f"{indent}}}")
        else:
            code_lines.append(f"{indent}{field.name}")
        return "\n".join(code_lines)

    def _print_fragment(self, fragment: GraphQLFragmentType) -> str:
        code_lines = []
        code_lines.append(f"fragment {fragment.name} on {fragment.on} {{")
        for field in fragment.fields:
            code_lines.append(  # noqa: PERF401
                self._print_fragment_field(field, indent="  ")
            )
        code_lines.append("}")
        code_lines.append("")
        return "\n".join(code_lines)

    def _print_operation_variables(self, operation: GraphQLOperation) -> str:
        if not operation.variables:
            return ""

        variables = ", ".join(
            f"${v.name}: {self._print_graphql_type(v.type)}"
            for v in operation.variables
        )

        return f"({variables})"

    def _print_graphql_type(
        self, type: GraphQLType, parent_type: Optional[GraphQLType] = None
    ) -> str:
        if isinstance(type, GraphQLOptional):
            return self._print_graphql_type(type.of_type, type)

        if isinstance(type, GraphQLList):
            type_name = f"[{self._print_graphql_type(type.of_type, type)}]"
        else:
            type_name = type.name

        if parent_type and isinstance(parent_type, GraphQLOptional):
            return type_name

        return f"{type_name}!"

    def _print_argument_value(self, value: GraphQLArgumentValue) -> str:
        if isinstance(value, GraphQLStringValue):
            return f'"{value.value}"'

        if isinstance(value, GraphQLIntValue):
            return str(value.value)

        if isinstance(value, GraphQLVariableReference):
            return f"${value.value}"

        if isinstance(value, GraphQLListValue):
            return f"[{', '.join(self._print_argument_value(v) for v in value.values)}]"

        if isinstance(value, GraphQLEnumValue):
            return value.name

        if isinstance(value, GraphQLBoolValue):
            return str(value.value).lower()

        if isinstance(value, GraphQLObjectValue):
            return (
                "{"
                + ", ".join(
                    f"{name}: {self._print_argument_value(v)}"
                    for name, v in value.values.items()
                )
                + "}"
            )

        raise ValueError(f"not supported: {type(value)}")  # pragma: no cover

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

        if selection.alias:
            field = f"{selection.alias}: {field}"

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

    def _print_fragment_spread(self, fragment: GraphQLFragmentSpread) -> str:
        return f"...{fragment.name}"

    def _print_selection(self, selection: GraphQLSelection) -> str:
        if isinstance(selection, GraphQLFieldSelection):
            return self._print_field_selection(selection)

        if isinstance(selection, GraphQLInlineFragment):
            return self._print_inline_fragment(selection)

        if isinstance(selection, GraphQLFragmentSpread):
            return self._print_fragment_spread(selection)

        raise ValueError(f"Unsupported selection: {selection}")  # pragma: no cover

    def _print_selections(self, selections: List[GraphQLSelection]) -> str:
        selections_text = "\n".join(
            [self._print_selection(selection) for selection in selections]
        )

        return textwrap.indent(selections_text, " " * 2)
