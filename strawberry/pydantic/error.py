"""Generic error type for Pydantic validation errors in Strawberry GraphQL.

This module provides a generic Error type that can be used to represent
Pydantic validation errors in GraphQL responses.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from strawberry.types.object_type import type as strawberry_type

if TYPE_CHECKING:
    from pydantic import ValidationError

    from strawberry.types.field import StrawberryField
    from strawberry.types.info import Info


def _get_validation_error_types() -> tuple[type[BaseException], ...]:
    from pydantic import ValidationError

    error_types: list[type[BaseException]] = [ValidationError]

    try:
        from pydantic.v1 import ValidationError as V1ValidationError
    except ImportError:
        pass
    else:
        if V1ValidationError is not ValidationError:
            error_types.append(V1ValidationError)

    return tuple(error_types)


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


class PydanticValidationErrorHandler:
    exception_types = _get_validation_error_types()
    error_types = (Error,)

    def handle_exception(
        self,
        exception: Exception,
        *,
        field: StrawberryField,
        info: Info,
    ) -> Error:
        return Error.from_validation_error(exception)
