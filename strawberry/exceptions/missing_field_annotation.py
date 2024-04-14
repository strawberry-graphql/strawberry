from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING, Optional, Type

from .exception import StrawberryException
from .utils.source_finder import SourceFinder

if TYPE_CHECKING:
    from .exception_source import ExceptionSource


class MissingFieldAnnotationError(StrawberryException):
    def __init__(self, field_name: str, cls: Type) -> None:
        self.cls = cls
        self.field_name = field_name

        self.message = (
            f'Unable to determine the type of field "{field_name}". Either '
            f"annotate it directly, or provide a typed resolver using "
            f"@strawberry.field."
        )
        self.rich_message = (
            f"Missing annotation for field `[underline]{self.field_name}[/]`"
        )
        self.suggestion = (
            "To fix this error you can add an annotation, "
            f"like so [italic]`{self.field_name}: str`"
        )
        self.annotation_message = "field missing annotation"

        super().__init__(self.message)

    @cached_property
    def exception_source(self) -> Optional[ExceptionSource]:
        if self.cls is None:
            return None  # pragma: no cover

        source_finder = SourceFinder()

        return source_finder.find_class_attribute_from_object(self.cls, self.field_name)
