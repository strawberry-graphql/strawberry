"""Comprehensive mutation error tests for JIT compiler.

Tests error handling in mutations with focus on:
- Non-nullable vs nullable field errors
- Serial execution semantics with errors
- Async mutation errors
- Partial results in mutations
"""

import pytest

import strawberry
from strawberry.jit import compile_query


@strawberry.type
class MutationResult:
    """Result type with nullable success field."""

    success: bool
    message: str
    data: str | None = None


@strawberry.type
class Mutation:
    @strawberry.mutation
    def nullable_error_mutation(self) -> MutationResult | None:
        """Nullable mutation that always errors."""
        raise ValueError("This mutation always errors")

    @strawberry.mutation
    def non_nullable_error_mutation(self) -> MutationResult:
        """Non-nullable mutation that always errors."""
        raise ValueError("This non-nullable mutation always errors")

    @strawberry.mutation
    def success_mutation(self, value: str) -> MutationResult:
        """Mutation that succeeds."""
        return MutationResult(
            success=True, message=f"Success with {value}", data=value
        )

    @strawberry.mutation
    def error_in_result_field(self) -> MutationResult:
        """Mutation that succeeds but has error in nested field."""
        return MutationResult(success=True, message="Root succeeds", data=None)

    @strawberry.mutation
    async def async_error_mutation(self) -> MutationResult:
        """Async mutation that errors."""
        raise ValueError("Async mutation error")

    @strawberry.mutation
    async def async_success_mutation(self, value: str) -> MutationResult:
        """Async mutation that succeeds."""
        return MutationResult(
            success=True, message=f"Async success with {value}", data=value
        )

    @strawberry.mutation
    def partial_error_mutation(self) -> MutationResult:
        """Mutation with error in a nullable field."""

        class ResultWithError(MutationResult):
            @strawberry.field
            def error_field(self) -> str | None:
                raise ValueError("Field error")

        return ResultWithError(success=True, message="Partial success", data="data")


@strawberry.type
class Query:
    @strawberry.field
    def hello(self) -> str:
        return "Hello"


def test_nullable_mutation_error():
    """Test error in nullable mutation field.

    When a nullable mutation errors, it should return null for that
    mutation and include the error in the errors array.
    """
    schema = strawberry.Schema(query=Query, mutation=Mutation)

    query = """
    mutation TestNullableError {
        nullableErrorMutation {
            success
            message
        }
    }
    """

    compiled = compile_query(schema, query)
    result = compiled(Mutation())

    # Nullable mutation should return null
    assert result["data"]["nullableErrorMutation"] is None
    assert "errors" in result
    assert len(result["errors"]) == 1
    assert "This mutation always errors" in result["errors"][0]["message"]
    assert result["errors"][0]["path"] == ["nullableErrorMutation"]


def test_non_nullable_mutation_error():
    """Test error in non-nullable mutation field.

    When a non-nullable mutation errors, the entire data should be null
    and the error should be included.
    """
    schema = strawberry.Schema(query=Query, mutation=Mutation)

    query = """
    mutation TestNonNullableError {
        nonNullableErrorMutation {
            success
            message
        }
    }
    """

    compiled = compile_query(schema, query)
    result = compiled(Mutation())

    # Non-nullable mutation error should propagate to root
    assert result["data"] is None
    assert "errors" in result
    assert len(result["errors"]) == 1
    assert "This non-nullable mutation always errors" in result["errors"][0]["message"]


def test_multiple_mutations_with_errors_serial():
    """Test multiple mutations with errors execute serially.

    Mutations should execute in order. If one errors, subsequent mutations
    should still execute (unless the error propagates to root).
    """
    schema = strawberry.Schema(query=Query, mutation=Mutation)

    query = """
    mutation TestSerialErrors {
        first: successMutation(value: "first") {
            success
            message
            data
        }
        second: nullableErrorMutation {
            success
            message
        }
        third: successMutation(value: "third") {
            success
            message
            data
        }
    }
    """

    compiled = compile_query(schema, query)
    result = compiled(Mutation())

    # First should succeed
    assert result["data"]["first"]["success"] is True
    assert result["data"]["first"]["data"] == "first"

    # Second should be null (nullable error)
    assert result["data"]["second"] is None

    # Third should still succeed (serial execution continues)
    assert result["data"]["third"]["success"] is True
    assert result["data"]["third"]["data"] == "third"

    # Should have one error
    assert "errors" in result
    assert len(result["errors"]) == 1


@pytest.mark.asyncio
async def test_async_mutation_error():
    """Test error in async mutation."""
    schema = strawberry.Schema(query=Query, mutation=Mutation)

    query = """
    mutation TestAsyncError {
        asyncErrorMutation {
            success
            message
        }
    }
    """

    compiled = compile_query(schema, query)
    result = await compiled(Mutation())

    # Non-nullable async mutation error propagates to root
    assert result["data"] is None
    assert "errors" in result
    assert len(result["errors"]) == 1
    assert "Async mutation error" in result["errors"][0]["message"]


