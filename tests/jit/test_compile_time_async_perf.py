"""
Test to verify performance improvement from compile-time async detection.
"""

import asyncio
import inspect
import time

import strawberry
from strawberry.jit import JITCompiler


@strawberry.type
class Item:
    id: str

    @strawberry.field
    async def async_field1(self) -> str:
        return "async1"

    @strawberry.field
    async def async_field2(self) -> str:
        return "async2"

    @strawberry.field
    def sync_field1(self) -> str:
        return "sync1"

    @strawberry.field
    def sync_field2(self) -> str:
        return "sync2"


@strawberry.type
class Query:
    @strawberry.field
    def items(self, limit: int = 100) -> list[Item]:
        return [Item(id=f"i{i}") for i in range(limit)]


def test_compile_time_async_detection_overhead():
    """Test that we're using compile-time async detection, not runtime checks."""
    schema = strawberry.Schema(Query)
    compiler = JITCompiler(schema)

    query = """
    query {
        items(limit: 10) {
            id
            asyncField1
            syncField1
            asyncField2
            syncField2
        }
    }
    """

    # Compile the query
    compiled_fn = compiler.compile_query(query)

    # Check that _is_field_async method exists (our optimization)
    assert hasattr(compiler, "_is_field_async"), (
        "Compiler should have _is_field_async method"
    )

    # Verify that we're accessing the StrawberryField metadata
    # by checking a field from the schema
    query_type = schema._schema.type_map["Query"]
    items_field = query_type.fields["items"]

    # The field should have extensions with the StrawberryField
    assert hasattr(items_field, "extensions"), "Field should have extensions"
    assert "strawberry-definition" in items_field.extensions, (
        "Should have StrawberryField in extensions"
    )

    # Test that the _is_field_async method works correctly
    item_type = schema._schema.type_map["Item"]
    async_field = item_type.fields["asyncField1"]
    sync_field = item_type.fields["syncField1"]

    # Our method should correctly identify async fields using metadata
    assert compiler._is_field_async(async_field) is True, "Should detect async field"
    assert compiler._is_field_async(sync_field) is False, "Should detect sync field"

    print("✅ Compile-time async detection is working correctly!")


def benchmark_async_detection():
    """Benchmark the performance improvement of compile-time async detection."""
    schema = strawberry.Schema(Query)

    # Create test fields
    item_type = schema._schema.type_map["Item"]
    async_field = item_type.fields["asyncField1"]
    sync_field = item_type.fields["syncField1"]

    # Get the StrawberryField from extensions
    strawberry_async_field = async_field.extensions.get("strawberry-definition")
    strawberry_sync_field = sync_field.extensions.get("strawberry-definition")

    iterations = 100000

    # Benchmark runtime inspection (old method)
    start = time.perf_counter()
    for _ in range(iterations):
        if async_field.resolve:
            is_async = inspect.iscoroutinefunction(async_field.resolve)
    runtime_time = time.perf_counter() - start

    # Benchmark compile-time lookup (new method)
    start = time.perf_counter()
    for _ in range(iterations):
        if strawberry_async_field:
            is_async = strawberry_async_field.is_async
    compile_time = time.perf_counter() - start

    speedup = runtime_time / compile_time
    per_check_saving_ns = ((runtime_time - compile_time) / iterations) * 1_000_000_000

    print("\\n📊 Async Detection Performance:")
    print(
        f"   Runtime inspection: {runtime_time * 1000:.2f}ms for {iterations:,} checks"
    )
    print(
        f"   Compile-time lookup: {compile_time * 1000:.2f}ms for {iterations:,} checks"
    )
    print(f"   Speedup: {speedup:.1f}x faster")
    print(f"   Per-check saving: {per_check_saving_ns:.1f}ns")

    # Assert reasonable performance improvement
    assert speedup > 2.0, f"Expected at least 2x speedup, got {speedup:.1f}x"


async def test_async_execution_still_works():
    """Ensure async execution still works correctly with our optimization."""
    schema = strawberry.Schema(Query)
    compiler = JITCompiler(schema)

    query = """
    query {
        items(limit: 5) {
            id
            asyncField1
            asyncField2
            syncField1
            syncField2
        }
    }
    """

    compiled_fn = compiler.compile_query(query)
    result = await compiled_fn(Query())

    # Verify results
    assert "data" in result
    assert "items" in result["data"]
    assert len(result["data"]["items"]) == 5

    for item in result["data"]["items"]:
        assert item["asyncField1"] == "async1"
        assert item["asyncField2"] == "async2"
        assert item["syncField1"] == "sync1"
        assert item["syncField2"] == "sync2"

    print("✅ Async execution works correctly with compile-time detection!")


if __name__ == "__main__":
    test_compile_time_async_detection_overhead()
    benchmark_async_detection()
    asyncio.run(test_async_execution_still_works())
    print("\\n🎉 All performance tests passed!")
