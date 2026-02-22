"""Generic error type for Pydantic validation errors in Strawberry GraphQL.

This module provides a generic Error type that can be used to represent
Pydantic validation errors in GraphQL responses.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from strawberry.types.object_type import type as strawberry_type

if TYPE_CHECKING:
    from pydantic import ValidationError


@strawberry_type
class ErrorDetail:
    """Represents a single validation error detail."""

    type: str
    loc: list[str]
    msg: str


@strawberry_type
class Error:
    """Generic error type for Pydantic validation errors."""

    errors: list[ErrorDetail]

    @staticmethod
    def from_validation_error(exc: ValidationError) -> Error:
        """Create an Error instance from a Pydantic ValidationError.

        Args:
            exc: The Pydantic ValidationError to convert

        Returns:
            An Error instance containing all validation errors
        """
        return Error(
            errors=[
                ErrorDetail(
                    type=error["type"],
                    loc=[str(loc) for loc in error["loc"]],
                    msg=error["msg"],
                )
                for error in exc.errors()
            ]
        )
