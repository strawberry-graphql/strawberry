from __future__ import annotations

from typing import Optional, Type

from .exception import StrawberryException
from .exception_source import ExceptionSource
from .utils.source_finder import SourceFinder


class DuplicatedTypeName(StrawberryException):
    """Raised when the same type with different definition is reused inside a schema"""

    def __init__(self, cls: Optional[Type], duplicated_type_name: str):
        self.cls = cls

        self.message = (
            f"Type {duplicated_type_name} is defined multiple times in the schema"
        )

        self.rich_message = (
            f"Type `[underline]{duplicated_type_name}[/]` "
            "is defined multiple times in the schema"
        )

        self.annotation_message = "class defined here"
        self.suggestion = (
            "To fix this error you should either rename the type or "
            "remove the duplicated definition."
        )

        super().__init__(self.message)

    @property
    def exception_source(self) -> Optional[ExceptionSource]:
        if self.cls is None:
            return None  # pragma: no cover

        source_finder = SourceFinder()

        return source_finder.find_class_from_object(self.cls)
