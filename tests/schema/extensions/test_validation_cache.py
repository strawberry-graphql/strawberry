from unittest.mock import patch

import pytest
from graphql import validate

import strawberry
from strawberry.extensions import ValidationCache


@patch("strawberry.schema.schema.validate", wraps=validate)
def test_validation_cache_extension(mock_validate):
    @strawberry.type
    class Query:
        @strawberry.field
        def hello(self) -> str:
            return "world"

        @strawberry.field
        def ping(self) -> str:
            return "pong"

    schema = strawberry.Schema(query=Query, extensions=[ValidationCache()])

    query = "query { hello }"

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data == {"hello": "world"}

    assert mock_validate.call_count == 1

    # Run query multiple times
    for _ in range(3):
        result = schema.execute_sync(query)
        assert not result.errors
        assert result.data == {"hello": "world"}

    # validate is still only called once
    assert mock_validate.call_count == 1

    # Running a second query doesn't cache
    query2 = "query { ping }"
    result = schema.execute_sync(query2)

    assert not result.errors
    assert result.data == {"ping": "pong"}

    assert mock_validate.call_count == 2


@patch("strawberry.schema.schema.validate", wraps=validate)
def test_validation_cache_extension_max_size(mock_validate):
    @strawberry.type
    class Query:
        @strawberry.field
        def hello(self) -> str:
            return "world"

        @strawberry.field
        def ping(self) -> str:
            return "pong"

    schema = strawberry.Schema(query=Query, extensions=[ValidationCache(maxsize=1)])

    query = "query { hello }"

    for _ in range(2):
        result = schema.execute_sync(query)
        assert not result.errors
        assert result.data == {"hello": "world"}

    assert mock_validate.call_count == 1

    query2 = "query { ping }"
    result = schema.execute_sync(query2)

    assert not result.errors
    assert mock_validate.call_count == 2

    # running the first query again doesn't cache
    result = schema.execute_sync(query)
    assert not result.errors

    # validate is still only called once
    assert mock_validate.call_count == 3


@pytest.mark.asyncio
async def test_validation_cache_extension_async():
    @strawberry.type
    class Query:
        @strawberry.field
        def hello(self) -> str:
            return "world"

        @strawberry.field
        def ping(self) -> str:
            return "pong"

    schema = strawberry.Schema(query=Query, extensions=[ValidationCache()])

    query = "query { hello }"

    with patch("strawberry.schema.schema.validate", wraps=validate) as mock_validate:
        result = await schema.execute(query)

        assert not result.errors
        assert result.data == {"hello": "world"}

        assert mock_validate.call_count == 1

        # Run query multiple times
        for _ in range(3):
            result = await schema.execute(query)
            assert not result.errors
            assert result.data == {"hello": "world"}

        # validate is still only called once
        assert mock_validate.call_count == 1

        # Running a second query doesn't cache
        query2 = "query { ping }"
        result = await schema.execute(query2)

        assert not result.errors
        assert result.data == {"ping": "pong"}

        assert mock_validate.call_count == 2
