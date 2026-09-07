from collections.abc import Iterable

import pytest
from pytest_codspeed import BenchmarkFixture

import strawberry
from strawberry import relay


@strawberry.federation.type(keys=["id"])
class Product:
    id: strawberry.ID
    name: str

    @classmethod
    def resolve_reference(cls, id: strawberry.ID) -> "Product":
        return cls(id=id, name=f"Product {id}")


@strawberry.type
class RelayProduct(relay.Node):
    code: relay.NodeID[int]
    name: str


nodes = [RelayProduct(code=i, name=f"Product {i}") for i in range(1000)]


@strawberry.type
class Query:
    @relay.connection(relay.ListConnection[RelayProduct])
    def products(self) -> Iterable[RelayProduct]:
        return nodes


@pytest.mark.parametrize("count", [1, 100])
def test_federation_entities(benchmark: BenchmarkFixture, count: int):
    schema = strawberry.federation.Schema(query=Query, types=[Product])
    query = "query ($items: [_Any!]!) { _entities(representations: $items) { ... on Product { id name } } }"

    def setup():
        # Entity resolution consumes __typename; every invocation needs fresh input.
        return (query,), {
            "variable_values": {
                "items": [{"__typename": "Product", "id": str(i)} for i in range(count)]
            }
        }

    result = benchmark.pedantic(
        schema.execute_sync, setup=setup, rounds=30, iterations=1
    )
    assert result.errors is None
    assert result.data == {
        "_entities": [{"id": str(i), "name": f"Product {i}"} for i in range(count)]
    }


@pytest.mark.parametrize("count", [1, 100])
def test_relay_connection(benchmark: BenchmarkFixture, count: int):
    schema = strawberry.Schema(query=Query)
    result = benchmark(
        schema.execute_sync,
        "query ($count: Int!) { products(first: $count) { edges { cursor node { id name } } pageInfo { hasNextPage hasPreviousPage } } }",
        variable_values={"count": count},
    )
    assert result.errors is None
    connection = result.data["products"]
    assert len(connection["edges"]) == count
    assert [edge["node"]["name"] for edge in connection["edges"]] == [
        f"Product {i}" for i in range(count)
    ]
    assert len({edge["cursor"] for edge in connection["edges"]}) == count
    assert connection["pageInfo"] == {"hasNextPage": True, "hasPreviousPage": False}
