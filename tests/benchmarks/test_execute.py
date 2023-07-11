import datetime
import random
from datetime import date
from typing import List

import pytest
from asgiref.sync import async_to_sync
from pytest_codspeed.plugin import BenchmarkFixture

import strawberry


@pytest.mark.benchmark
def test_execute(benchmark: BenchmarkFixture):
    birthday = datetime.datetime.now()
    pets = ("cat", "shark", "dog", "lama")

    @strawberry.type
    class Pet:
        id: int
        name: str

    @strawberry.type
    class Patron:
        id: int
        name: str
        age: int
        birthday: date
        tags: List[str]

        @strawberry.field
        def pets(self) -> List[Pet]:
            return [
                Pet(
                    id=i,
                    name=random.choice(pets),  # noqa: S311
                )
                for i in range(5)
            ]

    @strawberry.type
    class Query:
        @strawberry.field
        def patrons(self) -> List[Patron]:
            return [
                Patron(
                    id=i,
                    name="Patrick",
                    age=100,
                    birthday=birthday,
                    tags=["go", "ajax"],
                )
                for i in range(1000)
            ]

    schema = strawberry.Schema(query=Query)

    query = """
        query something{
          patrons {
            id
            name
            age
            birthday
            tags
            pets {
                id
                name
            }
          }
        }
    """

    benchmark(async_to_sync(schema.execute), query)
