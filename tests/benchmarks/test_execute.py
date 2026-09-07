import asyncio
from datetime import date
from typing import cast

import pytest
from pytest_codspeed.plugin import BenchmarkFixture

import strawberry
from strawberry.scalars import ID


@pytest.mark.benchmark
def test_execute_v2(
    benchmark: BenchmarkFixture, benchmark_loop: asyncio.AbstractEventLoop
):
    birthday = date(2000, 1, 1)
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
        tags: list[str]

        @strawberry.field
        def pets(self) -> list[Pet]:
            return [
                Pet(
                    id=i,
                    name=pets[i % len(pets)],
                )
                for i in range(5)
            ]

    @strawberry.type
    class Query:
        @strawberry.field
        def patrons(self) -> list[Patron]:
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

    def run():
        return benchmark_loop.run_until_complete(schema.execute(query))

    result = benchmark(run)
    assert result.errors is None
    assert result.data is not None

    assert len(result.data["patrons"]) == 1000
    assert all(len(patron["pets"]) == 5 for patron in result.data["patrons"])
    assert result.data["patrons"][0]["birthday"] == "2000-01-01"


@pytest.mark.parametrize(
    "ntypes", [1, 16, 256, pytest.param(4096, marks=pytest.mark.benchmark_stress)]
)
def test_interface_performance_v2(
    benchmark: BenchmarkFixture, ntypes: int, benchmark_loop: asyncio.AbstractEventLoop
):
    @strawberry.interface
    class Item:
        id: ID

    CONCRETE_TYPES: list[type[Item]] = [
        strawberry.type(type(f"Item{i}", (Item,), {})) for i in range(ntypes)
    ]

    @strawberry.type
    class Query:
        items: list[Item]

    schema = strawberry.Schema(query=Query, types=CONCRETE_TYPES)
    query = "query { items { id } }"

    def run():
        return benchmark_loop.run_until_complete(
            schema.execute(
                query,
                root_value=Query(
                    items=[
                        CONCRETE_TYPES[i % ntypes](id=cast("ID", i))
                        for i in range(1000)
                    ]
                ),
            )
        )

    result = benchmark(run)
    assert result.errors is None
    assert result.data == {"items": [{"id": str(i)} for i in range(1000)]}
