from __future__ import annotations

from inspect import getframeinfo, stack
from pathlib import Path
from typing import TYPE_CHECKING, Optional, Type

from strawberry.exceptions.utils.source_finder import SourceFinder

from .exception import StrawberryException
from .exception_source import ExceptionSource


if TYPE_CHECKING:
    from strawberry.union import StrawberryUnion


class InvalidUnionTypeError(StrawberryException):
    """The union is constructed with an invalid type"""

    invalid_type: Type

    def __init__(self, union_name: str, invalid_type: Type) -> None:
        self.union_name = union_name
        self.invalid_type = invalid_type

        # assuming that the exception happens two stack frames above the current one.
        # one is our code checking for invalid types, the other is the caller
        self.frame = getframeinfo(stack()[2][0])

        type_name = invalid_type.__name__

        self.message = f"Type `{type_name}` cannot be used in a GraphQL Union"
        self.rich_message = (
            f"Type `[underline]{type_name}[/]` cannot be used in a GraphQL Union"
        )
        self.suggestion = (
            "To fix this error you should replace the type a strawberry.type"
        )
        self.annotation_message = "invalid type here"

    @property
    def exception_source(self) -> Optional[ExceptionSource]:
        path = Path(self.frame.filename)

        source_finder = SourceFinder()

        return source_finder.find_union_call(path, self.union_name, self.invalid_type)


class InvalidTypeForUnionMergeError(StrawberryException):
    """A specialized version of InvalidUnionTypeError for when trying
    to merge unions using the pipe operator."""

    invalid_type: Type

    def __init__(self, union: StrawberryUnion, other: object) -> None:
        self.union = union
        self.other = other

        # assuming that the exception happens two stack frames above the current one.
        # one is our code checking for invalid types, the other is the caller
        self.frame = getframeinfo(stack()[2][0])

        type_name = "LOL this is a todo"

        self.message = f"Type `{type_name}` cannot be used in a GraphQL Union"
        self.rich_message = (
            f"Type `[underline]{type_name}[/]` cannot be used in a GraphQL Union"
        )
        self.suggestion = (
            "To fix this error you should replace the type a strawberry.type"
        )
        self.annotation_message = "invalid type here"

    @property
    def exception_source(self) -> Optional[ExceptionSource]:
        source_finder = SourceFinder()

        return source_finder.find_union_merge(self.union, self.other, frame=self.frame)
