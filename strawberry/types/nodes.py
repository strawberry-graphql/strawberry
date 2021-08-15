"""
Abstraction layer for graphql-core field nodes.

Call `SelectedField` on a graphql `FieldNode`, such as in `info.field_nodes`.

If a node has only one useful value, it's value is inlined.

If a list of nodes have unique names, it's transformed into a mapping.
Note Python dicts maintain ordering (for all supported versions).
"""

import dataclasses
from typing import Any, Dict, Iterable, List, NewType, Optional, Union

from graphql.language import (  # type: ignore
    ArgumentNode,
    DirectiveNode,
    FieldNode,
    FragmentSpreadNode,
    InlineFragmentNode,
    Node,
    ValueNode,
)


Arguments = NewType("Arguments", Dict[str, Any])
Directives = NewType("Directives", Dict[str, Arguments])
Selection = Union["SelectedField", "FragmentSpread", "InlineFragment"]


def value(node: ValueNode) -> Any:
    """Return useful value from any node."""
    if hasattr(node, "fields"):
        return {
            field.name.value: value(field.value)
            for field in node.fields  # type: ignore
        }
    if hasattr(node, "values"):
        return list(map(value, node.values))  # type: ignore
    if hasattr(node, "name"):
        return node.name.value  # type: ignore
    return getattr(node, "value", None)


def arguments(nodes: Iterable[ArgumentNode]) -> Arguments:
    """Return mapping of arguments."""
    return {node.name.value: value(node.value) for node in nodes}  # type: ignore


def directives(nodes: Iterable[DirectiveNode]) -> Directives:
    """Return mapping of directives."""
    return {node.name.value: arguments(node.arguments) for node in nodes}  # type: ignore


def selection(node: Node) -> Selection:
    """Return typed `Selection` based on node type."""
    if hasattr(node, "alias"):
        return SelectedField(node)  # type: ignore
    if hasattr(node, "selection_set"):
        return InlineFragment(node)  # type: ignore
    return FragmentSpread(node)  # type: ignore


@dataclasses.dataclass
class FragmentSpread:
    """Wrapper for a FragmentSpreadNode."""

    name: str
    directives: Directives

    def __init__(self, node: FragmentSpreadNode):
        self.name = node.name.value
        self.directives = directives(node.directives)


@dataclasses.dataclass
class InlineFragment:
    """Wrapper for a InlineFragmentNode."""

    type_condition: str
    selections: List[Selection]
    directives: Directives

    def __init__(self, node: InlineFragmentNode):
        self.type_condition = node.type_condition.name.value
        self.selections = list(
            map(selection, getattr(node.selection_set, "selections", []))
        )
        self.directives = directives(node.directives)


@dataclasses.dataclass
class SelectedField(FragmentSpread):
    """Wrapper for a FieldNode."""

    alias: Optional[str]
    arguments: Arguments
    selections: List[Selection]

    def __init__(self, node: FieldNode):
        super().__init__(node)  # type: ignore
        self.alias = getattr(node.alias, "value", None)
        self.arguments = arguments(node.arguments)
        self.selections = list(
            map(selection, getattr(node.selection_set, "selections", []))
        )
