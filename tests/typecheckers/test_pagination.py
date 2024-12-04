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
    List,
    Optional,
    Union,
)

import strawberry
from strawberry.pagination import Connection, ListConnection, connection
from typing_extensions import Self


@strawberry.type
class Fruit:
    id: int
    name: str
    color: str


@strawberry.type
class FruitCustomPaginationConnection(Connection[Fruit]):
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


def fruits_resolver() -> List[Fruit]:
    ...


@strawberry.type
class Query:
    fruits: Connection[Fruit] = connection(
        resolver=fruits_resolver,
    )
    fruits_conn: Connection[Fruit] = connection(
        resolver=fruits_resolver,
    )
    fruits_custom_pagination: FruitCustomPaginationConnection

    @connection(Connection[Fruit])
    def fruits_custom_resolver(
        self,
        info: strawberry.Info,
        name_endswith: Optional[str] = None,
    ) -> List[Fruit]:
        ...

    @connection(Connection[Fruit])
    def fruits_custom_resolver_iterator(
        self,
        info: strawberry.Info,
        name_endswith: Optional[str] = None,
    ) -> Iterator[Fruit]:
        ...

    @connection(Connection[Fruit])
    def fruits_custom_resolver_iterable(
        self,
        info: strawberry.Info,
        name_endswith: Optional[str] = None,
    ) -> Iterable[Fruit]:
        ...

    @connection(Connection[Fruit])
    def fruits_custom_resolver_generator(
        self,
        info: strawberry.Info,
        name_endswith: Optional[str] = None,
    ) -> Generator[Fruit, None, None]:
        ...

    @connection(Connection[Fruit])
    async def fruits_custom_resolver_async_iterator(
        self,
        info: strawberry.Info,
        name_endswith: Optional[str] = None,
    ) -> AsyncIterator[Fruit]:
        ...

    @connection(Connection[Fruit])
    async def fruits_custom_resolver_async_iterable(
        self,
        info: strawberry.Info,
        name_endswith: Optional[str] = None,
    ) -> AsyncIterable[Fruit]:
        ...

    @connection(Connection[Fruit])
    async def fruits_custom_resolver_async_generator(
        self,
        info: strawberry.Info,
        name_endswith: Optional[str] = None,
    ) -> AsyncGenerator[Fruit, None]:
        ...

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
                type="error",
                message='Import "ListConnection" is not accessed',
                line=16,
                column=47,
            ),
            Result(
                type="information",
                message='Type of "Query.fruits" is "Connection[Fruit]"',
                line=127,
                column=13,
            ),
            Result(
                type="information",
                message='Type of "Query.fruits_conn" is "Connection[Fruit]"',
                line=128,
                column=13,
            ),
            Result(
                type="information",
                message='Type of "Query.fruits_custom_pagination" is "FruitCustomPaginationConnection"',
                line=129,
                column=13,
            ),
            Result(
                type="information",
                message='Type of "Query.fruits_custom_resolver" is "Any"',
                line=130,
                column=13,
            ),
            Result(
                type="information",
                message='Type of "Query.fruits_custom_resolver_iterator" is "Any"',
                line=131,
                column=13,
            ),
            Result(
                type="information",
                message='Type of "Query.fruits_custom_resolver_iterable" is "Any"',
                line=132,
                column=13,
            ),
            Result(
                type="information",
                message='Type of "Query.fruits_custom_resolver_generator" is "Any"',
                line=133,
                column=13,
            ),
            Result(
                type="information",
                message='Type of "Query.fruits_custom_resolver_async_iterator" is "Any"',
                line=134,
                column=13,
            ),
            Result(
                type="information",
                message='Type of "Query.fruits_custom_resolver_async_iterable" is "Any"',
                line=135,
                column=13,
            ),
            Result(
                type="information",
                message='Type of "Query.fruits_custom_resolver_async_generator" is "Any"',
                line=136,
                column=13,
            ),
        ]
    )
    assert results.mypy == snapshot(
        [
            Result(type="error", message="Missing return statement", line=34, column=5),
            Result(type="error", message="Missing return statement", line=57, column=1),
            Result(
                type="error",
                message='Untyped decorator makes function "fruits_custom_resolver" untyped',
                line=71,
                column=6,
            ),
            Result(type="error", message="Missing return statement", line=72, column=5),
            Result(
                type="error",
                message='Untyped decorator makes function "fruits_custom_resolver_iterator" untyped',
                line=79,
                column=6,
            ),
            Result(type="error", message="Missing return statement", line=80, column=5),
            Result(
                type="error",
                message='Untyped decorator makes function "fruits_custom_resolver_iterable" untyped',
                line=87,
                column=6,
            ),
            Result(type="error", message="Missing return statement", line=88, column=5),
            Result(
                type="error",
                message='Untyped decorator makes function "fruits_custom_resolver_generator" untyped',
                line=95,
                column=6,
            ),
            Result(type="error", message="Missing return statement", line=96, column=5),
            Result(
                type="error",
                message='Untyped decorator makes function "fruits_custom_resolver_async_iterator" untyped',
                line=103,
                column=6,
            ),
            Result(
                type="error", message="Missing return statement", line=104, column=5
            ),
            Result(
                type="error",
                message='Untyped decorator makes function "fruits_custom_resolver_async_iterable" untyped',
                line=111,
                column=6,
            ),
            Result(
                type="error", message="Missing return statement", line=112, column=5
            ),
            Result(
                type="error",
                message='Untyped decorator makes function "fruits_custom_resolver_async_generator" untyped',
                line=119,
                column=6,
            ),
            Result(
                type="error", message="Missing return statement", line=120, column=5
            ),
            Result(
                type="note",
                message='Revealed type is "strawberry.pagination.types.Connection[mypy_test.Fruit]"',
                line=127,
                column=13,
            ),
            Result(
                type="note",
                message='Revealed type is "strawberry.pagination.types.Connection[mypy_test.Fruit]"',
                line=128,
                column=13,
            ),
            Result(
                type="note",
                message='Revealed type is "mypy_test.FruitCustomPaginationConnection"',
                line=129,
                column=13,
            ),
            Result(type="note", message='Revealed type is "Any"', line=130, column=13),
            Result(type="note", message='Revealed type is "Any"', line=131, column=13),
            Result(type="note", message='Revealed type is "Any"', line=132, column=13),
            Result(type="note", message='Revealed type is "Any"', line=133, column=13),
            Result(type="note", message='Revealed type is "Any"', line=134, column=13),
            Result(type="note", message='Revealed type is "Any"', line=135, column=13),
            Result(type="note", message='Revealed type is "Any"', line=136, column=13),
        ]
    )
