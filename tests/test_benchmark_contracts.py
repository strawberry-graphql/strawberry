import asyncio
from typing import Any

import pytest
from graphql import GraphQLError

from strawberry.types import ExecutionResult
from tests.benchmarks import (
    test_execute_sync,
    test_federation_relay,
    test_subscriptions,
)
from tests.benchmarks.assertions import assert_items


def test_benchmark_rejects_graphql_errors():
    broken = ExecutionResult(data=None, errors=[GraphQLError("Invalid query")])
    with pytest.raises(AssertionError):
        test_execute_sync.test_execute_basic(lambda *args, **kwargs: broken)


def test_benchmark_rejects_truncated_results():
    with pytest.raises(AssertionError):
        assert_items(ExecutionResult(data={"items": []}, errors=None), 10)


def test_federation_benchmark_recreates_inputs_between_rounds():
    class RepeatedBenchmark:
        def __call__(self, target, *args: Any, **kwargs: Any):
            # Like walltime mode, return the first result after repeated calls.
            first = target(*args, **kwargs)
            assert target(*args, **kwargs).errors is None
            return first

        def pedantic(self, target, *, setup, rounds, iterations):
            assert iterations == 1
            for _ in range(rounds):
                args, kwargs = setup()
                result = target(*args, **kwargs)
                assert result.errors is None
                assert len(result.data["_entities"]) == 2
            return result

    test_federation_relay.test_federation_entities(RepeatedBenchmark(), count=2)


@pytest.mark.parametrize("events", [0, 9])
def test_benchmark_rejects_truncated_subscription(monkeypatch, events):
    async def subscribe(*args: Any, **kwargs: Any):
        async def values():
            for i in range(events):
                yield ExecutionResult(data={"longRunning": i}, errors=None)

        return values()

    monkeypatch.setattr(test_subscriptions.schema, "subscribe", subscribe)
    loop = asyncio.new_event_loop()
    try:
        with pytest.raises(AssertionError):
            test_subscriptions.test_subscription_long_run_v2(
                lambda run: run(), loop, count=10
            )
    finally:
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()
