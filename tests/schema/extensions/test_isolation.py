"""Regression suite for issue #4369.

Concurrent requests must each see their own ``ExecutionContext``, regardless
of whether the extension is passed as a class, a factory callable, or (the
deprecated path) a pre-built instance. Built-in tracing extensions must keep
their per-request mutable state isolated as well.
"""

from __future__ import annotations

import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import pytest

import strawberry
from strawberry.extensions import SchemaExtension
from strawberry.extensions.tracing import (
    ApolloTracingExtension,
    ApolloTracingExtensionSync,
)


@strawberry.type
class Query:
    @strawberry.field
    def hello(self) -> str:
        time.sleep(0.05)
        return "world"

    @strawberry.field
    async def hello_async(self) -> str:
        await asyncio.sleep(0.05)
        return "world"


class _CapturingExtension(SchemaExtension):
    """Captures ``execution_context.query`` into ``get_results``.

    Any request that reads the *other* request's query is observing leaked
    state from a shared instance.
    """

    def __init__(self, *, execution_context=None, label: str = "default") -> None:
        super().__init__(execution_context=execution_context)
        self.label = label

    def get_results(self) -> dict[str, Any]:
        return {
            "query": str(self.execution_context.query),
            "label": self.label,
        }


def test_sync_concurrent_class_passed():
    schema = strawberry.Schema(query=Query, extensions=[_CapturingExtension])

    queries = ["{ hello }", "{ test: hello }"]

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(schema.execute_sync, queries))

    assert results[0].extensions == {"query": queries[0], "label": "default"}
    assert results[1].extensions == {"query": queries[1], "label": "default"}


def test_sync_concurrent_factory_passed():
    schema = strawberry.Schema(
        query=Query,
        extensions=[lambda: _CapturingExtension(label="sync-factory")],
    )

    queries = ["{ hello }", "{ test: hello }"]

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(schema.execute_sync, queries))

    assert results[0].extensions == {"query": queries[0], "label": "sync-factory"}
    assert results[1].extensions == {"query": queries[1], "label": "sync-factory"}


@pytest.mark.asyncio
async def test_async_concurrent_class_passed():
    schema = strawberry.Schema(query=Query, extensions=[_CapturingExtension])

    queries = ["{ helloAsync }", "{ test: helloAsync }"]
    results = await asyncio.gather(*(schema.execute(q) for q in queries))

    assert results[0].extensions == {"query": queries[0], "label": "default"}
    assert results[1].extensions == {"query": queries[1], "label": "default"}


@pytest.mark.asyncio
async def test_async_concurrent_factory_passed():
    schema = strawberry.Schema(
        query=Query,
        extensions=[lambda: _CapturingExtension(label="async-factory")],
    )

    queries = ["{ helloAsync }", "{ test: helloAsync }"]
    results = await asyncio.gather(*(schema.execute(q) for q in queries))

    assert results[0].extensions == {"query": queries[0], "label": "async-factory"}
    assert results[1].extensions == {"query": queries[1], "label": "async-factory"}


def test_class_constructed_per_request():
    construction_count = 0

    class _Counting(SchemaExtension):
        def __init__(self, *, execution_context=None) -> None:
            super().__init__(execution_context=execution_context)
            nonlocal construction_count
            construction_count += 1

    schema = strawberry.Schema(query=Query, extensions=[_Counting])

    for _ in range(3):
        schema.execute_sync("{ hello }")

    assert construction_count == 3, "every request must build a fresh instance"


def test_factory_called_per_request():
    factory_call_count = 0

    def factory() -> SchemaExtension:
        nonlocal factory_call_count
        factory_call_count += 1
        return _CapturingExtension(label=f"req-{factory_call_count}")

    schema = strawberry.Schema(query=Query, extensions=[factory])

    for _ in range(3):
        schema.execute_sync("{ hello }")

    assert factory_call_count == 3, "factory must be invoked once per request"


def test_instance_passed_emits_deprecation_warning():
    with pytest.warns(
        DeprecationWarning,
        match=r"Passing an extension instance.*deprecated",
    ):
        strawberry.Schema(
            query=Query,
            extensions=[_CapturingExtension()],  # type: ignore[list-item]
        )


def test_extensions_can_be_a_generator():
    # ``Schema.__init__`` materializes the iterable so a generator passed as
    # ``extensions`` still produces extensions on every request.
    def gen():
        yield _CapturingExtension

    schema = strawberry.Schema(query=Query, extensions=gen())

    for _ in range(2):
        result = schema.execute_sync("{ hello }")
        assert result.extensions == {"query": "{ hello }", "label": "default"}


def test_apollo_tracing_sync_concurrent_class_passed():
    schema = strawberry.Schema(query=Query, extensions=[ApolloTracingExtensionSync])

    queries = ["{ hello }", "{ test: hello }"]
    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(schema.execute_sync, queries))

    # Each request gets its own tracing payload and own resolver list.
    for result in results:
        assert result.errors is None
        assert result.extensions is not None
        tracing = result.extensions["tracing"]
        resolvers = tracing["execution"]["resolvers"]
        # Both queries resolve a single ``hello`` field.
        assert len(resolvers) == 1
        assert resolvers[0]["field_name"] == "hello"


@pytest.mark.asyncio
async def test_apollo_tracing_async_concurrent_class_passed():
    schema = strawberry.Schema(query=Query, extensions=[ApolloTracingExtension])

    queries = ["{ helloAsync }", "{ test: helloAsync }"]
    results = await asyncio.gather(*(schema.execute(q) for q in queries))

    for result in results:
        assert result.errors is None
        assert result.extensions is not None
        tracing = result.extensions["tracing"]
        resolvers = tracing["execution"]["resolvers"]
        assert len(resolvers) == 1
        assert resolvers[0]["field_name"] == "helloAsync"


@pytest.mark.asyncio
async def test_apollo_tracing_async_concurrent_factory_passed():
    schema = strawberry.Schema(
        query=Query,
        extensions=[lambda: ApolloTracingExtension(execution_context=None)],
    )

    queries = ["{ helloAsync }", "{ test: helloAsync }", "{ alias: helloAsync }"]
    results = await asyncio.gather(*(schema.execute(q) for q in queries))

    for result in results:
        assert result.errors is None
        assert result.extensions is not None
        tracing = result.extensions["tracing"]
        resolvers = tracing["execution"]["resolvers"]
        assert len(resolvers) == 1
        assert resolvers[0]["field_name"] == "helloAsync"
