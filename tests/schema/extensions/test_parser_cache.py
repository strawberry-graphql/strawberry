from unittest.mock import patch

import pytest
from graphql import SourceLocation, parse

import strawberry
from strawberry.extensions import MaxTokensLimiter, ParserCache


@patch("strawberry.extensions.parser_cache.parse", wraps=parse)
def test_parser_cache_extension(mock_parse):
    @strawberry.type
    class Query:
        @strawberry.field
        def hello(self) -> str:
            return "world"

        @strawberry.field
        def ping(self) -> str:
            return "pong"

    schema = strawberry.Schema(query=Query, extensions=[ParserCache()])

    query = "query { hello }"

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data == {"hello": "world"}

    assert mock_parse.call_count == 1

    # Run query multiple times
    for _ in range(3):
        result = schema.execute_sync(query)
        assert not result.errors
        assert result.data == {"hello": "world"}

    # validate is still only called once
    assert mock_parse.call_count == 1

    # Running a second query doesn't cache
    query2 = "query { ping }"
    result = schema.execute_sync(query2)

    assert not result.errors
    assert result.data == {"ping": "pong"}

    assert mock_parse.call_count == 2


@patch("strawberry.extensions.parser_cache.parse", wraps=parse)
def test_parser_cache_extension_arguments(mock_parse):
    @strawberry.type
    class Query:
        @strawberry.field
        def hello(self) -> str:
            return "world"

        @strawberry.field
        def ping(self) -> str:
            return "pong"

    schema = strawberry.Schema(
        query=Query, extensions=[MaxTokensLimiter(max_token_count=20), ParserCache()]
    )

    query = "query { hello }"

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data == {"hello": "world"}

    mock_parse.assert_called_with("query { hello }", max_tokens=20)


@patch("strawberry.extensions.parser_cache.parse", wraps=parse)
def test_parser_cache_extension_syntax_error(mock_parse):
    @strawberry.type
    class Query:
        @strawberry.field
        def hello(self) -> str:  # pragma: no cover
            return "world"

    schema = strawberry.Schema(query=Query, extensions=[ParserCache()])

    query = "query { hello"

    result = schema.execute_sync(query)

    assert len(result.errors) == 1
    assert result.errors[0].message == "Syntax Error: Expected Name, found <EOF>."
    assert result.errors[0].locations == [SourceLocation(line=1, column=14)]
    assert mock_parse.call_count == 1


@patch("strawberry.extensions.parser_cache.parse", wraps=parse)
def test_parser_cache_extension_max_size(mock_parse):
    @strawberry.type
    class Query:
        @strawberry.field
        def hello(self) -> str:
            return "world"

        @strawberry.field
        def ping(self) -> str:
            return "pong"

    schema = strawberry.Schema(query=Query, extensions=[ParserCache(maxsize=1)])

    query = "query { hello }"

    for _ in range(2):
        result = schema.execute_sync(query)
        assert not result.errors
        assert result.data == {"hello": "world"}

    assert mock_parse.call_count == 1

    query2 = "query { ping }"
    result = schema.execute_sync(query2)

    assert not result.errors
    assert mock_parse.call_count == 2

    # running the first query again doesn't cache
    result = schema.execute_sync(query)
    assert not result.errors

    # validate is still only called once
    assert mock_parse.call_count == 3


@pytest.mark.asyncio
@patch("strawberry.extensions.parser_cache.parse", wraps=parse)
async def test_parser_cache_extension_async(mock_parse):
    @strawberry.type
    class Query:
        @strawberry.field
        def hello(self) -> str:
            return "world"

        @strawberry.field
        def ping(self) -> str:
            return "pong"

    schema = strawberry.Schema(query=Query, extensions=[ParserCache()])

    query = "query { hello }"

    result = await schema.execute(query)

    assert not result.errors
    assert result.data == {"hello": "world"}

    assert mock_parse.call_count == 1

    # Run query multiple times
    for _ in range(3):
        result = await schema.execute(query)
        assert not result.errors
        assert result.data == {"hello": "world"}

    # validate is still only called once
    assert mock_parse.call_count == 1

    # Running a second query doesn't cache
    query2 = "query { ping }"
    result = await schema.execute(query2)

    assert not result.errors
    assert result.data == {"ping": "pong"}

    assert mock_parse.call_count == 2
