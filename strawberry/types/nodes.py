"""
Abstraction layer for graphql-core field nodes.

Call `SelectedField` on a graphql `FieldNode`, such as in `info.field_nodes`.

If a node has only one useful value, it's value is inlined.

If a list of nodes have unique names, it's transformed into a mapping.
Note Python dicts maintain ordering (for all supported versions).
"""

import dataclasses
from typing import Any, Dict, Iterable, List, Optional, Union

from graphql.language import (
    ArgumentNode as GQLArgumentNode,
    DirectiveNode as GQLDirectiveNode,
    FieldNode as GQLFieldNode,
    FragmentDefinitionNode as GQLFragmentDefinitionNode,
    FragmentSpreadNode as GQLFragmentSpreadNode,
    InlineFragmentNode as GQLInlineFragment,
    InlineFragmentNode as GQLInlineFragmentNode,
    ValueNode as GQLValueNode,
)


Arguments = Dict[str, Any]
Directives = Dict[str, Arguments]
Selection = Union["SelectedField", "FragmentSpread", "InlineFragment"]
GQLFragments = Dict[str, GQLFragmentDefinitionNode]


def convert_value(node: GQLValueNode) -> Any:
    """Return useful value from any node."""
    if hasattr(node, "fields"):
        return {
            field.name.value: convert_value(field.value)
            for field in node.fields  # type: ignore
        }
    if hasattr(node, "values"):
        return list(map(convert_value, node.values))  # type: ignore
    if hasattr(node, "name"):
        return node.name.value  # type: ignore
    return getattr(node, "value", None)


def convert_arguments(nodes: Iterable[GQLArgumentNode]) -> Arguments:
    """Return mapping of arguments."""
    return {node.name.value: convert_value(node.value) for node in nodes}


def convert_directives(nodes: Iterable[GQLDirectiveNode]) -> Directives:
    """Return mapping of directives."""
    return {node.name.value: convert_arguments(node.arguments) for node in nodes}


def convert_selections(
    fragments: GQLFragments, field_nodes: List[GQLFieldNode]
) -> List[Selection]:
    """Return typed `Selection` based on node type."""
    selections: List[Selection] = []
    for node in field_nodes:
        if isinstance(node, GQLFieldNode):
            selections.append(SelectedField.from_node(fragments, node))
        elif isinstance(node, GQLInlineFragment):
            selections.append(InlineFragment.from_node(fragments, node))
        elif isinstance(node, GQLFragmentSpreadNode):
            selections.append(FragmentSpread.from_node(fragments, node))
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
    def from_node(cls, fragments: GQLFragments, node: GQLFragmentSpreadNode):
        # Look up fragment
        name = node.name.value
        fragment = fragments[name]
        return cls(
            name=name,
            directives=convert_directives(node.directives),
            type_condition=fragment.type_condition.name.value,
            selections=convert_selections(
                fragments, getattr(fragment.selection_set, "selections", [])
            ),
        )


@dataclasses.dataclass
class InlineFragment:
    """Wrapper for a InlineFragmentNode."""

    type_condition: str
    selections: List[Selection]
    directives: Directives

    @classmethod
    def from_node(cls, fragments: GQLFragments, node: GQLInlineFragmentNode):
        return cls(
            type_condition=node.type_condition.name.value,
            selections=convert_selections(
                fragments, getattr(node.selection_set, "selections", [])
            ),
            directives=convert_directives(node.directives),
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
    def from_node(cls, fragments: GQLFragments, node: GQLFieldNode):
        return cls(
            name=node.name.value,
            directives=convert_directives(node.directives),
            alias=getattr(node.alias, "value", None),
            arguments=convert_arguments(node.arguments),
            selections=convert_selections(
                fragments, getattr(node.selection_set, "selections", [])
            ),
        )
