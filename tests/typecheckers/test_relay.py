from inline_snapshot import snapshot

from .utils.marks import requires_mypy, requires_pyright, skip_on_windows
from .utils.typecheck import Result, typecheck

pytestmark = [skip_on_windows, requires_pyright, requires_mypy]


CODE = """
from typing import List, Optional

import strawberry
from strawberry import relay


@strawberry.type
class Fruit(relay.Node):
    id: relay.NodeID[int]
    name: str
    color: str


@strawberry.type
class Query:
    node: relay.Node
    nodes: List[relay.Node]
    node_optional: Optional[relay.Node]
    nodes_optional: List[Optional[relay.Node]]


reveal_type(Query.node)
reveal_type(Query.nodes)
reveal_type(Query.node_optional)
reveal_type(Query.nodes_optional)
"""


def test():
    results = typecheck(CODE)

    assert results.pyright == snapshot(
        [
            Result(
                type="information",
                message='Type of "Query.node" is "Node"',
                line=23,
                column=13,
            ),
            Result(
                type="information",
                message='Type of "Query.nodes" is "List[Node]"',
                line=24,
                column=13,
            ),
            Result(
                type="information",
                message='Type of "Query.node_optional" is "Node | None"',
                line=25,
                column=13,
            ),
            Result(
                type="information",
                message='Type of "Query.nodes_optional" is "List[Node | None]"',
                line=26,
                column=13,
            ),
        ]
    )
    assert results.mypy == snapshot(
        [
            Result(
                type="note",
                message='Revealed type is "strawberry.relay.types.Node"',
                line=23,
                column=13,
            ),
            Result(
                type="note",
                message='Revealed type is "builtins.list[strawberry.relay.types.Node]"',
                line=24,
                column=13,
            ),
            Result(
                type="note",
                message='Revealed type is "Union[strawberry.relay.types.Node, None]"',
                line=25,
                column=13,
            ),
            Result(
                type="note",
                message='Revealed type is "builtins.list[Union[strawberry.relay.types.Node, None]]"',
                line=26,
                column=13,
            ),
        ]
    )
