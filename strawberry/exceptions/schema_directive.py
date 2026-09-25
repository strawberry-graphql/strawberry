from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING, Any

from .exception import StrawberryException
from .utils.source_finder import SourceFinder

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

    from strawberry.schema_directive import Location

    from .exception_source import ExceptionSource


class _SchemaDirectiveApplicationError(StrawberryException):
    def __init__(
        self,
        message: str,
        *,
        suggestion: str,
        source: type | Callable[..., Any] | None,
        source_attribute: str | None,
        source_argument: str | None,
    ) -> None:
        self.rich_message = message
        self.annotation_message = "directive applied here"
        self.suggestion = suggestion
        self.source = source
        self.source_attribute = source_attribute
        self.source_argument = source_argument

        super().__init__(message)

    @cached_property
    def exception_source(self) -> ExceptionSource | None:
        source_finder = SourceFinder()

        if self.source_argument is not None and callable(self.source):
            return source_finder.find_argument_from_object(
                self.source, self.source_argument
            )

        if self.source_attribute is not None and isinstance(self.source, type):
            return source_finder.find_class_attribute_from_object(
                self.source, self.source_attribute
            )

        if isinstance(self.source, type):
            return source_finder.find_class_from_object(self.source)

        return None


class InvalidSchemaDirectiveLocationError(_SchemaDirectiveApplicationError):
    def __init__(
        self,
        directive_name: str,
        location: Location,
        element: str,
        allowed_locations: Iterable[Location],
        *,
        source: type | Callable[..., Any] | None = None,
        source_attribute: str | None = None,
        source_argument: str | None = None,
    ) -> None:
        allowed = ", ".join(location.name for location in allowed_locations) or "none"
        message = (
            f"Schema directive '@{directive_name}' cannot be applied to "
            f"{location.name} schema element '{element}'. Allowed locations: "
            f"{allowed}."
        )

        super().__init__(
            message,
            suggestion=(
                f"Add Location.{location.name} to the directive's locations or "
                "move the directive to a supported schema element."
            ),
            source=source,
            source_attribute=source_attribute,
            source_argument=source_argument,
        )


class DuplicateSchemaDirectiveError(_SchemaDirectiveApplicationError):
    def __init__(
        self,
        directive_name: str,
        location: Location,
        element: str,
        *,
        source: type | Callable[..., Any] | None = None,
        source_attribute: str | None = None,
        source_argument: str | None = None,
    ) -> None:
        message = (
            f"Schema directive '@{directive_name}' is not repeatable and cannot be "
            f"applied more than once to {location.name} schema element '{element}'."
        )

        super().__init__(
            message,
            suggestion=(
                "Remove the duplicate application or define the directive with "
                "repeatable=True."
            ),
            source=source,
            source_attribute=source_attribute,
            source_argument=source_argument,
        )


__all__ = [
    "DuplicateSchemaDirectiveError",
    "InvalidSchemaDirectiveLocationError",
]
