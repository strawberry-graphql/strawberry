import subprocess
import sys

import pytest
from pytest_codspeed import BenchmarkFixture

import strawberry

# A single build of a small schema is too short for CodSpeed's simulation: each
# measurement starts with empty CPU caches, and unrelated changes moved that
# build's estimate by up to 13%. Each round builds several schemas instead.
SCHEMAS_PER_ROUND = 10


@pytest.mark.benchmark_memory
@pytest.mark.parametrize("types_count", [10, 100])
def test_schema_construction_v2(benchmark: BenchmarkFixture, types_count: int):
    types = [
        strawberry.type(type(f"BenchType{i}", (), {"__annotations__": {"value": int}}))
        for i in range(types_count)
    ]
    query = strawberry.type(
        type(
            "Query",
            (),
            {"__annotations__": {f"field{i}": t for i, t in enumerate(types)}},
        )
    )

    def build_schemas() -> list[strawberry.Schema]:
        return [strawberry.Schema(query=query) for _ in range(SCHEMAS_PER_ROUND)]

    schemas = benchmark(build_schemas)
    assert len(schemas) == SCHEMAS_PER_ROUND
    for schema in schemas:
        assert len(schema._schema.query_type.fields) == types_count
        assert all(
            f"BenchType{i}" in schema._schema.type_map for i in range(types_count)
        )


@pytest.mark.benchmark_native
def test_process_import_and_schema(benchmark: BenchmarkFixture):
    # This case deliberately includes a new process and interpreter startup.
    script = """
import strawberry
@strawberry.type
class Query:
    value: int
schema = strawberry.Schema(query=Query)
assert schema.execute_sync('{ value }', root_value=Query(value=42)).data == {'value': 42}
print('ready')
"""
    result = benchmark(
        subprocess.run,
        [sys.executable, "-c", script],
        check=True,
        capture_output=True,
        text=True,
    )
    assert result.stdout.strip() == "ready"
