from enum import EnumMeta
from typing import Optional

from strawberry.utils.cached_property import cached_property

from .exception import StrawberryException
from .exception_source import ExceptionSource
from .utils.source_finder import SourceFinder


class NotAStrawberryEnumError(StrawberryException):
    def __init__(self, enum: EnumMeta):
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
