from typing import List

import pytest

import strawberry
from strawberry.graphql import execute


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "items", [25, 100, 250],
)
async def test_execute(aio_benchmark, items):
    @strawberry.type
    class Patron:
        id: int
        name: str
        age: int

    @strawberry.type
    class Query:
        @strawberry.field
        async def patrons(self, info) -> List[Patron]:
            return [
                Patron(id=i, name="Patrick", age=100) for i in range(items)
            ]

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
    result = aio_benchmark(execute, schema, query)
    assert len(result.data["patrons"]) == items
    assert not result.errors
