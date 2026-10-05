from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING, Literal

from .exception import StrawberryException
from .utils.source_finder import SourceFinder

if TYPE_CHECKING:
    from .exception_source import ExceptionSource


class InvalidOneOfInputFieldError(StrawberryException):
    """A field of a OneOf input type that clients couldn't set on its own.

    GraphQL requires the fields of a OneOf input type to be nullable and without
    a default, as clients set exactly one of them.
    """

    def __init__(
        self,
        field_name: str,
        cls: type,
        type_name: str,
        problem: Literal["required", "default"],
    ) -> None:
        self.cls = cls
        self.field_name = field_name

        if problem == "required":
            reason = "must be nullable"
            self.annotation_message = "this field is required"
        else:
            reason = "can't have a default value"
            self.annotation_message = "this field has a default value"

        self.message = (
            f"Field `{field_name}` of the OneOf input type `{type_name}` {reason}"
        )
        self.rich_message = (
            f"Field `[underline]{field_name}[/]` of the OneOf input type "
            f"`[underline]{type_name}[/]` {reason}"
        )
        self.suggestion = (
            "Clients set exactly one field of a OneOf input type, so GraphQL "
            "requires its fields to be nullable and without a default value. Make "
            "it nullable and remove its default, for example by declaring it as "
            f"`{field_name}: strawberry.Maybe[...]`."
        )

        super().__init__(self.message)

    @cached_property
    def exception_source(self) -> ExceptionSource | None:
        source_finder = SourceFinder()

        return source_finder.find_class_attribute_from_object(self.cls, self.field_name)
