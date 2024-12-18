import asyncio
from typing import Generic, Optional, TypeVar

from pytest_codspeed.plugin import BenchmarkFixture

import strawberry

T = TypeVar("T")


@strawberry.input(description="Filter for GraphQL queries")
class GraphQLFilter(Generic[T]):
    """EXTERNAL Filter for GraphQL queries"""

    eq: Optional[T] = None
    in_: Optional[list[T]] = None
    nin: Optional[list[T]] = None
    gt: Optional[T] = None
    gte: Optional[T] = None
    lt: Optional[T] = None
    lte: Optional[T] = None
    contains: Optional[T] = None
    icontains: Optional[T] = None


@strawberry.type
class Author:
    name: str


@strawberry.type
class Book:
    title: str

    @strawberry.field
    async def authors(
        self,
        name: Optional[GraphQLFilter[str]] = None,
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


def test_execute_generic_input(benchmark: BenchmarkFixture):
    def run():
        coroutine = schema.execute(query)

        return asyncio.run(coroutine)

    result = benchmark(run)

    assert not result.errors
