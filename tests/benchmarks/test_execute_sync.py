from pathlib import Path

import pytest
from pytest_codspeed.plugin import BenchmarkFixture

from .api import schema, schema_with_directives

ROOT = Path(__file__).parent / "queries"

basic_query = (ROOT / "simple.graphql").read_text()
many_fields_query = (ROOT / "many_fields.graphql").read_text()
many_fields_query_directives = (ROOT / "many_fields_directives.graphql").read_text()
items_query = (ROOT / "items.graphql").read_text()


@pytest.mark.benchmark
def test_execute_basic(benchmark: BenchmarkFixture):
    benchmark(schema.execute_sync, basic_query)


@pytest.mark.benchmark
def test_execute_with_many_fields(benchmark: BenchmarkFixture):
    benchmark(schema.execute_sync, many_fields_query)


@pytest.mark.benchmark
def test_execute_with_many_fields_and_directives(benchmark: BenchmarkFixture):
    benchmark(schema_with_directives.execute_sync, many_fields_query_directives)


@pytest.mark.benchmark
def test_execute_with_10_items(benchmark: BenchmarkFixture):
    benchmark(schema.execute_sync, items_query, variable_values={"count": 10})


@pytest.mark.benchmark
def test_execute_with_100_items(benchmark: BenchmarkFixture):
    benchmark(schema.execute_sync, items_query, variable_values={"count": 100})


@pytest.mark.benchmark
def test_execute_with_1000_items(benchmark: BenchmarkFixture):
    benchmark(schema.execute_sync, items_query, variable_values={"count": 1000})
