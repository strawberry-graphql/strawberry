from typing import Iterable, List, Optional

import strawberry
from strawberry.relay.utils import to_base64
from strawberry.types import Info


@strawberry.type
class Fruit(strawberry.relay.Node):
    id: strawberry.relay.NodeID[int]
    name: str
    color: str

    @classmethod
    def resolve_nodes(
        cls,
        *,
        info: Info,
        node_ids: Optional[Iterable[str]] = None,
        required: bool = False,
    ):
        if node_ids is not None:
            return [fruits[nid] if required else fruits.get(nid) for nid in node_ids]

        return fruits.values()


@strawberry.type
class FruitAsync(Fruit):
    @classmethod
    async def resolve_nodes(
        cls,
        *,
        info: Optional[Info] = None,
        node_ids: Optional[Iterable[str]] = None,
        required: bool = False,
    ):
        if node_ids is not None:
            return [
                fruits_async[nid] if required else fruits_async.get(nid)
                for nid in node_ids
            ]

        return fruits_async.values()


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
    str(f.id): f
    for f in [
        Fruit(id=1, name="Banana", color="yellow"),
        Fruit(id=2, name="Apple", color="red"),
        Fruit(id=3, name="Pineapple", color="yellow"),
        Fruit(id=4, name="Grape", color="purple"),
        Fruit(id=5, name="Orange", color="orange"),
    ]
}
fruits_async = {
    k: FruitAsync(id=v.id, name=v.name, color=v.color) for k, v in fruits.items()
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

    @strawberry.relay.input_mutation
    def create_fruit(
        self,
        info: Info,
        name: str,
        color: str,
    ) -> Fruit:
        return Fruit(
            id=len(fruits) + 1,
            name=name,
            color=color,
        )

    @strawberry.relay.input_mutation
    async def create_fruit_async(
        self,
        info: Info,
        name: str,
        color: str,
    ) -> Fruit:
        return Fruit(
            id=len(fruits) + 1,
            name=name,
            color=color,
        )


schema = strawberry.Schema(query=Query)
