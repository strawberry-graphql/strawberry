import asyncio
from typing import Generic, TypeVar

from pytest_codspeed.plugin import BenchmarkFixture

import strawberry

T = TypeVar("T")


@strawberry.input(description="Filter for GraphQL queries")
class GraphQLFilter(Generic[T]):
    """EXTERNAL Filter for GraphQL queries"""

    eq: T | None = None
    in_: list[T] | None = None
    nin: list[T] | None = None
    gt: T | None = None
    gte: T | None = None
    lt: T | None = None
    lte: T | None = None
    contains: T | None = None
    icontains: T | None = None


@strawberry.type
class Author:
    name: str


@strawberry.type
class Book:
    title: str

    @strawberry.field
    async def authors(
        self,
        name: GraphQLFilter[str] | None = None,
    ) -> list[Author]:
        return [Author(name="F. Scott Fitzgerald")]


def get_books():
    return [
        Book(title="The Great Gatsby"),
    ] * 1000


@strawberry.type
class Query:
    books: list[Book] = strawberry.field(resolver=get_books)


schema = strawberry.Schema(query=Query)

query = """{
    books {
        title
        authors(name: {eq: "F. Scott Fitzgerald"}) {
            name
        }
    }
}
"""


def test_execute_generic_input_v2(
    benchmark: BenchmarkFixture, benchmark_loop: asyncio.AbstractEventLoop
):
    def run():
        coroutine = schema.execute(query)

        return benchmark_loop.run_until_complete(coroutine)

    result = benchmark(run)

    assert not result.errors

    assert result.data is not None
    assert len(result.data["books"]) == 1000
    assert all(
        book["authors"] == [{"name": "F. Scott Fitzgerald"}]
        for book in result.data["books"]
    )
