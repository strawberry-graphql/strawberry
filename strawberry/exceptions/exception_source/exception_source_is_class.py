from typing import Optional, Type

from ..utils.source_finder import SourceFinder
from .exception_source import ExceptionSource


class ExceptionSourceIsClass(Exception):
    cls: Type

    def __init__(self, message: str) -> None:
        super().__init__(message)

    @property
    def exception_source(self) -> Optional[ExceptionSource]:
        if self.cls is None:
            return None

        source_finder = SourceFinder()

        return source_finder.find_class_from_object(self.cls)
