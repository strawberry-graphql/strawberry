"""Utility functions for JIT compiler."""

from __future__ import annotations

from typing import TYPE_CHECKING

from graphql import (
    FieldNode,
    FragmentSpreadNode,
    GraphQLObjectType,
    InlineFragmentNode,
    SelectionSetNode,
)

if TYPE_CHECKING:
    from typing import Any


def sanitize_identifier(name: str) -> str:
    """Sanitize identifier for safe code generation (defense-in-depth).

    While GraphQL parser validates identifiers, this provides an additional
    security layer to prevent any potential code injection through names
    embedded in generated code.

    Args:
        name: Identifier to sanitize (field name, alias, variable name, etc.)

    Returns:
        The validated identifier

    Raises:
        ValueError: If identifier is invalid
    """
    if not name:
        raise ValueError("Identifier cannot be empty")

    # Must start with letter or underscore
    if not (name[0].isalpha() or name[0] == "_"):
        raise ValueError(
            f"Invalid identifier '{name}': must start with letter or underscore"
        )

    # Rest must be alphanumeric or underscore
    if not all(c.isalnum() or c == "_" for c in name):
        raise ValueError(f"Invalid identifier '{name}': contains invalid characters")

    # Reject Python keywords for extra safety
    import keyword

    if keyword.iskeyword(name):
        raise ValueError(f"Invalid identifier '{name}': Python keyword")

    return name


def serialize_value(value: Any) -> str:
    """Serialize Python value for code generation.

    Args:
        value: Python value to serialize

    Returns:
        String representation suitable for code generation
    """
    if value is None:
        return "None"
    if isinstance(value, bool):
        return "True" if value else "False"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, str):
        return repr(value)
    if isinstance(value, list):
        items = [serialize_value(item) for item in value]
        return f"[{', '.join(items)}]"
    if isinstance(value, dict):
        items = [f"{k!r}: {serialize_value(v)}" for k, v in value.items()]
        return f"{{{', '.join(items)}}}"
    return repr(value)


class CodeEmitter:
    """Helper class for emitting indented code."""

    def __init__(self):
        self.generated_code: list[str] = []
        self.indent_level = 0

    def emit(self, line: str) -> None:
        """Emit line of code with proper indentation."""
        indent = "    " * self.indent_level
        self.generated_code.append(f"{indent}{line}")

    def get_code(self) -> list[str]:
        """Get all generated code lines."""
        return self.generated_code


def detect_async_resolvers(
    selection_set: SelectionSetNode,
    parent_type: GraphQLObjectType,
    fragments: dict,
    schema,
    is_field_async_func,
) -> bool:
    """Pre-scan for async resolvers in selection set.

    Args:
        selection_set: GraphQL selection set to scan
        parent_type: Parent object type
        fragments: Fragment definitions
        schema: GraphQL schema
        is_field_async_func: Function to check if field is async

    Returns:
        True if any async resolvers found
    """
    has_async = False

    for selection in selection_set.selections:
        if isinstance(selection, FieldNode):
            field_name = selection.name.value
            if field_name == "__typename":
                continue

            field_def = parent_type.fields.get(field_name)
            if field_def:
                # Use compile-time async detection from StrawberryField
                if is_field_async_func(field_def):
                    has_async = True

                if selection.selection_set:
                    field_type = field_def.type
                    while hasattr(field_type, "of_type"):
                        field_type = field_type.of_type
                    if isinstance(field_type, GraphQLObjectType):
                        if detect_async_resolvers(
                            selection.selection_set,
                            field_type,
                            fragments,
                            schema,
                            is_field_async_func,
                        ):
                            has_async = True

        elif isinstance(selection, FragmentSpreadNode):
            fragment_name = selection.name.value
            if fragment_name in fragments:
                fragment_def = fragments[fragment_name]
                if fragment_def.selection_set:
                    if detect_async_resolvers(
                        fragment_def.selection_set,
                        parent_type,
                        fragments,
                        schema,
                        is_field_async_func,
                    ):
                        has_async = True

        elif isinstance(selection, InlineFragmentNode):
            if selection.selection_set:
                if selection.type_condition:
                    type_name = selection.type_condition.name.value
                    fragment_type = schema.type_map.get(type_name)
                    if fragment_type and isinstance(fragment_type, GraphQLObjectType):
                        if detect_async_resolvers(
                            selection.selection_set,
                            fragment_type,
                            fragments,
                            schema,
                            is_field_async_func,
                        ):
                            has_async = True
                elif detect_async_resolvers(
                    selection.selection_set,
                    parent_type,
                    fragments,
                    schema,
                    is_field_async_func,
                ):
                    has_async = True

    return has_async


__all__ = [
    "CodeEmitter",
    "detect_async_resolvers",
    "sanitize_identifier",
    "serialize_value",
]
