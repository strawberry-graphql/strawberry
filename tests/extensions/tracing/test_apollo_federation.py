import base64
from unittest.mock import Mock, patch

import pytest

import strawberry
from strawberry.extensions.tracing.apollo_federation import (
    ApolloFederationTracingExtension,
    ApolloFederationTracingExtensionSync,
)


@pytest.fixture
def mock_request_with_ftv1_header():
    """Create a mock request with FTV1 header."""
    request = Mock()
    request.headers = {"apollo-federation-include-trace": "ftv1"}
    return request


@pytest.fixture
def mock_request_without_header():
    """Create a mock request without FTV1 header."""
    request = Mock()
    request.headers = {}
    return request


def test_tracing_sync_with_ftv1_header(mock_request_with_ftv1_header):
    """Test that tracing activates with FTV1 header."""

    @strawberry.type
    class Person:
        name: str = "Alice"

    @strawberry.type
    class Query:
        @strawberry.field
        def person(self) -> Person:
            return Person()

    schema = strawberry.Schema(
        query=Query, extensions=[ApolloFederationTracingExtensionSync]
    )

    query = """
        query {
            person {
                name
            }
        }
    """

    result = schema.execute_sync(
        query, context_value={"request": mock_request_with_ftv1_header}
    )

    assert not result.errors
    assert "ftv1" in result.extensions
    # Verify it's base64 encoded
    ftv1_data = result.extensions["ftv1"]
    assert isinstance(ftv1_data, str)
    # Should be able to decode base64
    decoded = base64.b64decode(ftv1_data)
    assert isinstance(decoded, bytes)
    assert len(decoded) > 0


def test_tracing_sync_without_header(mock_request_without_header):
    """Test that tracing does not activate without FTV1 header."""

    @strawberry.type
    class Person:
        name: str = "Bob"

    @strawberry.type
    class Query:
        @strawberry.field
        def person(self) -> Person:
            return Person()

    schema = strawberry.Schema(
        query=Query, extensions=[ApolloFederationTracingExtensionSync]
    )

    query = """
        query {
            person {
                name
            }
        }
    """

    result = schema.execute_sync(
        query, context_value={"request": mock_request_without_header}
    )

    assert not result.errors
    # Should not have ftv1 in extensions
    assert "ftv1" not in result.extensions


@pytest.mark.asyncio
async def test_tracing_async_with_ftv1_header(mock_request_with_ftv1_header):
    """Test async tracing with FTV1 header."""

    @strawberry.type
    class Person:
        name: str = "Charlie"

    @strawberry.type
    class Query:
        @strawberry.field
        async def person(self) -> Person:
            return Person()

    schema = strawberry.Schema(
        query=Query, extensions=[ApolloFederationTracingExtension]
    )

    query = """
        query {
            person {
                name
            }
        }
    """

    result = await schema.execute(
        query, context_value={"request": mock_request_with_ftv1_header}
    )

    assert not result.errors
    assert "ftv1" in result.extensions
    ftv1_data = result.extensions["ftv1"]
    assert isinstance(ftv1_data, str)
    decoded = base64.b64decode(ftv1_data)
    assert isinstance(decoded, bytes)
    assert len(decoded) > 0


@pytest.mark.asyncio
async def test_tracing_async_without_header(mock_request_without_header):
    """Test async tracing without FTV1 header."""

    @strawberry.type
    class Person:
        name: str = "Diana"

    @strawberry.type
    class Query:
        @strawberry.field
        async def person(self) -> Person:
            return Person()

    schema = strawberry.Schema(
        query=Query, extensions=[ApolloFederationTracingExtension]
    )

    query = """
        query {
            person {
                name
            }
        }
    """

    result = await schema.execute(
        query, context_value={"request": mock_request_without_header}
    )

    assert not result.errors
    assert "ftv1" not in result.extensions


def test_tracing_with_nested_fields(mock_request_with_ftv1_header):
    """Test tracing with nested field resolvers."""

    @strawberry.type
    class Address:
        street: str = "Main St"
        city: str = "Springfield"

    @strawberry.type
    class Person:
        name: str = "Eve"

        @strawberry.field
        def address(self) -> Address:
            return Address()

    @strawberry.type
    class Query:
        @strawberry.field
        def person(self) -> Person:
            return Person()

    schema = strawberry.Schema(
        query=Query, extensions=[ApolloFederationTracingExtensionSync]
    )

    query = """
        query {
            person {
                name
                address {
                    street
                    city
                }
            }
        }
    """

    result = schema.execute_sync(
        query, context_value={"request": mock_request_with_ftv1_header}
    )

    assert not result.errors
    assert "ftv1" in result.extensions


