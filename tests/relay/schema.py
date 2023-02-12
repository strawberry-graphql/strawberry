from collections import namedtuple
from typing import (
    Any,
    AsyncGenerator,
    AsyncIterable,
    AsyncIterator,
    Generator,
    Iterable,
    Iterator,
    List,
    Optional,
)

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
class FruitAsync(strawberry.relay.Node):
    id: strawberry.relay.NodeID[int]
    name: str
    color: str

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
        **kwargs: Any,
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


FruitAlike = namedtuple("FruitAlike", ["id", "name", "color"])


def fruit_converter(fruit_alike: FruitAlike) -> Fruit:
    return Fruit(
        id=fruit_alike.id,
        name=fruit_alike.name,
        color=fruit_alike.color,
    )


def fruit_converter_forward_ref(fruit_alike: FruitAlike) -> "Fruit":
    return Fruit(
        id=fruit_alike.id,
        name=fruit_alike.name,
        color=fruit_alike.color,
    )


@strawberry.type
class Query:
    node: strawberry.relay.Node
    nodes: List[strawberry.relay.Node]
    node_optional: Optional[strawberry.relay.Node]
    nodes_optional: List[Optional[strawberry.relay.Node]]
    fruits: strawberry.relay.Connection[Fruit]
    fruits_async: strawberry.relay.Connection[FruitAsync]
    fruits_custom_pagination: FruitCustomPaginationConnection

    @strawberry.relay.connection
    def fruits_custom_resolver(
        self,
        info: Info,
        name_endswith: Optional[str] = None,
    ) -> List[Fruit]:
        return [
            f
            for f in fruits.values()
            if name_endswith is None or f.name.endswith(name_endswith)
        ]

    @strawberry.relay.connection(node_converter=fruit_converter)
    def fruits_custom_resolver_with_node_converter(
        self,
        info: Info,
        name_endswith: Optional[str] = None,
    ) -> List[FruitAlike]:
        return [
            FruitAlike(f.id, f.name, f.color)
            for f in fruits.values()
            if name_endswith is None or f.name.endswith(name_endswith)
        ]

    @strawberry.relay.connection(node_converter=fruit_converter_forward_ref)
    def fruits_custom_resolver_with_node_converter_forward_ref(
        self,
        info: Info,
        name_endswith: Optional[str] = None,
    ) -> List[FruitAlike]:
        return [
            FruitAlike(f.id, f.name, f.color)
            for f in fruits.values()
            if name_endswith is None or f.name.endswith(name_endswith)
        ]

    @strawberry.relay.connection
    def fruits_custom_resolver_iterator(
        self,
        info: Info,
        name_endswith: Optional[str] = None,
    ) -> Iterator[Fruit]:
        for f in fruits.values():
            if name_endswith is None or f.name.endswith(name_endswith):
                yield f

    @strawberry.relay.connection
    def fruits_custom_resolver_iterable(
        self,
        info: Info,
        name_endswith: Optional[str] = None,
    ) -> Iterator[Fruit]:
        for f in fruits.values():
            if name_endswith is None or f.name.endswith(name_endswith):
                yield f

    @strawberry.relay.connection
    def fruits_custom_resolver_generator(
        self,
        info: Info,
        name_endswith: Optional[str] = None,
    ) -> Generator[Fruit, None, None]:
        for f in fruits.values():
            if name_endswith is None or f.name.endswith(name_endswith):
                yield f

    @strawberry.relay.connection
    async def fruits_custom_resolver_async_iterable(
        self,
        info: Info,
        name_endswith: Optional[str] = None,
    ) -> AsyncIterable[Fruit]:
        for f in fruits.values():
            if name_endswith is None or f.name.endswith(name_endswith):
                yield f

    @strawberry.relay.connection
    async def fruits_custom_resolver_async_iterator(
        self,
        info: Info,
        name_endswith: Optional[str] = None,
    ) -> AsyncIterator[Fruit]:
        for f in fruits.values():
            if name_endswith is None or f.name.endswith(name_endswith):
                yield f

    @strawberry.relay.connection
    async def fruits_custom_resolver_async_generator(
        self,
        info: Info,
        name_endswith: Optional[str] = None,
    ) -> AsyncGenerator[Fruit, None]:
        for f in fruits.values():
            if name_endswith is None or f.name.endswith(name_endswith):
                yield f


schema = strawberry.Schema(query=Query)
