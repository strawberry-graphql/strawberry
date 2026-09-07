from pathlib import Path

import pytest
from graphql import parse, validate
from pytest_codspeed import BenchmarkFixture

from strawberry import Schema
from strawberry.extensions import ParserCache, ValidationCache

from .api import Query

ROOT = Path(__file__).parent / "queries"
large_query = (ROOT / "large_items.graphql").read_text()


def test_parse_large_query(benchmark: BenchmarkFixture):
    result = benchmark(parse, large_query)
    assert result == parse(large_query)


def test_validate_large_query(benchmark: BenchmarkFixture):
    schema = Schema(query=Query)
    document = parse(large_query)
    assert benchmark(validate, schema._schema, document) == []


@pytest.mark.parametrize(
    ("parser", "validation", "warm"),
    [
        (False, False, False),
        (True, False, False),
        (True, False, True),
        (True, True, False),
        (True, True, True),
    ],
    ids=["uncached", "parser_cold", "parser_warm", "both_cold", "both_warm"],
)
def test_execute_large_query_v2(
    benchmark: BenchmarkFixture, parser: bool, validation: bool, warm: bool
):
    # Shared caches need per-round setup, including in walltime mode.
    parse_cache = ParserCache(maxsize=2).cached_parse_document
    validate_cache = ValidationCache(maxsize=2).cached_validate_document
    extensions = []
    if parser:
        extensions.append(lambda: ParserCache(maxsize=2))
    if validation:
        extensions.append(lambda: ValidationCache(maxsize=2))
    schema = Schema(query=Query, extensions=extensions)

    def run():
        return schema.execute_sync(large_query, variable_values={"count": 1})

    def setup():
        parse_cache.cache_clear()
        validate_cache.cache_clear()
        if warm:
            assert run().errors is None

    try:
        result = benchmark.pedantic(run, setup=setup, rounds=5, iterations=1)
        assert result.errors is None
        assert (
            result.data
            == Schema(query=Query)
            .execute_sync(large_query, variable_values={"count": 1})
            .data
        )
        assert result.data is not None
        for enabled, cache in [(parser, parse_cache), (validation, validate_cache)]:
            info = cache.cache_info()
            assert info.misses == int(enabled)
            assert info.hits == int(enabled and warm)
    finally:
        parse_cache.cache_clear()
        validate_cache.cache_clear()
