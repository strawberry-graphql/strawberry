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
        nodes: Union[
            Iterator[Fruit],
            AsyncIterator[Fruit],
            Iterable[Fruit],
            AsyncIterable[Fruit],
        ],
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


class FruitAlike:
    ...


def fruit_converter(fruit_alike: FruitAlike) -> Fruit:
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
    ) -> List[Fruit]:
        ...

    @strawberry.relay.connection(node_converter=fruit_converter)
    def fruits_custom_resolver_with_node_converter(
        self,
        info: Info[Any, Any],
        name_endswith: Optional[str] = None,
    ) -> List[FruitAlike]:
        ...

    @strawberry.relay.connection
    def fruits_custom_resolver_iterator(
        self,
        info: Info[Any, Any],
        name_endswith: Optional[str] = None,
    ) -> Iterator[Fruit]:
        ...

    @strawberry.relay.connection
    def fruits_custom_resolver_iterable(
        self,
        info: Info[Any, Any],
        name_endswith: Optional[str] = None,
    ) -> Iterable[Fruit]:
        ...

    @strawberry.relay.connection
    def fruits_custom_resolver_generator(
        self,
        info: Info[Any, Any],
        name_endswith: Optional[str] = None,
    ) -> Generator[Fruit, None, None]:
        ...

    @strawberry.relay.connection
    async def fruits_custom_resolver_async_iterator(
        self,
        info: Info[Any, Any],
        name_endswith: Optional[str] = None,
    ) -> AsyncIterator[Fruit]:
        ...

    @strawberry.relay.connection
    async def fruits_custom_resolver_async_iterable(
        self,
        info: Info[Any, Any],
        name_endswith: Optional[str] = None,
    ) -> AsyncIterable[Fruit]:
        ...

    @strawberry.relay.connection
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
reveal_type(Query.fruits_custom_resolver_with_node_converter)
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
            line=136,
            column=13,
        ),
        Result(
            type="information",
            message='Type of "Query.nodes" is "List[Node]"',
            line=137,
            column=13,
        ),
        Result(
            type="information",
            message='Type of "Query.node_optional" is "Node | None"',
            line=138,
            column=13,
        ),
        Result(
            type="information",
            message='Type of "Query.nodes_optional" is "List[Node | None]"',
            line=139,
            column=13,
        ),
        Result(
            type="information",
            message='Type of "Query.fruits" is "Connection[Fruit]"',
            line=140,
            column=13,
        ),
        Result(
            type="information",
            message='Type of "Query.fruits_conn" is "Connection[Fruit]"',
            line=141,
            column=13,
        ),
        Result(
            type="information",
            message='Type of "Query.fruits_custom_pagination" is '
            '"FruitCustomPaginationConnection"',
            line=142,
            column=13,
        ),
        Result(
            type="information",
            message='Type of "Query.fruits_custom_resolver" is "ConnectionField"',
            line=143,
            column=13,
        ),
        Result(
            type="information",
            message='Type of "Query.fruits_custom_resolver_with_node_converter" is '
            '"Any"',
            line=144,
            column=13,
        ),
        Result(
            type="information",
            message='Type of "Query.fruits_custom_resolver_iterator" is '
            '"ConnectionField"',
            line=145,
            column=13,
        ),
        Result(
            type="information",
            message='Type of "Query.fruits_custom_resolver_iterable" is '
            '"ConnectionField"',
            line=146,
            column=13,
        ),
        Result(
            type="information",
            message='Type of "Query.fruits_custom_resolver_generator" is '
            '"ConnectionField"',
            line=147,
            column=13,
        ),
        Result(
            type="information",
            message='Type of "Query.fruits_custom_resolver_async_iterator" is '
            '"ConnectionField"',
            line=148,
            column=13,
        ),
        Result(
            type="information",
            message='Type of "Query.fruits_custom_resolver_async_iterable" is '
            '"ConnectionField"',
            line=149,
            column=13,
        ),
        Result(
            type="information",
            message='Type of "Query.fruits_custom_resolver_async_generator" is '
            '"ConnectionField"',
            line=150,
            column=13,
        ),
    ]
