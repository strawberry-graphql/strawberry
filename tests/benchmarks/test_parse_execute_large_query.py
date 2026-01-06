from pathlib import Path

import pytest
from graphql import parse
from pytest_codspeed.plugin import BenchmarkFixture

from strawberry import Schema

from .api import Query

ROOT = Path(__file__).parent / "queries"
large_query = (ROOT / "large_items.graphql").read_text()


@pytest.mark.benchmark
def test_parse_large_query(benchmark: BenchmarkFixture):
    benchmark(parse, large_query)


@pytest.mark.benchmark
@pytest.mark.parametrize(
    "use_parser_cache",
    [False, True],
    ids=["baseline", "with_parser_cache"],
)
def test_execute_large_query(
    benchmark: BenchmarkFixture,
    use_parser_cache: bool,
):
    extension_instances = []
    if use_parser_cache:
        from strawberry.extensions import ParserCache

        extension_instances.append(ParserCache())

    schema = Schema(query=Query, extensions=extension_instances)

    benchmark(
        schema.execute_sync,
        large_query,
        variable_values={"count": 1},
    )
