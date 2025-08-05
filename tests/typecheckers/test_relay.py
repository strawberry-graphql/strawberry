from inline_snapshot import snapshot

from .utils.marks import requires_mypy, requires_pyright, skip_on_windows
from .utils.typecheck import Result, typecheck

pytestmark = [skip_on_windows, requires_pyright, requires_mypy]


CODE = """
from typing import (
    Any,
    AsyncIterator,
    AsyncGenerator,
    AsyncIterable,
    Generator,
    Iterable,
    Iterator,
    Optional,
    Union,
)

import strawberry
from strawberry import relay
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
        info: Optional[strawberry.Info] = None,
        before: Optional[str] = None,
        after: Optional[str] = None,
        first: Optional[int] = None,
        last: Optional[int] = None,
        **kwargs: Any,
    ) -> Self:
        ...


class FruitAlike:
    ...


def fruits_resolver() -> list[Fruit]:
    ...


@strawberry.type
class Query:
    node: relay.Node
    nodes: list[relay.Node]
    node_optional: Optional[relay.Node]
    nodes_optional: list[Optional[relay.Node]]
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
        info: strawberry.Info,
        name_endswith: Optional[str] = None,
    ) -> list[Fruit]:
        ...

    @relay.connection(relay.Connection[Fruit])
    def fruits_custom_resolver_iterator(
        self,
        info: strawberry.Info,
        name_endswith: Optional[str] = None,
    ) -> Iterator[Fruit]:
        ...

    @relay.connection(relay.Connection[Fruit])
    def fruits_custom_resolver_iterable(
        self,
        info: strawberry.Info,
        name_endswith: Optional[str] = None,
    ) -> Iterable[Fruit]:
        ...

    @relay.connection(relay.Connection[Fruit])
    def fruits_custom_resolver_generator(
        self,
        info: strawberry.Info,
        name_endswith: Optional[str] = None,
    ) -> Generator[Fruit, None, None]:
        ...

    @relay.connection(relay.Connection[Fruit])
    async def fruits_custom_resolver_async_iterator(
        self,
        info: strawberry.Info,
        name_endswith: Optional[str] = None,
    ) -> AsyncIterator[Fruit]:
        ...

    @relay.connection(relay.Connection[Fruit])
    async def fruits_custom_resolver_async_iterable(
        self,
        info: strawberry.Info,
        name_endswith: Optional[str] = None,
    ) -> AsyncIterable[Fruit]:
        ...

    @relay.connection(relay.Connection[Fruit])
    async def fruits_custom_resolver_async_generator(
        self,
        info: strawberry.Info,
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


def test():
    results = typecheck(CODE)

    assert results.pyright == snapshot(
        [
            Result(
                type="information",
                message='Type of "Query.node" is "Node"',
                line=130,
                column=13,
            ),
            Result(
                type="information",
                message='Type of "Query.nodes" is "list[Node]"',
                line=131,
                column=13,
            ),
            Result(
                type="information",
                message='Type of "Query.node_optional" is "Node | None"',
                line=132,
                column=13,
            ),
            Result(
                type="information",
                message='Type of "Query.nodes_optional" is "list[Node | None]"',
                line=133,
                column=13,
            ),
            Result(
                type="information",
                message='Type of "Query.fruits" is "Connection[Fruit]"',
                line=134,
                column=13,
            ),
            Result(
                type="information",
                message='Type of "Query.fruits_conn" is "Connection[Fruit]"',
                line=135,
                column=13,
            ),
            Result(
                type="information",
                message='Type of "Query.fruits_custom_pagination" is "FruitCustomPaginationConnection"',
                line=136,
                column=13,
            ),
            Result(
                type="information",
                message='Type of "Query.fruits_custom_resolver" is "Any"',
                line=137,
                column=13,
            ),
            Result(
                type="information",
                message='Type of "Query.fruits_custom_resolver_iterator" is "Any"',
                line=138,
                column=13,
            ),
            Result(
                type="information",
                message='Type of "Query.fruits_custom_resolver_iterable" is "Any"',
                line=139,
                column=13,
            ),
            Result(
                type="information",
                message='Type of "Query.fruits_custom_resolver_generator" is "Any"',
                line=140,
                column=13,
            ),
            Result(
                type="information",
                message='Type of "Query.fruits_custom_resolver_async_iterator" is "Any"',
                line=141,
                column=13,
            ),
            Result(
                type="information",
                message='Type of "Query.fruits_custom_resolver_async_iterable" is "Any"',
                line=142,
                column=13,
            ),
            Result(
                type="information",
                message='Type of "Query.fruits_custom_resolver_async_generator" is "Any"',
                line=143,
                column=13,
            ),
        ]
    )
    assert results.mypy == snapshot(
        [
            Result(type="error", message="Missing return statement", line=33, column=5),
            Result(type="error", message="Missing return statement", line=56, column=1),
            Result(
                type="error",
                message='Untyped decorator makes function "fruits_custom_resolver" untyped',
                line=74,
                column=6,
            ),
            Result(type="error", message="Missing return statement", line=75, column=5),
            Result(
                type="error",
                message='Untyped decorator makes function "fruits_custom_resolver_iterator" untyped',
                line=82,
                column=6,
            ),
            Result(type="error", message="Missing return statement", line=83, column=5),
            Result(
                type="error",
                message='Untyped decorator makes function "fruits_custom_resolver_iterable" untyped',
                line=90,
                column=6,
            ),
            Result(type="error", message="Missing return statement", line=91, column=5),
            Result(
                type="error",
                message='Untyped decorator makes function "fruits_custom_resolver_generator" untyped',
                line=98,
                column=6,
            ),
            Result(type="error", message="Missing return statement", line=99, column=5),
            Result(
                type="error",
                message='Untyped decorator makes function "fruits_custom_resolver_async_iterator" untyped',
                line=106,
                column=6,
            ),
            Result(
                type="error", message="Missing return statement", line=107, column=5
            ),
            Result(
                type="error",
                message='Untyped decorator makes function "fruits_custom_resolver_async_iterable" untyped',
                line=114,
                column=6,
            ),
            Result(
                type="error", message="Missing return statement", line=115, column=5
            ),
            Result(
                type="error",
                message='Untyped decorator makes function "fruits_custom_resolver_async_generator" untyped',
                line=122,
                column=6,
            ),
            Result(
                type="error", message="Missing return statement", line=123, column=5
            ),
            Result(
                type="note",
                message='Revealed type is "strawberry.relay.types.Node"',
                line=130,
                column=13,
            ),
            Result(
                type="note",
                message='Revealed type is "builtins.list[strawberry.relay.types.Node]"',
                line=131,
                column=13,
            ),
            Result(
                type="note",
                message='Revealed type is "Union[strawberry.relay.types.Node, None]"',
                line=132,
                column=13,
            ),
            Result(
                type="note",
                message='Revealed type is "builtins.list[Union[strawberry.relay.types.Node, None]]"',
                line=133,
                column=13,
            ),
            Result(
                type="note",
                message='Revealed type is "strawberry.relay.types.Connection[mypy_test.Fruit]"',
                line=134,
                column=13,
            ),
            Result(
                type="note",
                message='Revealed type is "strawberry.relay.types.Connection[mypy_test.Fruit]"',
                line=135,
                column=13,
            ),
            Result(
                type="note",
                message='Revealed type is "mypy_test.FruitCustomPaginationConnection"',
                line=136,
                column=13,
            ),
            Result(type="note", message='Revealed type is "Any"', line=137, column=13),
            Result(type="note", message='Revealed type is "Any"', line=138, column=13),
            Result(type="note", message='Revealed type is "Any"', line=139, column=13),
            Result(type="note", message='Revealed type is "Any"', line=140, column=13),
            Result(type="note", message='Revealed type is "Any"', line=141, column=13),
            Result(type="note", message='Revealed type is "Any"', line=142, column=13),
            Result(type="note", message='Revealed type is "Any"', line=143, column=13),
        ]
    )
