from typing import List

import pytest

import strawberry
from asgiref.sync import async_to_sync
from strawberry.graphql import execute


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "items", [25, 100, 250],
)
def test_execute(benchmark, items):
    @strawberry.type
    class Patron:
        id: int
        name: str
        age: int

    @strawberry.type
    class Query:
        @strawberry.field
        def patrons(self, info) -> List[Patron]:
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
    result = benchmark(async_to_sync(execute), schema, query)
    assert len(result.data["patrons"]) == items
    assert not result.errors
