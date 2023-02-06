from typing import Iterable, List, Optional
from typing_extensions import Self

import strawberry
from strawberry.relay.utils import to_base64
from strawberry.types import Info


@strawberry.type
class Fruit(strawberry.relay.Node):
    _id: strawberry.Private[int]
    name: str
    color: str

    @classmethod
    def resolve_id(cls, root: Self, *, info: Optional[Info] = None):
        return root._id

    @classmethod
    def resolve_nodes(
        cls,
        *,
        info: Optional[Info] = None,
        node_ids: Optional[Iterable[str]] = None,
    ):
        if node_ids is not None:
            return [fruits[nid] for nid in node_ids]

        return list(fruits.values())

    @classmethod
    def resolve_node(
        cls,
        node_id: str,
        *,
        info: Optional[Info] = None,
        required: bool = False,
    ):
        obj = fruits.get(node_id, None)
        if required and obj is None:
            raise ValueError(f"No fruit by id {node_id}")

        return obj


@strawberry.type
class FruitAsync(Fruit):
    @classmethod
    async def resolve_id(cls, root: Self, *, info: Optional[Info] = None):
        return super().resolve_id(root, info=info)

    @classmethod
    async def resolve_nodes(
        cls,
        *,
        info: Optional[Info] = None,
        node_ids: Optional[Iterable[str]] = None,
    ):
        if node_ids is not None:
            return [fruits_async[nid] for nid in node_ids]

        return list(fruits_async.values())

    @classmethod
    async def resolve_node(
        cls,
        node_id: str,
        *,
        info: Optional[Info] = None,
        required: bool = False,
    ):
        obj = fruits_async.get(node_id, None)
        if required and obj is None:
            raise ValueError(f"No fruit by id {node_id}")

        return obj


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
        info: Optional[Info] = None,
        total_count: Optional[int] = None,
        before: Optional[str] = None,
        after: Optional[str] = None,
        first: Optional[int] = None,
        last: Optional[int] = None,
    ):
        edges_mapping = {
            to_base64("fruit_name", n.name): strawberry.relay.Edge(
                node=n,
                cursor=to_base64("fruit_name", n.name),
            )
            for n in sorted(nodes, key=lambda f: f.name)
        }
        edges = list(edges_mapping.values())
        first_edge = edges[0] if edges else None
        last_edge = edges[-1] if edges else None

        if after is not None:
            after_edge_idx = edges.index(edges_mapping[after])
            edges = [e for e in edges if edges.index(e) > after_edge_idx]

        if before is not None:
            before_edge_idx = edges.index(edges_mapping[before])
            edges = [e for e in edges if edges.index(e) < before_edge_idx]

        if first is not None:
            edges = edges[:first]

        if last is not None:
            edges = edges[-last:]

        return cls(
            edges=edges,
            page_info=strawberry.relay.PageInfo(
                start_cursor=edges[0].cursor if edges else None,
                end_cursor=edges[-1].cursor if edges else None,
                has_previous_page=first_edge is not None
                and bool(edges)
                and edges[0] != first_edge,
                has_next_page=last_edge is not None
                and bool(edges)
                and edges[-1] != last_edge,
            ),
        )


fruits = {
    str(f._id): f
    for f in [
        Fruit(_id=1, name="Banana", color="yellow"),
        Fruit(_id=2, name="Apple", color="red"),
        Fruit(_id=3, name="Pineapple", color="yellow"),
        Fruit(_id=4, name="Grape", color="purple"),
        Fruit(_id=5, name="Orange", color="orange"),
    ]
}
fruits_async = {
    k: FruitAsync(_id=v._id, name=v.name, color=v.color) for k, v in fruits.items()
}


@strawberry.type
class Query:
    node: strawberry.relay.Node
    nodes: List[strawberry.relay.Node]
    fruits: strawberry.relay.Connection[Fruit]
    fruits_async: strawberry.relay.Connection[FruitAsync]
    fruits_custom_pagination: FruitCustomPaginationConnection

    @strawberry.relay.connection
    def fruits_custom_resolver(
        self,
        info: Info,
        name_endswith: Optional[str] = None,
    ) -> Iterable[Fruit]:
        for f in fruits.values():
            if name_endswith is None or f.name.endswith(name_endswith):
                yield f

    @strawberry.relay.connection
    def fruits_custom_resolver_returning_list(
        self,
        info: Info,
        name_endswith: Optional[str] = None,
    ) -> List[Fruit]:
        return [
            f
            for f in fruits.values()
            if name_endswith is None or f.name.endswith(name_endswith)
        ]


schema = strawberry.Schema(query=Query)
