import asyncio
from collections.abc import AsyncGenerator, AsyncIterator, Iterator
from typing import Any

import pytest

import strawberry
from strawberry.extensions import SchemaExtension
from strawberry.extensions.mask_errors import MaskErrors
from strawberry.types import ExecutionResult


# Dummy extension that uses the new hook
class StreamModifierExtension(SchemaExtension):
    def on_subscription_result(self, result: ExecutionResult) -> Iterator[None]:
        if result.data and "count" in result.data:
            # Mutate the outgoing data stream
            result.data["count"] = f"Modified: {result.data['count']}"
        yield None


# Create a basic schema with a subscription
@strawberry.type
class Query:
    hello: str = "world"


@strawberry.type
class Subscription:
    @strawberry.subscription
    async def count(self) -> AsyncGenerator[int, None]:
        yield 1
        yield 2

    @strawberry.subscription
    async def dangerous_stream(self) -> AsyncGenerator[int, None]:
        yield 1
        raise ValueError("Secret database credentials leaked!")


# Tests
@pytest.mark.asyncio
async def test_extension_modifies_subscription_stream():
    schema = strawberry.Schema(
        query=Query, subscription=Subscription, extensions=[StreamModifierExtension]
    )

    query = "subscription { count }"

    sub_generator = await schema.subscribe(query)

    # Get all yielded results
    results = [result async for result in sub_generator]

    assert len(results) == 2

    # Assert that the extension successfully intercepted and modified the stream
    assert results[0].data["count"] == "Modified: 1"
    assert results[1].data["count"] == "Modified: 2"


@pytest.mark.asyncio
async def test_mask_errors_scrubs_subscription_exceptions():
    # Initialize schema with the MaskErrors extension
    schema = strawberry.Schema(
        query=Query, subscription=Subscription, extensions=[MaskErrors()]
    )

    query = "subscription { dangerousStream }"

    sub_generator = await schema.subscribe(query)

    # Get all yielded results
    results = [result async for result in sub_generator]

    # We expect 2 results: the successful yield, and the error
    assert len(results) == 2

    # Assert the first yield worked normally
    assert results[0].data["dangerousStream"] == 1
    assert not results[0].errors

    # Assert the error was caught and MASKED
    assert results[1].data is None
    assert len(results[1].errors) == 1

    # The crucial check: The raw exception message MUST NOT be exposed
    error_message = results[1].errors[0].message
    assert error_message == "Unexpected error."
    assert "Secret database credentials" not in error_message


class AsyncStreamModifierExtension(SchemaExtension):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.side_effect_ran = False  # Attached to the instance

    async def _side_effect(self) -> None:
        # Simulate an async dependency / side effect
        await asyncio.sleep(0)
        self.side_effect_ran = True

    async def on_subscription_result(
        self, result: ExecutionResult
    ) -> AsyncIterator[None]:
        # This should be awaited by extensions_runner.on_subscription_result
        await self._side_effect()

        if result.data and "count" in result.data:
            # Mutate the outgoing data stream after the async side effect
            result.data["count"] = f"Modified: {result.data['count']}"
        yield None


@pytest.mark.asyncio
async def test_async_on_subscription_result_is_awaited() -> None:
    extension = AsyncStreamModifierExtension()

    schema = strawberry.Schema(
        query=Query,
        subscription=Subscription,
        extensions=[extension],
    )

    query = "subscription { count }"
    sub_generator = await schema.subscribe(query)

    # Consume first result from the async iterator
    first_result = await sub_generator.__anext__()

    assert first_result.errors is None
    assert first_result.data == {"count": "Modified: 1"}
    assert extension.side_effect_ran is True


@pytest.mark.asyncio
async def test_mask_errors_scrubs_pre_execution_errors():
    # Initialize schema with MaskErrors
    schema = strawberry.Schema(
        query=Query, subscription=Subscription, extensions=[MaskErrors()]
    )

    # Querying a field that doesn't exist triggers Validation errors BEFORE execution
    query = "subscription { fieldThatDoesNotExist }"

    # Run the subscription
    sub_generator = await schema.subscribe(query)

    # Exhaust the generator
    results = [result async for result in sub_generator]

    # Pre-execution errors immediately yield exactly 1 result containing the error
    assert len(results) == 1

    for result in results:
        assert result.data is None
        assert len(result.errors) == 1

        # The crucial check: MaskErrors successfully intercepted and masked it!
        error_message = result.errors[0].message
        assert error_message == "Unexpected error."
        assert "fieldThatDoesNotExist" not in error_message
