"""Errors for pydantic inputs that fail validation."""

from __future__ import annotations

from typing import TYPE_CHECKING

from strawberry.exceptions import StrawberryInputCoercionError
from strawberry.schema.exception_handlers import ExceptionHandler
from strawberry.types.field import field
from strawberry.types.object_type import type as strawberry_type

if TYPE_CHECKING:
    from strawberry.types.field import StrawberryField
    from strawberry.types.info import Info


@strawberry_type(description="A problem with an input value.")
class ValidationErrorDetail:
    """A problem with an input value."""

    location: list[str] = field(
        description=("The argument, then field names and list indexes, all as strings.")
    )
    message: str = field(description="The reason the value is invalid.")
    type: str = field(description="The Pydantic error type, like `string_too_short`.")


@strawberry_type(description="The inputs failed validation.")
class ValidationError:
    """The inputs failed validation."""

    errors: list[ValidationErrorDetail] = field(
        description="The problems with the input values."
    )


# all the errors are in the extensions, the message only summarizes them
_MAX_ERRORS_IN_MESSAGE = 5


class InputValidationError(StrawberryInputCoercionError):
    """Raised when a pydantic input fails validation.

    It's an input coercion error, so it's returned as a GraphQL error, with the
    errors in its `validationErrors` extension, unless the field can return a
    `ValidationError` and `PydanticValidationErrorHandler` is used.

    Its `errors` are the `ValidationErrorDetail`s of the problems with the input.
    """

    def __init__(self, errors: list[ValidationErrorDetail]) -> None:
        self.errors = errors

        details = "; ".join(
            f"{'.'.join(error.location)}: {error.message}"
            if error.location
            else error.message
            for error in errors[:_MAX_ERRORS_IN_MESSAGE]
        )

        if len(errors) > _MAX_ERRORS_IN_MESSAGE:
            details += f" (and {len(errors) - _MAX_ERRORS_IN_MESSAGE} more)"

        super().__init__(
            f"Invalid input: {details}",
            extensions={
                "validationErrors": [
                    {
                        "location": error.location,
                        "message": error.message,
                        "type": error.type,
                    }
                    for error in errors
                ]
            },
        )


class PydanticValidationErrorHandler(
    ExceptionHandler[InputValidationError, ValidationError]
):
    """Returns `ValidationError` for invalid pydantic inputs.

    Only fields that can return a `ValidationError` are affected, for example
    `-> User | strawberry.pydantic.ValidationError`.
    """

    def handle(
        self,
        exception: InputValidationError,
        *,
        field: StrawberryField,
        info: Info,
    ) -> ValidationError | None:
        return ValidationError(errors=exception.errors)
