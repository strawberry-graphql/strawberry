import pytest
from pytest_codspeed import BenchmarkFixture

import strawberry
from strawberry.extensions import ParserCache

from .api import Query


@pytest.mark.benchmark_memory
def test_parser_cache_churn(benchmark: BenchmarkFixture):
    cache = ParserCache(maxsize=8).cached_parse_document
    schema = strawberry.Schema(query=Query, extensions=[lambda: ParserCache(maxsize=8)])
    queries = [f"query Operation{i} {{ hello }}" for i in range(16)]

    def run():
        return [schema.execute_sync(query) for query in queries]

    try:
        results = benchmark.pedantic(
            run, setup=cache.cache_clear, rounds=5, iterations=1
        )
        assert len(results) == 16
        assert all(
            result.errors is None and result.data == {"hello": "Hello World!"}
            for result in results
        )
        assert cache.cache_info().currsize == 8
        assert cache.cache_info().misses == 16
    finally:
        cache.cache_clear()
