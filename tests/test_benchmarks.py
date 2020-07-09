import asyncio
from typing import List

import pytest

import strawberry
from strawberry.graphql import execute
from graphql import graphql, graphql_sync


@pytest.mark.asyncio
async def test_graphql(benchmark):
    @strawberry.type
    class Patron:
        id: int
        name: str
        age: int


    @strawberry.type
    class Query:
        @strawberry.field
        async def patrons(self, info) -> List[Patron]:
            return [Patron(id=i, name="Patrick", age=100) for i in range(100)]

    schema = strawberry.Schema(query=Query)

    query = """
        query something{
          patrons {
            id
            name
            age
          }
        }
    """
    result = await benchmark(lambda: graphql(schema, query))
    assert len(result.data['patrons']) == 100
    assert not result.errors


def test_graphql_sync(benchmark):
    @strawberry.type
    class Patron:
        id: int
        name: str
        age: int

    @strawberry.type
    class Query:
        @strawberry.field
        def patrons(self, info) -> List[Patron]:
            return [Patron(id=i, name="Patrick", age=100) for i in range(100)]

    schema = strawberry.Schema(query=Query)

    query = """
        query something{
          patrons {
            id
            name
            age
          }
        }
    """
    result = benchmark(lambda: graphql_sync(schema, query))
    assert len(result.data['patrons']) == 100
    assert not result.errors
