"""Test that mutations execute serially even with async resolvers."""

import asyncio
import time

import strawberry
from strawberry.jit import compile_query

# Global counter to track execution order
execution_order = []


@strawberry.type
class Counter:
    value: int
    name: str


@strawberry.type
class CounterResult:
    counter: Counter
    success: bool


@strawberry.type
class Mutation:
    @strawberry.mutation
    async def increment_async(self, name: str, delay: float = 0.01) -> CounterResult:
        """Async mutation that increments a counter with a delay."""
        global execution_order

        # Record when we start
        start_time = time.time()
        execution_order.append((name, "start", start_time))

        # Simulate async work
        await asyncio.sleep(delay)

        # Record when we finish
        end_time = time.time()
        execution_order.append((name, "end", end_time))

        return CounterResult(
            counter=Counter(value=len(execution_order), name=name), success=True
        )

    @strawberry.mutation
    def increment_sync(self, name: str, delay: float = 0.01) -> CounterResult:
        """Sync mutation that increments a counter with a delay."""
        global execution_order

        # Record when we start
        start_time = time.time()
        execution_order.append((name, "start", start_time))

        # Simulate work
        time.sleep(delay)

        # Record when we finish
        end_time = time.time()
        execution_order.append((name, "end", end_time))

        return CounterResult(
            counter=Counter(value=len(execution_order), name=name), success=True
        )


@strawberry.type
class Query:
    @strawberry.field
    def dummy(self) -> str:
        return "dummy"


def test_async_mutations_execute_serially():
    """Test that async mutations execute one at a time, not in parallel."""
    global execution_order
    execution_order = []

    schema = strawberry.Schema(Query, Mutation)

    # Multiple async mutations
    query = """
    mutation TestSerial {
        first: incrementAsync(name: "first", delay: 0.02) {
            counter { value name }
            success
        }
        second: incrementAsync(name: "second", delay: 0.02) {
            counter { value name }
            success
        }
        third: incrementAsync(name: "third", delay: 0.02) {
            counter { value name }
            success
        }
    }
    """

    compiled_fn = compile_query(schema, query)

    # Run the mutations
    start_time = time.time()
    asyncio.run(compiled_fn(Mutation()))
    total_time = time.time() - start_time

    # If mutations run in parallel, total time would be ~0.02 seconds
    # If they run serially, total time would be ~0.06 seconds
    assert total_time >= 0.06, (
        f"Mutations ran too fast ({total_time:.3f}s), they may be parallel!"
    )

    # Check execution order
    assert len(execution_order) == 6  # 3 starts + 3 ends

    # Verify serial execution: each mutation should complete before the next starts
    assert execution_order[0] == ("first", "start", execution_order[0][2])
    assert execution_order[1] == ("first", "end", execution_order[1][2])
    assert execution_order[2] == ("second", "start", execution_order[2][2])
    assert execution_order[3] == ("second", "end", execution_order[3][2])
    assert execution_order[4] == ("third", "start", execution_order[4][2])
    assert execution_order[5] == ("third", "end", execution_order[5][2])

    # Verify timing - each mutation should finish before the next starts
    first_end = execution_order[1][2]
    second_start = execution_order[2][2]
    assert second_start >= first_end, "Second mutation started before first finished!"

    second_end = execution_order[3][2]
    third_start = execution_order[4][2]
    assert third_start >= second_end, "Third mutation started before second finished!"


def test_mixed_sync_async_mutations_serial():
    """Test that mixed sync/async mutations execute serially."""
    global execution_order
    execution_order = []

    schema = strawberry.Schema(Query, Mutation)

    query = """
    mutation TestMixed {
        first: incrementSync(name: "sync1", delay: 0.01) {
            counter { value }
        }
        second: incrementAsync(name: "async1", delay: 0.01) {
            counter { value }
        }
        third: incrementSync(name: "sync2", delay: 0.01) {
            counter { value }
        }
        fourth: incrementAsync(name: "async2", delay: 0.01) {
            counter { value }
        }
    }
    """

    compiled_fn = compile_query(schema, query)

    # Run the mutations
    asyncio.run(compiled_fn(Mutation()))

    # Check execution order
    assert len(execution_order) == 8  # 4 starts + 4 ends

    # Verify they executed in order
    names_in_order = [entry[0] for entry in execution_order if entry[1] == "start"]
    assert names_in_order == ["sync1", "async1", "sync2", "async2"]

    # Verify each completed before the next started
    for i in range(0, len(execution_order) - 2, 2):
        current_end = execution_order[i + 1]
        if i + 2 < len(execution_order):
            next_start = execution_order[i + 2]
            assert current_end[1] == "end"
            assert next_start[1] == "start"
            assert next_start[2] >= current_end[2], (
                f"{next_start[0]} started before {current_end[0]} finished!"
            )


def test_query_fields_can_be_parallel():
    """Verify that query fields can still execute in parallel for performance."""
    global execution_order
    execution_order = []

    @strawberry.type
    class Query:
        @strawberry.field
        async def async_field1(self) -> str:
            execution_order.append(("field1", "start", time.time()))
            await asyncio.sleep(0.02)
            execution_order.append(("field1", "end", time.time()))
            return "field1"

        @strawberry.field
        async def async_field2(self) -> str:
            execution_order.append(("field2", "start", time.time()))
            await asyncio.sleep(0.02)
            execution_order.append(("field2", "end", time.time()))
            return "field2"

        @strawberry.field
        async def async_field3(self) -> str:
            execution_order.append(("field3", "start", time.time()))
            await asyncio.sleep(0.02)
            execution_order.append(("field3", "end", time.time()))
            return "field3"

    schema = strawberry.Schema(Query, Mutation)

    query = """
    query TestParallel {
        asyncField1
        asyncField2
        asyncField3
    }
    """

    compiled_fn = compile_query(schema, query)

    # Run the query
    start_time = time.time()
    asyncio.run(compiled_fn(Query()))
    total_time = time.time() - start_time

    # If fields run in parallel, total time would be ~0.02 seconds
    # If they run serially, total time would be ~0.06 seconds
    assert total_time < 0.04, (
        f"Query fields ran too slow ({total_time:.3f}s), they should be parallel!"
    )

    # Check that fields started before previous ones finished (parallel execution)
    starts = [(e[0], e[2]) for e in execution_order if e[1] == "start"]
    ends = [(e[0], e[2]) for e in execution_order if e[1] == "end"]

    # At least some fields should have started before others finished
    parallel_detected = False
    for start_name, start_time in starts:
        for end_name, end_time in ends:
            if start_name != end_name and start_time < end_time:
                # This field started before another finished - parallel execution!
                parallel_detected = True
                break

    assert parallel_detected, "Query fields did not execute in parallel!"


if __name__ == "__main__":
    test_async_mutations_execute_serially()
    test_mixed_sync_async_mutations_serial()
    test_query_fields_can_be_parallel()
