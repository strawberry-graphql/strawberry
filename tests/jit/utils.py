"""Shared test utilities for JIT compiler tests.

This module provides common functions to eliminate duplication across
the JIT test suite, including result comparison, error type creation,
and test schema factories.
"""

from typing import Any, Optional

import strawberry
from graphql import ExecutionResult, execute, parse
from strawberry.jit import compile_query


def compare_jit_and_standard(
    schema: strawberry.Schema,
    query: str,
    root_value: Any = None,
    variable_values: Optional[dict[str, Any]] = None,
    operation_name: Optional[str] = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Execute a query with both JIT and standard execution, return both results.

    Args:
        schema: Strawberry schema to use
        query: GraphQL query string
        root_value: Root value for execution
        variable_values: Variables for the query
        operation_name: Operation name if query has multiple operations

    Returns:
        Tuple of (jit_result, standard_result) as dictionaries
    """
    # Execute with JIT
    compiled_fn = compile_query(schema, query)
    jit_result = compiled_fn(
        root_value,
        variables=variable_values,
        operation_name=operation_name,
    )

    # Execute with standard GraphQL
    standard_execution = execute(
        schema._schema,
        parse(query),
        root_value=root_value,
        variable_values=variable_values,
        operation_name=operation_name,
    )

    # Handle both sync and async execution results
    if isinstance(standard_execution, ExecutionResult):
        standard_result = standard_execution
    else:
        # It's an awaitable, this shouldn't happen in our sync tests
        raise TypeError("Expected sync execution result")

    # Convert standard result to dict format
    standard_dict = {
        "data": standard_result.data,
        "errors": [
            {
                "message": str(e),
                "path": list(e.path) if e.path else [],
                "locations": [
                    {"line": loc.line, "column": loc.column}
                    for loc in (e.locations or [])
                ],
            }
            for e in (standard_result.errors or [])
        ]
        if standard_result.errors
        else [],
    }

    return jit_result, standard_dict


def assert_jit_matches_standard(
    schema: strawberry.Schema,
    query: str,
    root_value: Any = None,
    variable_values: Optional[dict[str, Any]] = None,
    operation_name: Optional[str] = None,
) -> dict[str, Any]:
    """Execute query with both JIT and standard, assert they match, return result.

    This is the primary test utility for verifying JIT correctness.

    Args:
        schema: Strawberry schema to use
        query: GraphQL query string
        root_value: Root value for execution
        variable_values: Variables for the query
        operation_name: Operation name if query has multiple operations

    Returns:
        The JIT result (since both should match)

    Raises:
        AssertionError: If results don't match
    """
    jit_result, standard_result = compare_jit_and_standard(
        schema, query, root_value, variable_values, operation_name
    )

    # Compare data
    assert jit_result["data"] == standard_result["data"], (
        f"Data mismatch:\n"
        f"JIT:      {jit_result['data']}\n"
        f"Standard: {standard_result['data']}"
    )

    # Compare error count
    jit_errors = jit_result.get("errors", [])
    std_errors = standard_result.get("errors", [])
    assert len(jit_errors) == len(std_errors), (
        f"Error count mismatch:\n"
        f"JIT:      {len(jit_errors)} errors\n"
        f"Standard: {len(std_errors)} errors"
    )

    # Compare error messages (locations may differ slightly)
    for jit_err, std_err in zip(jit_errors, std_errors):
        assert jit_err["message"] == std_err["message"], (
            f"Error message mismatch:\n"
            f"JIT:      {jit_err['message']}\n"
            f"Standard: {std_err['message']}"
        )
        assert jit_err["path"] == std_err["path"], (
            f"Error path mismatch:\n"
            f"JIT:      {jit_err['path']}\n"
            f"Standard: {std_err['path']}"
        )

    return jit_result


def create_error_type(
    field_name: str = "errorField",
    nullable: bool = True,
    error_message: str = "Field error",
    is_async: bool = False,
):
    """Factory for creating types with error fields for testing.

    Args:
        field_name: Name of the error field
        nullable: Whether the error field is nullable
        error_message: Error message to raise
        is_async: Whether the error field is async

    Returns:
        A Strawberry type class with the error field

    Example:
        >>> ErrorType = create_error_type("broken", nullable=False)
        >>> @strawberry.type
        >>> class Query:
        >>>     item: ErrorType
    """
    if is_async:
        if nullable:

            @strawberry.type
            class AsyncErrorTypeNullable:
                id: int

                @strawberry.field
                async def error_field(self) -> Optional[str]:
                    raise ValueError(error_message)

            return AsyncErrorTypeNullable
        else:

            @strawberry.type
            class AsyncErrorTypeNonNull:
                id: int

                @strawberry.field
                async def error_field(self) -> str:
                    raise ValueError(error_message)

            return AsyncErrorTypeNonNull
    else:
        if nullable:

            @strawberry.type
            class SyncErrorTypeNullable:
                id: int

                @strawberry.field
                def error_field(self) -> Optional[str]:
                    raise ValueError(error_message)

            return SyncErrorTypeNullable
        else:

            @strawberry.type
            class SyncErrorTypeNonNull:
                id: int

                @strawberry.field
                def error_field(self) -> str:
                    raise ValueError(error_message)

            return SyncErrorTypeNonNull


def create_list_with_errors(
    items: list[Any],
    error_indices: list[int],
    error_message: str = "Item error",
) -> list[Any]:
    """Create a list where specific items will raise errors when accessed.

    Args:
        items: List of items
        error_indices: Indices that should raise errors
        error_message: Error message for failing items

    Returns:
        List with error-raising proxy objects at specified indices

    Example:
        >>> items = create_list_with_errors(
        ...     [Item(id=1), Item(id=2), Item(id=3)],
        ...     error_indices=[1],
        ... )
        >>> # items[1] will raise when accessed
    """

    class ErrorProxy:
        def __getattr__(self, name):
            raise ValueError(error_message)

    result = items.copy()
    for idx in error_indices:
        if 0 <= idx < len(result):
            result[idx] = ErrorProxy()
    return result


__all__ = [
    "compare_jit_and_standard",
    "assert_jit_matches_standard",
    "create_error_type",
    "create_list_with_errors",
]