def test_tracing_with_context_dict(mock_request_with_ftv1_header):
    """Test header detection with dict-style context."""

    @strawberry.type
    class Query:
        @strawberry.field
        def hello(self) -> str:
            return "world"

    schema = strawberry.Schema(
        query=Query, extensions=[ApolloFederationTracingExtensionSync]
    )

    result = schema.execute_sync(
        "query { hello }", context_value={"request": mock_request_with_ftv1_header}
    )

    assert not result.errors
    assert "ftv1" in result.extensions


def test_tracing_with_context_object():
    """Test header detection with object-style context."""

    @strawberry.type
    class Query:
        @strawberry.field
        def hello(self) -> str:
            return "world"

    schema = strawberry.Schema(
        query=Query, extensions=[ApolloFederationTracingExtensionSync]
    )

    # Create a context object with request attribute
    context = type("Context", (), {})()
    request = Mock()
    request.headers = {"apollo-federation-include-trace": "ftv1"}
    context.request = request

    result = schema.execute_sync("query { hello }", context_value=context)

    assert not result.errors
    assert "ftv1" in result.extensions


def test_tracing_handles_missing_protobuf():
    """Test graceful handling when protobuf is not installed."""

    @strawberry.type
    class Query:
        @strawberry.field
        def hello(self) -> str:
            return "world"

    schema = strawberry.Schema(
        query=Query, extensions=[ApolloFederationTracingExtensionSync]
    )

    request = Mock()
    request.headers = {"apollo-federation-include-trace": "ftv1"}

    with patch(
        "strawberry.extensions.tracing.apollo_federation._check_protobuf_available",
        side_effect=ImportError("protobuf not installed"),
    ):
        result = schema.execute_sync(
            "query { hello }", context_value={"request": request}
        )

        # Should not error, just not include ftv1
        assert not result.errors
        assert "ftv1" not in result.extensions


def test_tracing_with_case_insensitive_header():
    """Test that header matching is case-insensitive."""

    @strawberry.type
    class Query:
        @strawberry.field
        def hello(self) -> str:
            return "world"

    schema = strawberry.Schema(
        query=Query, extensions=[ApolloFederationTracingExtensionSync]
    )

    request = Mock()
    # Mix of uppercase and lowercase
    request.headers = {"Apollo-Federation-Include-Trace": "FTV1"}

    result = schema.execute_sync("query { hello }", context_value={"request": request})

    assert not result.errors
    assert "ftv1" in result.extensions


def test_tracing_with_wrong_header_value():
    """Test that tracing only activates with correct header value."""

    @strawberry.type
    class Query:
        @strawberry.field
        def hello(self) -> str:
            return "world"

    schema = strawberry.Schema(
        query=Query, extensions=[ApolloFederationTracingExtensionSync]
    )

    request = Mock()
    request.headers = {"apollo-federation-include-trace": "wrong-value"}

    result = schema.execute_sync("query { hello }", context_value={"request": request})

    assert not result.errors
    assert "ftv1" not in result.extensions


def test_tracing_with_no_context():
    """Test that extension handles missing context gracefully."""

    @strawberry.type
    class Query:
        @strawberry.field
        def hello(self) -> str:
            return "world"

    schema = strawberry.Schema(
        query=Query, extensions=[ApolloFederationTracingExtensionSync]
    )

    result = schema.execute_sync("query { hello }", context_value=None)

    assert not result.errors
    assert "ftv1" not in result.extensions


def test_tracing_with_no_request_in_context():
    """Test that extension handles missing request in context."""

    @strawberry.type
    class Query:
        @strawberry.field
        def hello(self) -> str:
            return "world"

    schema = strawberry.Schema(
        query=Query, extensions=[ApolloFederationTracingExtensionSync]
    )

    result = schema.execute_sync("query { hello }", context_value={"other": "data"})

    assert not result.errors
    assert "ftv1" not in result.extensions
