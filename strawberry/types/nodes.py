"""
Abstraction layer for graphql-core field nodes.

Call `convert_sections` on a list of GraphQL `FieldNode`s, such as in `info.field_nodes`.

If a node has only one useful value, it's value is inlined.

If a list of nodes have unique names, it's transformed into a mapping.
Note Python dicts maintain ordering (for all supported versions).
"""

import dataclasses
from typing import Any, Collection, Dict, Iterable, List, Optional, Union

from graphql import GraphQLResolveInfo
from graphql.language import (
    ArgumentNode as GQLArgumentNode,
    DirectiveNode as GQLDirectiveNode,
    FieldNode as GQLFieldNode,
    FragmentSpreadNode as GQLFragmentSpreadNode,
    InlineFragmentNode as GQLInlineFragment,
    InlineFragmentNode as GQLInlineFragmentNode,
    ListValueNode as GQLListValueNode,
    ObjectValueNode as GQLObjectValueNode,
    ValueNode as GQLValueNode,
    VariableNode as GQLVariableNode,
)


Arguments = Dict[str, Any]
Directives = Dict[str, Arguments]
Selection = Union["SelectedField", "FragmentSpread", "InlineFragment"]


def convert_value(info: GraphQLResolveInfo, node: GQLValueNode) -> Any:
    """Return useful value from any node."""
    if isinstance(node, GQLVariableNode):
        # Look up variable
        name = node.name.value
        return info.variable_values.get(name)
    if isinstance(node, GQLListValueNode):
        return [convert_value(info, value) for value in node.values]
    if isinstance(node, GQLObjectValueNode):
        return {
            field.name.value: convert_value(info, field.value) for field in node.fields
        }
    return getattr(node, "value", None)


def convert_arguments(
    info: GraphQLResolveInfo, nodes: Iterable[GQLArgumentNode]
) -> Arguments:
    """Return mapping of arguments."""
    return {node.name.value: convert_value(info, node.value) for node in nodes}


def convert_directives(
    info: GraphQLResolveInfo, nodes: Iterable[GQLDirectiveNode]
) -> Directives:
    """Return mapping of directives."""
    return {node.name.value: convert_arguments(info, node.arguments) for node in nodes}


def convert_selections(
    info: GraphQLResolveInfo, field_nodes: Collection[GQLFieldNode]
) -> List[Selection]:
    """Return typed `Selection` based on node type."""
    selections: List[Selection] = []
    for node in field_nodes:
        if isinstance(node, GQLFieldNode):
            selections.append(SelectedField.from_node(info, node))
        elif isinstance(node, GQLInlineFragment):
            selections.append(InlineFragment.from_node(info, node))
        elif isinstance(node, GQLFragmentSpreadNode):
            selections.append(FragmentSpread.from_node(info, node))
        else:
            raise TypeError(f"Unknown node type: {node}")

    return selections


@dataclasses.dataclass
class FragmentSpread:
    """Wrapper for a FragmentSpreadNode."""

    name: str
    type_condition: str
    directives: Directives
    selections: List[Selection]

    @classmethod
    def from_node(cls, info: GraphQLResolveInfo, node: GQLFragmentSpreadNode):
        # Look up fragment
        name = node.name.value
        fragment = info.fragments[name]
        return cls(
            name=name,
            directives=convert_directives(info, node.directives),
            type_condition=fragment.type_condition.name.value,
            selections=convert_selections(
                info, getattr(fragment.selection_set, "selections", [])
            ),
        )


@dataclasses.dataclass
class InlineFragment:
    """Wrapper for a InlineFragmentNode."""

    type_condition: str
    selections: List[Selection]
    directives: Directives

    @classmethod
    def from_node(cls, info: GraphQLResolveInfo, node: GQLInlineFragmentNode):
        return cls(
            type_condition=node.type_condition.name.value,
            selections=convert_selections(
                info, getattr(node.selection_set, "selections", [])
            ),
            directives=convert_directives(info, node.directives),
        )


@dataclasses.dataclass
class SelectedField:
    """Wrapper for a FieldNode."""

    name: str
    directives: Directives
    arguments: Arguments
    selections: List[Selection]
    alias: Optional[str] = None

    @classmethod
    def from_node(cls, info: GraphQLResolveInfo, node: GQLFieldNode):
        return cls(
            name=node.name.value,
            directives=convert_directives(info, node.directives),
            alias=getattr(node.alias, "value", None),
            arguments=convert_arguments(info, node.arguments),
            selections=convert_selections(
                info, getattr(node.selection_set, "selections", [])
            ),
        )
