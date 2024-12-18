from __future__ import annotations

import dataclasses
from collections.abc import (
    AsyncGenerator,
    AsyncIterable,
    AsyncIterator,
    Generator,
    Iterable,
    Iterator,
)
from typing import (
    Annotated,
    Any,
    NamedTuple,
    Optional,
    cast,
)
from typing_extensions import Self

import strawberry
from strawberry import relay
from strawberry.permission import BasePermission
from strawberry.relay.utils import to_base64
from strawberry.types import Info


@strawberry.type
class Fruit(relay.Node):
    id: relay.NodeID[int]
    name: str
    color: str

    @classmethod
    def resolve_nodes(
        cls,
        *,
        info: strawberry.Info,
        node_ids: Iterable[str],
        required: bool = False,
    ) -> Iterable[Optional[Self]]:
        if node_ids is not None:
            return [fruits[nid] if required else fruits.get(nid) for nid in node_ids]

        return fruits.values()

    @classmethod
    def is_type_of(cls, obj: Any, _info: strawberry.Info) -> bool:
        # This is here to support FruitConcrete, which is mimicing an integration
        # object which would return an object alike Fruit (e.g. the django integration)
        return isinstance(obj, (cls, FruitConcrete))


@dataclasses.dataclass
class FruitConcrete:
    id: int
    name: str
    color: str


@strawberry.type
class FruitAsync(relay.Node):
    id: relay.NodeID[int]
    name: str
    color: str

    @classmethod
    async def resolve_nodes(
        cls,
        *,
        info: Optional[Info] = None,
        node_ids: Iterable[str],
        required: bool = False,
    ) -> Iterable[Optional[Self]]:
        if node_ids is not None:
            return [
                fruits_async[nid] if required else fruits_async.get(nid)
                for nid in node_ids
            ]

        return fruits_async.values()

    @classmethod
    async def resolve_id(cls, root: Self, *, info: strawberry.Info) -> str:
        return str(root.id)


