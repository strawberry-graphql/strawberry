from .utils import Result, requires_pyright, run_pyright, skip_on_windows

pytestmark = [skip_on_windows, requires_pyright]


CODE = """
from typing import (
    Any,
    AsyncIterator,
    AsyncGenerator,
    AsyncIterable,
    Generator,
    Iterable,
    Iterator,
    List,
    Optional,
    Union,
)

import strawberry
from strawberry import relay
from strawberry.types import Info
from typing_extensions import Self


@strawberry.type
class Fruit(relay.Node):
    id: relay.NodeID[int]
    name: str
    color: str


@strawberry.type
class FruitCustomPaginationConnection(relay.Connection[Fruit]):
    @strawberry.field
    def something(self) -> str:
        return "foobar"

    @classmethod
    def resolve_connection(
        cls,
        nodes: Union[
            Iterator[Fruit],
            AsyncIterator[Fruit],
            Iterable[Fruit],
            AsyncIterable[Fruit],
        ],
        *,
        info: Optional[Info[Any, Any]] = None,
        before: Optional[str] = None,
        after: Optional[str] = None,
        first: Optional[int] = None,
        last: Optional[int] = None,
        **kwargs: Any,
    ) -> Self:
        ...


class FruitAlike:
    ...


def fruits_resolver() -> List[Fruit]:
    ...


@strawberry.type
class Query:
    node: relay.Node
    nodes: List[relay.Node]
    node_optional: Optional[relay.Node]
    nodes_optional: List[Optional[relay.Node]]
    fruits: relay.Connection[Fruit] = strawberry.relay.connection(
        resolver=fruits_resolver,
    )
    fruits_conn: relay.Connection[Fruit] = relay.connection(
        resolver=fruits_resolver,
    )
    fruits_custom_pagination: FruitCustomPaginationConnection

    @relay.connection(relay.Connection[Fruit])
    def fruits_custom_resolver(
        self,
        info: Info[Any, Any],
        name_endswith: Optional[str] = None,
    ) -> List[Fruit]:
        ...

    @relay.connection(relay.Connection[Fruit])
    def fruits_custom_resolver_iterator(
        self,
        info: Info[Any, Any],
        name_endswith: Optional[str] = None,
    ) -> Iterator[Fruit]:
        ...

    @relay.connection(relay.Connection[Fruit])
    def fruits_custom_resolver_iterable(
        self,
        info: Info[Any, Any],
        name_endswith: Optional[str] = None,
    ) -> Iterable[Fruit]:
        ...

    @relay.connection(relay.Connection[Fruit])
    def fruits_custom_resolver_generator(
        self,
        info: Info[Any, Any],
        name_endswith: Optional[str] = None,
    ) -> Generator[Fruit, None, None]:
        ...

    @relay.connection(relay.Connection[Fruit])
    async def fruits_custom_resolver_async_iterator(
        self,
        info: Info[Any, Any],
        name_endswith: Optional[str] = None,
    ) -> AsyncIterator[Fruit]:
        ...

    @relay.connection(relay.Connection[Fruit])
    async def fruits_custom_resolver_async_iterable(
        self,
        info: Info[Any, Any],
        name_endswith: Optional[str] = None,
    ) -> AsyncIterable[Fruit]:
        ...

    @relay.connection(relay.Connection[Fruit])
    async def fruits_custom_resolver_async_generator(
        self,
        info: Info[Any, Any],
        name_endswith: Optional[str] = None,
    ) -> AsyncGenerator[Fruit, None]:
        ...

reveal_type(Query.node)
reveal_type(Query.nodes)
reveal_type(Query.node_optional)
reveal_type(Query.nodes_optional)
reveal_type(Query.fruits)
reveal_type(Query.fruits_conn)
reveal_type(Query.fruits_custom_pagination)
reveal_type(Query.fruits_custom_resolver)
reveal_type(Query.fruits_custom_resolver_iterator)
reveal_type(Query.fruits_custom_resolver_iterable)
reveal_type(Query.fruits_custom_resolver_generator)
reveal_type(Query.fruits_custom_resolver_async_iterator)
reveal_type(Query.fruits_custom_resolver_async_iterable)
reveal_type(Query.fruits_custom_resolver_async_generator)
"""


def test_pyright():
    results = run_pyright(CODE)

    assert results == [
        Result(
            type="information",
            message='Type of "Query.node" is "Node"',
            line=132,
            column=13,
        ),
        Result(
            type="information",
            message='Type of "Query.nodes" is "List[Node]"',
            line=133,
            column=13,
        ),
        Result(
            type="information",
            message='Type of "Query.node_optional" is "Node | None"',
            line=134,
            column=13,
        ),
        Result(
            type="information",
            message='Type of "Query.nodes_optional" is "List[Node | None]"',
            line=135,
            column=13,
        ),
        Result(
            type="information",
            message='Type of "Query.fruits" is "Connection[Fruit]"',
            line=136,
            column=13,
        ),
        Result(
            type="information",
            message='Type of "Query.fruits_conn" is "Connection[Fruit]"',
            line=137,
            column=13,
        ),
        Result(
            type="information",
            message='Type of "Query.fruits_custom_pagination" is '
            '"FruitCustomPaginationConnection"',
            line=138,
            column=13,
        ),
        Result(
            type="information",
            message='Type of "Query.fruits_custom_resolver" is "Any"',
            line=139,
            column=13,
        ),
        Result(
            type="information",
            message='Type of "Query.fruits_custom_resolver_iterator" is "Any"',
            line=140,
            column=13,
        ),
        Result(
            type="information",
            message='Type of "Query.fruits_custom_resolver_iterable" is "Any"',
            line=141,
            column=13,
        ),
        Result(
            type="information",
            message='Type of "Query.fruits_custom_resolver_generator" is "Any"',
            line=142,
            column=13,
        ),
        Result(
            type="information",
            message='Type of "Query.fruits_custom_resolver_async_iterator" is ' '"Any"',
            line=143,
            column=13,
        ),
        Result(
            type="information",
            message='Type of "Query.fruits_custom_resolver_async_iterable" is ' '"Any"',
            line=144,
            column=13,
        ),
        Result(
            type="information",
            message='Type of "Query.fruits_custom_resolver_async_generator" is '
            '"Any"',
            line=145,
            column=13,
        ),
    ]
