"""Test custom scalar support in JIT compiler."""

import base64
from datetime import datetime
from typing import NewType

from graphql import execute_sync, parse

import strawberry
from strawberry.jit import compile_query

# Define custom scalars
Base64Encoded = strawberry.scalar(
    NewType("Base64Encoded", bytes),
    serialize=lambda v: base64.b64encode(v).decode("ascii")
    if isinstance(v, bytes)
    else v,
    parse_value=lambda v: base64.b64decode(v) if isinstance(v, str) else v,
)


DateTimeScalar = strawberry.scalar(
    NewType("DateTime", datetime),
    serialize=lambda v: v.isoformat() if isinstance(v, datetime) else str(v),
    parse_value=lambda v: datetime.fromisoformat(v) if isinstance(v, str) else v,
)


CaseInsensitiveString = strawberry.scalar(
    NewType("CaseInsensitiveString", str),
    serialize=lambda v: v.upper() if isinstance(v, str) else str(v),
    parse_value=lambda v: v.lower() if isinstance(v, str) else str(v),
)


def test_custom_scalar_serialization():
    """Test that custom scalars are properly serialized in output."""

    @strawberry.type
    class Query:
        @strawberry.field
        def encoded_data(self) -> Base64Encoded:
            return Base64Encoded(b"Hello World")

        @strawberry.field
        def current_time(self) -> DateTimeScalar:
            return DateTimeScalar(datetime(2023, 1, 1, 12, 0, 0))

        @strawberry.field
        def case_test(self) -> CaseInsensitiveString:
            return "hello"  # Will be serialized to uppercase

    schema = strawberry.Schema(Query)

    # Test Base64 scalar
    query = "{ encodedData }"

    # Standard execution
    result = execute_sync(schema._schema, parse(query))
    standard_data = result.data

    # JIT execution
    compiled_fn = compile_query(schema, query)
    jit_result = compiled_fn(None)

    assert jit_result["encodedData"] == standard_data["encodedData"]
    assert base64.b64decode(jit_result["encodedData"]) == b"Hello World"

    # Test DateTime scalar
    query = "{ currentTime }"

    # Standard execution
    result = execute_sync(schema._schema, parse(query))
    standard_data = result.data

    # JIT execution
    compiled_fn = compile_query(schema, query)
    jit_result = compiled_fn(None)

    assert jit_result["currentTime"] == standard_data["currentTime"]
    assert jit_result["currentTime"] == "2023-01-01T12:00:00"

    # Test CaseInsensitive scalar
    query = "{ caseTest }"

    # Standard execution
    result = execute_sync(schema._schema, parse(query))
    standard_data = result.data

    # JIT execution
    compiled_fn = compile_query(schema, query)
    jit_result = compiled_fn(None)

    assert jit_result["caseTest"] == standard_data["caseTest"]
    assert jit_result["caseTest"] == "HELLO"  # Serialized to uppercase

    print("✅ Custom scalar serialization works")


def test_custom_scalar_deserialization():
    """Test that custom scalars are properly parsed from input."""

    @strawberry.type
    class Query:
        @strawberry.field
        def decode_base64(self, data: Base64Encoded) -> str:
            return bytes(data).decode("utf-8")

        @strawberry.field
        def format_date(self, date: DateTimeScalar) -> str:
            return date.strftime("%Y-%m-%d")

        @strawberry.field
        def echo_case(self, text: CaseInsensitiveString) -> str:
            return text  # Already lowercased by parse_value

    schema = strawberry.Schema(Query)

    # Test Base64 input with variables
    query = """query DecodeData($data: Base64Encoded!) {
        decodeBase64(data: $data)
    }"""

    encoded = base64.b64encode(b"Hello JIT").decode("ascii")
    variables = {"data": encoded}

    # Standard execution
    result = execute_sync(schema._schema, parse(query), variable_values=variables)
    standard_data = result.data

    # JIT execution
    compiled_fn = compile_query(schema, query)
    jit_result = compiled_fn(None, variables=variables)

    assert jit_result["decodeBase64"] == standard_data["decodeBase64"]
    assert jit_result["decodeBase64"] == "Hello JIT"

    # Test DateTime input
    query = """query FormatDate($date: DateTime!) {
        formatDate(date: $date)
    }"""

    variables = {"date": "2023-06-15T14:30:00"}

    # Standard execution
    result = execute_sync(schema._schema, parse(query), variable_values=variables)
    standard_data = result.data

    # JIT execution
    compiled_fn = compile_query(schema, query)
    jit_result = compiled_fn(None, variables=variables)

    assert jit_result["formatDate"] == standard_data["formatDate"]
    assert jit_result["formatDate"] == "2023-06-15"

    # Test CaseInsensitive input with inline value
    query = """{
        echoCase(text: "UPPERCASE")
    }"""

    # Standard execution
    result = execute_sync(schema._schema, parse(query))
    standard_data = result.data

    # JIT execution
    compiled_fn = compile_query(schema, query)
    jit_result = compiled_fn(None)

    assert jit_result["echoCase"] == standard_data["echoCase"]
    assert jit_result["echoCase"] == "uppercase"  # Parsed to lowercase

    print("✅ Custom scalar deserialization works")


