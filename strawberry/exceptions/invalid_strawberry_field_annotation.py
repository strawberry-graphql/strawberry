from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING

from .exception import StrawberryException
from .utils.source_finder import SourceFinder

if TYPE_CHECKING:
    from .exception_source import ExceptionSource


class InvalidStrawberryFieldAnnotationError(StrawberryException):
    def __init__(self, field_name: str, cls: type) -> None:
        self.cls = cls
        self.field_name = field_name

        self.message = (
            f"`strawberry.field()` for field `{field_name}` on type `{cls.__name__}` "
            "must be placed at the top level of the field annotation"
        )
        self.rich_message = (
            f"`strawberry.field()` for field `[underline]{field_name}[/]` on type "
            f"`[underline]{cls.__name__}[/]` cannot be nested inside another type"
        )
        self.annotation_message = "strawberry.field() is nested inside another type"
        self.suggestion = (
            "To fix this error, move `strawberry.field()` to the outermost "
            "`Annotated` metadata for the field."
        )

        super().__init__(self.message)

    @cached_property
    def exception_source(self) -> ExceptionSource | None:
        source_finder = SourceFinder()

        return source_finder.find_class_attribute_from_object(self.cls, self.field_name)
