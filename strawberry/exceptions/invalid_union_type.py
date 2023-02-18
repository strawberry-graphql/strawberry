from __future__ import annotations

from inspect import getframeinfo, stack
from pathlib import Path
from typing import TYPE_CHECKING, Optional, Type

from strawberry.exceptions.utils.source_finder import SourceFinder
from strawberry.utils.cached_property import cached_property

from .exception import StrawberryException

if TYPE_CHECKING:
    from strawberry.union import StrawberryUnion

    from .exception_source import ExceptionSource


class InvalidUnionTypeError(StrawberryException):
    """The union is constructed with an invalid type"""

    invalid_type: object

    def __init__(self, union_name: str, invalid_type: object) -> None:
        from strawberry.custom_scalar import ScalarWrapper

        self.union_name = union_name
        self.invalid_type = invalid_type

        # assuming that the exception happens two stack frames above the current one.
        # one is our code checking for invalid types, the other is the caller
        self.frame = getframeinfo(stack()[2][0])

        if isinstance(invalid_type, ScalarWrapper):
            type_name = invalid_type.wrap.__name__
        else:
            type_name = invalid_type.__name__  # type: ignore

        self.message = f"Type `{type_name}` cannot be used in a GraphQL Union"
        self.rich_message = (
            f"Type `[underline]{type_name}[/]` cannot be used in a GraphQL Union"
        )
        self.suggestion = (
            "To fix this error you should replace the type a strawberry.type"
        )
        self.annotation_message = "invalid type here"

    @cached_property
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

        other_name = getattr(other, "__name__", str(other))

        self.message = f"`{other_name}` cannot be used when merging GraphQL Unions"
        self.rich_message = (
            f"`[underline]{other_name}[/]` cannot be used when merging GraphQL Unions"
        )
        self.suggestion = ""
        self.annotation_message = "invalid type here"

    @cached_property
    def exception_source(self) -> Optional[ExceptionSource]:
        source_finder = SourceFinder()

        return source_finder.find_union_merge(self.union, self.other, frame=self.frame)
