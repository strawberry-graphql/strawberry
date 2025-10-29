"""Directive and abstract type handling for JIT compiler."""

from __future__ import annotations

from typing import TYPE_CHECKING

from graphql import (
    DirectiveNode,
    FieldNode,
    FragmentSpreadNode,
    GraphQLInterfaceType,
    GraphQLObjectType,
    GraphQLUnionType,
    InlineFragmentNode,
    SelectionSetNode,
)

if TYPE_CHECKING:
    from .compiler import JITCompiler


def generate_abstract_type_selection(
    compiler: JITCompiler,
    selection_set: SelectionSetNode,
    abstract_type: GraphQLUnionType | GraphQLInterfaceType,
    parent_var: str,
    result_var: str,
    info_var: str,
    path: str,
) -> None:
    """Generate selection for union or interface types with runtime type resolution."""
    # First, always add __typename for proper type discrimination
    compiler._emit(f"# Resolve abstract type: {abstract_type.name}")

    # Get the actual typename from the object
    compiler._emit("# Get runtime type")
    compiler._emit("actual_typename = None")
    compiler._emit(f'if hasattr({parent_var}, "__typename"):')
    compiler.indent_level += 1
    compiler._emit(f"actual_typename = {parent_var}.__typename")
    compiler.indent_level -= 1
    compiler._emit(f'elif hasattr({parent_var}.__class__, "__name__"):')
    compiler.indent_level += 1
    compiler._emit(f"actual_typename = {parent_var}.__class__.__name__")
    compiler.indent_level -= 1

    # Add __typename to result if requested
    for selection in selection_set.selections:
        if isinstance(selection, FieldNode) and selection.name.value == "__typename":
            alias = (
                compiler._sanitize_identifier(selection.alias.value)
                if selection.alias
                else "__typename"
            )
            compiler._emit(f'{result_var}["{alias}"] = actual_typename')
            break

    # Collect fragments and inline fragments by type
    type_selections = {}  # type_name -> selections
    common_selections = []  # Selections without type condition

    for selection in selection_set.selections:
        if isinstance(selection, FieldNode):
            if selection.name.value != "__typename":
                common_selections.append(selection)
        elif isinstance(selection, InlineFragmentNode):
            if selection.type_condition:
                type_name = selection.type_condition.name.value
                if type_name not in type_selections:
                    type_selections[type_name] = []
                type_selections[type_name].extend(selection.selection_set.selections)
            else:
                # No type condition means it applies to all types
                common_selections.extend(selection.selection_set.selections)
        elif isinstance(selection, FragmentSpreadNode):
            # Handle fragment spreads
            fragment_name = selection.name.value
            if fragment_name in compiler.fragments:
                fragment_def = compiler.fragments[fragment_name]
                if fragment_def.type_condition:
                    type_name = fragment_def.type_condition.name.value
                    if type_name not in type_selections:
                        type_selections[type_name] = []
                    type_selections[type_name].extend(
                        fragment_def.selection_set.selections
                    )

    # Get possible types for the union/interface
    possible_types = []
    if isinstance(abstract_type, GraphQLUnionType):
        possible_types = list(abstract_type.types)
    elif isinstance(abstract_type, GraphQLInterfaceType):
        # For interfaces, we need to get implementing types from schema
        for gql_type in compiler.schema.type_map.values():
            if (
                isinstance(gql_type, GraphQLObjectType)
                and abstract_type in gql_type.interfaces
            ):
                possible_types.append(gql_type)

    # Generate type-specific selections
    if type_selections or common_selections:
        first_type = True
        for possible_type in possible_types:
            type_name = possible_type.name

            # Check if we have selections for this type
            selections_for_type = common_selections.copy()
            if type_name in type_selections:
                selections_for_type.extend(type_selections[type_name])

            if selections_for_type:
                if first_type:
                    compiler._emit(f'if actual_typename == "{type_name}":')
                    first_type = False
                else:
                    compiler._emit(f'elif actual_typename == "{type_name}":')

                compiler.indent_level += 1

                # Generate selections for this concrete type
                for selection in selections_for_type:
                    if isinstance(selection, FieldNode):
                        compiler._generate_field(
                            selection,
                            possible_type,
                            parent_var,
                            result_var,
                            info_var,
                            path,
                        )

                compiler.indent_level -= 1

        # Add else clause for unknown types (just process common selections)
        if not first_type and common_selections:
            compiler._emit("else:")
            compiler.indent_level += 1
            compiler._emit("# Unknown type, process common fields only")

            # Try to resolve common fields
            for selection in common_selections:
                if isinstance(selection, FieldNode):
                    field_name = compiler._sanitize_identifier(selection.name.value)
                    alias = (
                        compiler._sanitize_identifier(selection.alias.value)
                        if selection.alias
                        else field_name
                    )
                    compiler._emit(
                        f'{result_var}["{alias}"] = getattr({parent_var}, "{field_name}", None)'
                    )

            compiler.indent_level -= 1


def generate_skip_include_checks(
    compiler: JITCompiler, directives: list[DirectiveNode], info_var: str
) -> str:
    """Generate directive conditions for @skip and @include.

    Args:
        compiler: JITCompiler instance
        directives: List of GraphQL directive nodes
        info_var: Variable name for info object

    Returns:
        Condition string like "if condition1 and condition2:" or empty string
    """
    conditions = []

    for directive in directives:
        directive_name = directive.name.value

        if directive_name == "skip":
            if_arg = get_directive_argument(compiler, directive, "if", info_var)
            if if_arg:
                conditions.append(f"not ({if_arg})")
        elif directive_name == "include":
            if_arg = get_directive_argument(compiler, directive, "if", info_var)
            if if_arg:
                conditions.append(if_arg)

    if conditions:
        return f"if {' and '.join(conditions)}:"
    return ""


def get_directive_argument(
    compiler: JITCompiler, directive: DirectiveNode, arg_name: str, info_var: str
) -> str:
    """Get directive argument value.

    Args:
        compiler: JITCompiler instance
        directive: GraphQL directive node
        arg_name: Name of argument to extract
        info_var: Variable name for info object

    Returns:
        Generated code for argument value or empty string
    """
    for arg in directive.arguments or []:
        if arg.name.value == arg_name:
            return compiler._generate_argument_value(arg.value, info_var)
    return ""


__all__ = [
    "generate_abstract_type_selection",
    "generate_skip_include_checks",
    "get_directive_argument",
]
