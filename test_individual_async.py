"""Test individual async test cases."""
import asyncio
from tests.test_jit_optimized_async import (
    test_optimized_async_single_field,
    test_optimized_async_nested_fields,
    test_optimized_async_list_fields,
    test_optimized_mixed_sync_async,
    test_optimized_parallel_async_execution,
    test_optimized_async_with_arguments,
)


async def main():
    tests = [
        ("Single field", test_optimized_async_single_field),
        ("Nested fields", test_optimized_async_nested_fields),
        ("List fields", test_optimized_async_list_fields),
        ("Mixed sync/async", test_optimized_mixed_sync_async),
        ("Parallel execution", test_optimized_parallel_async_execution),
        ("With arguments", test_optimized_async_with_arguments),
    ]
    
    for name, test_fn in tests:
        try:
            print(f"Running {name}...", end=" ")
            await test_fn()
            print("✅ PASSED")
        except Exception as e:
            print(f"❌ FAILED: {e}")


if __name__ == "__main__":
    asyncio.run(main())