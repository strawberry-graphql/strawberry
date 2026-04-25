"""Regression tests for issue #4369: extension state must not leak between
concurrent requests, regardless of whether the extension is passed to
``strawberry.Schema`` as a class or as an instance, and regardless of
whether the request is run via ``execute`` (async) or ``execute_sync``
(threaded)."""

from __future__ import annotations

import asyncio
import time
from collections.abc import AsyncGenerator
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import pytest

import strawberry
from strawberry.extensions import SchemaExtension


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


@strawberry.type
class Subscription:
    @strawberry.subscription
    async def tick(self) -> AsyncGenerator[int, None]:
        for i in range(3):
            await asyncio.sleep(0.01)
            yield i


class QueryEchoExtension(SchemaExtension):
    """Echoes the running request's query into the extensions payload.

    Reads ``self.execution_context.query`` — the exact attribute the
    reporter showed leaking between concurrent requests.
    """

    def get_results(self) -> dict[str, Any]:
        return {"query": str(self.execution_context.query)}


def _build_schema(extensions: list) -> strawberry.Schema:
    return strawberry.Schema(query=Query, extensions=extensions)


def _run_sync_concurrent(schema: strawberry.Schema) -> list:
    queries = ["{ hello }", "{ test: hello }"]
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(schema.execute_sync, q) for q in queries]
        return [f.result() for f in futures]


async def _run_async_concurrent(schema: strawberry.Schema) -> list:
    return list(
        await asyncio.gather(
            schema.execute("{ helloAsync }"),
            schema.execute("{ test: helloAsync }"),
        )
    )


def _assert_no_leak(results: list, queries: list[str]) -> None:
    """Each result's echoed query must match its own request, not the other."""
    assert len(results) == len(queries)
    for result, expected_query in zip(results, queries, strict=True):
        assert result.errors is None, result.errors
        assert result.extensions is not None
        assert result.extensions["query"] == expected_query, (
            f"extension state leaked: expected {expected_query!r}, "
            f"got {result.extensions['query']!r}"
        )


def test_sync_concurrent_instance_passed():
    """Reporter's exact sync repro: instance-passed extension must not leak."""
    schema = _build_schema([QueryEchoExtension()])
    results = _run_sync_concurrent(schema)
    _assert_no_leak(results, ["{ hello }", "{ test: hello }"])


def test_sync_concurrent_class_passed():
    """Sync, class-passed: also must not leak (PR #4256 only fixed async)."""
    schema = _build_schema([QueryEchoExtension])
    results = _run_sync_concurrent(schema)
    _assert_no_leak(results, ["{ hello }", "{ test: hello }"])


@pytest.mark.asyncio
async def test_async_concurrent_instance_passed():
    """Reporter's exact async repro: instance-passed extension must not leak."""
    schema = _build_schema([QueryEchoExtension()])
    results = await _run_async_concurrent(schema)
    _assert_no_leak(results, ["{ helloAsync }", "{ test: helloAsync }"])


@pytest.mark.asyncio
async def test_async_concurrent_class_passed():
    schema = _build_schema([QueryEchoExtension])
    results = await _run_async_concurrent(schema)
    _assert_no_leak(results, ["{ helloAsync }", "{ test: helloAsync }"])


def test_instance_passed_extension_is_shared_but_context_isolated():
    """Instance-passed extensions are reused across requests (no copying);
    isolation comes from the ContextVar-backed ``execution_context``."""
    captured_instances: list[SchemaExtension] = []
    captured_queries: list[str] = []

    class RecorderExtension(SchemaExtension):
        def on_operation(self):
            captured_instances.append(self)
            captured_queries.append(str(self.execution_context.query))
            yield

    @strawberry.type
    class TinyQuery:
        @strawberry.field
        def x(self) -> str:
            return ""

    extension = RecorderExtension()
    schema = strawberry.Schema(query=TinyQuery, extensions=[extension])

    schema.execute_sync("{ x }")
    schema.execute_sync("query Two { x }")

    assert captured_instances == [extension, extension], (
        "the same instance must be reused across requests"
    )
    assert captured_queries == ["{ x }", "query Two { x }"]


def test_execution_context_outside_hook_raises():
    """Reading ``execution_context`` outside an extension lifecycle hook
    should raise rather than silently return a stale value."""

    class MyExtension(SchemaExtension):
        pass

    extension = MyExtension()
    with pytest.raises(RuntimeError, match="ExecutionContext"):
        _ = extension.execution_context


