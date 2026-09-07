import asyncio
import types
from collections.abc import Generator
from typing import Any

import pytest
from pytest_codspeed import BenchmarkFixture

import strawberry
from strawberry.execution import optimized_is_awaitable
from strawberry.types import ExecutionResult


@strawberry.type
class Item:
    id: int
    name: str
    active: bool


class CustomAwaitable:
    def __await__(self) -> Generator[None, None, int]:
        yield
        return 1


async def native_coroutine() -> int:
    return 1


@types.coroutine
def generator_coroutine() -> Generator[None, None, int]:
    yield
    return 1


@pytest.fixture
def detector_workloads() -> Generator[dict[str, list[tuple[Any, bool]]], None, None]:
    native = native_coroutine()
    generator = generator_coroutine()
    try:
        primitives = [
            (value, False)
            for value in (
                None,
                True,
                1,
                1.5,
                "value",
                b"value",
                bytearray(),
                [],
                (),
                {},
                set(),
                frozenset(),
            )
        ]
        objects = [
            (Item(id=i, name=f"item-{i}", active=True), False) for i in range(100)
        ]
        custom = CustomAwaitable()
        yield {
            "primitive-heavy": primitives * 8 + objects[:4],
            "object-heavy": objects[:88] + primitives,
            "native-coroutine": [(native, True)] * 100,
            "generator-coroutine": [(generator, True)] * 100,
            "custom-awaitable": [(custom, True)] * 100,
            "mixed": (
                primitives
                + objects[:1]
                + [(native, True), (generator, True), (custom, True)]
            )
            * 6,
        }
    finally:
        native.close()
        generator.close()


@pytest.mark.benchmark
@pytest.mark.parametrize(
    "workload",
    [
        "primitive-heavy",
        "object-heavy",
        "native-coroutine",
        "generator-coroutine",
        "custom-awaitable",
        "mixed",
    ],
)
def test_is_awaitable(
    benchmark: BenchmarkFixture,
    detector_workloads: dict[str, list[tuple[Any, bool]]],
    workload: str,
) -> None:
    cases = detector_workloads[workload]
    values = [value for value, _ in cases]
    assert [optimized_is_awaitable(value) for value in values] == [
        expected for _, expected in cases
    ]

    def run() -> None:
        # Time only iteration and detection on reused values. Creating or awaiting
        # coroutine objects would measure unrelated work and change the workload.
        for _ in range(1_000):
            for value in values:
                optimized_is_awaitable(value)

    benchmark(run)


@pytest.mark.benchmark
@pytest.mark.parametrize("count", [1, 1_000], ids=["small", "large-list"])
@pytest.mark.parametrize("mode", ["sync", "async"])
def test_execute_awaitable_results(
    benchmark: BenchmarkFixture, count: int, mode: str
) -> None:
    items = [Item(id=i, name=f"item-{i}", active=True) for i in range(count)]

    @strawberry.type
    class Query:
        @strawberry.field
        def sync_items(self) -> list[Item]:
            return items

        @strawberry.field
        async def async_items(self) -> list[Item]:
            return items

    schema = strawberry.Schema(query=Query)
    field = "syncItems" if mode == "sync" else "asyncItems"
    query = f"{{ {field} {{ id name active }} }}"
    expected = {
        field: [
            {"id": item.id, "name": item.name, "active": item.active} for item in items
        ]
    }

    def check(result: ExecutionResult) -> None:
        assert result.errors is None
        assert result.data == expected

    # Include parsing, validation and execution; schema/fixture construction and
    # assertions stay outside the timed callback. No cache extensions are enabled.
    if mode == "sync":
        check(schema.execute_sync(query))
        result = benchmark(schema.execute_sync, query)
    else:
        # Reuse one event loop: time coroutine execution and loop driving, but not
        # loop creation/teardown. The resolver performs no simulated I/O.
        loop = asyncio.new_event_loop()
        try:

            def run_async() -> ExecutionResult:
                return loop.run_until_complete(schema.execute(query))

            check(run_async())
            result = benchmark(run_async)
        finally:
            loop.close()

    check(result)
