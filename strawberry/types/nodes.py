"""Abstraction layer for graphql-core field nodes.

Call `convert_sections` on a list of GraphQL `FieldNode`s,
such as in `info.field_nodes`.

If a node has only one useful value, it's value is inlined.

If a list of nodes have unique names, it's transformed into a mapping.
Note Python dicts maintain ordering (for all supported versions).
"""

from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING, Any, Optional, Union

from graphql.language import FieldNode as GQLFieldNode
from graphql.language import FragmentSpreadNode as GQLFragmentSpreadNode
from graphql.language import InlineFragmentNode as GQLInlineFragmentNode
from graphql.language import ListValueNode as GQLListValueNode
from graphql.language import ObjectValueNode as GQLObjectValueNode
from graphql.language import VariableNode as GQLVariableNode

if TYPE_CHECKING:
    from collections.abc import Collection, Iterable

    from graphql import GraphQLResolveInfo
    from graphql.language import ArgumentNode as GQLArgumentNode
    from graphql.language import DirectiveNode as GQLDirectiveNode
    from graphql.language import ValueNode as GQLValueNode
Arguments = dict[str, Any]
Directives = dict[str, Arguments]
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
) -> list[Selection]:
    """Return typed `Selection` based on node type."""
    selections: list[Selection] = []
    for node in field_nodes:
        if isinstance(node, GQLFieldNode):
            selections.append(SelectedField.from_node(info, node))
        elif isinstance(node, GQLInlineFragmentNode):
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
    selections: list[Selection]

    @classmethod
    def from_node(
        cls,
        info: GraphQLResolveInfo,
        node: GQLFragmentSpreadNode,
    ) -> FragmentSpread:
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
    selections: list[Selection]
    directives: Directives

    @classmethod
    def from_node(
        cls,
        info: GraphQLResolveInfo,
        node: GQLInlineFragmentNode,
    ) -> InlineFragment:
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
    selections: list[Selection]
    alias: Optional[str] = None

    @classmethod
    def from_node(cls, info: GraphQLResolveInfo, node: GQLFieldNode) -> SelectedField:
        return cls(
            name=node.name.value,
            directives=convert_directives(info, node.directives),
            alias=getattr(node.alias, "value", None),
            arguments=convert_arguments(info, node.arguments),
            selections=convert_selections(
                info, getattr(node.selection_set, "selections", [])
            ),
        )


__all__ = ["FragmentSpread", "InlineFragment", "SelectedField", "convert_selections"]