def test_list_of_custom_scalars():
    """Test lists of custom scalars."""

    @strawberry.type
    class Query:
        @strawberry.field
        def encode_multiple(self) -> list[Base64Encoded]:
            return [
                Base64Encoded(b"First"),
                Base64Encoded(b"Second"),
                Base64Encoded(b"Third"),
            ]

        @strawberry.field
        def decode_multiple(self, encoded: list[Base64Encoded]) -> list[str]:
            return [bytes(e).decode("utf-8") for e in encoded]

    schema = strawberry.Schema(Query)

    # Test list output
    query = "{ encodeMultiple }"

    # Standard execution
    result = execute_sync(schema._schema, parse(query))
    standard_data = result.data

    # JIT execution
    compiled_fn = compile_query(schema, query)
    jit_result = compiled_fn(None)

    assert jit_result["encodeMultiple"] == standard_data["encodeMultiple"]
    assert len(jit_result["encodeMultiple"]) == 3
    assert base64.b64decode(jit_result["encodeMultiple"][0]) == b"First"

    # Test list input
    query = """query DecodeMultiple($encoded: [Base64Encoded!]!) {
        decodeMultiple(encoded: $encoded)
    }"""

    variables = {
        "encoded": [
            base64.b64encode(b"One").decode("ascii"),
            base64.b64encode(b"Two").decode("ascii"),
            base64.b64encode(b"Three").decode("ascii"),
        ]
    }

    # Standard execution
    result = execute_sync(schema._schema, parse(query), variable_values=variables)
    standard_data = result.data

    # JIT execution
    compiled_fn = compile_query(schema, query)
    jit_result = compiled_fn(None, variables=variables)

    assert jit_result["decodeMultiple"] == standard_data["decodeMultiple"]
    assert jit_result["decodeMultiple"] == ["One", "Two", "Three"]

    print("✅ List of custom scalars works")


def test_nested_custom_scalars():
    """Test custom scalars in nested types."""

    @strawberry.type
    class EncodedMessage:
        content: Base64Encoded
        timestamp: DateTimeScalar

    @strawberry.type
    class Query:
        @strawberry.field
        def get_message(self) -> EncodedMessage:
            return EncodedMessage(
                content=Base64Encoded(b"Secret Message"),
                timestamp=DateTimeScalar(datetime(2023, 12, 25, 0, 0, 0)),
            )

    schema = strawberry.Schema(Query)

    query = "{ getMessage { content timestamp } }"

    # Standard execution
    result = execute_sync(schema._schema, parse(query))
    standard_data = result.data

    # JIT execution
    compiled_fn = compile_query(schema, query)
    jit_result = compiled_fn(None)

    assert jit_result == standard_data
    assert base64.b64decode(jit_result["getMessage"]["content"]) == b"Secret Message"
    assert jit_result["getMessage"]["timestamp"] == "2023-12-25T00:00:00"

    print("✅ Nested custom scalars work")


def test_nullable_custom_scalars():
    """Test nullable custom scalars."""

    from typing import Optional

    @strawberry.type
    class Query:
        @strawberry.field
        def maybe_encoded(self, return_null: bool = False) -> Optional[Base64Encoded]:
            if return_null:
                return None
            return Base64Encoded(b"Not null")

        @strawberry.field
        def process_optional(self, data: Optional[Base64Encoded] = None) -> str:
            if data is None:
                return "No data"
            return bytes(data).decode("utf-8")

    schema = strawberry.Schema(Query)

    # Test nullable output
    query = "{ maybeEncoded(returnNull: true) }"

    # Standard execution
    result = execute_sync(schema._schema, parse(query))
    standard_data = result.data

    # JIT execution
    compiled_fn = compile_query(schema, query)
    jit_result = compiled_fn(None)

    assert jit_result == standard_data
    assert jit_result["maybeEncoded"] is None

    # Test with non-null value
    query = "{ maybeEncoded(returnNull: false) }"

    # Standard execution
    result = execute_sync(schema._schema, parse(query))
    standard_data = result.data

    # JIT execution
    compiled_fn = compile_query(schema, query)
    jit_result = compiled_fn(None)

    assert jit_result == standard_data
    assert base64.b64decode(jit_result["maybeEncoded"]) == b"Not null"

    # Test nullable input
    query = "{ processOptional }"

    # Standard execution
    result = execute_sync(schema._schema, parse(query))
    standard_data = result.data

    # JIT execution
    compiled_fn = compile_query(schema, query)
    jit_result = compiled_fn(None)

    assert jit_result == standard_data
    assert jit_result["processOptional"] == "No data"

    print("✅ Nullable custom scalars work")


def test_custom_scalar_errors():
    """Test error handling with custom scalars."""

    FailingScalar = strawberry.scalar(
        NewType("FailingScalar", str),
        serialize=lambda v: 1 / 0,  # Always fails
        parse_value=lambda v: v,
    )

    @strawberry.type
    class Query:
        @strawberry.field
        def failing_field(self) -> FailingScalar:
            return "test"

    schema = strawberry.Schema(Query)

    query = "{ failingField }"

    # Standard execution
    result = execute_sync(schema._schema, parse(query))
    assert result.errors

    # JIT execution
    compiled_fn = compile_query(schema, query)
    jit_result = compiled_fn(None)

    assert "errors" in jit_result
    assert len(jit_result["errors"]) > 0

    print("✅ Custom scalar error handling works")


if __name__ == "__main__":
    test_custom_scalar_serialization()
    test_custom_scalar_deserialization()
    test_list_of_custom_scalars()
    test_nested_custom_scalars()
    test_nullable_custom_scalars()
    test_custom_scalar_errors()

    print("\n✅ All custom scalar tests passed!")
