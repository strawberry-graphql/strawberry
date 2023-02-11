from .utils import Result, requires_pyright, run_pyright, skip_on_windows

pytestmark = [skip_on_windows, requires_pyright]


CODE = """
from typing import Any, Iterable, List, Optional

import strawberry
from strawberry.types import Info
from typing_extensions import Self


@strawberry.type
class Fruit(strawberry.relay.Node):
    id: strawberry.relay.NodeID[int]
    name: str
    color: str


@strawberry.type
class FruitCustomPaginationConnection(strawberry.relay.Connection[Fruit]):
    @strawberry.field
    def something(self) -> str:
        return "foobar"

    @classmethod
    def from_nodes(
        cls,
        nodes: Iterable[Fruit],
        *,
        info: Optional[Info[Any, Any]] = None,
        total_count: Optional[int] = None,
        before: Optional[str] = None,
        after: Optional[str] = None,
        first: Optional[int] = None,
        last: Optional[int] = None,
        **kwargs: Any,
    ) -> Self:
        ...


@strawberry.type
class Query:
    node: strawberry.relay.Node
    nodes: List[strawberry.relay.Node]
    node_optional: Optional[strawberry.relay.Node]
    nodes_optional: List[Optional[strawberry.relay.Node]]
    fruits: strawberry.relay.Connection[Fruit]
    fruits_conn: strawberry.relay.Connection[Fruit] = strawberry.relay.connection()
    fruits_custom_pagination: FruitCustomPaginationConnection

    @strawberry.relay.connection
    def fruits_custom_resolver(
        self,
        info: Info[Any, Any],
        name_endswith: Optional[str] = None,
    ) -> Iterable[Fruit]:
        ...

    @strawberry.relay.connection
    def fruits_custom_resolver_returning_list(
        self,
        info: Info[Any, Any],
        name_endswith: Optional[str] = None,
    ) -> List[Fruit]:
        ...

reveal_type(Query.node)
reveal_type(Query.nodes)
reveal_type(Query.node_optional)
reveal_type(Query.nodes_optional)
reveal_type(Query.fruits)
reveal_type(Query.fruits_conn)
reveal_type(Query.fruits_custom_pagination)
reveal_type(Query.fruits_custom_resolver)
reveal_type(Query.fruits_custom_resolver_returning_list)
"""


def test_pyright():
    results = run_pyright(CODE)

    assert results == [
        Result(
            type="information",
            message='Type of "Query.node" is "Node"',
            line=64,
            column=13,
        ),
        Result(
            type="information",
            message='Type of "Query.nodes" is "List[Node]"',
            line=65,
            column=13,
        ),
        Result(
            type="information",
            message='Type of "Query.node_optional" is "Node | None"',
            line=66,
            column=13,
        ),
        Result(
            type="information",
            message='Type of "Query.nodes_optional" is "List[Node | None]"',
            line=67,
            column=13,
        ),
        Result(
            type="information",
            message='Type of "Query.fruits" is "Connection[Fruit]"',
            line=68,
            column=13,
        ),
        Result(
            type="information",
            message='Type of "Query.fruits_conn" is "Connection[Fruit]"',
            line=69,
            column=13,
        ),
        Result(
            type="information",
            message='Type of "Query.fruits_custom_pagination" is '
            '"FruitCustomPaginationConnection"',
            line=70,
            column=13,
        ),
        Result(
            type="information",
            message='Type of "Query.fruits_custom_resolver" is "ConnectionField"',
            line=71,
            column=13,
        ),
        Result(
            type="information",
            message='Type of "Query.fruits_custom_resolver_returning_list" is '
            '"ConnectionField"',
            line=72,
            column=13,
        ),
    ]
