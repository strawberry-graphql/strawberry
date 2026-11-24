import pytest
from pytest_codspeed import BenchmarkFixture

import strawberry
from strawberry.schema.config import StrawberryConfig
from strawberry.schema.types.scalar import DEFAULT_SCALAR_REGISTRY
from strawberry.types.arguments import convert_argument
from strawberry.types.base import StrawberryList


@pytest.mark.parametrize(
    "ntypes",
    [
        pytest.param(2**k, marks=pytest.mark.benchmark_stress) if k >= 20 else 2**k
        for k in range(14, 23, 2)
    ],
)
def test_convert_argument_large_list_v2(benchmark: BenchmarkFixture, ntypes):
    test_value = list(range(ntypes))
    type_ = StrawberryList(int)
    config = StrawberryConfig()

    def run():
        return convert_argument(test_value, type_, DEFAULT_SCALAR_REGISTRY, config)

    assert benchmark(run) == test_value


@strawberry.type
class Query:
    @strawberry.field
    def total(self, ids: list[int]) -> int:
        return len(ids)


schema = strawberry.Schema(query=Query)
large_list_query = "query ($ids: [Int!]!) { total(ids: $ids) }"


@pytest.mark.parametrize(
    "count",
    [
        pytest.param(2**k, marks=pytest.mark.benchmark_stress) if k >= 18 else 2**k
        for k in range(10, 19, 4)
    ],
)
def test_execute_with_large_list_argument(benchmark: BenchmarkFixture, count: int):
    # Unlike the conversion alone, this includes graphql-core's coercion of the
    # list, which is what a request pays for it
    variables = {"ids": list(range(count))}

    result = benchmark(schema.execute_sync, large_list_query, variable_values=variables)

    assert result.errors is None
    assert result.data == {"total": count}
