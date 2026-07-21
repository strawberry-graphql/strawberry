from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING

from .exception import StrawberryException
from .utils.source_finder import SourceFinder

if TYPE_CHECKING:
    from .exception_source import ExceptionSource


class MultipleStrawberryFieldsError(StrawberryException):
    def __init__(self, field_name: str, cls: type) -> None:
        self.cls = cls
        self.field_name = field_name

        self.message = (
            f"Annotation for field `{field_name}` on type `{cls.__name__}` "
            "cannot have multiple `strawberry.field`s"
        )
        self.rich_message = (
            f"Field `[underline]{self.field_name}[/]` on type "
            f"`[underline]{self.cls.__name__}[/]` cannot have multiple "
            "`strawberry.field`s"
        )
        self.annotation_message = "field with multiple strawberry.field annotations"
        self.suggestion = (
            "To fix this error you should use only one `strawberry.field()` "
            "in the `Annotated` type annotation."
        )

        super().__init__(self.message)

    @cached_property
    def exception_source(self) -> ExceptionSource | None:
        if self.cls is None:
            return None  # pragma: no cover

        source_finder = SourceFinder()

        return source_finder.find_class_attribute_from_object(self.cls, self.field_name)
