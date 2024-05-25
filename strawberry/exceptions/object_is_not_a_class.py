from __future__ import annotations

from enum import Enum
from functools import cached_property
from typing import TYPE_CHECKING, Optional

from .exception import StrawberryException
from .utils.source_finder import SourceFinder

if TYPE_CHECKING:
    from .exception_source import ExceptionSource


class ObjectIsNotClassError(StrawberryException):
    class MethodType(Enum):
        INPUT = "input"
        INTERFACE = "interface"
        TYPE = "type"

    def __init__(self, obj: object, method_type: MethodType) -> None:
        self.obj = obj
        self.function = obj

        # TODO: assert obj is a function for now and skip the error if it is
        # something else
        obj_name = obj.__name__  # type: ignore

        self.message = (
            f"strawberry.{method_type.value} can only be used with class types. "
            f"Provided object {obj_name} is not a type."
        )

        self.rich_message = (
            f"strawberry.{method_type.value} can only be used with class types. "
            f"Provided object `[underline]{obj_name}[/]` is not a type."
        )

        self.annotation_message = "function defined here"
        self.suggestion = (
            "To fix this error, make sure your use "
            f"strawberry.{method_type.value} on a class."
        )

        super().__init__(self.message)

    @classmethod
    def input(cls, obj: object) -> ObjectIsNotClassError:
        return cls(obj, cls.MethodType.INPUT)

    @classmethod
    def interface(cls, obj: object) -> ObjectIsNotClassError:
        return cls(obj, cls.MethodType.INTERFACE)

    @classmethod
    def type(cls, obj: object) -> ObjectIsNotClassError:
        return cls(obj, cls.MethodType.TYPE)

    @cached_property
    def exception_source(self) -> Optional[ExceptionSource]:
        if self.function is None:
            return None  # pragma: no cover

        source_finder = SourceFinder()

        return source_finder.find_function_from_object(self.function)  # type: ignore
