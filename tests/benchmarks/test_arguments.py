import pytest
from pytest_codspeed import BenchmarkFixture

from strawberry.schema.config import StrawberryConfig
from strawberry.schema.types.scalar import DEFAULT_SCALAR_REGISTRY
from strawberry.types.arguments import convert_argument
from strawberry.types.base import StrawberryList


@pytest.mark.parametrize("ntypes", [2**k for k in range(14, 23, 2)])
def test_convert_argument_large_list(benchmark: BenchmarkFixture, ntypes):
    test_value = list(range(ntypes))
    type_ = StrawberryList(int)

    def run():
        result = convert_argument(
            test_value, type_, DEFAULT_SCALAR_REGISTRY, StrawberryConfig()
        )
        assert test_value == result

    benchmark(run)
