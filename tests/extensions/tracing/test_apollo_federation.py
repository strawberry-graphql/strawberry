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


def test_lazy_import_from_public_tracing_module(mock_request_with_ftv1_header):
    """The extensions must be importable via the public lazy `tracing` module."""
    from strawberry.extensions import tracing

    assert tracing.ApolloFederationTracingExtension is ApolloFederationTracingExtension
    assert (
        tracing.ApolloFederationTracingExtensionSync
        is ApolloFederationTracingExtensionSync
    )

    @strawberry.type
    class Query:
        @strawberry.field
        def hello(self) -> str:
            return "world"

    schema = strawberry.Schema(
        query=Query, extensions=[tracing.ApolloFederationTracingExtensionSync]
    )

    result = schema.execute_sync(
        "query { hello }",
        context_value={"request": mock_request_with_ftv1_header},
    )

    assert not result.errors
    assert "ftv1" in result.extensions


def test_tracing_captures_errors_sync(mock_request_with_ftv1_header):
    """Test that errors are captured in FTV1 trace (sync)."""

    @strawberry.type
    class Query:
        @strawberry.field
        def failing(self) -> str:
            raise ValueError("Something went wrong")

    schema = strawberry.Schema(
        query=Query, extensions=[ApolloFederationTracingExtensionSync]
    )

    result = schema.execute_sync(
        "query { failing }", context_value={"request": mock_request_with_ftv1_header}
    )

    # Should have errors in the result
    assert result.errors is not None
    assert len(result.errors) == 1
    assert "Something went wrong" in str(result.errors[0])

    # Should still have ftv1 trace with error encoded
    assert "ftv1" in result.extensions
    ftv1_data = result.extensions["ftv1"]
    decoded = base64.b64decode(ftv1_data)
    assert isinstance(decoded, bytes)
    assert len(decoded) > 0
    # The error message should be in the trace
    assert b"Something went wrong" in decoded


@pytest.mark.asyncio
async def test_tracing_captures_errors_async(mock_request_with_ftv1_header):
    """Test that errors are captured in FTV1 trace (async)."""

    @strawberry.type
    class Query:
        @strawberry.field
        async def failing(self) -> str:
            raise ValueError("Async error occurred")

    schema = strawberry.Schema(
        query=Query, extensions=[ApolloFederationTracingExtension]
    )

    result = await schema.execute(
        "query { failing }", context_value={"request": mock_request_with_ftv1_header}
    )

    # Should have errors in the result
    assert result.errors is not None
    assert len(result.errors) == 1
    assert "Async error occurred" in str(result.errors[0])

    # Should still have ftv1 trace with error encoded
    assert "ftv1" in result.extensions
    ftv1_data = result.extensions["ftv1"]
    decoded = base64.b64decode(ftv1_data)
    assert isinstance(decoded, bytes)
    assert len(decoded) > 0
    # The error message should be in the trace
    assert b"Async error occurred" in decoded


def test_tracing_captures_nested_errors(mock_request_with_ftv1_header):
    """Test that errors in nested resolvers are captured."""

    @strawberry.type
    class Person:
        name: str = "Alice"

        @strawberry.field
        def failing_field(self) -> str:
            raise RuntimeError("Nested resolver failed")

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
                failingField
            }
        }
    """

    result = schema.execute_sync(
        query, context_value={"request": mock_request_with_ftv1_header}
    )

    assert result.errors is not None
    assert len(result.errors) == 1
    assert "Nested resolver failed" in str(result.errors[0])

    # Should still have ftv1 trace
    assert "ftv1" in result.extensions
    decoded = base64.b64decode(result.extensions["ftv1"])
    assert b"Nested resolver failed" in decoded


def test_tracing_error_json_includes_path(mock_request_with_ftv1_header):
    """Test that error JSON includes the field path."""

    @strawberry.type
    class Person:
        name: str = "Alice"

        @strawberry.field
        def failing_field(self) -> str:
            raise RuntimeError("Path test error")

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
                failingField
            }
        }
    """

    result = schema.execute_sync(
        query, context_value={"request": mock_request_with_ftv1_header}
    )

    assert result.errors is not None
    decoded = base64.b64decode(result.extensions["ftv1"])

    # Verify JSON field contains path information
    assert b'"path"' in decoded
    assert b"failingField" in decoded
    assert b"person" in decoded


def test_simple_error_serialization():
    """Test _SimpleError serializes all fields correctly."""
    from strawberry.extensions.tracing.apollo_federation import _SimpleError

    error = _SimpleError(
        message="Test error",
        location_line=5,
        location_column=10,
        json_error='{"message":"Test error","path":["query","field"]}',
    )
    serialized = error.SerializeToString()

    # Verify message is in serialized output
    assert b"Test error" in serialized
    # Verify JSON content is in serialized output
    assert b'"path"' in serialized
    assert b'"message"' in serialized


def test_tracing_captures_multiple_errors(mock_request_with_ftv1_header):
    """Test that multiple errors in a single query are all captured."""

    @strawberry.type
    class Query:
        @strawberry.field
        def failing_one(self) -> str | None:
            raise ValueError("First error")

        @strawberry.field
        def failing_two(self) -> str | None:
            raise ValueError("Second error")

    schema = strawberry.Schema(
        query=Query, extensions=[ApolloFederationTracingExtensionSync]
    )

    query = """
        query {
            failingOne
            failingTwo
        }
    """

    result = schema.execute_sync(
        query, context_value={"request": mock_request_with_ftv1_header}
    )

    # Should have both errors (nullable fields allow independent failures)
    assert result.errors is not None
    assert len(result.errors) == 2

    # Both error messages should be in the trace
    assert "ftv1" in result.extensions
    decoded = base64.b64decode(result.extensions["ftv1"])
    assert b"First error" in decoded
    assert b"Second error" in decoded


def test_tracing_error_location_encoding(mock_request_with_ftv1_header):
    """Test that error location (line/column) is encoded in FTV1 trace."""
    from strawberry.extensions.tracing.apollo_federation import (
        _SimpleError,
    )

    # Unit test: verify location encoding in _SimpleError
    error = _SimpleError(
        message="Location test",
        location_line=3,
        location_column=15,
        json_error='{"message":"Location test"}',
    )
    serialized = error.SerializeToString()

    # Field 2 (location) should be present with wire type 2 (length-delimited)
    # 0x12 = (2 << 3) | 2 = field 2, wire type 2
    assert b"\x12" in serialized

    # Integration test: verify location is captured from actual query
    @strawberry.type
    class Query:
        @strawberry.field
        def failing(self) -> str:
            raise ValueError("Location error")

    schema = strawberry.Schema(
        query=Query, extensions=[ApolloFederationTracingExtensionSync]
    )

    result = schema.execute_sync(
        "query { failing }", context_value={"request": mock_request_with_ftv1_header}
    )

    assert result.errors is not None
    decoded = base64.b64decode(result.extensions["ftv1"])

    # The location field marker (0x12) should be in the trace
    assert b"\x12" in decoded
    # The JSON should contain locations array
    assert b'"locations"' in decoded
    assert b'"line"' in decoded
    assert b'"column"' in decoded
