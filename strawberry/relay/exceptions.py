from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING, Optional, Type

from strawberry.exceptions.exception import StrawberryException
from strawberry.exceptions.utils.source_finder import SourceFinder

if TYPE_CHECKING:
    from strawberry.exceptions.exception_source import ExceptionSource


class NodeIDAnnotationError(StrawberryException):
    def __init__(self, message: str, cls: Type) -> None:
        self.cls = cls

        self.message = message
        self.rich_message = (
            "Expected exactly one `relay.NodeID` annotated field to be "
            f"defined in `[underline]{self.cls.__name__}[/]` type."
        )
        self.suggestion = (
            "To fix this error you should annotate exactly one of your fields "
            "using `relay.NodeID`. That field should be unique among "
            "your type objects (usually its `id` for ORM objects)."
        )
        self.annotation_message = "node missing node id private annotation"

        super().__init__(self.message)

    @cached_property
    def exception_source(self) -> Optional[ExceptionSource]:
        if self.cls is None:
            return None  # pragma: no cover

        source_finder = SourceFinder()

        return source_finder.find_class_from_object(self.cls)


__all__ = ["NodeIDAnnotationError"]