@pytest.mark.asyncio
async def test_multiple_async_mutations_serial():
    """Test that multiple async mutations execute serially, not in parallel."""
    schema = strawberry.Schema(query=Query, mutation=Mutation)

    query = """
    mutation TestAsyncSerial {
        first: asyncSuccessMutation(value: "first") {
            success
            data
        }
        second: asyncSuccessMutation(value: "second") {
            success
            data
        }
    }
    """

    compiled = compile_query(schema, query)
    result = await compiled(Mutation())

    # Both should succeed
    assert result["data"]["first"]["success"] is True
    assert result["data"]["first"]["data"] == "first"
    assert result["data"]["second"]["success"] is True
    assert result["data"]["second"]["data"] == "second"

    # No errors
    assert "errors" not in result


def test_mutation_stops_on_non_nullable_error():
    """Test that mutations stop executing after a non-nullable field error.

    When a non-nullable mutation field errors and propagates to root,
    subsequent mutations should not execute.
    """
    schema = strawberry.Schema(query=Query, mutation=Mutation)

    # Track execution order
    execution_log = []

    @strawberry.type
    class TrackedMutation:
        @strawberry.mutation
        def first(self) -> MutationResult:
            execution_log.append("first")
            return MutationResult(success=True, message="First")

        @strawberry.mutation
        def error_mutation(self) -> MutationResult:
            execution_log.append("error")
            raise ValueError("Error stops execution")

        @strawberry.mutation
        def third(self) -> MutationResult:
            execution_log.append("third")
            return MutationResult(success=True, message="Third")

    schema = strawberry.Schema(query=Query, mutation=TrackedMutation)

    query = """
    mutation TestStopOnError {
        first {
            success
        }
        errorMutation {
            success
        }
        third {
            success
        }
    }
    """

    compiled = compile_query(schema, query)
    result = compiled(TrackedMutation())

    # First should execute
    assert "first" in execution_log

    # Error mutation should execute
    assert "error" in execution_log

    # Third should NOT execute because error propagated to root
    # (In GraphQL, when data becomes null, execution stops)
    assert result["data"] is None


def test_error_in_nested_mutation_field():
    """Test error in a nested field within mutation result.

    Errors in nested fields should be collected properly.
    """

    @strawberry.type
    class NestedResult:
        success: bool
        nested_data: str | None

        @strawberry.field
        def error_field(self) -> str | None:
            raise ValueError("Nested field error")

    @strawberry.type
    class MutationWithNested:
        @strawberry.mutation
        def mutation_with_nested_error(self) -> NestedResult:
            return NestedResult(success=True, nested_data="data")

    schema = strawberry.Schema(query=Query, mutation=MutationWithNested)

    query = """
    mutation TestNestedError {
        mutationWithNestedError {
            success
            nestedData
            errorField
        }
    }
    """

    compiled = compile_query(schema, query)
    result = compiled(MutationWithNested())

    # Mutation should succeed
    assert result["data"]["mutationWithNestedError"]["success"] is True
    assert result["data"]["mutationWithNestedError"]["nestedData"] == "data"

    # Error field should be null
    assert result["data"]["mutationWithNestedError"]["errorField"] is None

    # Should have error
    assert "errors" in result
    assert len(result["errors"]) == 1
    assert "Nested field error" in result["errors"][0]["message"]


def test_mutation_with_variables_error():
    """Test mutation error handling with variables."""
    schema = strawberry.Schema(query=Query, mutation=Mutation)

    query = """
    mutation TestVariableError($value: String!) {
        success: successMutation(value: $value) {
            success
            data
        }
    }
    """

    compiled = compile_query(schema, query)

    # Missing required variable should cause error
    result = compiled(Mutation(), variables={})

    assert "errors" in result
    assert len(result["errors"]) > 0


def test_mutation_partial_success():
    """Test mutations where some fields succeed and others error."""
    schema = strawberry.Schema(query=Query, mutation=Mutation)

    query = """
    mutation TestPartialSuccess {
        success1: successMutation(value: "one") {
            success
            data
        }
        error: nullableErrorMutation {
            success
        }
        success2: successMutation(value: "two") {
            success
            data
        }
    }
    """

    compiled = compile_query(schema, query)
    result = compiled(Mutation())

    # Successes should return data
    assert result["data"]["success1"]["success"] is True
    assert result["data"]["success1"]["data"] == "one"
    assert result["data"]["success2"]["success"] is True
    assert result["data"]["success2"]["data"] == "two"

    # Error should be null
    assert result["data"]["error"] is None

    # Should have one error
    assert "errors" in result
    assert len(result["errors"]) == 1
