from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING, Optional, Type

from .exception import StrawberryException
from .utils.source_finder import SourceFinder

if TYPE_CHECKING:
    from .exception_source import ExceptionSource


class PrivateStrawberryFieldError(StrawberryException):
    def __init__(self, field_name: str, cls: Type) -> None:
        self.cls = cls
        self.field_name = field_name

        self.message = (
            f"Field {field_name} on type {cls.__name__} cannot be both "
            "private and a strawberry.field"
        )
        self.rich_message = (
            f"`[underline]{self.field_name}[/]` field cannot be both "
            "private and a strawberry.field "
        )
        self.annotation_message = "private field defined here"
        self.suggestion = (
            "To fix this error you should either make the field non private, "
            "or remove the strawberry.field annotation."
        )

        super().__init__(self.message)

    @cached_property
    def exception_source(self) -> Optional[ExceptionSource]:
        if self.cls is None:
            return None  # pragma: no cover

        source_finder = SourceFinder()

        return source_finder.find_class_attribute_from_object(self.cls, self.field_name)
