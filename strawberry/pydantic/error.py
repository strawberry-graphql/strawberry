"""Errors for pydantic inputs that fail validation."""

from __future__ import annotations

from typing import TYPE_CHECKING

from strawberry.exceptions import StrawberryInputCoercionError
from strawberry.schema.exception_handlers import ExceptionHandler
from strawberry.types.object_type import type as strawberry_type

if TYPE_CHECKING:
    from strawberry.types.field import StrawberryField
    from strawberry.types.info import Info


@strawberry_type
class ValidationIssue:
    """A problem with an input value."""

    location: list[str]
    """GraphQL location of the value, starting with the argument name."""

    message: str

    type: str
    """The pydantic error type, like `string_too_short`."""


@strawberry_type
class ValidationError:
    """The inputs failed validation."""

    issues: list[ValidationIssue]


# all the issues are in the extensions, the message only summarizes them
_MAX_ISSUES_IN_MESSAGE = 5


class InputValidationError(StrawberryInputCoercionError):
    """Raised when a pydantic input fails validation.

    It's an input coercion error, so it's returned as a GraphQL error, with the
    issues in its `validationErrors` extension, unless the field can return a
    `ValidationError` and `PydanticValidationErrorHandler` is used.
    """

    def __init__(self, issues: list[ValidationIssue]) -> None:
        self.issues = issues

        details = "; ".join(
            f"{'.'.join(issue.location)}: {issue.message}"
            if issue.location
            else issue.message
            for issue in issues[:_MAX_ISSUES_IN_MESSAGE]
        )

        if len(issues) > _MAX_ISSUES_IN_MESSAGE:
            details += f" (and {len(issues) - _MAX_ISSUES_IN_MESSAGE} more)"

        super().__init__(
            f"Invalid input: {details}",
            extensions={
                "validationErrors": [
                    {
                        "location": issue.location,
                        "message": issue.message,
                        "type": issue.type,
                    }
                    for issue in issues
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
        return ValidationError(issues=exception.issues)
