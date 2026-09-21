from pathlib import Path

import pytest
from pytest_codspeed.plugin import BenchmarkFixture

from .api import schema, schema_with_directives
from .assertions import assert_items, assert_people

ROOT = Path(__file__).parent / "queries"

basic_query = (ROOT / "simple.graphql").read_text()
many_fields_query = (ROOT / "many_fields.graphql").read_text()
many_fields_query_directives = (ROOT / "many_fields_directives.graphql").read_text()
items_query = (ROOT / "items.graphql").read_text()


@pytest.mark.benchmark
def test_execute_basic(benchmark: BenchmarkFixture):
    result = benchmark(schema.execute_sync, basic_query)
    assert result.errors is None
    assert result.data == {"hello": "Hello World!"}


@pytest.mark.benchmark
def test_execute_with_many_fields(benchmark: BenchmarkFixture):
    assert_people(benchmark(schema.execute_sync, many_fields_query))


@pytest.mark.benchmark
def test_execute_with_many_fields_and_directives(benchmark: BenchmarkFixture):
    assert_people(
        benchmark(schema_with_directives.execute_sync, many_fields_query_directives),
        uppercase=True,
    )


@pytest.mark.benchmark
def test_execute_with_10_items(benchmark: BenchmarkFixture):
    assert_items(
        benchmark(schema.execute_sync, items_query, variable_values={"count": 10}), 10
    )


@pytest.mark.benchmark
def test_execute_with_100_items(benchmark: BenchmarkFixture):
    assert_items(
        benchmark(schema.execute_sync, items_query, variable_values={"count": 100}), 100
    )


@pytest.mark.benchmark
@pytest.mark.benchmark_memory
def test_execute_with_1000_items(benchmark: BenchmarkFixture):
    assert_items(
        benchmark(schema.execute_sync, items_query, variable_values={"count": 1000}),
        1000,
    )
