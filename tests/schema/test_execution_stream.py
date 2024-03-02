from typing import Any, AsyncIterator

import pytest

import strawberry
from strawberry.schema.execute import (
    ExecutionResult,
    IncrementalExecutionResult,
    MoreIncrementalExecutionResult,
)

try:  # pragma: no cover
    anext  # pyright: ignore
except NameError:  # pragma: no cover (Python < 3.10)
    # noinspection PyShadowingBuiltins
    async def anext(iterator: AsyncIterator[Any]) -> Any:
        """Return the next item from an async iterator."""
        return await iterator.__anext__()


@pytest.mark.asyncio
async def test_streamable_field_without_stream():
    @strawberry.type
    class Query:
        @strawberry.field
        async def count(self) -> strawberry.Streamable[int]:
            yield 1
            yield 2

    schema = strawberry.Schema(query=Query)

    query = """
        query {
            count
        }
    """

    result = await schema.execute(query)

    assert isinstance(result, ExecutionResult)

    assert result.data == {"count": [1, 2]}


@pytest.mark.asyncio
async def test_streamable_field_with_stream():
    @strawberry.type
    class Query:
        @strawberry.field
        async def count(self) -> strawberry.Streamable[int]:
            yield 1
            yield 2

    schema = strawberry.Schema(query=Query)

    query = """
        query {
            count @stream
        }
    """

    result = await schema.execute(query)

    assert isinstance(result, IncrementalExecutionResult)

    assert result.initial_result.data == {"count": []}

    all_results = [r async for r in result.more_results]

    assert all_results == [
        MoreIncrementalExecutionResult(items=[1], errors=None, path=["count", 0]),
        MoreIncrementalExecutionResult(items=[2], errors=None, path=["count", 1]),
    ]
