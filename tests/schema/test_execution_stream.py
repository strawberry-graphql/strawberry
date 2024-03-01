import pytest

import strawberry
from strawberry.schema.execute import ExecutionResult, IncrementalExecutionResult


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