@pytest.mark.asyncio
async def test_apollo_tracing_concurrent_instance_passed():
    """ApolloTracingExtension instance shared across concurrent requests must
    produce a separate tracing payload per request."""
    from strawberry.extensions.tracing.apollo import ApolloTracingExtension

    @strawberry.type
    class TracingQuery:
        @strawberry.field
        async def slow(self) -> str:
            await asyncio.sleep(0.05)
            return "ok"

    schema = strawberry.Schema(
        query=TracingQuery, extensions=[ApolloTracingExtension()]
    )

    results = await asyncio.gather(
        schema.execute("{ slow }"),
        schema.execute("{ slow }"),
        schema.execute("{ slow }"),
    )

    for result in results:
        assert result.errors is None
        assert result.extensions is not None
        tracing = result.extensions["tracing"]
        # Each request must produce its own resolver list: one entry for the
        # single ``slow`` field. If the instance leaked state between
        # requests, the lists would have accumulated 2 or 3 resolvers.
        assert len(tracing["execution"]["resolvers"]) == 1
        assert tracing["execution"]["resolvers"][0]["field_name"] == "slow"


def test_apollo_tracing_concurrent_threaded_instance_passed():
    """Same regression for the threaded sync path."""
    from strawberry.extensions.tracing.apollo import ApolloTracingExtensionSync

    @strawberry.type
    class TracingQuery:
        @strawberry.field
        def slow(self) -> str:
            time.sleep(0.05)
            return "ok"

    schema = strawberry.Schema(
        query=TracingQuery, extensions=[ApolloTracingExtensionSync()]
    )

    queries = ["{ slow }"] * 4
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(schema.execute_sync, q) for q in queries]
        results = [f.result() for f in futures]

    for result in results:
        assert result.errors is None
        assert result.extensions is not None
        tracing = result.extensions["tracing"]
        assert len(tracing["execution"]["resolvers"]) == 1
        assert tracing["execution"]["resolvers"][0]["field_name"] == "slow"


@pytest.mark.asyncio
async def test_subscribe_resets_execution_context_var():
    """After a subscription is fully consumed, the per-request
    ``ExecutionContext`` ContextVar must be reset — otherwise reading
    ``extension.execution_context`` in the caller's task would silently
    return the stale subscription context instead of raising."""
    extension = SchemaExtension()
    schema = strawberry.Schema(
        query=Query, subscription=Subscription, extensions=[extension]
    )

    async for _ in await schema.subscribe("subscription { tick }"):
        pass

    with pytest.raises(RuntimeError, match="ExecutionContext"):
        _ = extension.execution_context


@pytest.mark.asyncio
async def test_subscribe_concurrent_instance_passed():
    """Two concurrent subscriptions sharing the same extension instance
    must each see their own ``execution_context``."""
    captured: list[tuple[int, str]] = []

    class RecorderExtension(SchemaExtension):
        async def on_operation(self):
            captured.append((id(self), str(self.execution_context.query)))
            yield

    schema = strawberry.Schema(
        query=Query,
        subscription=Subscription,
        extensions=[RecorderExtension()],
    )

    queries = ["subscription { tick }", "subscription Two { tick }"]

    async def consume(q: str) -> None:
        async for _ in await schema.subscribe(q):
            pass

    await asyncio.gather(*(consume(q) for q in queries))

    assert sorted(q for _, q in captured) == sorted(queries)


@pytest.mark.asyncio
async def test_subscribe_aclosed_resets_context_var():
    """Resetting must happen even if the consumer breaks out of the
    iteration early (the generator's ``aclose`` runs the ``finally``)."""
    extension = SchemaExtension()
    schema = strawberry.Schema(
        query=Query, subscription=Subscription, extensions=[extension]
    )

    agen = await schema.subscribe("subscription { tick }")
    async for _ in agen:
        await agen.aclose()
        break

    with pytest.raises(RuntimeError, match="ExecutionContext"):
        _ = extension.execution_context


@pytest.mark.asyncio
async def test_apollo_tracing_nested_execution_does_not_leak():
    """A resolver that triggers a nested ``schema.execute()`` must not
    overwrite the outer request's tracing state — the state ContextVar
    is now reset when ``on_operation`` exits, so the outer request's
    payload still describes its own resolvers."""
    from strawberry.extensions.tracing.apollo import ApolloTracingExtension

    inner_schema = strawberry.Schema(query=Query)

    @strawberry.type
    class OuterQuery:
        @strawberry.field
        async def outer(self) -> str:
            inner_result = await inner_schema.execute("{ helloAsync }")
            assert inner_result.errors is None
            return "outer-done"

    schema = strawberry.Schema(query=OuterQuery, extensions=[ApolloTracingExtension()])
    result = await schema.execute("{ outer }")
    assert result.errors is None
    assert result.extensions is not None
    tracing = result.extensions["tracing"]
    # The outer payload should describe exactly one resolver: ``outer``.
    # If the inner ``schema.execute`` had leaked into the outer state,
    # this list would contain the inner request's ``helloAsync`` too.
    assert len(tracing["execution"]["resolvers"]) == 1
    assert tracing["execution"]["resolvers"][0]["field_name"] == "outer"
