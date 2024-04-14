from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING, Optional

from .exception import StrawberryException
from .utils.source_finder import SourceFinder

if TYPE_CHECKING:
    from enum import EnumMeta

    from .exception_source import ExceptionSource


class NotAStrawberryEnumError(StrawberryException):
    def __init__(self, enum: EnumMeta) -> None:
        self.enum = enum

        self.message = f'Enum "{enum.__name__}" is not a Strawberry enum.'
        self.rich_message = (
            f"Enum `[underline]{enum.__name__}[/]` is not a Strawberry enum."
        )
        self.suggestion = (
            "To fix this error you can declare the enum using `@strawberry.enum`."
        )

        self.annotation_message = "enum defined here"

        super().__init__(self.message)

    @cached_property
    def exception_source(self) -> Optional[ExceptionSource]:
        if self.enum is None:
            return None  # pragma: no cover

        source_finder = SourceFinder()

        return source_finder.find_class_from_object(self.enum)