@strawberry.type
class FruitCustomPaginationConnection(relay.Connection[Fruit]):
    @strawberry.field
    def something(self) -> str:
        return "foobar"

    @classmethod
    def resolve_connection(
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
    ) -> Self:
        edges_mapping = {
            to_base64("fruit_name", n.name): relay.Edge(
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
            page_info=relay.PageInfo(
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


class FruitAlike(NamedTuple):
    id: int
    name: str
    color: str


@strawberry.type
class FruitAlikeConnection(relay.ListConnection[Fruit]):
    @classmethod
    def resolve_node(
        cls, node: FruitAlike, *, info: strawberry.Info, **kwargs: Any
    ) -> Fruit:
        return Fruit(
            id=node.id,
            name=node.name,
            color=node.color,
        )


def fruits_resolver() -> Iterable[Fruit]:
    return fruits.values()


async def fruits_async_resolver() -> Iterable[FruitAsync]:
    return fruits_async.values()


class DummyPermission(BasePermission):
    message = "Dummy message"

    async def has_permission(
        self, source: Any, info: strawberry.Info, **kwargs: Any
    ) -> bool:
        return True


@strawberry.type
class Query:
    node: relay.Node = relay.node()
    node_with_async_permissions: relay.Node = relay.node(
        permission_classes=[DummyPermission]
    )
    nodes: list[relay.Node] = relay.node()
    node_optional: Optional[relay.Node] = relay.node()
    nodes_optional: list[Optional[relay.Node]] = relay.node()
    fruits: relay.ListConnection[Fruit] = relay.connection(resolver=fruits_resolver)
    fruits_lazy: relay.ListConnection[
        Annotated[Fruit, strawberry.lazy("tests.relay.schema")]
    ] = relay.connection(resolver=fruits_resolver)
    fruits_async: relay.ListConnection[FruitAsync] = relay.connection(
        resolver=fruits_async_resolver
    )
    fruits_custom_pagination: FruitCustomPaginationConnection = relay.connection(
        resolver=fruits_resolver
    )

    @relay.connection(relay.ListConnection[Fruit])
    def fruits_concrete_resolver(
        self,
        info: strawberry.Info,
        name_endswith: Optional[str] = None,
    ) -> list[Fruit]:
        # This is mimicing integrations, like Django
        return [
            cast(
                Fruit,
                FruitConcrete(
                    id=f.id,
                    name=f.name,
                    color=f.color,
                ),
            )
            for f in fruits.values()
            if name_endswith is None or f.name.endswith(name_endswith)
        ]

    @relay.connection(relay.ListConnection[Fruit])
    def fruits_custom_resolver(
        self,
        info: strawberry.Info,
        name_endswith: Optional[str] = None,
    ) -> list[Fruit]:
        return [
            f
            for f in fruits.values()
            if name_endswith is None or f.name.endswith(name_endswith)
        ]

    @relay.connection(relay.ListConnection[Fruit])
    def fruits_custom_resolver_lazy(
        self,
        info: strawberry.Info,
        name_endswith: Optional[str] = None,
    ) -> list[Annotated[Fruit, strawberry.lazy("tests.relay.schema")]]:
        return [
            f
            for f in fruits.values()
            if name_endswith is None or f.name.endswith(name_endswith)
        ]

    @relay.connection(relay.ListConnection[Fruit])
    def fruits_custom_resolver_iterator(
        self,
        info: strawberry.Info,
        name_endswith: Optional[str] = None,
    ) -> Iterator[Fruit]:
        for f in fruits.values():
            if name_endswith is None or f.name.endswith(name_endswith):
                yield f

    @relay.connection(relay.ListConnection[Fruit])
    def fruits_custom_resolver_iterable(
        self,
        info: strawberry.Info,
        name_endswith: Optional[str] = None,
    ) -> Iterator[Fruit]:
        for f in fruits.values():
            if name_endswith is None or f.name.endswith(name_endswith):
                yield f

    @relay.connection(relay.ListConnection[Fruit])
    def fruits_custom_resolver_generator(
        self,
        info: strawberry.Info,
        name_endswith: Optional[str] = None,
    ) -> Generator[Fruit, None, None]:
        for f in fruits.values():
            if name_endswith is None or f.name.endswith(name_endswith):
                yield f

    @relay.connection(relay.ListConnection[Fruit])
    async def fruits_custom_resolver_async_iterable(
        self,
        info: strawberry.Info,
        name_endswith: Optional[str] = None,
    ) -> AsyncIterable[Fruit]:
        for f in fruits.values():
            if name_endswith is None or f.name.endswith(name_endswith):
                yield f

    @relay.connection(relay.ListConnection[Fruit])
    async def fruits_custom_resolver_async_iterator(
        self,
        info: strawberry.Info,
        name_endswith: Optional[str] = None,
    ) -> AsyncIterator[Fruit]:
        for f in fruits.values():
            if name_endswith is None or f.name.endswith(name_endswith):
                yield f

    @relay.connection(relay.ListConnection[Fruit])
    async def fruits_custom_resolver_async_generator(
        self,
        info: strawberry.Info,
        name_endswith: Optional[str] = None,
    ) -> AsyncGenerator[Fruit, None]:
        for f in fruits.values():
            if name_endswith is None or f.name.endswith(name_endswith):
                yield f

    @relay.connection(FruitAlikeConnection)
    def fruit_alike_connection_custom_resolver(
        self,
        info: strawberry.Info,
        name_endswith: Optional[str] = None,
    ) -> list[FruitAlike]:
        return [
            FruitAlike(f.id, f.name, f.color)
            for f in fruits.values()
            if name_endswith is None or f.name.endswith(name_endswith)
        ]

    @strawberry.relay.connection(strawberry.relay.ListConnection[Fruit])
    def some_fruits(self) -> list[Fruit]:
        return [Fruit(id=x, name="apple", color="green") for x in range(200)]


@strawberry.type
class CreateFruitPayload:
    fruit: Fruit


@strawberry.type
class Mutation:
    @strawberry.mutation
    def create_fruit(
        self,
        info: strawberry.Info,
        name: str,
        color: str,
    ) -> CreateFruitPayload: ...


schema = strawberry.Schema(query=Query, mutation=Mutation)
