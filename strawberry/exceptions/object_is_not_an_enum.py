from enum import Enum
from typing import Type

from .exception import StrawberryException
from .exception_source import ExceptionSourceIsClass


class ObjectIsNotAnEnumError(ExceptionSourceIsClass, StrawberryException):
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
