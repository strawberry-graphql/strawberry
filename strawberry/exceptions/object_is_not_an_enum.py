from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING, Optional

from .exception import StrawberryException
from .utils.source_finder import SourceFinder

if TYPE_CHECKING:
    from enum import Enum

    from .exception_source import ExceptionSource


class ObjectIsNotAnEnumError(StrawberryException):
    def __init__(self, cls: type[Enum]) -> None:
        self.cls = cls
        self.message = (
            "strawberry.enum can only be used with subclasses of Enum. "
            f"Provided object {cls.__name__} is not an enum."
        )
        self.rich_message = (
            "strawberry.enum can only be used with subclasses of Enum. "
            f"Provided object `[underline]{cls.__name__}[/]` is not an enum."
        )
        self.annotation_message = "class defined here"
        self.suggestion = (
            "To fix this error, make sure your class is a subclass of enum.Enum."
        )

        super().__init__(self.message)

    @cached_property
    def exception_source(self) -> Optional[ExceptionSource]:
        if self.cls is None:
            return None  # pragma: no cover

        source_finder = SourceFinder()

        return source_finder.find_class_from_object(self.cls)
