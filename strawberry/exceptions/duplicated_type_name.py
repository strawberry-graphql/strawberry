from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Type

from strawberry.utils.cached_property import cached_property

from .exception import StrawberryException
from .exception_source import ExceptionSource
from .utils.source_finder import SourceFinder

if TYPE_CHECKING:
    from rich.console import RenderableType


class DuplicatedTypeName(StrawberryException):
    """Raised when the same type with different definition is reused inside a schema"""

    def __init__(
        self,
        first_cls: Optional[Type],
        second_cls: Optional[Type],
        duplicated_type_name: str,
    ):
        self.first_cls = first_cls
        self.second_cls = second_cls

        self.message = (
            f"Type {duplicated_type_name} is defined multiple times in the schema"
        )

        self.rich_message = (
            f"Type `[underline]{duplicated_type_name}[/]` "
            "is defined multiple times in the schema"
        )

        self.suggestion = (
            "To fix this error you should either rename the type or "
            "remove the duplicated definition."
        )

        super().__init__(self.message)

    @property
    def __rich_body__(self) -> RenderableType:
        if self.first_cls is None or self.second_cls is None:
            return ""

        from rich.console import Group

        source_finder = SourceFinder()

        first_class_source = self.exception_source
        assert first_class_source

        second_class_source = source_finder.find_class_from_object(self.second_cls)

        if second_class_source is None:
            return self._get_error_inline(
                first_class_source, "first class defined here"
            )

        return Group(
            self._get_error_inline(first_class_source, "first class defined here"),
            "",
            self._get_error_inline(second_class_source, "second class defined here"),
        )

    @cached_property
    def exception_source(self) -> Optional[ExceptionSource]:
        if self.first_cls is None:
            return None  # pragma: no cover

        source_finder = SourceFinder()

        return source_finder.find_class_from_object(self.first_cls)
