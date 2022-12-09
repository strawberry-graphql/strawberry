from enum import Enum
from typing import Optional, Type

from strawberry.utils.cached_property import cached_property

from .exception import StrawberryException
from .exception_source import ExceptionSource
from .utils.source_finder import SourceFinder


class ObjectIsNotAnEnumError(StrawberryException):
    def __init__(self, cls: Type[Enum]):
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
