from collections.abc import AsyncGenerator

import pytest

import strawberry
from strawberry.extensions import SchemaExtension
from strawberry.extensions.mask_errors import MaskErrors
from strawberry.types import ExecutionResult


# Dummy extension that uses the new hook
class StreamModifierExtension(SchemaExtension):
    def on_subscription_result(self, result: ExecutionResult) -> None:
        if result.data and "count" in result.data:
            # Mutate the outgoing data stream
            result.data["count"] = f"Modified: {result.data['count']}"


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
