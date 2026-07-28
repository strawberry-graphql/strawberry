from __future__ import annotations

from typing import TYPE_CHECKING, cast

from graphql import GraphQLError, parse
from graphql.language import FieldNode, FragmentSpreadNode, InlineFragmentNode
from graphql.language.printer import print_ast

if TYPE_CHECKING:
    from collections.abc import Callable

    from graphql.language import (
        OperationDefinitionNode,
        SelectionNode,
        SelectionSetNode,
    )


def apply_name_converter(field_set: str, name_converter: Callable[[str], str]) -> str:
    """Apply ``name_converter`` to every field name in a federation FieldSet.

    A FieldSet (used by the ``@key``, ``@requires`` and ``@provides``
    directives) is a GraphQL selection set given as a string, e.g.
    ``"upc"`` or ``"organization { id } upc"``. Field names inside it are
    not automatically renamed by the schema's name converter the way
    regular fields are, so without this, a snake_case Python field ends up
    referenced by its Python name in the directive even though the field
    itself is printed under its (e.g. camelCased) GraphQL name -- producing
    a FieldSet that points at a field that doesn't exist.

    Arguments and fragment spreads inside the selection set are left
    untouched. If ``field_set`` can't be parsed as a selection set, it's
    returned unchanged rather than raising, since callers may hold FieldSet
    values that predate this validation.
    """
    try:
        document = parse(f"{{ {field_set} }}")
    except GraphQLError:
        return field_set

    operation = cast("OperationDefinitionNode", document.definitions[0])

    return _print_selection_set(operation.selection_set, name_converter)


def _print_selection_set(
    selection_set: SelectionSetNode, name_converter: Callable[[str], str]
) -> str:
    return " ".join(
        _print_selection(selection, name_converter)
        for selection in selection_set.selections
    )


def _print_selection(
    selection: SelectionNode, name_converter: Callable[[str], str]
) -> str:
    if isinstance(selection, FieldNode):
        printed = name_converter(selection.name.value)

        if selection.arguments:
            args = ", ".join(
                f"{argument.name.value}: {print_ast(argument.value)}"
                for argument in selection.arguments
            )
            printed += f"({args})"

        if selection.selection_set is not None:
            nested = _print_selection_set(selection.selection_set, name_converter)
            printed += f" {{ {nested} }}"

        return printed

    if isinstance(selection, InlineFragmentNode):
        type_condition = (
            f" on {selection.type_condition.name.value}"
            if selection.type_condition
            else ""
        )
        nested = (
            _print_selection_set(selection.selection_set, name_converter)
            if selection.selection_set is not None
            else ""
        )
        return f"...{type_condition} {{ {nested} }}"

    if isinstance(selection, FragmentSpreadNode):
        return f"...{selection.name.value}"

    return print_ast(selection)  # pragma: no cover


__all__ = ["apply_name_converter"]
